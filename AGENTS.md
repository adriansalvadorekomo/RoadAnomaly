# AGENTS.md

Repository-specific instructions for coding agents. Read this before changing
anything; it is shorter and stricter than the README.

## What this repository is

A Deep Learning module project on the RoadAnomaly benchmark: compare three
anomaly-segmentation approaches (autoencoder reconstruction error, image
resynthesis, transfer-learned segmentation), select on normal-road validation,
score the 60 RoadAnomaly frames held-out, and serve the selected model through a
FastAPI + Astro/Streamlit demo. The project follows CRISP-DM
([ADR-0007](docs/adr/0007-crisp-dm-methodology.md)).

Status vocabulary used throughout the repository: `implemented`,
`in progress`, `missing`, `blocked`. Read
[`docs/validation/requirements-matrix.md`](docs/validation/requirements-matrix.md)
before claiming that anything works.

## Non-negotiable

1. **RoadAnomaly is evaluation-only.** Never fit weights, early stopping,
   model selection or the registry alias on the 60 frames. The separately
   reported threshold-tuned regime may choose one scalar on scene-grouped
   benchmark folds; that result never promotes a model. See
   [`docs/adr/0001-evaluation-only-benchmark.md`](docs/adr/0001-evaluation-only-benchmark.md).
2. **Do not invent results.** The README results table is empty on purpose.
   A published number must trace to a file in `docs/experiments/` with the
   commit, config, command, dataset manifest and hardware that produced it.
3. **Do not mark a requirement `implemented` because it is documented.** It
   needs a file or a command that proves it. The matrix defines the evidence
   bar for each item.
4. **Do not change dataset splits, label semantics or `data/credits.txt`.**
   Attribution travels with every published frame.
5. **Selection and promotion come from normal-road validation only.** All three
   candidate SavedModels stay in the registry; `selected.json` is an alias, not
   the only artifact. There is no benchmark-to-registry path. See
   [`docs/adr/0008-promotion-and-model-registry.md`](docs/adr/0008-promotion-and-model-registry.md).
6. **XAI is a gate, not a promotion signal.** Its method is still undecided
   (gap G1); do not invent one or render a placeholder explanation. See
   [`docs/adr/0009-xai-evaluation-gate.md`](docs/adr/0009-xai-evaluation-gate.md).

## Layout

| Path | What it is | Status |
|---|---|---|
| `data/` | 60 frames, labels and credits (tracked, 15 MB) | implemented |
| `dl/` | models, training, evaluation, inference, notebooks | missing (directories only) |
| `configs/` | run YAML + pinned dataset manifests | missing (README only) |
| `backend/` | FastAPI inference service | missing (package stub) |
| `frontend/` | Astro landing page + Streamlit prototype | missing (READMEs) |
| `infra/` | `docker/` + `compose/` container files | missing |
| `tests/` | `dataset/` and `architecture/` implemented; `unit/`, `integration/` missing | in progress |
| `docs/` | ADRs 0001–0009, experiments template, report, architecture, validation | in progress |
| `assets/` | generated README images; regenerate from `architecture.json` | implemented |

## Commands

```bash
make install       # .venv + dev, deep learning, API and prototype dependencies
make lint type     # ruff + mypy
make test          # full pytest suite (dataset + architecture today)
make data-check    # dataset contract only (fast, no GPU)
pytest -q tests/architecture  # CRISP-DM regions, promotion rule, XAI gate, PNGs
```

CI (`.github/workflows/ci.yml`) runs ruff, mypy, the dataset tests and the
architecture contract tests on every pull request. Keep it green. Do not add a
suppression (`# type: ignore`, a skipped test, a lowered threshold) without a
comment explaining why on the line above it.

When changing `docs/architecture/architecture.json`, run the architecture tests,
`archify validate ... --quality showcase` and regenerate `architecture.html`,
`assets/architecture.png` and `assets/architecture-dark.png`. The PNGs are the
README artifact; do not hand-edit the HTML.

## Conventions

- Python 3.12 (the version CI, training and serving pin), 100-character lines,
  `from __future__ import annotations`.
- TensorFlow/Keras is the deep learning framework (ADR-0005). Do not
  introduce PyTorch, TorchScript, ONNX Runtime or a second model ecosystem.
- Metrics are defined once, in `dl/evaluation/metrics.py`; do not duplicate one.
- Experiment configs live in `configs/`, not inside `dl/`. A run config must
  reference the normal-road dataset manifest and split hash; a run without both
  is not reproducible and must not produce a published number.
- CRISP-DM is the project methodology (ADR-0007). Each experiment record names
  its phase and separates normal-road selection from held-out RoadAnomaly
  scoring. Never mix the two in one column.
- Artifacts are never committed or baked into an image. Publish the model bundle
  to GHCR and mount it read-only; pin image and model references by immutable
  digest. `latest` and moving `major.minor` tags are not deployment references.
- CI does not hold cluster credentials. Promotion is a reviewed commit; Argo CD
  pulls it. Do not add `kubectl apply` to CI to make a demo work.
- Architecture decisions that are expensive to reverse go to `docs/adr/` as a
  new numbered record. Do not rewrite an accepted ADR; supersede it explicitly.
  XAI method changes go through ADR-0009's gate first.
- Commit subjects: `feat:`, `fix:`, `exp:`, `docs:`, `ci:`, `refactor:`,
  `chore:`.
- The dataset is small enough to keep in git. Do not introduce LFS or DVC.

## Before you finish

Run `make lint type test`. If you moved a file, update every reference
(`git grep` for the old path) and the repository map in `README.md`. If you
changed the architecture or a promotion rule, also run `pytest -q
tests/architecture` and check the ADR/matrix links you touched.
