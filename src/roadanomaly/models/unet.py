"""Binôme C main model: U-Net (Ronneberger et al., 2015), ported from Walid's PyTorch code
(archive/C_unet_original_run_walid.ipynb).

- build_unet: Walid's U-Net trained from scratch. Four encoder stages of two Conv-BN-ReLU blocks
  (16, 32, 64, 128 channels) with max pooling, a 256-channel bottleneck, and a decoder that
  upsamples with ConvTranspose 2x2 and concatenates the encoder features of the same resolution
  (skip connections) before two more Conv-BN-ReLU blocks. Skips bring back the detail lost by
  pooling, the difference with the CNN baseline.
- build_unet_resnet50: Walid's improved U-Net with a pretrained ImageNet encoder. His encoder was
  ResNet34 (segmentation_models_pytorch); Keras has no ResNet34, so ResNet50 is used, with skips
  from its stride-2, 4, 8 and 16 outputs and its stride-32 output as the bridge. BatchNorm layers
  of the encoder stay in inference mode (batches of 4-8 images are too small to re-estimate them).

Both end with 'anomaly_logits' -> float32 sigmoid (shared model format, Seg-Grad-CAM-ready) and take
[0, 1] images (normalisation inside the model).
"""
import keras
from keras import layers

from roadanomaly.models.cnn import conv_bn_relu, normalise_imagenet, segmentation_head

RESNET50_SKIPS = ("conv1_relu", "conv2_block3_out", "conv3_block4_out", "conv4_block6_out")   # strides 2, 4, 8, 16
RESNET50_BRIDGE = "conv5_block3_out"                                                           # stride 32


def double_conv(x, filters, name):
    """Two Conv-BN-ReLU blocks."""
    return conv_bn_relu(conv_bn_relu(x, filters, f"{name}_a"), filters, f"{name}_b")


def up_block(x, skip, filters, name):
    """ConvTranspose 2x2 (x2 resolution), concatenation with the skip features, double conv."""
    x = layers.Conv2DTranspose(filters, 2, strides=2, name=f"{name}_up")(x)
    x = layers.Concatenate(name=f"{name}_concat")([x, skip])
    return double_conv(x, filters, name)


def build_unet(input_shape=(352, 640, 3), filters=(16, 32, 64, 128), bottleneck=256):
    """Walid's U-Net from scratch; height and width must be divisible by 2 ** len(filters)."""
    inputs = keras.Input(shape=input_shape, name="rgb_0_1")
    x, skips = normalise_imagenet(inputs), []
    for i, f in enumerate(filters, start=1):
        x = double_conv(x, f, f"enc{i}")
        skips.append(x)
        x = layers.MaxPooling2D(2, name=f"enc{i}_pool")(x)
    x = double_conv(x, bottleneck, "bottleneck")
    for i, (f, skip) in enumerate(zip(reversed(filters), reversed(skips), strict=True), start=1):
        x = up_block(x, skip, f, f"dec{i}")
    return keras.Model(inputs, segmentation_head(x), name="unet")


def build_unet_resnet50(input_shape=(352, 640, 3), weights="imagenet", decoder_filters=(256, 128, 64, 32, 16)):
    """U-Net with an ImageNet ResNet50 encoder (trainable, BatchNorm frozen); sides divisible by 32."""
    inputs = keras.Input(shape=input_shape, name="rgb_0_1")
    x = layers.Rescaling(255.0, name="to_0_255")(inputs)
    x = keras.applications.resnet50.preprocess_input(x)
    backbone = keras.applications.ResNet50(include_top=False, weights=weights, input_shape=input_shape)
    for layer in backbone.layers:
        if isinstance(layer, layers.BatchNormalization):
            layer.trainable = False
    encoder = keras.Model(backbone.input, [backbone.get_layer(n).output for n in (*RESNET50_SKIPS, RESNET50_BRIDGE)],
                          name="resnet50_encoder")
    *skips, x = encoder(x)
    for i, (f, skip) in enumerate(zip(decoder_filters[:-1], reversed(skips), strict=True), start=1):
        x = up_block(x, skip, f, f"dec{i}")
    x = layers.Conv2DTranspose(decoder_filters[-1], 2, strides=2, name="dec5_up")(x)   # stride 2 -> full size
    x = double_conv(x, decoder_filters[-1], "dec5")
    return keras.Model(inputs, segmentation_head(x), name="unet_resnet50")
