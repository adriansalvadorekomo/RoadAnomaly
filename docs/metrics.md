# Metrics contract

> **Status:** planned contract. `dl/evaluation/metrics.py` does not exist yet.
> This file defines what the implementation must compute; it is not evidence
> that a metric has been run. No value from this document is a project result.

The evaluation has two layers that are never mixed:

1. **Native normal-road validation** supplies the selection scorecard.
2. **Held-out RoadAnomaly scoring** is report-only and never selects or
   promotes a model.

XAI faithfulness metrics are defined separately in [`docs/xai.md`](xai.md).
They evaluate an explanation, not a model, and never enter selection.

## Common RoadAnomaly binary metrics

Every model emits a per-pixel anomaly score map. A threshold fixed on normal-road
validation turns it into a binary mask (`anomaly` / `background`). The following
metrics are reported for all three models:

| Metric | Definition | Notes |
|---|---|---|
| Precision | `TP / (TP + FP)` | Thresholded; report per frame and pooled |
| Recall | `TP / (TP + FN)` | Thresholded; same mask as precision |
| F1 | `2PR / (P + R)` | For a binary mask, F1 equals Dice; do not present them as independent evidence |
| IoU | `TP / (TP + FP + FN)` | Jaccard index; always `IoU <= Dice` for the same mask |
| Dice | `2TP / (2TP + FP + FN)` | For a binary mask, Dice equals F1 |

Rules:

- RoadAnomaly label value `2` maps to anomaly and `0` to background. Any
  documented ignore/void value is excluded before counting.
- Report the per-frame distribution (including worst frames), not only the mean.
  A pixel-pooled value may be reported beside it but must not replace it.
- The zero-shot and threshold-tuned regimes are separate columns. The
  threshold-tuned scalar is chosen on scene-grouped benchmark folds for the
  report only and never promotes a model.
- The threshold used for the primary binary metrics is fixed on normal-road
  validation. If a benchmark-tuned threshold is reported, label the regime
  explicitly.
- An empty ground-truth mask is not silently scored as a perfect frame. The
  implementation defines and tests its empty-mask policy; the result is
  reported with the frame count.

## Complementary model diagnostics

These are not a second selection signal. They explain a model family where the
binary-mask metrics alone are not enough.

### Autoencoder: AUROC and AUPRO

- **AUROC** is the area under the receiver-operating-characteristic curve over
  pixel scores. It is threshold-free and sensitive to class imbalance; report
  it with the anomaly pixel ratio.
- **AUPRO** is the area under the per-region overlap curve. Report the
  false-positive-rate integration limit with every value. The primary protocol
  uses `AUPRO@30%` (FPR `<= 0.30`) for comparability with the anomaly-detection
  literature and may also report `AUPRO@5%` as a strict secondary value. A
  value without its cap is incomplete.
- AUROC and AUPRO require a ground-truth anomaly mask and are therefore
  RoadAnomaly diagnostics, not normal-road selection metrics.

### U-Net: HD95

- **HD95** is the 95th percentile of the symmetric boundary-distance
  distribution. Report it in pixels, record the pixel spacing if it is not 1:1,
  and state the empty-prediction/empty-ground-truth policy. Lower is better.
- HD95 is computed on the normal-road segmentation validation set and, when a
  binary anomaly mask exists, on the held-out benchmark as a report-only
  boundary diagnostic.

### DeepLabV3+: mIoU and Boundary IoU

- **mIoU** is the mean IoU over the evaluated classes. Report per-class IoU and
  the class set; do not hide a failed class behind the mean. Void/ignore labels
  are excluded.
- **Boundary IoU** measures IoU in a band around the ground-truth and predicted
  boundaries. Report the band width with the value. The default is 2 % of the
  image diagonal unless an experiment record states otherwise.
- These are native normal-road segmentation diagnostics; any benchmark use is
  report-only and must state its target definition.

## Optional secondary diagnostics

AUPRC and FPR@95 are not part of the primary comparison in this revision. If an
experiment reports them, it must label them as secondary, compute them for every
model in the same table, and keep them out of selection.

## Metric invariants

The eventual unit tests must assert at least:

- for a binary mask, `F1 == Dice`;
- `IoU <= Dice` for the same mask;
- precision and recall are zero-safe when their denominators are zero;
- the AUPRO integration limit is recorded in the result object;
- HD95 is in pixels and its empty-mask policy is explicit;
- mIoU is the mean of the per-class values, not a pixel average.

## Selection scorecard

Native metrics are not commensurable across reconstruction and segmentation
models. There is no automatic cross-family ranking. `selected.json` records the
alias and the scorecard reference; the scorecard records the native metrics,
uncertainty, threshold, failure modes and rationale. It contains no
RoadAnomaly number.

## Provenance

A published metric must trace to an experiment record in `docs/experiments/`
with the commit, config, dataset manifest, split hash, command and hardware.
Illustrative values from planning documents are not results.
