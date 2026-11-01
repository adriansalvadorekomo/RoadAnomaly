"""DeepLabV3+ binaire pour RoadAnomaly.

Entrée : images RGB float32 dans [0, 1].
Sortie : probabilité d'anomalie pour chaque pixel.

Encodeur ResNet50 préentraîné sur ImageNet et gelé par défaut.
ASPP et décodeur initialisés pour notre tâche.
"""

import keras
from keras import layers


def conv_block(x, filters, name, kernel_size=3, dilation_rate=1):
    """Convolution, normalisation et activation."""
    x = layers.Conv2D(
        filters,
        kernel_size,
        padding="same",
        dilation_rate=dilation_rate,
        use_bias=False,
        name=f"{name}_conv",
    )(x)
    x = layers.BatchNormalization(name=f"{name}_bn")(x)
    return layers.Activation("relu", name=name)(x)


def build_deeplabv3plus(
    input_shape=(352, 640, 3),
    weights="imagenet",
    decoder_channels=128,
):
    """Construire le modèle avec un encodeur gelé."""
    height, width, channels = input_shape

    if channels != 3:
        raise ValueError("Le modèle attend une image RGB.")
    if min(height, width) < 32 or height % 32 or width % 32:
        raise ValueError("Hauteur et largeur : multiples de 32, au moins 32.")
    if decoder_channels < 1:
        raise ValueError("decoder_channels doit être positif.")

    inputs = keras.Input(shape=input_shape, name="rgb_0_1")

    # Le chargeur commun fournit [0, 1].
    # ResNet50 attend son prétraitement sur une image dans [0, 255].
    x = layers.Rescaling(255.0, name="to_0_255")(inputs)
    x = keras.applications.resnet50.preprocess_input(x)

    backbone = keras.applications.ResNet50(
        include_top=False,
        weights=weights,
        input_shape=input_shape,
    )

    encoder = keras.Model(
        backbone.input,
        [
            backbone.get_layer("conv2_block3_out").output,
            backbone.get_layer("conv4_block6_out").output,
        ],
        name="resnet50_encoder",
    )
    encoder.trainable = False

    # Statistiques BatchNorm du backbone conservées.
    low, high = encoder(x, training=False)
    high_height, high_width = height // 16, width // 16

    # ASPP : plusieurs champs de vision sur les mêmes caractéristiques.
    branches = [
        conv_block(
            high, decoder_channels, "aspp_1x1", kernel_size=1
        )
    ]

    for rate in (6, 12, 18):
        branches.append(
            conv_block(
                high,
                decoder_channels,
                name=f"aspp_rate_{rate}",
                dilation_rate=rate,
            )
        )

    pooled = layers.GlobalAveragePooling2D(
        keepdims=True, name="aspp_pool"
    )(high)
    pooled = layers.Conv2D(
        decoder_channels,
        1,
        activation="relu",
        name="aspp_global",
    )(pooled)
    pooled = layers.Resizing(
        high_height,
        high_width,
        interpolation="bilinear",
        name="aspp_global_resize",
    )(pooled)

    x = layers.Concatenate(name="aspp_concat")(
        [*branches, pooled]
    )
    x = conv_block(
        x, decoder_channels, "aspp_projection", kernel_size=1
    )

    # Décodeur : réintroduire les détails spatiaux de bas niveau.
    x = layers.Resizing(
        height // 4,
        width // 4,
        interpolation="bilinear",
        name="decoder_resize",
    )(x)

    low = conv_block(
        low, 48, "low_projection", kernel_size=1
    )
    x = layers.Concatenate(name="decoder_concat")([x, low])
    x = conv_block(x, decoder_channels, "decoder_1")
    x = conv_block(x, decoder_channels, "decoder_2")

    x = layers.Conv2D(
        1, 1, name="anomaly_logits_small"
    )(x)
    x = layers.Resizing(
        height,
        width,
        interpolation="bilinear",
        name="anomaly_logits",
    )(x)

    outputs = layers.Activation(
        "sigmoid",
        dtype="float32",
        name="anomaly_probability",
    )(x)

    return keras.Model(
        inputs, outputs, name="deeplabv3plus_binary"
    )
