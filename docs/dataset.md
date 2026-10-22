# Dataset and evaluation protocol

The 60 RoadAnomaly frames in `data/` are the held-out evaluation set. They are
tracked in git (15 MB) so a clone is reproducible, and `tests/dataset/` asserts
the contract below. If this file and `data/readme.md` disagree, the original
authors' `data/readme.md` wins.

## Verified facts

| Property | Value |
|---|---|
| Images | **60** frames, `data/frames/*.webp`, all **1280 × 720**, RGB |
| Index | `data/frame_list.json` — frame order used by every loader |
| Annotation dirs | **60** — one `<frame>.labels/` per frame |
| Semantic masks | `labels_semantic.png`, uint8, **{0 = normal, 2 = anomaly}** in all 60 |
| Colour masks | `labels_semantic_color.png` — black = normal, orange `#FF4500` = anomaly |
| Instance masks | `labels_instance.png` in **46** frames; pixel value = instance id |
| Instances | **201** bounding regions, all `cls = 2` (one anomaly class) |
| Semantic-only frames | **14** — annotated but with no instance masks |
| Anomaly coverage | **9.8 %** of all pixels; per frame **0.4 % → 42.3 %** (median 6.6 %) |
| Object scale | median instance ≈ **87 × 87 px**; **35 of 201** are smaller than 32 × 32 px |
| Categories | animals 31 · obstacles 15 · cones 8 · lost_tires 3 · vehicle 3 |
| Attribution | [`data/credits.txt`](../data/credits.txt) — per-image author, source and licence |

**Category distribution** (by frame-name prefix, the natural scene grouping):

```text
animals     31  ███████████████████████████████
obstacles   15  ███████████████
cones        8  ████████
lost_tires   3  ███
vehicle      3  ███
```

Inside a label directory the loader uses `labels_semantic.png`,
`labels_semantic_color.png`, `labels_instance.png` and `index.json`. The
GrabCut editor state (`instance_XXX_gc_mask.png` and
`instance_XXX_gc_state.npy`) is kept for provenance only and is never read.

## Why the benchmark is hard

- **Long tail of scale.** 17 % of instances are under 32 × 32 px, while in some
  frames the anomaly covers more than 40 % of the image. One operating threshold
  cannot serve both, so results report per-frame distributions, not just means.
- **Uneven coverage.** Six frames contain under 1 % anomalous pixels. A model
  that predicts "all normal" scores well on those and poorly overall; a single
  aggregate hides the failure that matters.
- **Single class, no hierarchy.** `cls = 2` for every instance means the project
  can measure localisation but not recognition. It does not claim to know a deer
  from a cone.

## Evaluation-only protocol

**RoadAnomaly is an evaluation-only benchmark. We never fit weights on its 60
frames.** Every mask contains normal pixels and an anomaly; there is no image
without something abnormal. The usual "random split, train, report test metrics"
recipe is unavailable: any model trained here would be tested on its own
training set.

The protocol in [ADR-0001](adr/0001-evaluation-only-benchmark.md):

1. **Train on normal** — Cityscapes/BDD100K normal subsets with a pinned release
   and scene-grouped split manifest, plus ImageNet-pretrained backbones. The
   anomaly is defined by absence, never shown as a class.
2. **Report all 60 frames** — including the ones we fail on, with per-frame
   distributions published, not just the mean.
3. **Split only for tuning** — scene-grouped folds by benchmark scene prefix
   (`animals*`, `cones*`, `obstacles*`) for the separately reported
   *threshold-tuned* regime. These folds never select weights, checkpoints or the
   registry alias; early stopping uses normal-road folds whose release and split
   hash are pinned in the run manifest.
4. **Two regimes, labelled honestly** — *zero-shot* (nothing tuned on
   RoadAnomaly) and *threshold-tuned* (one scalar chosen on held-out benchmark
   folds). They never share a column and never pick the model.

## Licensing

The code is MIT. The data is not: images are third-party photographs provided
for research use with per-image terms ([`data/credits.txt`](../data/credits.txt)),
and the annotations are **CC BY-SA 4.0**. Republishing frames in a paper, figure
or slide deck requires that attribution to travel with them. See
[`LICENSE`](../LICENSE) for the full carve-out.

## Related documents

- [ADR-0001 — evaluation-only benchmark](adr/0001-evaluation-only-benchmark.md)
- [ADR-0010 — model lineup and evaluation contract](adr/0010-model-lineup-and-evaluation-contract.md)
- [`docs/metrics.md`](metrics.md) — normative metric contract
- [`tests/dataset/test_dataset_integrity.py`](../tests/dataset/test_dataset_integrity.py)
  — the executable version of the facts above
