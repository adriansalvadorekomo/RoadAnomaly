"""Binôme A: binary DeepLabV3+ for RoadAnomaly (Ines Trabelsi).

Input: RGB float32 images in [0, 1]. Output: anomaly probability of every pixel.

- Encoder: ResNet50 pretrained on ImageNet, frozen (BatchNorm statistics kept), cut at
  stride 4 (low-level features) and stride 16 (high-level features). The ResNet50
  preprocessing is inside the model, so it takes the shared loader's [0, 1] images.
- ASPP: a 1x1 branch, 3x3 branches with dilation 6, 12 and 18, and a global-context
  branch, concatenated and projected (several fields of view on the same features).
- Decoder: the ASPP output, upsampled to stride 4, is fused with the low-level features,
  refined by two convolution blocks and upsampled to the input size.
- Output: one logit per pixel (layer "anomaly_logits", used by Seg-Grad-CAM), then a
  float32 sigmoid (safe with mixed precision).
"""
import keras
from keras import layers


def conv_block(x, filters, name, kernel_size=3, dilation_rate=1):
    """Convolution (no bias), batch normalisation and ReLU."""
    x = layers.Conv2D(filters, kernel_size, padding="same", dilation_rate=dilation_rate, use_bias=False,
                      name=f"{name}_conv")(x)
    x = layers.BatchNormalization(name=f"{name}_bn")(x)
    return layers.Activation("relu", name=name)(x)


def build_deeplabv3plus(input_shape=(352, 640, 3), weights="imagenet", decoder_channels=128):
    """DeepLabV3+ with a frozen ResNet50 encoder; height and width must be multiples of 32."""
    height, width, channels = input_shape
    if channels != 3:
        raise ValueError("the model expects RGB images")
    if min(height, width) < 32 or height % 32 or width % 32:
        raise ValueError("height and width must be multiples of 32, at least 32")
    if decoder_channels < 1:
        raise ValueError("decoder_channels must be positive")

    inputs = keras.Input(shape=input_shape, name="rgb_0_1")
    # The shared loader gives [0, 1]; ResNet50 expects its own preprocessing of [0, 255] images
    x = layers.Rescaling(255.0, name="to_0_255")(inputs)
    x = keras.applications.resnet50.preprocess_input(x)

    backbone = keras.applications.ResNet50(include_top=False, weights=weights, input_shape=input_shape)
    encoder = keras.Model(backbone.input, [backbone.get_layer("conv2_block3_out").output,
                                           backbone.get_layer("conv4_block6_out").output],
                          name="resnet50_encoder")
    encoder.trainable = False
    low, high = encoder(x, training=False)   # training=False keeps the ImageNet BatchNorm statistics

    # ASPP: several fields of view on the stride-16 features
    branches = [conv_block(high, decoder_channels, "aspp_1x1", kernel_size=1)]
    for rate in (6, 12, 18):
        branches.append(conv_block(high, decoder_channels, f"aspp_rate_{rate}", dilation_rate=rate))
    pooled = layers.GlobalAveragePooling2D(keepdims=True, name="aspp_pool")(high)
    pooled = layers.Conv2D(decoder_channels, 1, activation="relu", name="aspp_global")(pooled)
    pooled = layers.Resizing(height // 16, width // 16, interpolation="bilinear", name="aspp_global_resize")(pooled)
    x = layers.Concatenate(name="aspp_concat")([*branches, pooled])
    x = conv_block(x, decoder_channels, "aspp_projection", kernel_size=1)

    # Decoder: bring back the spatial detail of the stride-4 features
    x = layers.Resizing(height // 4, width // 4, interpolation="bilinear", name="decoder_resize")(x)
    low = conv_block(low, 48, "low_projection", kernel_size=1)
    x = layers.Concatenate(name="decoder_concat")([x, low])
    x = conv_block(x, decoder_channels, "decoder_1")
    x = conv_block(x, decoder_channels, "decoder_2")

    x = layers.Conv2D(1, 1, name="anomaly_logits_small")(x)
    x = layers.Resizing(height, width, interpolation="bilinear", name="anomaly_logits")(x)
    outputs = layers.Activation("sigmoid", dtype="float32", name="anomaly_probability")(x)
    return keras.Model(inputs, outputs, name="deeplabv3plus_binary")
