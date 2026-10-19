# AGENTS.md

Repository-specific instructions for coding agents. Read this before changing
anything; it is shorter and stricter than the README.

## What this repository is

A Deep Learning module project on the RoadAnomaly benchmark: compare three
anomaly-segmentation approaches (autoencoder reconstruction error, image
resynthesis, transfer-learned segmentation), evaluate them on 60 held-out
frames, and serve the selected model through a FastAPI + Next.js demo.

Status vocabulary used throughout the repository: `implemented`,
`in progress`, `missing`, `blocked`. Read
[`docs/validation/requirements-matrix.md`](docs/validation/requirements-matrix.md)
before claiming that anything works.

## Non-negotiable

1. **RoadAnomaly is evaluation-only.** Never fit weights, thresholds or
   hyperparameters on the 60 frames. Threshold tuning uses scene-grouped folds
   and is reported separately. See
   [`docs/adr/0001-evaluation-only-benchmark.md`](docs/adr/0001-evaluation-only-benchmark.md).
2. **Do not invent results.** The README results table is empty on purpose.
   A published number must trace to a file in `docs/experiments/` with the
   commit, config, command and hardware that produced it.
3. **Do not mark a requirement `implemented` because it is documented.** It
   needs a file or a command that proves it. The matrix defines the evidence
   bar for each item.
4. **Do not change dataset splits, label semantics or `data/credits.txt`.**
   Attribution travels with every published frame.

## Layout

| Path | What it is | Status |
|---|---|---|
| `data/` | 60 frames, labels and credits (tracked, 15 MB) | implemented |
| `dl/` | models, training, evaluation, inference, notebooks | missing (directories only) |
| `configs/` | one YAML per experiment | missing (directory only) |
| `backend/` | FastAPI inference service | missing (package stub) |
| `frontend/` | Next.js dashboard | missing (README only) |
| `infra/` | `docker/` + `compose/` container files | missing |
| `tests/` | `dataset/` implemented; `unit/`, `integration/` missing | in progress |
| `docs/` | ADRs, experiments, report, architecture, validation | in progress |
| `assets/` | generated README images | implemented |

## Commands

```bash
make install       # .venv + dev, deep learning and API dependencies
make lint type     # ruff + mypy
make test          # full pytest suite
make data-check    # dataset contract only (fast, no GPU)
```

CI (`.github/workflows/ci.yml`) runs ruff, mypy and the dataset tests on every
pull request. Keep it green. Do not add a suppression (`# type: ignore`, a
skipped test, a lowered threshold) without a comment explaining why on the
line above it.

## Conventions

- Python 3.10+, 100-character lines, `from __future__ import annotations`.
- Metrics are defined once, in `dl/evaluation/metrics.py`; do not duplicate one.
- Experiment configs live in `configs/`, not inside `dl/`.
- Architecture decisions that are expensive to reverse go to `docs/adr/` as a
  new numbered record. Do not rewrite an accepted ADR; supersede it explicitly.
- Commit subjects: `feat:`, `fix:`, `exp:`, `docs:`, `ci:`, `refactor:`,
  `chore:`.
- The dataset is small enough to keep in git. Do not introduce LFS or DVC.

## Before you finish

Run `make lint type test`. If you moved a file, update every reference
(`git grep` for the old path) and the repository map in `README.md`.
