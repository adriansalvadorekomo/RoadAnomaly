"""Inférence et diagnostic XAI pour le détecteur d'anomalies du binôme B."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import tensorflow as tf
from keras import Model
from scipy import ndimage

from roadanomaly.metrics import remove_small_components


class AnomalyDetector:
    """Charge un autoencodeur sauvegardé et produit score, masque et Grad-CAM."""

    def __init__(self, config_path: str | Path) -> None:
        """Charge la configuration et le modèle associés."""
        self.config_path = Path(config_path).resolve()
        if not self.config_path.is_file():
            raise FileNotFoundError(f"Configuration introuvable: {self.config_path}")
        self.config: dict[str, Any] = json.loads(self.config_path.read_text(encoding="utf-8"))
        model_value = self.config.get("model_path") or self.config.get("artifacts", {}).get("model_path")
        if not model_value:
            raise ValueError("La configuration doit définir 'model_path'.")
        model_path = Path(model_value)
        if not model_path.is_absolute():
            local_path = (self.config_path.parent / model_path).resolve()
            repository_path = (self.config_path.parent.parent / model_path).resolve()
            model_path = local_path if local_path.is_file() else repository_path
        if not model_path.is_file():
            raise FileNotFoundError(f"Modèle introuvable: {model_path}")
        self.model = tf.keras.models.load_model(model_path, compile=False)

        preprocessing = self.config.get("preprocessing", {})
        self.image_size = tuple(preprocessing.get("image_size_height_width", self.config.get("image_size", (352, 640))))
        postprocessing = self.config.get("postprocessing", self.config.get("anomaly_score", {}))
        self.sigma = float(
            postprocessing.get(
                "sigma",
                postprocessing.get("gaussian_sigma_selected_on_validation", 0),
            )
        )
        self.threshold = float(
            postprocessing.get(
                "threshold",
                postprocessing.get("threshold_selected_on_validation_for_mean_f1"),
            )
        )
        self.min_component_px = int(
            postprocessing.get(
                "min_component_px",
                self.config.get("min_object_px", 4),
            )
        )
        self.z_score = bool(postprocessing.get("per_image_z_score", True))
        if len(self.image_size) != 2 or min(self.image_size) <= 0:
            raise ValueError(f"image_size invalide: {self.image_size}")
        if self.sigma < 0 or self.min_component_px < 1:
            raise ValueError("sigma doit être >= 0 et min_component_px >= 1.")

    def _prepare_image(self, image: np.ndarray) -> np.ndarray:
        image = np.asarray(image)
        assert image.ndim == 3 and image.shape[-1] == 3, "L'image doit être RGB de forme (H,W,3)."
        assert image.shape[:2] == self.image_size, (
            f"Résolution attendue {self.image_size}, reçue {image.shape[:2]}."
        )
        image = image.astype(np.float32, copy=False)
        assert np.isfinite(image).all(), "L'image contient des NaN ou des valeurs infinies."
        assert image.min() >= 0.0 and image.max() <= 1.0, "L'image doit être normalisée dans [0,1]."
        return image

    def _score(self, image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        batch = image[None, ...]
        reconstruction = self.model(batch, training=False).numpy()[0]
        raw_error = np.mean(np.square(image - reconstruction), axis=-1)
        score = raw_error if self.sigma == 0 else ndimage.gaussian_filter(raw_error, self.sigma)
        if self.z_score:
            score_std = float(score.std())
            score = (score - score.mean()) / max(score_std, np.finfo(np.float32).eps)
        return reconstruction.astype(np.float32), score.astype(np.float32)

    def predict(self, image: np.ndarray) -> dict[str, Any]:
        """Prédit une carte de scores et un masque binaire pour une image RGB."""
        image = self._prepare_image(image)
        _, score_map = self._score(image)
        mask = remove_small_components(score_map >= self.threshold, self.min_component_px)
        return {
            "mask": mask.astype(np.uint8),
            "score_map": score_map.astype(np.float32),
            "threshold": self.threshold,
            "sigma": self.sigma,
        }

    def explain(self, image: np.ndarray) -> np.ndarray:
        """Calcule un Grad-CAM du code pour la MSE brute dans la ROI prédite."""
        image = self._prepare_image(image)
        prediction = self.predict(image)
        region = prediction["mask"].astype(np.float32)
        if not region.any():
            score_map = prediction["score_map"]
            region = (score_map >= np.quantile(score_map, 0.99)).astype(np.float32)

        code_model = Model(
            inputs=self.model.inputs,
            outputs=[self.model.get_layer("code").output, self.model.output],
        )
        image_tensor = tf.convert_to_tensor(image[None, ...], dtype=tf.float32)
        region_tensor = tf.convert_to_tensor(region[None, ...], dtype=tf.float32)
        with tf.GradientTape() as tape:
            code, reconstruction = code_model(image_tensor, training=False)
            tape.watch(code)
            raw_error = tf.reduce_mean(tf.square(image_tensor - reconstruction), axis=-1)
            target = tf.math.divide_no_nan(
                tf.reduce_sum(raw_error * region_tensor),
                tf.reduce_sum(region_tensor),
            )
        gradients = tape.gradient(target, code)
        if gradients is None:
            raise RuntimeError("Grad-CAM impossible: gradients absents du bottleneck 'code'.")
        weights = tf.reduce_mean(gradients, axis=(1, 2), keepdims=True)
        heatmap = tf.nn.relu(tf.reduce_sum(weights * code, axis=-1, keepdims=True))
        heatmap = tf.image.resize(heatmap, self.image_size, method="bilinear")[0, ..., 0]
        heatmap = heatmap / (tf.reduce_max(heatmap) + tf.keras.backend.epsilon())
        result = heatmap.numpy().astype(np.float32)
        assert result.shape == self.image_size and np.isfinite(result).all()
        return result
