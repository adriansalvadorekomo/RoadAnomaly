# `ml/` — models, training and evaluation

Owner: **M1–M4** (see `.github/CODEOWNERS`).

```
ml/
├── data/         dataset loading, mask decoding, splits, transforms      (M1)
├── models/       autoencoder.py · resynthesis.py · segmentation.py       (M2 M3 M4)
├── training/     train.py, one loop for all three models                 (M2)
├── evaluation/   metrics.py + evaluate.py — the shared scoring harness   (M4)
├── export/       checkpoint -> TorchScript/ONNX for the API              (M4)
├── configs/      one YAML per experiment, e.g. ae.yaml, smoke.yaml        (all)
└── notebooks/    01_dataset_eda · 02_baseline_ae · 03_resynthesis
                  04_comparison — narrative only, no model logic           (all)
```

## The three rules that keep this package coherent

1. **Notebooks contain no model logic.** They import from `ml/`. A result that
   only exists inside a notebook cannot be re-run by CI or by the API.
2. **Every model implements the same interface** — a module with
   `build(config)`, `forward(batch) -> score_map`, and `save/load` — so
   `ml/evaluation/` can score any of them without knowing which it is.
3. **Metrics live in exactly one place** (`ml/evaluation/metrics.py`). If a
   model needs a new metric, it gets added there, once, for all three.

## Splitting policy

See [ADR-0001](../docs/adr/0001-evaluation-only-benchmark.md): RoadAnomaly is
**evaluation-only**. Train on normal-road data, evaluate on all 60 frames,
tune thresholds with scene-grouped k-fold. Never fit weights on the 60 frames.
