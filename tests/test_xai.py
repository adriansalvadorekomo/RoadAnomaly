"""Grad-CAM and the deletion / insertion check on small synthetic models."""
import numpy as np

from roadanomaly import xai
from roadanomaly.inference import Predictor


def test_seg_grad_cam_is_normalised(segmentation_dir, random_images):
    model = Predictor(segmentation_dir).model
    region = np.zeros(random_images.shape[1:3], bool); region[8:16, 8:24] = True
    cam, raw_max = xai.grad_cam(model, random_images[0], "features", xai.logit_target(region),
                                output_name="anomaly_logits")
    assert cam.shape == region.shape and cam.min() >= 0 and cam.max() <= 1 + 1e-6 and raw_max >= 0


def test_autoencoder_grad_cam(pixel_ae_dir, random_images):
    model = Predictor(pixel_ae_dir).model
    region = np.ones(random_images.shape[1:3], bool)
    cam, _ = xai.grad_cam(model, random_images[0], "code", xai.reconstruction_target(region))
    assert cam.shape == region.shape and np.isfinite(cam).all()


def test_deletion_insertion_shapes(random_images):
    heatmap = np.random.default_rng(0).random(random_images.shape[1:3])
    results = xai.deletion_insertion(lambda batch: batch.mean(axis=(1, 2, 3)), random_images[0], heatmap,
                                     block=8, fractions=np.linspace(0, 1, 3))
    assert set(results) == {"attribution", "random_1", "random_2", "random_3"}
    assert len(results["attribution"]["deletion"]) == 3
    # nothing deleted: the deletion curve starts at the score of the original image
    assert results["attribution"]["deletion"][0] == float(random_images[0].mean())


def test_perceptual_autoencoder_trains_one_step():
    """Regression: a method named like a keras.Model internal broke train_step."""
    import keras
    from roadanomaly.models import autoencoder as pixel_ae
    features = keras.Sequential([keras.Input((16, 16, 3)), keras.layers.Conv2D(2, 3)])
    features.trainable = False
    model = pixel_ae.PerceptualAutoencoder(pixel_ae.build_autoencoder((4, 8)), features, perceptual_weight=0.1)
    model.compile(optimizer="adam")
    patches = np.random.default_rng(0).random((4, 16, 16, 3), dtype=np.float32)
    history = model.fit(patches, patches, epochs=1, batch_size=2, verbose=0).history
    assert {"loss", "mae", "perceptual_loss"} <= set(history)


def test_default_segmentation_layer(segmentation_dir):
    from roadanomaly.models.deeplabv3plus import build_deeplabv3plus
    assert xai.default_segmentation_layer(Predictor(segmentation_dir).model) == "features"
    assert xai.default_segmentation_layer(build_deeplabv3plus((64, 64, 3), weights=None)) == "decoder_2"


def test_grad_cam_plus_plus_is_normalised(segmentation_dir, random_images):
    model = Predictor(segmentation_dir).model
    region = np.zeros(random_images.shape[1:3], bool); region[8:16, 8:24] = True
    cam, raw_max = xai.grad_cam(model, random_images[0], "features", xai.logit_target(region),
                                output_name="anomaly_logits", method="gradcam++")
    assert cam.shape == region.shape and cam.min() >= 0 and cam.max() <= 1 + 1e-6 and raw_max >= 0


def test_factor_shapley_is_exact_and_attributes_the_right_factor(random_images):
    image = random_images[0]
    region = np.zeros(image.shape[:2], bool); region[8:20, 16:40] = True
    # a score that only depends on colour saturation: only "colour" may receive attribution
    score = lambda batch: (batch.max(axis=-1) - batch.min(axis=-1)).mean(axis=(1, 2))
    what = xai.factor_shapley(score, image, region)
    assert what["evaluations"] == 32 and what["efficiency_gap"] < 1e-9
    assert abs(sum(what["phi"].values()) - (what["full"] - what["base"])) < 1e-9
    assert max(what["phi"], key=lambda f: abs(what["phi"][f])) == "colour"


def test_remove_factors_keeps_the_image_unchanged_when_nothing_is_removed(random_images):
    region = np.zeros(random_images.shape[1:3], bool); region[4:10, 4:10] = True
    assert np.allclose(xai.remove_factors(random_images[0], region, set()), random_images[0])


def test_explain_pairs_where_and_what(pixel_ae_dir, random_images):
    e = xai.explain(Predictor(pixel_ae_dir), random_images[0])
    assert e["where"].shape == random_images.shape[1:3] and set(e["what"]["phi"]) == set(xai.FACTORS)
    assert xai.describe_what(e["what"], "The model").startswith("The model relies most on")
