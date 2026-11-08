"""Contract of the shared model format and of the Predictor, plus a regression test on the real models."""
import json
from pathlib import Path

import numpy as np
import pytest
from conftest import SIZE

from roadanomaly import data_pipeline as dp
from roadanomaly.inference import Predictor, available_models, prepare_image, validate_config
from roadanomaly.postprocessing import auprc
from roadanomaly.protocol import IMG_SIZE


@pytest.mark.parametrize("fixture", ["segmentation_dir", "pixel_ae_dir"])
def test_predict_output_contract(fixture, request, random_images):
    predictor = Predictor(request.getfixturevalue(fixture))
    result = predictor.predict(random_images)
    assert result["scores"].shape == result["masks"].shape == (2, *SIZE)
    assert result["scores"].dtype == np.float32 and result["masks"].dtype == np.uint8
    assert set(np.unique(result["masks"])) <= {0, 1}
    assert np.isfinite(result["scores"]).all()


def test_single_image_is_accepted(segmentation_dir, random_images):
    assert Predictor(segmentation_dir).predict(random_images[0])["masks"].shape == (1, *SIZE)


def test_z_score_is_applied_for_autoencoders(pixel_ae_dir, random_images):
    scores = Predictor(pixel_ae_dir).score_maps(random_images)
    assert np.allclose(scores.mean(axis=(1, 2)), 0, atol=1e-4)
    assert np.allclose(scores.std(axis=(1, 2)), 1, atol=1e-3)


def test_wrong_size_and_range_are_rejected(segmentation_dir):
    predictor = Predictor(segmentation_dir)
    with pytest.raises(ValueError, match="expected images"):
        predictor.predict(np.zeros((1, 16, 16, 3), np.float32))
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        predictor.predict(np.full((1, *SIZE, 3), 255, np.float32))


def test_prepare_image_resizes_uint8_to_unit_range():
    image = prepare_image(np.full((720, 1280, 3), 255, np.uint8), SIZE)
    assert image.shape == (*SIZE, 3) and image.dtype == np.float32 and image.max() == 1.0


def test_config_validation(segmentation_dir):
    config = json.loads((segmentation_dir / "config.json").read_text())
    validate_config(config)
    for broken in ({**config, "model_type": "svm"}, {k: v for k, v in config.items() if k != "postprocessing"},
                   {**config, "model_type": "feature_autoencoder"}):
        with pytest.raises(ValueError):
            validate_config(broken)


def test_saved_config_records_environment(segmentation_dir):
    config = json.loads((segmentation_dir / "config.json").read_text())
    assert {"python", "tensorflow", "keras", "device"} <= set(config["environment"])


@pytest.mark.parametrize("name", available_models(dp.MODELS_DIR))
def test_real_models_reproduce_their_validation_auprc(name):
    """Every trained model in models/ must give back the validation AuPRC saved by its notebook."""
    predictor = Predictor(dp.MODELS_DIR / name)
    _, x_val, y_val = dp.load_split("val", IMG_SIZE)
    scores = predictor.score_maps(x_val)
    # 1e-3: saturated sigmoids tie many pixels and float32 GPU kernels reorder ties (~1e-4); real errors are far larger
    assert auprc(y_val[..., 0], scores) == pytest.approx(predictor.config["validation"]["AuPRC"], abs=1e-3)


def test_models_dir_is_inside_the_repository():
    assert Path(dp.MODELS_DIR).parent == dp.REPO_ROOT
