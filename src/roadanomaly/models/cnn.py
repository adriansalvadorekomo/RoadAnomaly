"""Binôme C baseline: a simple encoder–decoder CNN without skip connections (Hejer).

Keras port of Hejer's PyTorch model (archive/C_cnn_original_run_hejer.ipynb):
- encoder: 3 x [Conv 3x3 -> BatchNorm -> ReLU -> MaxPool 2] with 32, 64, 128 channels (1/8 resolution);
- decoder: 3 x [ConvTranspose 2x2 stride 2 -> Conv 3x3 -> BatchNorm -> ReLU] with 64, 32, 16 channels;
- a 1x1 convolution gives one logit per pixel ("anomaly_logits"), then a float32 sigmoid.
Without skip connections, the fine detail lost by pooling cannot come back: this is the baseline
that the U-Net (models/unet.py) is compared with. ImageNet mean / std normalisation is inside the
model (as in Hejer's preprocessing), so it takes the shared loader's [0, 1] images.
"""
import keras
from keras import layers

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def normalise_imagenet(inputs):
    """[0, 1] RGB -> ImageNet-standardised RGB (a Keras Normalization layer, saved with the model)."""
    variance = [s ** 2 for s in IMAGENET_STD]
    return layers.Normalization(mean=IMAGENET_MEAN, variance=variance, name="imagenet_normalisation")(inputs)


def conv_bn_relu(x, filters, name):
    """Conv 3x3 (same padding) -> BatchNorm -> ReLU."""
    x = layers.Conv2D(filters, 3, padding="same", name=f"{name}_conv")(x)
    x = layers.BatchNormalization(name=f"{name}_bn")(x)
    return layers.Activation("relu", name=name)(x)


def segmentation_head(x):
    """1x1 logits named 'anomaly_logits', then a float32 sigmoid (shared model format)."""
    logits = layers.Conv2D(1, 1, name="anomaly_logits")(x)
    return layers.Activation("sigmoid", dtype="float32", name="anomaly_probability")(logits)


def build_cnn_baseline(input_shape=(352, 640, 3), encoder_filters=(32, 64, 128), decoder_filters=(64, 32, 16)):
    """Hejer's CNN baseline; height and width must be divisible by 2 ** len(encoder_filters)."""
    inputs = keras.Input(shape=input_shape, name="rgb_0_1")
    x = normalise_imagenet(inputs)
    for i, filters in enumerate(encoder_filters, start=1):
        x = conv_bn_relu(x, filters, f"enc{i}")
        x = layers.MaxPooling2D(2, name=f"enc{i}_pool")(x)
    for i, filters in enumerate(decoder_filters, start=1):
        x = layers.Conv2DTranspose(filters, 2, strides=2, name=f"dec{i}_up")(x)
        x = conv_bn_relu(x, filters, f"dec{i}")
    return keras.Model(inputs, segmentation_head(x), name="cnn_baseline")
