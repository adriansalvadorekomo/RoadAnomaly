"""Measure the peak GPU memory of one training epoch, to check that a resolution and batch
size fit on the team's smallest card (RTX 2060, 6 GB).

Usage (from the repo root, inside the venv):
    python scripts/gpu_memory_check.py unet 352 640 8
    python scripts/gpu_memory_check.py deeplab 352 640 4
    python scripts/gpu_memory_check.py deeplab 352 640 4 --cap 5500   # emulate a 6 GB card on a bigger GPU

The models are representative stand-ins (a 5-level U-Net, DeepLabV3+ on ResNet50), not the
final binôme models. jit_compile=False on purpose: with TF 2.20 + mixed_float16, XLA fails on
some graphs ("Seen floating point types of different precisions ... ReluGrad").
"""
import argparse

import numpy as np
import tensorflow as tf
import keras
from keras import layers

parser = argparse.ArgumentParser()
parser.add_argument("model", choices=["unet", "deeplab"])
parser.add_argument("height", type=int)
parser.add_argument("width", type=int)
parser.add_argument("batch_size", type=int)
parser.add_argument("--cap", type=int, default=None, help="GPU memory limit in MB (emulate a smaller card)")
args = parser.parse_args()

gpus = tf.config.list_physical_devices("GPU")
if args.cap:
    tf.config.set_logical_device_configuration(gpus[0], [tf.config.LogicalDeviceConfiguration(memory_limit=args.cap)])
keras.mixed_precision.set_global_policy("mixed_float16")


def get_unet(shape):
    inputs = keras.Input(shape)
    x, skips = inputs, []
    for filters in [32, 64, 128, 256]:
        x = layers.Conv2D(filters, 3, padding="same", activation="relu")(x)
        x = layers.Conv2D(filters, 3, padding="same", activation="relu")(x)
        skips.append(x)
        x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(512, 3, padding="same", activation="relu")(x)
    x = layers.Conv2D(512, 3, padding="same", activation="relu")(x)
    for filters, skip in zip([256, 128, 64, 32], reversed(skips)):
        x = layers.Conv2DTranspose(filters, 2, strides=2)(x)
        x = layers.Concatenate()([x, skip])
        x = layers.Conv2D(filters, 3, padding="same", activation="relu")(x)
        x = layers.Conv2D(filters, 3, padding="same", activation="relu")(x)
    outputs = layers.Conv2D(1, 1, activation="sigmoid", dtype="float32")(x)
    return keras.Model(inputs, outputs)


def get_deeplab(shape):
    base = keras.applications.ResNet50(weights=None, include_top=False, input_shape=shape)
    x = base.get_layer("conv4_block6_2_relu").output          # output stride 16
    low_level = base.get_layer("conv2_block3_2_relu").output  # stride 4
    branches = [layers.Conv2D(256, 1, padding="same", activation="relu")(x)]
    branches += [layers.Conv2D(256, 3, dilation_rate=r, padding="same", activation="relu")(x) for r in (6, 12, 18)]
    x = layers.Conv2D(256, 1, activation="relu")(layers.Concatenate()(branches))
    x = layers.UpSampling2D(4, interpolation="bilinear")(x)
    x = layers.Concatenate()([x, layers.Conv2D(48, 1, activation="relu")(low_level)])
    x = layers.Conv2D(256, 3, padding="same", activation="relu")(x)
    x = layers.UpSampling2D(4, interpolation="bilinear")(x)
    outputs = layers.Conv2D(1, 1, activation="sigmoid", dtype="float32")(x)
    return keras.Model(base.input, outputs)


shape = (args.height, args.width, 3)
model = get_unet(shape) if args.model == "unet" else get_deeplab(shape)
model.compile(optimizer=keras.optimizers.Adam(1e-4), loss="binary_crossentropy", jit_compile=False)

x = np.random.rand(args.batch_size * 2, *shape).astype("float32")
y = (np.random.rand(args.batch_size * 2, args.height, args.width, 1) > 0.9).astype("float32")
try:
    model.fit(x, y, batch_size=args.batch_size, epochs=1, verbose=0)
    peak = tf.config.experimental.get_memory_info("GPU:0")["peak"] / 2**30
    print(f"{args.model} {args.height}x{args.width} batch {args.batch_size}: OK, peak {peak:.2f} GB")
except tf.errors.ResourceExhaustedError:
    print(f"{args.model} {args.height}x{args.width} batch {args.batch_size}: OUT OF MEMORY")
