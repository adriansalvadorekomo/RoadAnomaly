# 0001. Treat RoadAnomaly as an evaluation-only benchmark

- **Status:** Accepted
- **Date:** 2026-10-18
- **Deciders:** whole team

## Context

The RoadAnomaly dataset folder in this repository contains 60 images, each
with a pixel-level mask. Every pixel in those masks is either **0 (normal
road scene)** or **2 (the anomalous object)**. There is no image without an
anomaly in it.

That means the standard supervised recipe — random split, train on 70 %, report
test metrics — is not available. A model trained to predict "anomaly" on these
60 images would be trained on exactly the evaluation set, and any number it
produced would be meaningless. This is the single most common way this
particular project goes wrong, so the protocol is written down before any
model code exists.

The paper the module points at (Lis et al., *Detecting the Unexpected via Image
Resynthesis*, ICCV 2019) faces the same situation: the anomalies are exactly
what was never seen during training.

## Decision

RoadAnomaly is used **exclusively for evaluation**, never for fitting model
weights.

1. **Training data comes from elsewhere.** Models are pre-trained on normal
   road scenes (Cityscapes/BDD100K normal subsets and/or ImageNet backbones),
   where *no* anomaly class exists. The anomaly is learned as "something that
   does not look like a road scene".
2. **All 60 frames are reported.** We report metrics on the full set, not on a
   hand-picked subset, and we publish the per-frame IoU distribution rather
   than only the mean, because the mean hides catastrophic frames.
3. **Splitting is for tuning only.** Where a split is needed (threshold
   selection, early stopping) we use **k-fold grouped by scene** — the
   `animals*`, `cones*`, `obstacles*`, `lost_tires*`, `vehicle*` prefixes —
   so a source image cannot appear in two folds. Any tuned value is then
   reported as such.
4. **Two evaluation regimes are distinguished in every results table.**
   *Zero-shot* (never saw an anomaly) and *threshold-tuned* (one scalar
   chosen on held-out folds). Mixing them in one column would silently
   inflate the numbers.

## Alternatives considered

| Option | Why not |
|---|---|
| Random 70/15/15 split over the 60 frames | Leaks the evaluation set into training; the reported test metrics would be optimistic by construction |
| Train a binary segmentation head directly on the 60 masks | The model can memorise the 60 scenes; a 60-image training set cannot support the claim "detects unexpected objects" |
| Report only on a curated "good" subset of frames | Selection bias; publish the failures instead |

## Consequences

**What gets easier.** Every number we report answers the question the module
actually asks: *can this detect something it has never seen?* Results are
comparable with the published literature, and the protocol defends itself in
the report.

**What gets harder.** We must obtain and prepare a normal-road training set,
which is more work than `train_test_split`. Threshold selection costs an extra
k-fold evaluation pass.

**How we would know this was wrong.** An additional normal-road dataset (or a
second anomaly dataset) becoming available would allow real held-out splitting
— at which point supervised training becomes defensible and this ADR should be
revisited.
