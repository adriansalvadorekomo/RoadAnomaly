"""Shared RoadAnomaly data pipeline (CRISP-DM Data Preparation, notebook 3).

Every binôme loads the data through these functions so that all three approaches use
the same frames, the same binary mask convention and the same frozen split.

Conventions
- Images: RGB float32 in [0, 1]. Backbone-specific normalisation (e.g. preprocess_input)
  is applied by each binôme inside its own model, not here.
- Masks: binary float32 of shape (H, W, 1), 1 = anomaly (label 2 in labels_semantic.png),
  0 = background (label 0).
- Sizes are given as (height, width), like keras / tf.image.resize.
- WebP is decoded with PIL because tf.io cannot decode WebP.
"""
import csv
import json
import os
import re
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image

# Every path of the project is defined here, relative to the repository (never absolute)
# ROADANOMALY_ROOT overrides the location, e.g. inside the Docker image
REPO_ROOT = Path(os.environ.get("ROADANOMALY_ROOT", Path(__file__).resolve().parents[2]))
DATA_DIR = REPO_ROOT / "data" / "raw" / "RoadAnomaly"   # tracked in git, read-only
INTERIM_DIR = REPO_ROOT / "data" / "interim"             # caches (git-ignored)
PROCESSED_DIR = REPO_ROOT / "data" / "processed"         # derived arrays (git-ignored)
MODELS_DIR = REPO_ROOT / "models"                        # one folder per model: model.keras + config.json
FIG_DIR = REPO_ROOT / "reports" / "figures"
MANIFEST_PATH = REPO_ROOT / "splits" / "split_manifest.csv"

ANOMALY_LABEL = 2  # value of anomaly pixels in labels_semantic.png (background = 0)


def list_frames(data_dir=DATA_DIR):
    """Frame names (without extension) in the order of frame_list.json."""
    with open(Path(data_dir) / "frame_list.json") as f:
        return [Path(name).stem for name in json.load(f)]


def category_of(frame):
    """Category from the file name prefix, e.g. 'obstacles12_rocks2' -> 'obstacles'."""
    return re.match(r"[a-z_]+?(?=\d)", frame).group(0)


def load_frame(frame, data_dir=DATA_DIR):
    """Return (image uint8 (H, W, 3), binary mask uint8 (H, W)) at full resolution."""
    frames_dir = Path(data_dir) / "frames"
    image = np.array(Image.open(frames_dir / f"{frame}.webp").convert("RGB"))
    labels = np.array(Image.open(frames_dir / f"{frame}.labels" / "labels_semantic.png"))
    mask = (labels == ANOMALY_LABEL).astype(np.uint8)
    return image, mask


def resize_pair(image, mask, img_size):
    """Resize to img_size = (height, width): bilinear for the image, nearest for the mask."""
    height, width = img_size
    image = np.array(Image.fromarray(image).resize((width, height), Image.BILINEAR))
    mask = np.array(Image.fromarray(mask).resize((width, height), Image.NEAREST))
    return image, mask


def read_manifest(manifest_path=MANIFEST_PATH):
    """List of dict rows: frame, category, scene_group, split."""
    with open(manifest_path, newline="") as f:
        return list(csv.DictReader(f))


def load_split(split, img_size, manifest_path=MANIFEST_PATH, data_dir=DATA_DIR):
    """Load one split ('train', 'val' or 'test') into memory.

    Returns (frames, images float32 (N, H, W, 3) in [0, 1], masks float32 (N, H, W, 1)).
    The dataset has only 60 images, so keeping a split in memory is cheap.
    """
    frames = [row["frame"] for row in read_manifest(manifest_path) if row["split"] == split]
    if not frames:
        raise ValueError(f"No frames for split '{split}' in {manifest_path}")
    images, masks = [], []
    for frame in frames:
        image, mask = resize_pair(*load_frame(frame, data_dir), img_size)
        images.append(image)
        masks.append(mask)
    images = np.stack(images).astype("float32") / 255.0
    masks = np.stack(masks)[..., None].astype("float32")
    return frames, images, masks


def augment(image, mask, min_crop=0.8, max_delta=0.1):
    """Random augmentation applied identically to image and mask (geometry only).

    - horizontal flip (no vertical flip: the road is always at the bottom)
    - random crop covering min_crop..1 of each side, resized back to the input size
    - brightness / contrast jitter on the image only (the mask is not photometric)
    """
    size = tf.shape(image)[:2]

    # Stack image and mask so that flip and crop are exactly the same for both
    stacked = tf.concat([image, mask], axis=-1)
    stacked = tf.image.random_flip_left_right(stacked)

    scale = tf.random.uniform([], min_crop, 1.0)
    crop_size = tf.cast(tf.cast(size, tf.float32) * scale, tf.int32)
    stacked = tf.image.random_crop(stacked, tf.concat([crop_size, [4]], axis=0))

    image = tf.image.resize(stacked[..., :3], size, method="bilinear")
    mask = tf.image.resize(stacked[..., 3:], size, method="nearest")

    image = tf.image.random_brightness(image, max_delta)
    image = tf.image.random_contrast(image, 1.0 - max_delta, 1.0 + max_delta)
    image = tf.clip_by_value(image, 0.0, 1.0)
    return image, mask


def get_dataset(images, masks, batch_size, training=False, seed=1337):
    """Returns a tf.data.Dataset of (image, mask) batches.

    training=True shuffles and augments; validation / test data are never augmented.
    """
    dataset = tf.data.Dataset.from_tensor_slices((images, masks))
    if training:
        dataset = dataset.shuffle(len(images), seed=seed, reshuffle_each_iteration=True)
        dataset = dataset.map(augment, num_parallel_calls=tf.data.AUTOTUNE)
    return dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
