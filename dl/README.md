# `dl/` — models, training and evaluation

Owner: **M1–M4** (see `.github/CODEOWNERS`).

```
dl/
├── data/         dataset loading, mask decoding, splits, transforms      (M1)
├── models/       autoencoder.py · unet.py · deeplabv3plus.py             (M2 M3 M4)
├── training/     train.py — one loop for all three models                (M2)
├── evaluation/   metrics.py + evaluate.py — the shared scoring harness   (M4)
├── inference/    checkpoint -> SavedModel + scoring helpers                (M4)
└── notebooks/    01_dataset_eda · 02_autoencoder · 03_segmentation
                  04_comparison · 05_xai — narrative only, no model logic  (all)
```

Experiment configs live at the repository root in `configs/`, one YAML per
run (e.g. `configs/autoencoder.yaml`, `configs/smoke.yaml`).

## The three rules that keep this package coherent

1. **Notebooks contain no model logic.** They import from `dl/`. A result that
   only exists inside a notebook cannot be re-run by CI or by the API.
2. **Every model implements the same interface** — a module with
   `build(config)`, `predict(batch) -> score_map`, and `export(saved_model_dir)`,
   so `dl/evaluation/` can score any of them without knowing which it is.
3. **Metrics and XAI live in exactly one place** — `dl/evaluation/metrics.py`
   and `dl/evaluation/xai.py` (planned). If a model needs a new metric, it gets
   added there, once, for all three. F1 and Dice are the same binary-mask
   metric, not two results.

## Model lineup

The current lineup and contract are [ADR-0010](../docs/adr/0010-model-lineup-and-evaluation-contract.md):
`autoencoder` (reconstruction error), `unet` (`1 - max softmax`) and
`deeplabv3plus` (`1 - max softmax`). U-Net and DeepLabV3+ train on the same
normal-road semantic labels. No binary anomaly training, and no train/validation/
test split of the 60 benchmark frames.

## Splitting policy

See [ADR-0001](../docs/adr/0001-evaluation-only-benchmark.md): RoadAnomaly is
**evaluation-only**. Train on normal-road data, evaluate on all 60 frames,
tune thresholds with scene-grouped k-fold. Never fit weights on the 60 frames.

Metric definitions are in [`docs/metrics.md`](../docs/metrics.md); the XAI
methods and faithfulness checks are in [`docs/xai.md`](../docs/xai.md). Neither
has an implementation yet.
