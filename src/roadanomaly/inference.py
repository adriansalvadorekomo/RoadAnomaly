"""One model format and one Predictor for every binôme (rule 2 of the README).

Each final model is a folder models/<name>/ with:
- model.keras: the trained Keras model;
- config.json: what the model is and every post-processing setting, all chosen on validation;
- feature_stats.npz (feature autoencoder only): the train normal-cell statistics.

The model_type says how a raw score map is computed from an image in [0, 1]:
- "segmentation" (A, C): the model outputs an anomaly probability per pixel;
- "pixel_autoencoder" (B baseline): squared RGB reconstruction error per pixel;
- "feature_autoencoder" (B final): squared reconstruction error of standardised frozen
  ImageNet features per cell (coarse map, upsampled).
Optional `postprocessing.tta_flip` (segmentation): the probability is averaged with the
prediction of the horizontally mirrored image. The same post-processing
(postprocessing.anomaly_scores + to_masks) then gives the score
map and the mask. Notebook 5, the API and the Streamlit demo all go through this class, so
every number in the project comes from the same code path.
"""
import json
import platform
from pathlib import Path

import keras
import numpy as np
import tensorflow as tf
from PIL import Image

from roadanomaly import postprocessing
from roadanomaly.models import feature_ae

FORMAT_VERSION = 1
MODEL_TYPES = ("segmentation", "pixel_autoencoder", "feature_autoencoder")
REQUIRED_KEYS = ("format_version", "name", "binome", "model_type", "model_file", "input", "postprocessing",
                 "validation")
POSTPROCESSING_KEYS = ("sigma", "per_image_z_score", "threshold", "min_blob_px")
FEATURE_STATS_FILE = "feature_stats.npz"


def validate_config(config):
    """Raise ValueError if a config.json does not follow the shared format."""
    missing = [key for key in REQUIRED_KEYS if key not in config]
    if missing:
        raise ValueError(f"config.json is missing {missing}")
    if config["format_version"] != FORMAT_VERSION:
        raise ValueError(f"format_version {config['format_version']} != {FORMAT_VERSION}")
    if config["model_type"] not in MODEL_TYPES:
        raise ValueError(f"model_type must be one of {MODEL_TYPES}, got {config['model_type']!r}")
    missing = [key for key in POSTPROCESSING_KEYS if key not in config["postprocessing"]]
    if missing:
        raise ValueError(f"postprocessing is missing {missing}")
    if config["model_type"] == "feature_autoencoder" and "features" not in config:
        raise ValueError("a feature_autoencoder config needs a 'features' section (backbone, layer)")
    if len(config["input"].get("image_size", ())) != 2:
        raise ValueError("input.image_size must be [height, width]")


def environment():
    """Software and hardware used for a run, stored in every config.json."""
    gpus = tf.config.list_physical_devices("GPU")
    device = tf.config.experimental.get_device_details(gpus[0]).get("device_name", "GPU") if gpus else "CPU"
    return {"python": platform.python_version(), "tensorflow": tf.__version__, "keras": keras.__version__,
            "device": device}


def save_artifact(directory, model, config, feature_stats=None):
    """Write model.keras, config.json (validated) and, if given, the feature statistics."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    config = {"format_version": FORMAT_VERSION, "model_file": "model.keras", **config,
              "environment": environment()}
    validate_config(config)
    model.save(directory / config["model_file"])
    if feature_stats is not None:
        np.savez(directory / FEATURE_STATS_FILE, mean=feature_stats[0], std=feature_stats[1])
    (directory / "config.json").write_text(json.dumps(config, indent=2, default=_to_json), encoding="utf-8")
    return directory


def _to_json(value):
    """JSON encoder for NumPy scalars and arrays."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"not JSON serialisable: {type(value)}")


def available_models(models_dir):
    """Names of the folders of models_dir that contain a config.json, sorted."""
    return sorted(p.parent.name for p in Path(models_dir).glob("*/config.json"))


def prepare_image(image, image_size):
    """Any RGB image (uint8 array or PIL image) -> float32 (H, W, 3) in [0, 1] at image_size.

    Same resizing as the shared loader (bilinear), so API inputs match the training data.
    """
    pil = image if isinstance(image, Image.Image) else Image.fromarray(np.asarray(image, dtype=np.uint8))
    pil = pil.convert("RGB").resize((image_size[1], image_size[0]), Image.BILINEAR)
    return np.asarray(pil, dtype=np.float32) / 255.0


class Predictor:
    """Load one models/<name>/ folder and turn images into score maps and anomaly masks."""

    def __init__(self, directory):
        self.directory = Path(directory)
        self.config = json.loads((self.directory / "config.json").read_text(encoding="utf-8"))
        validate_config(self.config)
        self.name = self.config["name"]
        self.model_type = self.config["model_type"]
        self.image_size = tuple(self.config["input"]["image_size"])
        post = self.config["postprocessing"]
        self.sigma = float(post["sigma"])
        self.z_score = bool(post["per_image_z_score"])
        self.threshold = float(post["threshold"])
        self.min_blob = int(post["min_blob_px"])
        self.tta_flip = bool(post.get("tta_flip", False))   # optional: average with the mirrored image
        self.model = keras.models.load_model(self.directory / self.config["model_file"], compile=False)
        if self.model_type == "feature_autoencoder":
            stats = np.load(self.directory / FEATURE_STATS_FILE)
            self.feature_mean, self.feature_std = stats["mean"], stats["std"]
            self.backbone = self.config["features"]["backbone"]
            self.layer = self.config["features"]["layer"]

    def _check(self, images):
        images = np.asarray(images, dtype=np.float32)
        if images.ndim == 3:
            images = images[None]
        if images.shape[1:] != (*self.image_size, 3):
            raise ValueError(f"expected images of shape (N, {self.image_size[0]}, {self.image_size[1]}, 3), "
                             f"got {images.shape}; use prepare_image() first")
        if not np.isfinite(images).all() or images.min() < 0 or images.max() > 1:
            raise ValueError("images must be finite floats in [0, 1]")
        return images

    def features(self, images):
        """Standardised frozen features (feature autoencoder only)."""
        raw = feature_ae.extract_features(images, self.backbone, self.layer)
        return feature_ae.standardise(raw, self.feature_mean, self.feature_std)

    def raw_maps(self, images, batch_size=2):
        """Raw score maps before post-processing: (N, H, W), or (N, h, w) cells for the feature AE."""
        images = self._check(images)
        if self.model_type == "segmentation":
            probabilities = self.model.predict(images, batch_size=batch_size, verbose=0)[..., 0]
            if self.tta_flip:   # test-time augmentation: mean with the prediction of the mirrored image
                mirrored = self.model.predict(images[:, :, ::-1], batch_size=batch_size, verbose=0)[..., 0]
                probabilities = (probabilities + mirrored[:, :, ::-1]) / 2
            return probabilities
        if self.model_type == "pixel_autoencoder":
            reconstructions = self.model.predict(images, batch_size=batch_size, verbose=0)
            return ((images - reconstructions) ** 2).mean(axis=-1)
        return feature_ae.cell_error_maps(self.model, self.features(images))

    def score_maps(self, images):
        """Post-processed score maps (N, H, W): upsampled, smoothed and z-scored as in config.json."""
        return postprocessing.anomaly_scores(self.raw_maps(images), self.sigma, self.z_score, self.image_size)

    def predict(self, images):
        """{'scores': (N, H, W) float32, 'masks': (N, H, W) uint8} with the validation threshold."""
        scores = self.score_maps(images)
        return {"scores": scores.astype(np.float32),
                "masks": postprocessing.to_masks(scores, self.threshold, self.min_blob).astype(np.uint8)}
