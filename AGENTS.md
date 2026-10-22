# AGENTS.md

Repository-specific instructions for coding agents. Read this before changing
anything; it is shorter and stricter than the README.

## What this repository is

A Deep Learning module project on the RoadAnomaly benchmark: compare three
anomaly-scoring models (autoencoder reconstruction error, U-Net and DeepLabV3+
with a maximum-softmax anomaly score), select on normal-road validation, score
the 60 RoadAnomaly frames held-out, explain the selected model, and serve it
through a FastAPI + Astro/Streamlit demo. The project follows CRISP-DM
([ADR-0007](docs/adr/0007-crisp-dm-methodology.md)).

Only the dataset, its tests and the documentation guardrails exist today. There
is no model, metric implementation, XAI code, API, frontend, container or
deployment. Status vocabulary: `implemented`, `in progress`, `missing`,
`blocked`. Read
[`docs/validation/requirements-matrix.md`](docs/validation/requirements-matrix.md)
before claiming that anything works.

## Non-negotiable

1. **RoadAnomaly is evaluation-only.** Never fit weights, early stopping,
   model selection, a threshold or the registry alias on the 60 frames. The
   separately reported threshold-tuned regime may choose one scalar on
   scene-grouped benchmark folds; that result never promotes a model. See
   [`docs/adr/0001-evaluation-only-benchmark.md`](docs/adr/0001-evaluation-only-benchmark.md).
2. **Do not invent results.** The README results table is empty on purpose. A
   published number must trace to a file in `docs/experiments/` with the commit,
   config, normal-road manifest, split hash, command and hardware that produced
   it. Workbook examples are illustrative, not results.
3. **Do not mark a requirement `implemented` because it is documented.** It
   needs a file or a command that proves it. The matrix defines the evidence bar.
4. **Do not change dataset splits, label semantics or `data/credits.txt`.**
   Attribution travels with every published frame.
5. **Selection and promotion come from normal-road validation only.** All three
   candidates stay in the registry; `selected.json` is an alias, not the only
   artifact. There is no benchmark-to-registry path. See
   [`docs/adr/0008-promotion-and-model-registry.md`](docs/adr/0008-promotion-and-model-registry.md)
   and [`docs/adr/0010-model-lineup-and-evaluation-contract.md`](docs/adr/0010-model-lineup-and-evaluation-contract.md).
6. **XAI is a gate, not a promotion signal.** The methods are fixed in
   [`docs/adr/0011-xai-methods-and-faithfulness.md`](docs/adr/0011-xai-methods-and-faithfulness.md):
   reconstruction-error maps + Integrated Gradients for the autoencoder;
   Seg-Grad-CAM + Integrated Gradients for U-Net/DeepLabV3+. Heatmaps and error
   maps are not causal explanations and never promote a model.
7. **Do not add an architecture source other than Structurizr.** The C4 model is
   [`docs/architecture/workspace.dsl`](docs/architecture/workspace.dsl). Do not
   reintroduce archify JSON/HTML, Mermaid architecture diagrams or hand-edited
   PNGs.

## Layout

| Path | What it is | Status |
|---|---|---|
| `data/` | 60 frames, labels and credits (tracked, 15 MB) | implemented |
| `dl/` | models, training, evaluation, inference, notebooks | missing (directories only) |
| `configs/` | run YAML + pinned normal-road manifests | missing (README only) |
| `backend/` | FastAPI inference service | missing (package stub) |
| `frontend/` | Astro landing page + Streamlit prototype | missing (READMEs) |
| `infra/` | `docker/` + `compose/` container files | missing |
| `tests/` | `dataset/` and `architecture/` implemented; `unit/`, `integration/` missing | in progress |
| `docs/adr/` | ADRs 0001–0013 | implemented |
| `docs/architecture/` | Structurizr DSL, render script and C4 PNGs | implemented |
| `docs/experiments/` | template; no run records | template only |
| `docs/metrics.md`, `docs/xai.md` | normative contracts, not implementations | in progress |
| `docs/dataset.md`, `docs/sdd.md` | dataset facts + protocol; SDD workflow | implemented |
| `docs/validation/` | requirements traceability matrix | implemented |
| `specs/` | feature specs, plans and tasks (SDD) | empty (workflow ready) |
| `.specify/` | Spec Kit 1.2.2 scaffolding; constitution is a placeholder | tooling |
| `.opencode/commands/speckit.*` | generated SDD agent commands (only tracked `.opencode` files) | tooling |

## Commands

```bash
make install       # .venv + dev, deep learning, API and prototype dependencies
make lint type     # ruff + mypy
make test          # full pytest suite (dataset + architecture today)
make data-check    # dataset contract only (fast, no GPU)
make architecture  # render C1/C2 and diagrams/manifest.json (Java + Chromium)
pytest -q tests/architecture -v  # C4 guardrails, promotion rule, XAI gate, PNGs
```

Non-trivial feature work uses the Spec Kit loop
`/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`;
these are agent commands, not shell targets. Specs live in `specs/NNN-name/` and
are plans, not evidence. See [`docs/sdd.md`](docs/sdd.md) and
[ADR-0013](docs/adr/0013-spec-driven-development.md).

CI (`.github/workflows/ci.yml`) runs ruff, mypy, the dataset tests, the
architecture contract tests and Structurizr DSL validation on every pull
request. Keep it green. Do not add a suppression (`# type: ignore`, a skipped
test, a lowered threshold) without a comment explaining why on the line above
it.

When changing `docs/architecture/workspace.dsl`, run `make architecture`, then
`pytest -q tests/architecture -v`. Commit the regenerated PNGs and
`diagrams/manifest.json` with the DSL. Do not hand-edit the PNGs. If the pinned
renderer cannot produce readable C1/C2 images, reopen ADR-0012 rather than
weakening the guardrail to fit the renderer.

## Conventions

- Python 3.12 (the version CI, training and serving pin), 100-character lines,
  `from __future__ import annotations`.
- TensorFlow/Keras is the deep learning framework (ADR-0005). Do not introduce
  PyTorch, TorchScript, ONNX Runtime or a second model ecosystem.
- Model IDs are stable: `autoencoder`, `unet`, `deeplabv3plus`. Do not use
  `A`/`B`/`C` or "resynthesis" as a current model name.
- U-Net and DeepLabV3+ train on the same normal-road semantic labels and use
  `1 - max softmax` as the anomaly score. No binary training, no benchmark
  train/validation/test split.
- Metrics are defined once, in `docs/metrics.md` and eventually
  `dl/evaluation/metrics.py`; do not duplicate a metric. For a binary mask,
  F1 equals Dice; do not present them as independent evidence.
- Common benchmark metrics are Precision, Recall, F1, IoU and Dice. Complementary
  diagnostics are AUROC/AUPRO (autoencoder), HD95 (U-Net) and mIoU/Boundary IoU
  (DeepLabV3+). Report the AUPRO FPR cap, HD95 spacing/empty-mask policy and
  Boundary IoU band width.
- Thresholds are fixed on normal-road validation. Zero-shot and threshold-tuned
  benchmark results are separate columns; neither selects a model.
- Experiment configs live in `configs/`, not inside `dl/`. A run config must
  reference the normal-road dataset manifest and split hash; a run without both
  is not reproducible and must not produce a published number.
- CRISP-DM is the project methodology (ADR-0007). Each experiment record names
  its phase and separates normal-road selection from held-out RoadAnomaly
  scoring. Never mix the two in one column.
- Non-trivial feature work starts with a spec in `specs/` (ADR-0013). Link the
  ADR or contract the feature depends on; do not restate it. A checked task or a
  spec is never evidence that a requirement is `implemented`.
- Artifacts are never committed or baked into an image. Publish the model bundle
  to GHCR and mount it read-only; pin image and model references by immutable
  digest. `latest` and moving `major.minor` tags are not deployment references.
- CI does not hold cluster credentials. Promotion is a reviewed commit; Argo CD
  pulls it. Do not add `kubectl apply` to CI to make a demo work.
- Architecture decisions that are expensive to reverse go to `docs/adr/` as a
  new numbered record. Do not rewrite an accepted ADR; supersede it explicitly.
  XAI method changes go through ADR-0011 first.
- Commit subjects: `feat:`, `fix:`, `exp:`, `docs:`, `ci:`, `refactor:`,
  `chore:`.
- The dataset is small enough to keep in git. Do not introduce LFS or DVC.

## Before you finish

Run `make lint type test`. If you moved a file, update every reference
(`git grep` for the old path) and the repository map in `README.md`. If the
change came from a spec, update `specs/NNN-name/tasks.md` and the spec status.
If you changed the architecture or a promotion rule, also run
`pytest -q tests/architecture -v` and check the ADR/matrix links you touched.
