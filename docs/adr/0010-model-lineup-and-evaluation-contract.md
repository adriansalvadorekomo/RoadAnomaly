# 0010. Model lineup and evaluation contract

- **Status:** Accepted (target state; implementation not started)
- **Date:** 2026-10-21
- **Deciders:** whole team
- **Supersedes:** [ADR-0002](0002-three-model-families.md)
- **Amends:** the model-family clause in [ADR-0005](0005-tensorflow-framework.md)
- **Related:** [ADR-0001](0001-evaluation-only-benchmark.md),
  [ADR-0008](0008-promotion-and-model-registry.md), [ADR-0011](0011-xai-methods-and-faithfulness.md)

## Context

The project is a Deep Learning module project on RoadAnomaly, a 60-frame
pixel-level anomaly benchmark. The repository tracks the benchmark, its
contract tests and the delivery guard rails, but no model, training run, metric
implementation or API exists yet.

The earlier three-family decision named an autoencoder, image resynthesis and a
generic transfer-learned segmentation model. The revised project plan narrows
the comparison to three architectures that can share one anomaly-score
interface:

- an autoencoder that scores reconstruction error;
- U-Net, a CNN encoder-decoder segmentation baseline with skip connections;
- DeepLabV3+, a transfer-learned multi-class segmentation model with an ASPP
  encoder and a decoder.

The revision also defines a common evaluation vocabulary. Precision, recall,
F1, IoU and Dice are comparable across all three models when each produces a
binary anomaly mask. AUROC/AUPRO, HD95, mIoU and Boundary IoU are complementary
diagnostics for the model families where they are meaningful.

Two constraints from the existing protocol remain non-negotiable:

1. RoadAnomaly is evaluation-only. No weight update, early stopping, threshold
   sweep, model choice or registry alias may be fitted on its 60 frames.
2. The normal-road corpus, its segmentation labels and its scene-grouped split
   manifest are not yet pinned. This ADR records the target contract; it does
   not claim that training is reproducible today.

## Decision

### Model lineup

| ID | Model | Native task | Anomaly score | Planned status |
|---|---|---|---|---|
| `autoencoder` | Convolutional autoencoder | Reconstruct normal road scenes | Per-pixel reconstruction error | not implemented |
| `unet` | U-Net | Normal-road multi-class segmentation | `1 - max softmax` (MSP) | not implemented |
| `deeplabv3plus` | DeepLabV3+ | Normal-road multi-class segmentation | `1 - max softmax` (MSP) | not implemented |

- Image resynthesis is retired from the three-model comparison. The Lis et al.
  paper remains the RoadAnomaly dataset reference and related work.
- U-Net and DeepLabV3+ are trained on the same normal-road semantic labels and
  class map. Their anomaly score is the same MSP function, so the benchmark
  comparison changes the architecture rather than the scoring rule.
- No model is trained on RoadAnomaly, and no train/validation/test split of the
  60 benchmark frames is permitted. A binary anomaly target is produced only
  when a model's score map is thresholded for evaluation.
- Model IDs are stable and semantic. `A`, `B` and `C` remain useful in prose
  only when referring to historical ADR-0002.

### Evaluation layers

| Layer | Data | Metrics | Rights |
|---|---|---|---|
| Native normal-road validation | Pinned normal-road release and scene-grouped validation folds | Autoencoder: reconstruction loss; U-Net: Dice, IoU, HD95; DeepLabV3+: mIoU, Boundary IoU | Selection evidence and scorecard input only |
| Common RoadAnomaly benchmark | All 60 held-out frames, zero-shot and separately threshold-tuned | Precision, recall, F1, IoU, Dice for all models | Report-only; never selects or promotes |
| Complementary RoadAnomaly diagnostics | Same held-out frames | Autoencoder: AUROC, AUPRO; U-Net: HD95; DeepLabV3+: mIoU, Boundary IoU | Report-only |
| XAI faithfulness | Selected model and evaluation frames | Deletion/insertion, pointing game, baselines | Report-only; see ADR-0011 |

- F1 and Dice are identical for a binary mask. The report must say so instead of
  presenting them as independent evidence.
- Thresholds are fixed on normal-road validation. The separately reported
  threshold-tuned regime may choose one scalar on scene-grouped RoadAnomaly
  folds under ADR-0001, but that scalar never promotes a model.
- The metric contract is specified in [`docs/metrics.md`](../metrics.md). The
  eventual implementation lives once in `dl/evaluation/metrics.py`; a second
  implementation is a bug.
- AUROC and AUPRO require ground truth and are reported with the AUPRO
  false-positive-rate integration limit. HD95 is reported in pixels with its
  spacing and empty-mask policy. Boundary IoU reports its band width. mIoU is
  reported per class as well as averaged.

### Selection and registry

The native metrics are not directly comparable across a reconstruction model
and two segmentation models. There is no automatic cross-family argmax.

The selected alias is chosen by a written normal-road scorecard that records:

- the native metrics and their uncertainty;
- the chosen operating threshold and how it was fixed;
- the qualitative failure modes observed on normal-road validation;
- the reason the selected candidate is preferred.

The scorecard and `selected.json` never contain a RoadAnomaly number. All three
candidate SavedModels and their manifests remain in the registry; the alias is
a pointer, not a replacement. This implements ADR-0008 without inventing a
single metric that the project cannot compute.

## Consequences

**What gets easier.** The three models share a score-map interface, a metric
vocabulary and a selection record. The report can distinguish common benchmark
evidence from model-specific diagnostics. Retiring resynthesis removes a
training pipeline that was never started and was not in the revised plan.

**What gets harder.** U-Net and DeepLabV3+ need pinned normal-road segmentation
labels, a class map and a label-aware manifest before either can train. The
common benchmark metrics are report-only, so selection still depends on a
documented judgement rather than a single number.

**What we will not claim.** The repository does not implement any of these
models or metrics today. The README results table stays empty until an
experiment record traces a value to a commit, config, manifest, command and
hardware. Illustrative calculations from planning documents are not project
results.

## Alternatives considered

| Option | Why not |
|---|---|
| Keep image resynthesis as the third model | It is not in the revised plan; it adds a training pipeline without resolving the normal-road data blocker |
| Train U-Net/DeepLabV3+ on RoadAnomaly masks | Violates ADR-0001 and tests the models on their training distribution |
| Use RoadAnomaly to choose the best model | Benchmark-to-registry promotion; explicitly forbidden |
| Select by one pooled score across different native metrics | The metrics measure different tasks and are not commensurable |
| Add a separate image-level classifier | Not part of the revised three-model comparison; DeepLabV3+ already provides dense multi-class classification |

## How we would know this was wrong

If the normal-road corpus cannot supply segmentation labels for U-Net and
DeepLabV3+, or if the MSP score is not a defensible anomaly signal on the
normal-road validation folds, the segmentation comparison must be re-scoped
before a benchmark number is published.
