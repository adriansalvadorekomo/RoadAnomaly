"""Tests de contrat et de non-régression du pipeline du binôme B."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import tensorflow as tf
from keras import layers
from sklearn.metrics import average_precision_score

from roadanomaly import data_pipeline as dp, metrics
from roadanomaly.anomaly_detector import AnomalyDetector

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "models" / "B_best_config.json"
IMAGE_SIZE = (352, 640)


def _load_validation_reference() -> tuple[AnomalyDetector, np.ndarray, np.ndarray, dict]:
    if not CONFIG_PATH.is_file():
        pytest.skip(
            "Artefacts absents : exécuter le notebook d'amélioration pour générer "
            "models/B_best_config.json et son checkpoint."
        )
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    frames, images, masks = dp.load_split("val", IMAGE_SIZE)
    return AnomalyDetector(CONFIG_PATH), images, masks, {
        "config": config,
        "frames": frames,
    }


@pytest.fixture
def synthetic_detector(tmp_path: Path) -> AnomalyDetector:
    """Construit un petit modèle local pour tester le contrat sans données de production."""
    inputs = tf.keras.Input(shape=(None, None, 3))
    code = layers.Conv2D(2, 3, strides=2, padding="same", name="code")(inputs)
    hidden = layers.Conv2DTranspose(4, 3, strides=2, padding="same", activation="relu")(code)
    outputs = layers.Conv2D(3, 1, activation="sigmoid")(hidden)
    model = tf.keras.Model(inputs, outputs)
    model_path = tmp_path / "synthetic.keras"
    model.save(model_path)
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "model_path": model_path.name,
                "image_size": [32, 32],
                "postprocessing": {
                    "sigma": 1,
                    "threshold": 0.0,
                    "min_component_px": 1,
                    "per_image_z_score": True,
                },
            }
        ),
        encoding="utf-8",
    )
    return AnomalyDetector(config_path)


def test_predict_matches_saved_validation_reference() -> None:
    """Compare AuPRC et F1 au point de contrôle enregistré sur validation."""
    detector, images, masks, reference = _load_validation_reference()
    config = reference["config"]
    expected_by_frame = {
        row["frame"]: row for row in config["validation"]["per_image"]
    }
    frame = next(frame for frame in reference["frames"] if frame in expected_by_frame)
    index = reference["frames"].index(frame)
    prediction = detector.predict(images[index])
    truth = masks[index, ..., 0].astype(bool)
    actual_auprc = average_precision_score(
        truth.ravel(), prediction["score_map"].ravel()
    )
    actual_f1 = metrics.segmentation_scores(truth, prediction["mask"])["f1"]
    expected = expected_by_frame[frame]
    assert actual_auprc == pytest.approx(expected["auprc"], abs=1e-6)
    assert actual_f1 == pytest.approx(expected["f1"], abs=1e-6)


def test_predict_output_contract(synthetic_detector: AnomalyDetector) -> None:
    prediction = synthetic_detector.predict(np.zeros((32, 32, 3), dtype=np.float32))
    assert prediction["mask"].shape == (32, 32)
    assert prediction["mask"].dtype == np.uint8
    assert set(np.unique(prediction["mask"])).issubset({0, 1})
    assert prediction["score_map"].shape == (32, 32)
    assert prediction["score_map"].dtype == np.float32
    assert np.isfinite(prediction["score_map"]).all()
    assert prediction["threshold"] == synthetic_detector.threshold
    assert prediction["sigma"] == synthetic_detector.sigma


def test_explain_returns_normalized_validation_heatmap(
    synthetic_detector: AnomalyDetector,
) -> None:
    heatmap = synthetic_detector.explain(np.zeros((32, 32, 3), dtype=np.float32))
    assert heatmap.shape == (32, 32)
    assert heatmap.dtype == np.float32
    assert np.isfinite(heatmap).all()
    assert heatmap.min() >= 0.0
    assert heatmap.max() <= 1.0 + 1e-6


def test_detector_reports_invalid_input_shape(synthetic_detector: AnomalyDetector) -> None:
    with pytest.raises(AssertionError, match="Résolution attendue"):
        synthetic_detector.predict(np.zeros((16, 16, 3), dtype=np.float32))
