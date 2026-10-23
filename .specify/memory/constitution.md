# Constitution · RoadAnomaly

**Status:** normative · **Version:** 1.0 · **Ratified:** 2026-10-22 by ADR-0014.

1. Hierarchy: constitution > ADRs > `AGENTS.md` > specs; rules are linked, not copied; changing this constitution requires a new ADR.
2. Stack: Python 3.12 + TensorFlow 2.21/Keras 3 (ADR-0005), no PyTorch or ONNX; weights from Keras Applications, TF Hub or Hugging Face only if they load in Keras, with source, pinned revision, licence and preprocessing recorded.
3. Benchmark: the 60 RoadAnomaly frames are evaluation-only; nothing is fitted, selected or promoted on them (ADR-0001).
4. Models: only `autoencoder`, `unet` and `deeplabv3plus` (ADR-0010); U-Net and DeepLabV3+ train on multi-class normal-road labels and score with `1 − max softmax`; the autoencoder trains on normal images only.
5. Reproducibility: without a normal-road manifest and a scene-grouped split hash there is no valid run; fixed seed and `enable_op_determinism`, config in `configs/`, artifacts outside git and referenced by digest.
6. Selection: model and threshold are chosen on normal-road validation only; all three candidates stay in the registry (ADR-0008).
7. Metrics: a single implementation per `docs/metrics.md`; F1 = Dice on a binary mask; AUPRO with its FPR cap, HD95 in pixels, Boundary IoU with its band width.
8. Evidence: no published number without a record in `docs/experiments/` (commit, config, manifest, split hash, command, hardware); requirement status is decided by `requirements-matrix.md`, never by a spec.
9. XAI: a reporting gate, never a selection criterion; heatmaps are not causal explanations (ADR-0009, ADR-0011).
10. Quality: ruff, mypy, 100 columns and type hints; `make lint type test` green before every merge; every suppression carries a comment.
11. Tests: pytest by tier (dataset, architecture, unit, integration); code ships with its tests and every `AGENTS.md` invariant has a test in `tests/architecture/`; no skipped test and no lowered threshold.
12. Extensibility: public contracts (score `(N, H, W)` float32 in [0, 1], manifest, `schemas.py`) are stable; internal refactors are free; a new feature enters by spec and a contract or invariant change by ADR.
13. Limits: app and deployment only after a model and manifest exist; no secrets in git, no LFS or DVC, no edits to `data/` or `data/credits.txt`.
