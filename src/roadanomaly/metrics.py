"""Pixel-level metrics for binary anomaly masks (1 = anomaly, 0 = background).

These are the metrics FR requires for all three approaches. They are computed from the
pixel confusion matrix after the prediction has been turned into a binary mask with a
threshold chosen on the validation set only.

Note: for binary masks F1 and Dice are the same quantity, 2TP / (2TP + FP + FN).
Extra metrics are added only when Data Understanding justifies them.
"""
import numpy as np
from scipy import ndimage


def confusion_counts(y_true, y_pred):
    """Return (TP, FP, FN, TN) for two binary masks of the same shape."""
    y_true = np.asarray(y_true).astype(bool)
    y_pred = np.asarray(y_pred).astype(bool)
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: {y_true.shape} vs {y_pred.shape}")
    tp = int(np.sum(y_true & y_pred))
    fp = int(np.sum(~y_true & y_pred))
    fn = int(np.sum(y_true & ~y_pred))
    tn = int(np.sum(~y_true & ~y_pred))
    return tp, fp, fn, tn


def scores_from_counts(tp, fp, fn):
    """Precision, Recall, F1, IoU and Dice from confusion counts.

    Empty cases: if there is no anomaly in the ground truth AND none predicted,
    the mask is perfect and every score is 1.0. Otherwise a 0/0 ratio is 0.0.
    """
    if tp + fp + fn == 0:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "iou": 1.0, "dice": 1.0}
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    dice = 2 * tp / (2 * tp + fp + fn)
    iou = tp / (tp + fp + fn)
    return {"precision": precision, "recall": recall, "f1": dice, "iou": iou, "dice": dice}


def segmentation_scores(y_true, y_pred):
    """Scores for one image."""
    tp, fp, fn, _ = confusion_counts(y_true, y_pred)
    return scores_from_counts(tp, fp, fn)


def evaluate_masks(y_trues, y_preds):
    """Scores over a set of images, reported two ways:

    - "per_image_mean": average of the per-image scores (every image weighs the same,
      so small obstacles count as much as large ones)
    - "aggregated": scores from the confusion counts summed over all pixels
      (large objects dominate)
    """
    per_image = []
    totals = np.zeros(3, dtype=np.int64)
    for y_true, y_pred in zip(y_trues, y_preds, strict=True):
        tp, fp, fn, _ = confusion_counts(y_true, y_pred)
        totals += (tp, fp, fn)
        per_image.append(scores_from_counts(tp, fp, fn))
    keys = per_image[0].keys()
    per_image_mean = {k: float(np.mean([s[k] for s in per_image])) for k in keys}
    aggregated = scores_from_counts(*totals.tolist())
    return {"per_image": per_image, "per_image_mean": per_image_mean, "aggregated": aggregated}


# ---------------------------------------------------------------------------
# Object-level helpers, added because Data Understanding showed that:
#  - most images contain several obstacles whose sizes span orders of magnitude, so
#    pixel scores are dominated by the largest object and say little about small ones;
#  - the ground truth contains annotation speckle (components of a few pixels) that
#    must not count as obstacles. MIN_OBJECT_PX is measured in notebook 2, section 6.
# ---------------------------------------------------------------------------

EIGHT_CONNECTED = np.ones((3, 3), dtype=bool)


def remove_small_components(mask, min_size):
    """Binary mask without the 8-connected components smaller than min_size pixels."""
    mask = np.asarray(mask).astype(bool)
    labeled, n = ndimage.label(mask, structure=EIGHT_CONNECTED)
    if n == 0:
        return mask.astype(np.uint8)
    areas = ndimage.sum(mask, labeled, range(1, n + 1))
    keep = np.concatenate([[False], areas >= min_size])
    return keep[labeled].astype(np.uint8)


def object_scores(y_true, y_pred, min_size, overlap=0.5):
    """Obstacle-level detection scores for one image.

    - A ground-truth object (component >= min_size px) is detected when at least
      `overlap` of its pixels are predicted as anomaly.
    - A predicted component (>= min_size px) is a false alarm when less than `overlap`
      of its pixels lie on ground-truth anomaly pixels.

    Returns object recall, object precision, object F1 and the raw counts.
    """
    y_true = np.asarray(y_true).astype(bool).squeeze()
    y_pred = np.asarray(y_pred).astype(bool).squeeze()

    gt_labeled, n_gt = ndimage.label(remove_small_components(y_true, min_size), structure=EIGHT_CONNECTED)
    detected = int(sum(y_pred[gt_labeled == k].mean() >= overlap for k in range(1, n_gt + 1)))

    pred_labeled, n_pred = ndimage.label(remove_small_components(y_pred, min_size), structure=EIGHT_CONNECTED)
    false_alarms = int(sum(y_true[pred_labeled == k].mean() < overlap for k in range(1, n_pred + 1)))

    recall = detected / n_gt if n_gt > 0 else 1.0
    precision = (n_pred - false_alarms) / n_pred if n_pred > 0 else (1.0 if n_gt == 0 else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"object_recall": float(recall), "object_precision": float(precision), "object_f1": float(f1),
            "gt_objects": int(n_gt), "detected": int(detected),
            "pred_objects": int(n_pred), "false_alarms": int(false_alarms)}


def bootstrap_ci(per_image_values, n_boot=2000, alpha=0.05, seed=1337):
    """Mean and (1 - alpha) bootstrap confidence interval over images.

    With only ~9 test images, a single mean hides a large uncertainty; reporting the
    interval shows whether a difference between two models is meaningful.
    """
    values = np.asarray(per_image_values, dtype=float)
    rng = np.random.default_rng(seed)
    means = rng.choice(values, size=(n_boot, len(values)), replace=True).mean(axis=1)
    low, high = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(values.mean()), float(low), float(high)


def object_recall_by_size(y_true, y_pred, min_size, small_max, overlap=0.5):
    """Object recall split into small and large objects (notebook 2, section 10, decision 7).

    Objects with min_size <= area < small_max are "small", the others "large".
    Returns detected and total counts so that several images can be summed.
    """
    y_true = np.asarray(y_true).astype(bool).squeeze()
    y_pred = np.asarray(y_pred).astype(bool).squeeze()
    labeled, n = ndimage.label(remove_small_components(y_true, min_size), structure=EIGHT_CONNECTED)
    counts = {"small_detected": 0, "small_total": 0, "large_detected": 0, "large_total": 0}
    for k in range(1, n + 1):
        obj = labeled == k
        size = "small" if obj.sum() < small_max else "large"
        counts[f"{size}_total"] += 1
        counts[f"{size}_detected"] += int(y_pred[obj].mean() >= overlap)
    return counts


def aupro(y_trues, score_maps, min_size, fpr_limit=0.3, n_thresholds=100):
    """Area under the Per-Region-Overlap curve, up to a false positive rate of fpr_limit.

    For each threshold:
      - PRO = mean over all ground-truth objects of the fraction of the object that is
        above the threshold (every object counts the same, whatever its size);
      - FPR = fraction of background pixels above the threshold.
    The PRO curve is integrated over FPR in [0, fpr_limit] and divided by fpr_limit,
    so a perfect detector scores 1. The FPR cap must always be reported with the score.
    """
    y_trues = [np.asarray(y).astype(bool).squeeze() for y in y_trues]
    score_maps = [np.asarray(s, dtype=float).squeeze() for s in score_maps]

    # Ground-truth objects (speckle removed) of every image
    objects = []
    for y in y_trues:
        labeled, n = ndimage.label(remove_small_components(y, min_size), structure=EIGHT_CONNECTED)
        objects.append([labeled == k for k in range(1, n + 1)])

    all_scores = np.concatenate([s.ravel() for s in score_maps])
    thresholds = np.quantile(all_scores, np.linspace(1.0, 0.0, n_thresholds))  # high -> low

    background = np.concatenate([s[~y] for s, y in zip(score_maps, y_trues, strict=True)])
    fprs, pros = [], []
    for t in thresholds:
        fprs.append(float((background >= t).mean()))
        overlaps = [(s[obj] >= t).mean() for s, objs in zip(score_maps, objects, strict=True) for obj in objs]
        pros.append(float(np.mean(overlaps)))

    # Keep the part of the curve with FPR <= fpr_limit (add the exact end point by interpolation)
    fprs, pros = np.array(fprs), np.array(pros)
    keep = fprs <= fpr_limit
    x, y = fprs[keep], pros[keep]
    if keep.sum() < len(fprs):
        x = np.append(x, fpr_limit)
        y = np.append(y, np.interp(fpr_limit, fprs, pros))
    return float(np.trapezoid(y, x) / fpr_limit)


# ---------------------------------------------------------------------------
# Boundary metrics (FR, section 10: Boundary IoU for DeepLabV3+, HD95 for U-Net), computed for
# every model on speckle-filtered masks, in pixels at the working resolution.
# ---------------------------------------------------------------------------

def _inner_boundary(mask, band):
    """Pixels of `mask` within `band` px of its contour (the mask minus its erosion)."""
    mask = np.asarray(mask).astype(bool)
    eroded = ndimage.binary_erosion(mask, structure=EIGHT_CONNECTED, iterations=band, border_value=0)
    return mask & ~eroded


def boundary_iou(y_true, y_pred, band=3):
    """Boundary IoU (Cheng et al., 2021): IoU of the contour bands of width `band` px.

    Sensitive to the quality of the outline, unlike the pixel IoU which large interiors dominate.
    Both masks empty -> 1.0; exactly one empty -> 0.0.
    """
    gt_band, pred_band = _inner_boundary(y_true, band), _inner_boundary(y_pred, band)
    union = (gt_band | pred_band).sum()
    return 1.0 if union == 0 else float((gt_band & pred_band).sum() / union)


def hd95(y_true, y_pred):
    """95th percentile of the symmetric contour distances, in px (lower is better).

    Empty masks: both empty -> 0.0; exactly one empty -> NaN (undefined), reported apart.
    """
    gt, pred = np.asarray(y_true).astype(bool), np.asarray(y_pred).astype(bool)
    if not gt.any() and not pred.any():
        return 0.0
    if not gt.any() or not pred.any():
        return float("nan")
    gt_edge, pred_edge = _inner_boundary(gt, 1), _inner_boundary(pred, 1)
    to_pred = ndimage.distance_transform_edt(~pred_edge)[gt_edge]
    to_gt = ndimage.distance_transform_edt(~gt_edge)[pred_edge]
    return float(np.percentile(np.concatenate([to_pred, to_gt]), 95))
