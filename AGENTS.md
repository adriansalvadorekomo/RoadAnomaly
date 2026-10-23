# AGENTS.md

## Project

RoadAnomaly detects road anomalies at pixel level (Deep Learning module, ESPRIT): it compares
`autoencoder`, `unet` and `deeplabv3plus`, selects one on normal-road validation, scores the
60 RoadAnomaly frames as evaluation only and explains the selected model (XAI).
Stack: Python 3.12, TensorFlow 2.21 / Keras 3, FastAPI, Streamlit, Astro, Docker and
Argo CD/Minikube. Methodology: CRISP-DM + spec-driven development (Spec Kit).
The real status of each requirement is in `docs/validation/requirements-matrix.md`.

## Commands

* Run: `make help` lists every target (train, evaluate, export, serve).
* Tests: `make test`; without GPU or training: `make test-fast`.
* Lint/format: `make fmt`, `make lint`, `make type`. Full gate: `make lint type test`.

## Style and conventions

* Python 3.12, 100 columns, `from __future__ import annotations`, type hints. Code and
  documentation in English. Commits: `feat:` `fix:` `exp:` `docs:` `ci:` `refactor:` `chore:`.
* Stable model IDs: `autoencoder`, `unet`, `deeplabv3plus`.
* Specs in `specs/NNN-name/`, ADRs in `docs/adr/`, run configs in `configs/`.
## Rules

* Read `.specify/memory/constitution.md` and the active spec before touching code.
* Hierarchy when two documents conflict: constitution > ADRs > this file > specs.
  A requirement's status comes from the requirements matrix, not from a spec or a ticked task.
* Invariants (they mirror the constitution and CI enforces them in `tests/architecture/`; if
  one fails, stop and ask, do not edit the test to make it pass):
  1. RoadAnomaly is evaluation-only: nothing is fitted, selected or promoted on its 60 frames.
  2. U-Net and DeepLabV3+ train on multi-class normal-road labels and score with
     `1 - max softmax`; the autoencoder trains on normal images only.
  3. Selection and promotion come only from normal-road validation.
  4. No published number without a record in `docs/experiments/`.
  5. XAI is a reporting gate, never a selection criterion.
  6. TensorFlow/Keras only; Hugging Face weights are fine if they load in Keras without PyTorch.
  7. Every metric is defined exactly once.
  8. `data/` and `data/credits.txt` are not modified.
* Decision levels:
  * Free: internal refactors, tests and optimizations that respect the `dl/` contracts.
  * Spec (`/speckit.specify`): new feature, model, metric or endpoint.
  * New ADR: change to an invariant, a public contract or a major dependency.
* Extending is normal: follow the folder's recipe; an accepted ADR is superseded, not
  rewritten. Details in `docs/metrics.md`, `xai.md`, `dataset.md` and `sdd.md`.
* Safety: no secrets in git, no `push --force`, no destructive commands. In an agent session
  run smoke tests only; a full training run needs explicit approval.
* If a prerequisite is missing (manifest, labels, config), stop and report it; do not invent
  data, paths or results.

## After finishing any task

* Run `make lint type test` and quote the commands and their real output in your reply.
* Add or update the tests for the code you touched in the same change.
* If you moved something, `git grep` the old path and update references and the `README.md`
  map; if it comes from a spec, update `tasks.md`.
* Keep this file at 60 lines or fewer: if an agent repeats a mistake, add one line and delete
  an obsolete one.
