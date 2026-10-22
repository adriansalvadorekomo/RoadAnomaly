# `configs/` — run configs and pinned data manifests

One YAML file per run, plus one manifest per normal-road corpus release. Configs
are data, not code: the training entrypoint reads them, the experiment record
links to them, and CI can hash them.

## Run config

A run config names the model family, seed, preprocessing version and the data it
is allowed to see:

```yaml
# Illustrative shape, not a runnable config. The keys will be frozen with the
# loader interface in week 1.
name: ae-baseline
profile: official
model: autoencoder
seed: 1337
dataset_manifest: configs/datasets/cityscapes-normal-2026-10.yaml
split: train
preprocessing_version: 1
early_stopping:
  monitor: val_loss
  patience: 5
```

Rules:

- `profile`, `seed` and `preprocessing_version` are required, and `profile` is
  `official` or `learning`. An `official` config also requires
  `dataset_manifest`; a learning run that uses normal-road data must pin it, and
  a fixture-based learning run must record its fixture path in the config or its
  learning record. A run without this provenance is not reproducible.
- The run config must not reference `data/frames/`, `data/frame_list.json` or a
  RoadAnomaly label directly. The benchmark is scored by the evaluation command,
  never by the training loader, under either profile.
- Paths are relative to the repository root.
- Do not put secrets, absolute home paths or machine-specific device names in a
  committed config.

## Run profiles

| Profile | Use | Evidence |
|---|---|---|
| `official` | Training, evaluation, threshold selection and export for the project | Full provenance; record in `docs/experiments/`; can be cited after review |
| `learning` | Notebook and local teaching runs with reduced scope | Record in `docs/experiments/learning/`; never evidence, never selection or promotion |

Both profiles obey the evaluation-only benchmark rule. A learning config may use
fewer epochs, a smaller normal-road subset or a fixture, but it must state that in
its config and record. If a learning result should become official, create an
official config and rerun it; do not copy the notebook number into an official
record.

## Normal-road dataset manifest

The manifest is the missing piece that makes phase 3 defensible. It must pin at
least:

| Field | Meaning |
|---|---|
| `source` | Dataset name and release/version (for example a Cityscapes release) |
| `url` / `retrieved_at` | Where the release came from and when |
| `licence` | Licence identifier and a link to the terms |
| `scene_ids` | Stable source-scene identifiers used for grouping |
| `split_hash` | SHA-256 over the sorted scene-to-split assignment |
| `frames` | Relative paths plus SHA-256 per decoded image |
| `preprocessing_version` | Version of the decode/resize pipeline |
| `excluded` | Frames or scenes removed, with a reason |

`split_hash` is the value an experiment record quotes. Changing a scene's split
changes the hash and invalidates every comparison that used the old one.

No normal-road manifest exists yet; this file defines what must be committed
before the first training run. The validation matrix tracks that as gap G10.
