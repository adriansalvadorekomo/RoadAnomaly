"""Shared fixtures: small synthetic models saved in the shared format (no training, no dataset)."""
import keras
import numpy as np
import pytest
from keras import layers

from roadanomaly.inference import save_artifact

SIZE = (32, 64)


@pytest.fixture(autouse=True)
def _seed():
    keras.utils.set_random_seed(0)


def _config(name, model_type, **extra):
    return {"name": name, "binome": "T", "model_type": model_type,
            "input": {"image_size": list(SIZE), "channels": "RGB", "range": [0, 1]},
            "postprocessing": {"sigma": 1, "per_image_z_score": model_type != "segmentation",
                               "threshold": 0.5, "min_blob_px": 1},
            "validation": {}, **extra}


@pytest.fixture
def segmentation_dir(tmp_path):
    inputs = keras.Input((*SIZE, 3))
    x = layers.Conv2D(4, 3, padding="same", activation="relu", name="features")(inputs)
    logits = layers.Conv2D(1, 1, name="anomaly_logits")(x)
    model = keras.Model(inputs, layers.Activation("sigmoid", name="anomaly_probability")(logits))
    return save_artifact(tmp_path / "seg", model, _config("seg", "segmentation"))


@pytest.fixture
def pixel_ae_dir(tmp_path):
    from roadanomaly.models.autoencoder import build_autoencoder
    model = build_autoencoder((4, 8), code_channels=2)
    return save_artifact(tmp_path / "pixel", model, _config("pixel", "pixel_autoencoder"))


@pytest.fixture
def random_images():
    return np.random.default_rng(0).random((2, *SIZE, 3), dtype=np.float32)
