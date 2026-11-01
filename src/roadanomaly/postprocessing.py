"""From a raw score map to an anomaly mask, with every setting chosen on validation.

Steps, in this order (each one optional, as stored in a model's config.json):
1. upsample: coarse maps (e.g. 22x40 feature cells) are resized bilinearly to IMG_SIZE;
2. smooth: Gaussian smoothing of strength `sigma` (0 = none);
3. per-image z-score: "how unusual is this pixel compared with the rest of its own image";
4. threshold, then removal of the predicted blobs smaller than `min_blob` px.
"""
import numpy as np
import tensorflow as tf
from scipy import ndimage
from sklearn.metrics import average_precision_score

from roadanomaly import metrics
from roadanomaly.protocol import IMG_SIZE, MIN_OBJECT_PX

SIGMA_CANDIDATES = (0, 2, 4, 8, 16)
THRESHOLD_QUANTILES = np.linspace(0.50, 0.995, 60)   # candidate thresholds for score maps


def upsample(maps, size=IMG_SIZE):
    """Bilinear resize of (N, h, w) maps to (N, *size); maps already at that size are returned as is."""
    maps = np.asarray(maps, dtype=np.float32)
    if maps.shape[1:3] == tuple(size):
        return maps
    return tf.image.resize(maps[..., None], size, method="bilinear").numpy()[..., 0]


def smooth(maps, sigma):
    """Gaussian smoothing of each (H, W) map; sigma = 0 means no smoothing."""
    if sigma == 0:
        return np.asarray(maps)
    return np.stack([ndimage.gaussian_filter(m, sigma) for m in maps])


def standardise_per_image(maps):
    """z-score of each map against its own mean and standard deviation."""
    maps = np.asarray(maps, dtype=np.float32)
    std = np.maximum(maps.std(axis=(1, 2), keepdims=True), np.finfo(np.float32).eps)
    return (maps - maps.mean(axis=(1, 2), keepdims=True)) / std


def anomaly_scores(raw_maps, sigma, z_score=True, size=IMG_SIZE):
    """Full score post-processing: upsample to `size`, smooth, then (optionally) per-image z-score."""
    maps = smooth(upsample(raw_maps, size), sigma)
    return standardise_per_image(maps) if z_score else np.asarray(maps, dtype=np.float32)


def to_masks(scores, threshold, min_blob=MIN_OBJECT_PX):
    """Threshold score maps and drop predicted blobs smaller than `min_blob` px."""
    return np.stack([metrics.remove_small_components(s >= threshold, min_blob) for s in scores])


def auprc(gt, scores):
    """Pixel AuPRC (average precision) over all pixels of all images: the main ranking metric."""
    return float(average_precision_score(np.asarray(gt).ravel(), np.asarray(scores).ravel()))


def mean_f1(gt, scores, threshold, min_blob=MIN_OBJECT_PX):
    """Per-image mean F1 of the masks obtained with this threshold and minimum blob size."""
    masks = to_masks(scores, threshold, min_blob)
    return metrics.evaluate_masks(list(gt), list(masks))["per_image_mean"]["f1"]


def select_sigma(gt, raw_maps, candidates=SIGMA_CANDIDATES, z_score=True):
    """Smoothing strength with the best validation AuPRC; returns (sigma, {sigma: AuPRC})."""
    table = {s: auprc(gt, anomaly_scores(raw_maps, s, z_score)) for s in candidates}
    return max(table, key=table.get), table


def select_threshold(gt, scores, quantiles=THRESHOLD_QUANTILES, min_blob_candidates=(MIN_OBJECT_PX,)):
    """Threshold (a quantile of the validation scores) and minimum blob size with the best
    per-image mean F1 on validation. Returns (threshold, min_blob, F1, list of all trials)."""
    thresholds = np.unique(np.quantile(scores, quantiles))
    trials = [(float(t), int(b), mean_f1(gt, scores, t, b)) for b in min_blob_candidates for t in thresholds]
    threshold, min_blob, f1 = max(trials, key=lambda trial: trial[2])
    return threshold, min_blob, f1, trials
