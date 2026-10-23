# `dl/` — models, training and evaluation

Owner: **M1–M4** (see `.github/CODEOWNERS`).

```
dl/
├── data/         dataset loading, mask decoding, splits, transforms      (M1)
├── models/       autoencoder.py · unet.py · deeplabv3plus.py             (M2 M3 M4)
├── training/     train.py — one loop for all three models                (M2)
├── evaluation/   metrics.py + evaluate.py — the shared scoring harness   (M4)
├── inference/    checkpoint -> SavedModel + scoring helpers                (M4)
└── notebooks/    template_road_anomaly.ipynb — guided end-to-end client   (all)
                  01_dataset_eda · 02_deeplabv3plus · 03_autoencoder
                  04_cnn_unet · 05_xai — specialized clients (planned)
```

The notebook map, roles and concept-check policy are in
[`notebooks/README.md`](notebooks/README.md); the feature contract is
[`specs/002-notebook-workflow/spec.md`](../specs/002-notebook-workflow/spec.md).

Experiment configs live at the repository root in `configs/`, one YAML per
run (e.g. `configs/autoencoder.yaml`, `configs/smoke.yaml`).

## The three rules that keep this package coherent

1. **Notebooks are clients, not implementations.** They import from `dl/` and
   inspect the outputs. A short cell tagged `concept-check` may demonstrate an
   idea on toy data, but no authoritative model, training loop, metric,
   threshold, post-processing or XAI method may be defined there. A result that
   exists only inside a notebook is not official evidence; if it is recorded at
   all, it is a learning record.
2. **Every model implements the same interface** — a module with
   `build(config)`, `predict(batch) -> score_map`, and `export(saved_model_dir)`,
   so `dl/evaluation/` can score any of them without knowing which it is.
3. **Metrics and XAI live in exactly one place** — `dl/evaluation/metrics.py`
   and `dl/evaluation/xai.py` (planned). If a model needs a new metric, it gets
   added there, once, for all three. F1 and Dice are the same binary-mask
   metric, not two results.

Official runs use `profile: official` and write to `docs/experiments/`.
Notebook runs use `profile: learning` and write to
`docs/experiments/learning/`; they are reproducible learning records, never
published evidence or promotion candidates.

The template is preserved as the central guided tour. Its inline code cells are
legacy stubs being migrated into `dl/`; until that migration lands, the notebook
banner marks them non-authoritative.

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
