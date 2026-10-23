# 0000. Experiment title

> Copy this file to `NNNN-short-name.md` for an official run, or to
> `learning/NNNN-short-name.md` for a learning run. The profile and the directory
> must agree. A learning record never supports a README or report number.

- **Date:** YYYY-MM-DD
- **Owner:** M?
- **Profile:** `official` or `learning`
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
| Model ID | `autoencoder` / `unet` / `deeplabv3plus` |
| Normal-road dataset manifest | `configs/datasets/<name>.yaml` + `sha256:...` |
| Scene-grouped split hash | `sha256:...` |
| RoadAnomaly benchmark | `data/` at commit `<sha>`; `data/credits.txt` unchanged |
| Artifact / registry digest | `sha256:...` or `not exported` |

An official run without a dataset manifest, split hash and config hash is not a
valid experiment, even if it produced a number. A learning run records the same
provenance where it applies, but its `Profile: learning` mark keeps it outside
the official evidence chain.

## Results

Common binary-mask metrics are Precision, Recall, F1, IoU and Dice. F1 and Dice
are identical for a binary mask; report that once instead of treating them as
independent evidence.

| Regime | Set | Model | Common metrics | Complementary diagnostic | Notes |
|---|---|---|---|---|---|
| Normal-road validation (selection) | scene-grouped fold | | P / R / F1 / IoU / Dice | AE: reconstruction loss; U-Net: Dice/IoU/F1/HD95; DeepLab: mIoU/Boundary IoU | Only selection signal |
| RoadAnomaly held-out — zero-shot | all 60 frames | | P / R / F1 / IoU / Dice | AE: AUROC/AUPRO@30%; U-Net: HD95; DeepLab: mIoU/Boundary IoU | Report only; never tuned |
| RoadAnomaly held-out — threshold-tuned | held-out folds | | P / R / F1 / IoU / Dice | same as above | One scalar threshold; separate column |

Do not put RoadAnomaly metrics in the selection column. Do not mix zero-shot and
threshold-tuned values in one cell. Record the AUPRO FPR cap, HD95 spacing and
empty-mask policy, and Boundary IoU band width with the value.

A learning record may use a narrower table for the exercise. Mark those results
exploratory and keep them out of the official scorecard; to cite a value, rerun
it under an official config.

## XAI evidence

XAI is report-only and never enters the selection scorecard.

| Model | Method | Target layer/class/pixel | Faithfulness checks | Baselines | Artefact |
|---|---|---|---|---|---|
| | reconstruction error / Seg-Grad-CAM / Integrated Gradients | | deletion-insertion AUC, pointing game (segmentation only) | deletion/insertion: random, center prior; pointing: random hit | heatmap/error-map path + digest |

The method decision and evidence format are in
[`docs/xai.md`](../xai.md) and [ADR-0011](../adr/0011-xai-methods-and-faithfulness.md).

## Interpretation

What happened, what failed, and what the next run should change. Include the
per-frame worst case, not only the mean, when RoadAnomaly is scored.

## Links

- Architecture: [`docs/architecture/README.md`](../architecture/README.md)
- Metric contract: [`docs/metrics.md`](../metrics.md)
- Model and evaluation contract: [`ADR-0010`](../adr/0010-model-lineup-and-evaluation-contract.md)
- Promotion rule: [`ADR-0008`](../adr/0008-promotion-and-model-registry.md)
- XAI methods: [`docs/xai.md`](../xai.md), [`ADR-0011`](../adr/0011-xai-methods-and-faithfulness.md)
