"""Binôme B final model: an autoencoder on frozen ImageNet features (feature-space AE, "v2").

A pixel autoencoder measures unusual colour and texture, not unexpected objects. Here a
frozen pretrained network (VGG16, never trained) turns each image region into a feature
vector, and a small autoencoder learns to reconstruct the feature vectors of normal road
scenes. A region whose features it cannot reconstruct is an anomaly.

- Features: VGG16 block5_conv3, stride 16 -> 22x40 cells for a 352x640 image.
- Standardisation: per-channel z-score with the statistics of the TRAIN normal cells.
- Model: 3x3 conv -> narrow linear 1x1 code (8 channels per cell) -> 3x3 conv -> linear
  1x1 output. No stride: each cell already summarises a 16x16 region.
- Training: masked MSE, anomaly cells have weight 0 (normal_regions.normal_cells), early
  stopping on the validation normal cells.
"""
import keras
import numpy as np
from keras import layers

BACKBONE = "VGG16"
FEATURE_LAYER = "block5_conv3"
HIDDEN = 256           # width of the encoder and decoder convolutions
CODE_CHANNELS = 8      # linear code: 512 -> 8 channels per cell, 64 times narrower, so only normal road comes back well
LEARNING_RATE = 1e-3   # Adam's default step size
EPOCHS = 300           # upper bound; early stopping decides
PATIENCE = 15          # epochs without a lower validation loss before stopping
BATCH_SIZE = 8         # whole feature maps per step

# keras.applications constructor and its preprocessing, by name (preprocessing expects 0-255 RGB)
_BACKBONES = {
    "VGG16": (keras.applications.VGG16, keras.applications.vgg16.preprocess_input),
    "VGG19": (keras.applications.VGG19, keras.applications.vgg19.preprocess_input),
}
_extractors = {}       # built once per (backbone, layer): rebuilding makes TensorFlow re-trace


def get_extractor(backbone=BACKBONE, layer=FEATURE_LAYER):
    """Frozen ImageNet backbone cut at `layer` (weights download once into ~/.keras/models)."""
    key = (backbone, layer)
    if key not in _extractors:
        constructor, _ = _BACKBONES[backbone]
        base = constructor(include_top=False, weights="imagenet")
        base.trainable = False
        _extractors[key] = keras.Model(base.input, base.get_layer(layer).output, name=f"{backbone}_{layer}")
    return _extractors[key]


def extract_features(images, backbone=BACKBONE, layer=FEATURE_LAYER, batch_size=2):
    """Raw features (N, h, w, C) of images (N, H, W, 3) in [0, 1], with the backbone's own preprocessing."""
    preprocess = _BACKBONES[backbone][1]
    images = np.asarray(images, dtype=np.float32)
    return get_extractor(backbone, layer).predict(preprocess(images * 255.0), batch_size=batch_size, verbose=0)


def feature_statistics(features, normal):
    """Per-channel mean and std of the normal cells (fit on TRAIN only)."""
    return features[normal].mean(axis=0), features[normal].std(axis=0) + 1e-6


def standardise(features, mean, std):
    """Per-channel z-score with statistics from the train normal cells."""
    return (features - mean) / std


def build_feature_ae(channels, hidden=HIDDEN, code_channels=CODE_CHANNELS):
    """Autoencoder on feature maps of any size: 3x3 conv -> linear 1x1 code -> 3x3 conv -> linear 1x1."""
    inputs = keras.Input(shape=(None, None, channels), name="features")
    x = layers.Conv2D(hidden, 3, padding="same", activation="relu", name="encoder")(inputs)
    code = layers.Conv2D(code_channels, 1, activation=None, name="code")(x)       # bottleneck (linear)
    x = layers.Conv2D(hidden, 3, padding="same", activation="relu", name="decoder")(code)
    outputs = layers.Conv2D(channels, 1, activation=None, name="reconstruction")(x)   # unbounded z-scores
    return keras.Model(inputs, outputs, name="feature_autoencoder")


def train_feature_ae(train, normal_train, val, normal_val, seed, epochs=EPOCHS, patience=PATIENCE,
                     batch_size=BATCH_SIZE, learning_rate=LEARNING_RATE):
    """Train one feature AE on the normal cells only (anomaly cells have weight 0 in the loss).

    train / val: standardised features (N, h, w, C); normal_*: boolean (N, h, w).
    Returns (model, history).
    """
    keras.utils.set_random_seed(seed)
    model = build_feature_ae(train.shape[-1])
    # MSE on standardised features; sample_weight below gives weight 0 to cells that touch an obstacle (masked MSE)
    model.compile(optimizer=keras.optimizers.Adam(learning_rate), loss="mse")
    # Early stopping on the validation normal cells (never the test set), keeping the best epoch's weights
    early_stopping = keras.callbacks.EarlyStopping(monitor="val_loss", patience=patience, restore_best_weights=True)
    # input = target = the feature maps: the autoencoder learns to reproduce the features of normal road only
    history = model.fit(train, train, sample_weight=normal_train.astype("float32"),
                        validation_data=(val, val, normal_val.astype("float32")),
                        epochs=epochs, batch_size=batch_size, callbacks=[early_stopping], verbose=0)
    return model, history


def cell_error_maps(model, features, batch_size=BATCH_SIZE):
    """Squared reconstruction error of each cell, averaged over channels: (N, h, w)."""
    reconstructions = model.predict(features, batch_size=batch_size, verbose=0)
    return ((features - reconstructions) ** 2).mean(axis=-1)
