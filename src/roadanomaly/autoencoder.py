"""Composants TensorFlow du baseline autoencodeur du binôme B."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import tensorflow as tf
from keras import Model, layers
from scipy import ndimage

DEFAULT_ENCODER_FILTERS = (32, 64, 128, 256)
DEFAULT_CODE_CHANNELS = 2
DEFAULT_PATCH_SIZE = 64
DEFAULT_PATCH_STRIDE = 32
DEFAULT_MASK_MARGIN = 4


def build_autoencoder(
    encoder_filters: Sequence[int] = DEFAULT_ENCODER_FILTERS,
    code_channels: int = DEFAULT_CODE_CHANNELS,
) -> Model:
    """Construit l'autoencodeur convolutif entièrement convolutionnel."""
    if not encoder_filters or code_channels < 1:
        raise ValueError("L'encodeur et le code doivent avoir au moins un canal.")
    inputs = tf.keras.Input(shape=(None, None, 3), name="image")
    hidden = inputs
    for index, filters in enumerate(encoder_filters):
        hidden = layers.Conv2D(
            filters,
            3,
            strides=2,
            padding="same",
            activation="relu",
            name=f"encoder_{index + 1}",
        )(hidden)
    code = layers.Conv2D(
        code_channels,
        3,
        padding="same",
        activation=None,
        name="code",
    )(hidden)
    hidden = code
    for index, filters in enumerate(reversed(encoder_filters)):
        hidden = layers.Conv2DTranspose(
            filters,
            3,
            strides=2,
            padding="same",
            activation="relu",
            name=f"decoder_{index + 1}",
        )(hidden)
    outputs = layers.Conv2D(3, 3, padding="same", activation="sigmoid", name="reconstruction")(hidden)
    return tf.keras.Model(inputs, outputs, name="conv_autoencoder")


def extract_normal_patches(
    images: np.ndarray,
    masks: np.ndarray,
    patch_size: int = DEFAULT_PATCH_SIZE,
    stride: int = DEFAULT_PATCH_STRIDE,
    mask_margin: int = DEFAULT_MASK_MARGIN,
) -> np.ndarray:
    """Extrait les patches RGB ne recouvrant aucune anomalie annotée."""
    images = np.asarray(images, dtype=np.float32)
    masks = np.asarray(masks)
    if images.ndim != 4 or images.shape[-1] != 3:
        raise ValueError(f"Images attendues au format (N,H,W,3), reçu {images.shape}.")
    if masks.ndim != 4 or masks.shape[-1] != 1 or masks.shape[:3] != images.shape[:3]:
        raise ValueError(f"Masques incompatibles avec les images: {masks.shape} vs {images.shape}.")
    if patch_size <= 0 or stride <= 0 or mask_margin < 0:
        raise ValueError("patch_size et stride doivent être positifs, mask_margin non négatif.")
    height, width = images.shape[1:3]
    if height < patch_size or width < patch_size:
        raise ValueError("La résolution des images est inférieure à la taille des patches.")

    patches: list[np.ndarray] = []
    for image, mask in zip(images, masks):
        unsafe = ndimage.binary_dilation(mask[..., 0] > 0, iterations=mask_margin)
        for top in range(0, height - patch_size + 1, stride):
            for left in range(0, width - patch_size + 1, stride):
                if not unsafe[top : top + patch_size, left : left + patch_size].any():
                    patches.append(image[top : top + patch_size, left : left + patch_size])
    if not patches:
        raise ValueError("Aucun patch normal n'a été extrait.")
    return np.stack(patches).astype(np.float32, copy=False)


def reconstruction_error_maps(
    model: Model,
    images: np.ndarray,
    batch_size: int = 4,
) -> tuple[np.ndarray, np.ndarray]:
    """Retourne les reconstructions et la MSE pixel moyenne sur les canaux RGB."""
    images = np.asarray(images, dtype=np.float32)
    if images.ndim != 4 or images.shape[-1] != 3:
        raise ValueError(f"Images attendues au format (N,H,W,3), reçu {images.shape}.")
    reconstructions = model.predict(images, batch_size=batch_size, verbose=0)
    if reconstructions.shape != images.shape:
        raise ValueError(f"Sortie du modèle {reconstructions.shape} incompatible avec {images.shape}.")
    error_maps = np.mean(np.square(images - reconstructions), axis=-1)
    return reconstructions.astype(np.float32), error_maps.astype(np.float32)


def anomaly_scores(error_maps: np.ndarray, sigma: float) -> np.ndarray:
    """Lisse l'erreur puis la standardise séparément pour chaque image."""
    error_maps = np.asarray(error_maps, dtype=np.float32)
    if error_maps.ndim != 3:
        raise ValueError(f"Cartes attendues au format (N,H,W), reçu {error_maps.shape}.")
    if sigma < 0:
        raise ValueError("sigma doit être positif ou nul.")
    smoothed = (
        error_maps
        if sigma == 0
        else np.stack([ndimage.gaussian_filter(image, sigma=sigma) for image in error_maps])
    )
    std = smoothed.std(axis=(1, 2), keepdims=True)
    std = np.maximum(std, np.finfo(np.float32).eps)
    return ((smoothed - smoothed.mean(axis=(1, 2), keepdims=True)) / std).astype(np.float32)


def compile_reconstruction_loss(model: Model, loss_name: str, learning_rate: float) -> None:
    """Compile l'autoencodeur avec une perte MSE, MAE ou SSIM."""
    losses = {
        "mse": "mse",
        "mae": "mae",
        "ssim": _ssim_loss,
    }
    if loss_name not in losses:
        raise ValueError(f"Perte inconnue: {loss_name}. Choisir parmi {sorted(losses)}.")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate),
        loss=losses[loss_name],
    )


def _ssim_loss(targets: tf.Tensor, reconstructions: tf.Tensor) -> tf.Tensor:
    """Perte structurelle par exemple, pour des images RGB dans [0, 1]."""
    scores = tf.image.ssim(targets, reconstructions, max_val=1.0)
    return 1.0 - scores


class PerceptualAutoencoder(tf.keras.Model):
    """Entraîne un autoencodeur avec MAE et, facultativement, une perte VGG gelée."""

    def __init__(
        self,
        reconstruction_model: Model,
        feature_model: Model | None = None,
        perceptual_weight: float = 0.0,
    ) -> None:
        super().__init__()
        if perceptual_weight < 0:
            raise ValueError("Le poids perceptuel doit être positif ou nul.")
        if feature_model is not None and feature_model.trainable:
            raise ValueError("Le modèle extracteur de caractéristiques doit être gelé.")
        self.reconstruction_model = reconstruction_model
        self.feature_model = feature_model
        self.perceptual_weight = perceptual_weight
        self.total_tracker = tf.keras.metrics.Mean(name="loss")
        self.pixel_tracker = tf.keras.metrics.Mean(name="mae")
        self.perceptual_tracker = tf.keras.metrics.Mean(name="perceptual_loss")

    @property
    def metrics(self) -> list[tf.keras.metrics.Metric]:
        return [self.total_tracker, self.pixel_tracker, self.perceptual_tracker]

    def call(self, inputs: tf.Tensor, training: bool = False) -> tf.Tensor:
        return self.reconstruction_model(inputs, training=training)

    def _compute_components(
        self,
        inputs: tf.Tensor,
        targets: tf.Tensor,
        training: bool,
    ) -> tuple[tf.Tensor, tf.Tensor, tf.Tensor]:
        reconstruction = self.reconstruction_model(inputs, training=training)
        pixel_loss = tf.reduce_mean(tf.abs(targets - reconstruction))
        perceptual_loss = tf.constant(0.0, dtype=pixel_loss.dtype)
        if self.feature_model is not None:
            preprocess = tf.keras.applications.vgg19.preprocess_input
            target_features = self.feature_model(preprocess(targets * 255.0), training=False)
            reconstruction_features = self.feature_model(
                preprocess(reconstruction * 255.0), training=False
            )
            target_features = tf.nest.flatten(target_features)
            reconstruction_features = tf.nest.flatten(reconstruction_features)
            if len(target_features) != len(reconstruction_features):
                raise ValueError("Les sorties de l'extracteur VGG ne correspondent pas.")
            layer_losses = []
            for target_feature, reconstructed_feature in zip(
                target_features, reconstruction_features
            ):
                numerator = tf.reduce_mean(tf.abs(target_feature - reconstructed_feature))
                denominator = tf.reduce_mean(tf.abs(target_feature)) + tf.keras.backend.epsilon()
                layer_losses.append(numerator / denominator)
            perceptual_loss = tf.reduce_mean(tf.stack(layer_losses))
        total_loss = pixel_loss + self.perceptual_weight * perceptual_loss
        return total_loss, pixel_loss, perceptual_loss

    def train_step(self, data: tuple[tf.Tensor, tf.Tensor]) -> dict[str, tf.Tensor]:
        inputs, targets, sample_weight = tf.keras.utils.unpack_x_y_sample_weight(data)
        if sample_weight is not None:
            raise ValueError("Les poids d'échantillons ne sont pas pris en charge.")
        with tf.GradientTape() as tape:
            total_loss, pixel_loss, perceptual_loss = self._compute_components(
                inputs, targets, training=True
            )
        variables = self.reconstruction_model.trainable_variables
        gradients = tape.gradient(total_loss, variables)
        gradient_pairs = [
            (gradient, variable)
            for gradient, variable in zip(gradients, variables)
            if gradient is not None
        ]
        if not gradient_pairs:
            raise RuntimeError("Aucun gradient n'atteint les paramètres de l'autoencodeur.")
        self.optimizer.apply_gradients(gradient_pairs)
        self.total_tracker.update_state(total_loss)
        self.pixel_tracker.update_state(pixel_loss)
        self.perceptual_tracker.update_state(perceptual_loss)
        return {metric.name: metric.result() for metric in self.metrics}

    def test_step(self, data: tuple[tf.Tensor, tf.Tensor]) -> dict[str, tf.Tensor]:
        inputs, targets, sample_weight = tf.keras.utils.unpack_x_y_sample_weight(data)
        if sample_weight is not None:
            raise ValueError("Les poids d'échantillons ne sont pas pris en charge.")
        total_loss, pixel_loss, perceptual_loss = self._compute_components(
            inputs, targets, training=False
        )
        self.total_tracker.update_state(total_loss)
        self.pixel_tracker.update_state(pixel_loss)
        self.perceptual_tracker.update_state(perceptual_loss)
        return {metric.name: metric.result() for metric in self.metrics}


def build_vgg19_feature_model(patch_size: int = DEFAULT_PATCH_SIZE) -> Model:
    """Construit l'extracteur VGG19 ImageNet gelé demandé par le rapport."""
    backbone = tf.keras.applications.VGG19(
        include_top=False,
        weights="imagenet",
        input_shape=(patch_size, patch_size, 3),
    )
    backbone.trainable = False
    layer_names = (
        "block1_conv2",
        "block2_conv2",
        "block3_conv2",
        "block4_conv2",
        "block5_conv2",
    )
    features = tf.keras.Model(
        backbone.input,
        [backbone.get_layer(name).output for name in layer_names],
        name="frozen_vgg19_features",
    )
    features.trainable = False
    return features
