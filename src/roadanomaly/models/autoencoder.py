"""Binôme B baseline: convolutional autoencoder trained on normal 64x64 pixel patches.

Design (DL notes, Cap. 9): stride-2 convolutions halve the size four times (64 -> 4), a
narrow linear code (4x4x2 = 32 values for 12,288 input values, 384x compression) keeps
only the typical appearance of a road scene, and mirrored transposed convolutions rebuild
the patch. No skip connections: they would bypass the bottleneck (that would be a U-Net).
The network is fully convolutional, so it reconstructs whole 352x640 images at test time.

Loss variants (compared by Khaled on validation): MSE, MAE, SSIM, and MAE + a perceptual
loss on frozen VGG19 features.
"""
from collections.abc import Sequence

import keras
import numpy as np
import tensorflow as tf
from keras import layers

ENCODER_FILTERS = (32, 64, 128, 256)
CODE_CHANNELS = 2
VGG19_PERCEPTUAL_LAYERS = ("block1_conv2", "block2_conv2", "block3_conv2", "block4_conv2", "block5_conv2")


def build_autoencoder(encoder_filters: Sequence[int] = ENCODER_FILTERS, code_channels: int = CODE_CHANNELS):
    """Fully convolutional autoencoder; input size must be divisible by 2 ** len(encoder_filters)."""
    if not encoder_filters or code_channels < 1:
        raise ValueError("the encoder and the code need at least one channel")
    inputs = keras.Input(shape=(None, None, 3), name="image")
    x = inputs
    for index, filters in enumerate(encoder_filters):   # each stride-2 conv halves height and width
        x = layers.Conv2D(filters, 3, strides=2, padding="same", activation="relu", name=f"encoder_{index + 1}")(x)
    # Linear code on purpose: with 2 channels, a "dead" ReLU unit would delete half of the code
    code = layers.Conv2D(code_channels, 3, padding="same", activation=None, name="code")(x)
    x = code
    for index, filters in enumerate(reversed(encoder_filters)):   # each transposed conv doubles the size
        x = layers.Conv2DTranspose(filters, 3, strides=2, padding="same", activation="relu",
                                   name=f"decoder_{index + 1}")(x)
    outputs = layers.Conv2D(3, 3, padding="same", activation="sigmoid", name="reconstruction")(x)
    return keras.Model(inputs, outputs, name="conv_autoencoder")


def reconstruction_error_maps(model, images, batch_size=4):
    """(reconstructions, per-pixel squared error averaged over RGB) for images (N, H, W, 3) in [0, 1]."""
    images = np.asarray(images, dtype=np.float32)
    reconstructions = model.predict(images, batch_size=batch_size, verbose=0)
    return reconstructions, ((images - reconstructions) ** 2).mean(axis=-1)


def ssim_loss(targets, reconstructions):
    """1 - SSIM per example, for RGB images in [0, 1]."""
    return 1.0 - tf.image.ssim(targets, reconstructions, max_val=1.0)


def compile_reconstruction_loss(model, loss_name, learning_rate):
    """Compile with Adam and one of the reconstruction losses 'mse', 'mae' or 'ssim'."""
    losses = {"mse": "mse", "mae": "mae", "ssim": ssim_loss}
    if loss_name not in losses:
        raise ValueError(f"unknown loss {loss_name!r}; choose from {sorted(losses)}")
    model.compile(optimizer=keras.optimizers.Adam(learning_rate), loss=losses[loss_name])


def build_vgg19_feature_model(patch_size=64, layer_names=VGG19_PERCEPTUAL_LAYERS):
    """Frozen ImageNet VGG19 returning the activations used by the perceptual loss."""
    backbone = keras.applications.VGG19(include_top=False, weights="imagenet", input_shape=(patch_size, patch_size, 3))
    backbone.trainable = False
    features = keras.Model(backbone.input, [backbone.get_layer(n).output for n in layer_names],
                           name="frozen_vgg19_features")
    features.trainable = False
    return features


class PerceptualAutoencoder(keras.Model):
    """Trains an autoencoder with MAE plus, optionally, a perceptual loss on frozen VGG19 features.

    perceptual loss = mean over layers of |f(x) - f(x_hat)| / |f(x)| (scale-free per layer).
    Only the autoencoder's weights are updated; the feature model must be frozen.
    """

    def __init__(self, reconstruction_model, feature_model=None, perceptual_weight=0.0):
        super().__init__()
        if perceptual_weight < 0:
            raise ValueError("the perceptual weight must be >= 0")
        if feature_model is not None and feature_model.trainable:
            raise ValueError("the feature model must be frozen")
        self.reconstruction_model = reconstruction_model
        self.feature_model = feature_model
        self.perceptual_weight = perceptual_weight
        self.total_tracker = keras.metrics.Mean(name="loss")
        self.pixel_tracker = keras.metrics.Mean(name="mae")
        self.perceptual_tracker = keras.metrics.Mean(name="perceptual_loss")

    @property
    def metrics(self):
        return [self.total_tracker, self.pixel_tracker, self.perceptual_tracker]

    def call(self, inputs, training=False):
        return self.reconstruction_model(inputs, training=training)

    def _loss_terms(self, inputs, targets, training):
        reconstruction = self.reconstruction_model(inputs, training=training)
        pixel_loss = tf.reduce_mean(tf.abs(targets - reconstruction))
        perceptual_loss = tf.constant(0.0, dtype=pixel_loss.dtype)
        if self.feature_model is not None:
            preprocess = keras.applications.vgg19.preprocess_input
            target_features = tf.nest.flatten(self.feature_model(preprocess(targets * 255.0), training=False))
            recon_features = tf.nest.flatten(self.feature_model(preprocess(reconstruction * 255.0), training=False))
            per_layer = [tf.reduce_mean(tf.abs(t - r)) / (tf.reduce_mean(tf.abs(t)) + keras.backend.epsilon())
                         for t, r in zip(target_features, recon_features, strict=True)]
            perceptual_loss = tf.reduce_mean(tf.stack(per_layer))
        return pixel_loss + self.perceptual_weight * perceptual_loss, pixel_loss, perceptual_loss

    def _update_trackers(self, total, pixel, perceptual):
        self.total_tracker.update_state(total)
        self.pixel_tracker.update_state(pixel)
        self.perceptual_tracker.update_state(perceptual)
        return {m.name: m.result() for m in self.metrics}

    def train_step(self, data):
        inputs, targets, _ = keras.utils.unpack_x_y_sample_weight(data)
        with tf.GradientTape() as tape:
            total, pixel, perceptual = self._loss_terms(inputs, targets, training=True)
        variables = self.reconstruction_model.trainable_variables
        self.optimizer.apply_gradients(zip(tape.gradient(total, variables), variables, strict=True))
        return self._update_trackers(total, pixel, perceptual)

    def test_step(self, data):
        inputs, targets, _ = keras.utils.unpack_x_y_sample_weight(data)
        return self._update_trackers(*self._loss_terms(inputs, targets, training=False))
