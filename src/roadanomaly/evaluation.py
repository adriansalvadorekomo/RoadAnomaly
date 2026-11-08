"""The shared evaluation report: the same numbers, computed the same way, for every model.

The metrics come from notebook 2, section 10:
- threshold-free (score maps): AuPRC (main, chance = anomaly prevalence), AUROC (chance 0.5),
  AUPRO up to FPR_LIMIT (every object weighs the same) and FPR95, the share of background
  pixels flagged when 95 % of the anomaly pixels are found (the false-alarm criterion of the
  Business Understanding, as in the SegmentMeIfYouCan benchmark; lower is better);
- thresholded (masks): pixel Precision / Recall / F1 = Dice / IoU as the mean over images
  and aggregated over pixels, object recall / precision / F1, recall of small vs large
  objects, the pixel confusion matrix;
- boundary quality: Boundary IoU (band BOUNDARY_BAND_PX) and HD95 in px, per-image means
  (HD95 is undefined when exactly one mask is empty; those images are counted apart);
- 95 % bootstrap intervals over images for the per-image means.
"""
import time

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

from roadanomaly import metrics
from roadanomaly.postprocessing import auprc
from roadanomaly.protocol import (
    BOOTSTRAP_ALPHA,
    BOOTSTRAP_SAMPLES,
    BOUNDARY_BAND_PX,
    FPR_LIMIT,
    MIN_OBJECT_PX,
    OBJECT_OVERLAP,
    SEED,
    SMALL_OBJECT_PX,
)

PIXEL_KEYS = ("precision", "recall", "f1", "iou", "dice")


def fpr_at_tpr(gt, scores, tpr=0.95):
    """False positive rate at the first threshold that finds `tpr` of the anomaly pixels."""
    fpr, tprs, _ = roc_curve(np.asarray(gt).ravel(), np.asarray(scores).ravel())
    return float(fpr[np.searchsorted(tprs, tpr, side="left")])


def threshold_free_scores(gt, scores):
    """AuPRC, AUROC, AUPRO (each next to its chance level) and FPR95 of score maps."""
    gt = np.asarray(gt).astype(bool)
    return {"AuPRC": auprc(gt, scores), "AuPRC chance": float(gt.mean()),
            "AUROC": float(roc_auc_score(gt.ravel(), np.asarray(scores).ravel())), "AUROC chance": 0.5,
            "FPR95": fpr_at_tpr(gt, scores),
            "AUPRO": metrics.aupro(list(gt), list(scores), MIN_OBJECT_PX, fpr_limit=FPR_LIMIT),
            "AUPRO chance": FPR_LIMIT / 2}


def mask_report(gt, masks):
    """Every thresholded metric of the protocol for a set of predicted masks."""
    gt = np.asarray(gt).astype(bool)
    pixel = metrics.evaluate_masks(list(gt), list(masks))
    objects = pd.DataFrame(
        [metrics.object_scores(g, m, MIN_OBJECT_PX, OBJECT_OVERLAP) for g, m in zip(gt, masks, strict=True)]
    )
    sizes = pd.DataFrame([metrics.object_recall_by_size(g, m, MIN_OBJECT_PX, SMALL_OBJECT_PX, OBJECT_OVERLAP)
                          for g, m in zip(gt, masks, strict=True)]).sum()
    tp, fp, fn, tn = metrics.confusion_counts(gt, np.asarray(masks))
    # Boundary metrics on speckle-free masks (both sides), in px at the working resolution
    clean = [(metrics.remove_small_components(g, MIN_OBJECT_PX), metrics.remove_small_components(m, MIN_OBJECT_PX))
             for g, m in zip(gt, masks, strict=True)]
    hd = np.array([metrics.hd95(g, m) for g, m in clean])
    boundary = {"boundary_iou": [metrics.boundary_iou(g, m, BOUNDARY_BAND_PX) for g, m in clean],
                "hd95_px": hd.tolist(), "hd95_undefined_images": int(np.isnan(hd).sum())}
    return {"pixel": pixel, "objects": objects, "sizes": sizes.to_dict(), "boundary": boundary,
            "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn}}


def bootstrap_table(report, keys=("f1", "iou", "precision", "recall")):
    """95 % bootstrap interval over images of the per-image pixel metrics and object F1."""
    rows = []
    for key in keys:
        mean, low, high = metrics.bootstrap_ci([s[key] for s in report["pixel"]["per_image"]],
                                               BOOTSTRAP_SAMPLES, BOOTSTRAP_ALPHA, SEED)
        rows.append({"metric": f"pixel {key}", "mean": mean, "low": low, "high": high})
    mean, low, high = metrics.bootstrap_ci(report["objects"]["object_f1"], BOOTSTRAP_SAMPLES, BOOTSTRAP_ALPHA, SEED)
    rows.append({"metric": "object f1", "mean": mean, "low": low, "high": high})
    return pd.DataFrame(rows)


def summary(free, report):
    """Main protocol numbers of one model on one split, as a flat dict (one table column)."""
    pixel, objects, sizes = report["pixel"]["per_image_mean"], report["objects"], report["sizes"]
    return {"AuPRC (main)": free["AuPRC"], "AUROC": free["AUROC"], f"AUPRO@{FPR_LIMIT}": free["AUPRO"],
            "FPR95 (lower is better)": free["FPR95"],
            "F1 = Dice (per-image mean)": pixel["f1"], "IoU (per-image mean)": pixel["iou"],
            "precision (per-image mean)": pixel["precision"], "recall (per-image mean)": pixel["recall"],
            "F1 (aggregated)": report["pixel"]["aggregated"]["f1"],
            f"Boundary IoU ({BOUNDARY_BAND_PX} px band)": float(np.mean(report["boundary"]["boundary_iou"])),
            "HD95 px (lower is better)": float(np.nanmean(report["boundary"]["hd95_px"])),
            "objects detected": f"{objects['detected'].sum()}/{objects['gt_objects'].sum()}",
            "small objects detected": f"{sizes['small_detected']}/{sizes['small_total']}",
            "false alarms / predicted blobs": f"{objects['false_alarms'].sum()}/{objects['pred_objects'].sum()}"}


def per_image_table(frames, gt, report):
    """One row per image: anomaly share, pixel metrics and object counts."""
    gt = np.asarray(gt).astype(bool)
    table = pd.DataFrame(report["pixel"]["per_image"])[list(PIXEL_KEYS[:4])]
    table.insert(0, "frame", list(frames))
    table["anomaly %"] = 100 * gt.mean(axis=(1, 2))
    for column in ("gt_objects", "detected", "false_alarms"):
        table[column] = report["objects"][column].values
    return table


def trivial_baselines(gt):
    """Per-image mean scores of the 'all background' and 'all anomaly' predictors: the floor to beat."""
    gt = np.asarray(gt).astype(bool)
    return {name: metrics.evaluate_masks(list(gt), list(pred))["per_image_mean"]
            for name, pred in [("all background", np.zeros_like(gt)), ("all anomaly", np.ones_like(gt))]}


def paired_difference(values_a, values_b):
    """Mean per-image difference A - B with a 95 % paired bootstrap interval over the same images.

    Both models are scored on the same images, so resampling the images keeps the pairs and
    removes the image-difficulty variance that unpaired intervals include. If the interval
    contains 0, the difference is not established on this test set.
    """
    differences = np.asarray(values_a, dtype=float) - np.asarray(values_b, dtype=float)
    return metrics.bootstrap_ci(differences, BOOTSTRAP_SAMPLES, BOOTSTRAP_ALPHA, SEED)


def latency_ms(predict_fn, images, repeats=3):
    """Mean inference time per image in ms, after one warm-up call (score map + mask, batch of `images`)."""
    predict_fn(images[:1])
    start = time.perf_counter()
    for _ in range(repeats):
        predict_fn(images)
    return 1000 * (time.perf_counter() - start) / (repeats * len(images))
