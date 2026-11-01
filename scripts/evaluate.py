"""Evaluate one saved model (models/<name>/) on a split with the shared protocol, from the command line.

    python scripts/evaluate.py --model B_feature_ae --split val
    mise run evaluate B_feature_ae val

The official test evaluation of all models is notebook 5; use --split test only to reproduce it.
"""
import argparse
import json

import numpy as np
import pandas as pd

from roadanomaly import data_pipeline as dp, evaluation
from roadanomaly.inference import Predictor, available_models
from roadanomaly.protocol import IMG_SIZE


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, choices=available_models(dp.MODELS_DIR))
    parser.add_argument("--split", choices=("train", "val", "test"), default="val")
    parser.add_argument("--output", help="optional JSON file for the full report")
    args = parser.parse_args()
    if args.split == "test":
        print("Note: the test split is for the final comparison (notebook 5); nothing may be tuned on it.")

    predictor = Predictor(dp.MODELS_DIR / args.model)
    frames, images, masks = dp.load_split(args.split, IMG_SIZE)
    gt = masks[..., 0].astype(bool)
    out = predictor.predict(images)
    free = evaluation.threshold_free_scores(gt, out["scores"])
    report = evaluation.mask_report(gt, out["masks"])

    print(f"{predictor.config['title']} on {args.split} ({len(frames)} images)")
    print(pd.Series(evaluation.summary(free, report)).to_string())
    print(evaluation.bootstrap_table(report).round(3).to_string(index=False))
    if args.output:
        payload = {"model": args.model, "split": args.split, "frames": frames, "threshold_free": free,
                   "pixel": report["pixel"], "objects": report["objects"].to_dict(orient="list"),
                   "boundary": report["boundary"], "confusion": report["confusion"]}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=lambda v: v.item() if isinstance(v, np.generic) else str(v))
        print("saved", args.output)


if __name__ == "__main__":
    main()
