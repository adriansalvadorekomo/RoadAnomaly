# 0000. Experiment title

- **Date:** YYYY-MM-DD
- **Owner:** M?
- **CRISP-DM phase:** 4 Modeling / 5 Evaluation
- **Hypothesis:** What would be true if this run worked?
- **Falsification:** What result would make you reject the hypothesis?

## Provenance

| Field | Value |
|---|---|
| Git commit | `<full sha>` |
| Config | `configs/<name>.yaml` |
| Config hash | `sha256:...` |
| Command | `make train CONFIG=...` / `make eval ...` |
| Seed | e.g. `1337` |
| Python / TensorFlow | `3.12` / `2.21.x` |
| Hardware | CPU model or GPU, driver/CUDA if relevant |
| Normal-road dataset manifest | `configs/datasets/<name>.yaml` + `sha256:...` |
| Scene-grouped split hash | `sha256:...` |
| RoadAnomaly benchmark | `data/` at commit `<sha>`; `data/credits.txt` unchanged |
| Artifact / registry digest | `sha256:...` or `not exported` |

A run without a dataset manifest, split hash and config hash is not a valid
experiment, even if it produced a number.

## Results

| Regime | Set | Metric | Value | Notes |
|---|---|---|---|---|
| Normal-road validation (selection) | scene-grouped fold | IoU / Dice / F1 / AUPRC | | This is the only selection signal |
| RoadAnomaly held-out — zero-shot | all 60 frames | IoU / Dice / F1 / AUPRC | | Report only; never tuned |
| RoadAnomaly held-out — threshold-tuned | held-out folds | IoU / Dice / F1 / AUPRC | | One scalar threshold; report separately |
| XAI | selected model | method + faithfulness check | | Only when the method is chosen (G1) |

Do not put RoadAnomaly metrics in the selection column. Do not mix zero-shot and
threshold-tuned values in one cell.

## Interpretation

What happened, what failed, and what the next run should change. Include the
per-frame worst case, not only the mean, when RoadAnomaly is scored.

## Links

- Architecture: [`docs/architecture/README.md`](../architecture/README.md)
- Promotion rule: [`ADR-0008`](../adr/0008-promotion-and-model-registry.md)
- XAI gate: [`ADR-0009`](../adr/0009-xai-evaluation-gate.md)
