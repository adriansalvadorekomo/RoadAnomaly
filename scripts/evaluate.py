"""Évalue le détecteur sur un split explicitement choisi."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from roadanomaly import data_pipeline as dp, metrics
from roadanomaly.anomaly_detector import AnomalyDetector

IMG_SIZE = (352, 640)
MIN_OBJECT_PX = 4
SMALL_OBJECT_PX = round(1000 * (352 / 720) ** 2)
FPR_LIMIT = 0.3


def evaluate_split(
    detector: AnomalyDetector,
    split: str,
    manifest_path: Path,
    data_dir: Path,
) -> dict[str, Any]:
    """Calcule les métriques du protocole pour un split."""
    frames, images, masks = dp.load_split(
        split, IMG_SIZE, manifest_path=manifest_path, data_dir=data_dir
    )
    predictions = [detector.predict(image) for image in images]
    score_maps = [prediction["score_map"] for prediction in predictions]
    predicted_masks = [prediction["mask"] for prediction in predictions]
    ground_truth = [mask[..., 0].astype(bool) for mask in masks]

    threshold_free = {
        "auprc": float(
            average_precision_score(
                np.concatenate([mask.ravel() for mask in ground_truth]),
                np.concatenate([score.ravel() for score in score_maps]),
            )
        ),
        "auroc": float(
            roc_auc_score(
                np.concatenate([mask.ravel() for mask in ground_truth]),
                np.concatenate([score.ravel() for score in score_maps]),
            )
        ),
        "aupro_at_fpr_0_3": float(
            metrics.aupro(ground_truth, score_maps, MIN_OBJECT_PX, fpr_limit=FPR_LIMIT)
        ),
        "auprc_chance_prevalence": float(np.mean([mask.mean() for mask in ground_truth])),
        "auroc_chance": 0.5,
        "aupro_chance_at_fpr_0_3": FPR_LIMIT / 2,
    }
    pixel_metrics = metrics.evaluate_masks(ground_truth, predicted_masks)
    per_image = []
    object_rows = []
    size_totals = {
        "small_detected": 0,
        "small_total": 0,
        "large_detected": 0,
        "large_total": 0,
    }
    false_alarms = 0
    object_totals = {"gt_objects": 0, "detected": 0, "pred_objects": 0}
    confusion = np.zeros(4, dtype=np.int64)
    for frame, truth, prediction in zip(frames, ground_truth, predicted_masks):
        pixel = metrics.segmentation_scores(truth, prediction)
        objects = metrics.object_scores(truth, prediction, MIN_OBJECT_PX)
        tp, fp, fn, tn = metrics.confusion_counts(truth, prediction)
        confusion += (tp, fp, fn, tn)
        sizes = metrics.object_recall_by_size(
            truth, prediction, MIN_OBJECT_PX, SMALL_OBJECT_PX
        )
        for key in size_totals:
            size_totals[key] += sizes[key]
        false_alarms += objects["false_alarms"]
        for key in object_totals:
            object_totals[key] += objects[key]
        per_image.append({"frame": frame, **pixel})
        object_rows.append({"frame": frame, **objects, **sizes})

    report = {
        "split": split,
        "frames": frames,
        "threshold_free": threshold_free,
        "pixel": pixel_metrics,
        "objects": object_rows,
        "object_totals": object_totals,
        "object_recall_by_size": size_totals,
        "false_positive_blobs": int(false_alarms),
        "confusion_counts": {
            key: int(value)
            for key, value in zip(("tp", "fp", "fn", "tn"), confusion)
        },
        "per_image": per_image,
        "threshold": detector.threshold,
        "sigma": detector.sigma,
    }
    if split == "test":
        report["bootstrap_95_percent_images"] = {
            metric_name: dict(
                zip(
                    ("mean", "low", "high"),
                    metrics.bootstrap_ci(
                        [row[metric_name] for row in pixel_metrics["per_image"]],
                        n_boot=2000,
                        alpha=0.05,
                        seed=1337,
                    ),
                )
            )
            for metric_name in ("precision", "recall", "f1", "iou", "dice")
        }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=dp.REPO_ROOT / "models" / "B_best_config.json")
    parser.add_argument("--split", choices=("train", "val", "test"), required=True)
    parser.add_argument("--manifest", type=Path, default=dp.MANIFEST_PATH)
    parser.add_argument("--data-dir", type=Path, default=dp.DATA_DIR)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.split == "test":
        print(
            "AVERTISSEMENT : Test consulté lors d'une itération antérieure ; résultats "
            "exploratoires ; aucune décision modèle/post-traitement/XAI ne doit en découler."
        )
    detector = AnomalyDetector(args.config)
    report = evaluate_split(detector, args.split, args.manifest, args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["threshold_free"], indent=2))
    print(json.dumps(report["pixel"], indent=2))
    print(f"Rapport sauvegardé : {args.output}")


if __name__ == "__main__":
    main()
