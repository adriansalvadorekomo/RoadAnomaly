"""Binôme C builders, losses and the flip test-time augmentation of the Predictor."""
import json

import numpy as np
import pytest

from roadanomaly import losses, xai
from roadanomaly.inference import Predictor
from roadanomaly.models.cnn import build_cnn_baseline
from roadanomaly.models.unet import build_unet, build_unet_resnet50

SHAPE = (64, 128, 3)


@pytest.mark.parametrize("builder", [build_cnn_baseline, build_unet,
                                     lambda shape: build_unet_resnet50(shape, weights=None)])
def test_builders_follow_the_shared_format(builder):
    model = builder(SHAPE)
    out = model(np.random.default_rng(0).random((2, *SHAPE), dtype=np.float32), training=False).numpy()
    assert out.shape == (2, *SHAPE[:2], 1) and out.min() >= 0 and out.max() <= 1
    names = [layer.name for layer in model.layers]
    assert "anomaly_logits" in names and names[-1] == "anomaly_probability"
    xai.default_segmentation_layer(model)   # Seg-Grad-CAM finds a decoder layer


def test_normalisation_is_inside_the_models():
    cnn = build_cnn_baseline(SHAPE)
    normalised = cnn.get_layer("imagenet_normalisation")(np.full((1, *SHAPE), 0.485, np.float32)).numpy()
    assert abs(normalised[..., 0]).max() < 1e-5   # the ImageNet mean of the red channel maps to 0


def test_unet_resnet50_keeps_encoder_batchnorm_frozen():
    model = build_unet_resnet50(SHAPE, weights=None)
    encoder = model.get_layer("resnet50_encoder")
    batchnorms = [layer for layer in encoder.layers if layer.__class__.__name__ == "BatchNormalization"]
    assert batchnorms and not any(layer.trainable for layer in batchnorms)
    assert any(w.trainable for w in encoder.weights)   # convolutions are fine-tuned


@pytest.mark.parametrize("loss", [losses.dice_loss, losses.bce_dice_loss, losses.focal_loss,
                                  losses.focal_tversky_loss, losses.focal_plus_tversky_loss])
def test_losses_reward_the_right_mask(loss):
    truth = np.zeros((2, 16, 16, 1), np.float32)
    truth[:, 4:10, 4:10] = 1
    good, bad = float(loss(truth, truth)), float(loss(truth, 1 - truth))
    assert good < 0.05 and bad > good + 0.5


def test_tversky_penalises_misses_more_than_false_alarms():
    truth = np.zeros((1, 10, 10, 1), np.float32)
    truth[0, :5] = 1
    missed = truth.copy()
    missed[0, :2] = 0  # 20 anomaly pixels missed
    extra = truth.copy()
    extra[0, 5:7] = 1  # 20 background pixels flagged
    assert float(losses.focal_tversky_loss(truth, missed)) > float(losses.focal_tversky_loss(truth, extra))


def test_flip_tta_option(segmentation_dir, random_images):
    plain = Predictor(segmentation_dir).raw_maps(random_images)
    config_path = segmentation_dir / "config.json"
    config = json.loads(config_path.read_text())
    config["postprocessing"]["tta_flip"] = True
    config_path.write_text(json.dumps(config))
    predictor = Predictor(segmentation_dir)
    with_tta = predictor.raw_maps(random_images)
    mirrored = predictor.model.predict(random_images[:, :, ::-1], verbose=0)[..., 0][:, :, ::-1]
    assert np.allclose(with_tta, (plain + mirrored) / 2, atol=1e-6)
