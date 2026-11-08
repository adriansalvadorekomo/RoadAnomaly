"""Normal (anomaly-free) training data for the autoencoders of Binôme B.

Every RoadAnomaly image contains an obstacle (notebook 2, section 5), so "normal" data is
taken from the background of the training images. Annotation borders are loose, so each
obstacle is first dilated by `margin` px: regions touching an obstacle are not normal.
"""
import numpy as np
import tensorflow as tf
from scipy import ndimage

MASK_MARGIN = 4    # px added around each obstacle before selecting normal regions


def unsafe_mask(mask, margin=MASK_MARGIN):
    """Binary (H, W) mask of the pixels within `margin` px of an obstacle."""
    mask = np.asarray(mask) > 0
    # scipy treats iterations=0 as "dilate until nothing changes", so margin 0 is handled apart
    return ndimage.binary_dilation(mask, iterations=margin) if margin > 0 else mask


def normal_patches(images, masks, patch=64, stride=32, margin=MASK_MARGIN):
    """Cut images (N, H, W, 3) into overlapping patches and keep those with no unsafe pixel.

    Returns (patches float32 (M, patch, patch, 3), number of candidate patches).
    """
    images, masks = np.asarray(images, dtype=np.float32), np.asarray(masks)
    if images.ndim != 4 or images.shape[-1] != 3:
        raise ValueError(f"images must be (N, H, W, 3), got {images.shape}")
    if masks.shape != (*images.shape[:3], 1):
        raise ValueError(f"masks {masks.shape} do not match images {images.shape}")
    normal, total = [], 0
    for image, mask in zip(images, masks, strict=True):
        unsafe = unsafe_mask(mask[..., 0], margin)
        for y in range(0, image.shape[0] - patch + 1, stride):
            for x in range(0, image.shape[1] - patch + 1, stride):
                total += 1
                if not unsafe[y:y + patch, x:x + patch].any():
                    normal.append(image[y:y + patch, x:x + patch])
    if not normal:
        raise ValueError("no normal patch found")
    return np.stack(normal), total


def normal_cells(masks, cell_shape, margin=MASK_MARGIN):
    """True for each feature-map cell whose image region holds no unsafe pixel.

    masks: (N, H, W, 1); cell_shape: (h, w) of the feature map. "area" resizing averages
    the pixels of each cell, so a cell is normal when that average is exactly 0.
    """
    cells = []
    for mask in np.asarray(masks)[..., 0]:
        unsafe = unsafe_mask(mask, margin).astype("float32")[..., None]
        cells.append(tf.image.resize(unsafe, cell_shape, method="area").numpy()[..., 0] == 0)
    return np.stack(cells)
