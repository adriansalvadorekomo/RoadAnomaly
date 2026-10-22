<div align="center">

# RoadAnomaly — Pixel-Level Road Anomaly Detection

*Deep Learning module project · TensorFlow/Keras · autoencoder · U-Net · DeepLabV3+*

Per-pixel out-of-distribution detection for driving scenes: train on normal
roads, score objects a closed-set model was never trained to see.

[![CI](https://github.com/adriansalvadorekomo/RoadAnomaly/actions/workflows/ci.yml/badge.svg)](https://github.com/adriansalvadorekomo/RoadAnomaly/actions/workflows/ci.yml)
[![CD](https://github.com/adriansalvadorekomo/RoadAnomaly/actions/workflows/cd.yml/badge.svg)](https://github.com/adriansalvadorekomo/RoadAnomaly/actions/workflows/cd.yml)
[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Data: CC BY-SA 4.0](https://img.shields.io/badge/annotations-CC%20BY--SA%204.0-lightgrey.svg)](data/credits.txt)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776ab.svg)](pyproject.toml)
[![TensorFlow 2.21](https://img.shields.io/badge/TensorFlow-2.21-FF6F00?logo=tensorflow&logoColor=white)](docs/adr/0005-tensorflow-framework.md)

</div>

> **Snapshot 2026-10-22.** The dataset, its contract tests and the documentation
> guardrails exist. Models, metrics, XAI, API, frontend, containers and
> deployment do not. The authority is
> [`docs/validation/requirements-matrix.md`](docs/validation/requirements-matrix.md);
> a README sentence is not evidence.

## 1. What this project is

A segmentation model trained on Cityscapes or BDD100K knows a closed set of
classes. Anything else — a deer, a fallen ladder, a boulder — is absorbed into a
known class or ignored. This project treats that as per-pixel out-of-distribution
detection: produce a score map where high values mean the pixel does not match
the normal-road training distribution. The model never sees an anomaly class.

The project follows CRISP-DM ([ADR-0007](docs/adr/0007-crisp-dm-methodology.md)).
Its three goals are:

1. Freeze an honest evaluation protocol before model code.
2. Compare three models behind one score-map interface.
3. Explain and serve the selected model.

Protocol: [ADR-0001](docs/adr/0001-evaluation-only-benchmark.md). Model lineup:
[ADR-0010](docs/adr/0010-model-lineup-and-evaluation-contract.md).

## 2. Architecture

The C4 model is defined once in
[`docs/architecture/workspace.dsl`](docs/architecture/workspace.dsl) and rendered
below. **These are target-state diagrams, not a running system.** Implemented
elements are green; planned elements are amber and external planned systems are
grey.

### C1 — system context

<a href="docs/architecture/diagrams/c1-system-context.png"><img alt="C1 system context: researchers and evaluators use the RoadAnomaly system, which depends on normal-road corpora and pretrained weights; GitHub Actions runs the quality gate." src="docs/architecture/diagrams/c1-system-context.png" width="100%"></a>

### C2 — offline pipeline

<a href="docs/architecture/diagrams/c2-offline-pipeline.png"><img alt="C2 offline pipeline: normal-road data and pretrained weights feed training; model artifacts feed normal-road validation and the selection scorecard, which chooses the registry alias while retaining all three candidates. The held-out RoadAnomaly benchmark feeds report-only evaluation, and XAI consumes the selected model without promoting it." src="docs/architecture/diagrams/c2-offline-pipeline.png" width="100%"></a>

Online inference and deployment views stay absent until those files exist.
Render and verify with `make architecture` (Java 21 + Chromium) and
`pytest -q tests/architecture -v`. The C4 model, CRISP-DM mapping and renderer
pin are in [`docs/architecture/README.md`](docs/architecture/README.md).

## 3. Data and evaluation protocol

`data/` is tracked in git (15 MB) so a clone is reproducible;
[`tests/dataset/`](tests/dataset/) enforces the contract.

| Property | Value |
|---|---|
| Frames | **60** WebP, **1280 × 720**, RGB |
| Semantic masks | `labels_semantic.png`, uint8, **{0 = normal, 2 = anomaly}** in all 60 |
| Instances | **201** regions in **46** frames; **14** frames are semantic-only |
| Anomaly coverage | **9.8 %** of pixels; per frame **0.4 % → 42.3 %** |
| Categories | animals 31 · obstacles 15 · cones 8 · lost_tires 3 · vehicle 3 |
| Attribution | [`data/credits.txt`](data/credits.txt) — keep it with any published frame |

**RoadAnomaly is evaluation-only.** Nothing is trained, early-stopped or selected
on the 60 frames. Training must use a pinned normal-road release and scene-grouped
splits; the separately reported *threshold-tuned* regime may choose one scalar on
benchmark folds, but it never promotes a model. *Zero-shot* and *threshold-tuned*
results are separate columns. Report per-frame distributions, not only means.

Full dataset notes and the protocol are in [`docs/dataset.md`](docs/dataset.md)
and [ADR-0001](docs/adr/0001-evaluation-only-benchmark.md). Licensing is in
[License and credits](#license-and-credits).

## 4. Models, metrics and XAI

| Model ID | Architecture | Anomaly score |
|---|---|---|
| `autoencoder` | Convolutional autoencoder | per-pixel reconstruction error |
| `unet` | U-Net | `1 - max softmax` |
| `deeplabv3plus` | DeepLabV3+ | `1 - max softmax` |

All three expose one score-map interface, so the comparison is a config change.
No model trains on RoadAnomaly. U-Net and DeepLabV3+ share normal-road semantic
labels; the autoencoder is the reconstruction baseline. Details:
[ADR-0010](docs/adr/0010-model-lineup-and-evaluation-contract.md).

Common binary-mask metrics are Precision, Recall, F1, IoU and Dice. Model-specific
diagnostics are AUROC/AUPRO (autoencoder), HD95 (U-Net) and mIoU/Boundary IoU
(DeepLabV3+). For a binary mask F1 equals Dice. Contract:
[`docs/metrics.md`](docs/metrics.md).

XAI is an evaluation gate, not a fourth model: reconstruction error + Integrated
Gradients for the autoencoder; Seg-Grad-CAM + Integrated Gradients for the
segmentation models. No XAI code or artefact exists. Contract:
[`docs/xai.md`](docs/xai.md); methods:
[ADR-0011](docs/adr/0011-xai-methods-and-faithfulness.md).

## 5. Results

No model has been trained, so no number is published.

| Model | Normal-road validation (selection) | RoadAnomaly zero-shot | RoadAnomaly threshold-tuned |
|---|---|---|---|
| `autoencoder` | — | — | — |
| `unet` | — | — | — |
| `deeplabv3plus` | — | — | — |

A published number must trace to a file in `docs/experiments/` with the commit,
config, normal-road manifest, split hash, command and hardware. Illustrative
planning calculations are not results.

## 6. Development workflow

```bash
git clone https://github.com/adriansalvadorekomo/RoadAnomaly.git
cd RoadAnomaly

make install        # .venv + dev, deep learning, API and prototype dependencies
make data-check     # dataset contract, no GPU
make lint type test # what CI runs
make architecture   # render C1/C2 (Java 21 + Chromium)
```

Python 3.12. Java 21 + Chromium are needed only for the architecture render;
Node 20+ only for the Astro landing page. Training needs a GPU for reasonable
throughput and runs CPU-only at reduced speed. `make help` lists every target.

### Spec-driven development

Non-trivial features start with a spec in `specs/NNN-name/`:

```text
/speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
```

A spec is a plan, not evidence. Status comes from the
[requirements matrix](docs/validation/requirements-matrix.md), and published
numbers come from `docs/experiments/`. See
[ADR-0013](docs/adr/0013-spec-driven-development.md) and
[`docs/sdd.md`](docs/sdd.md).

### Reproducibility

Every published number traces to a commit, config, command, normal-road manifest
and split hash. Seeds are fixed and recorded; artifacts are never committed;
notebook outputs are stripped and the environment is pinned. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## 7. Repository map

```text
RoadAnomaly/
├── README.md               this file
├── AGENTS.md               coding-agent rules
├── CONTRIBUTING.md         branching, review, SDD and suppression rules
├── Makefile                developer targets
├── specs/                  feature specs, plans and tasks (SDD)
├── .specify/               Spec Kit workspace (tooling)
├── .opencode/commands/     generated SDD agent commands
├── data/                   60 frames + labels + credits        (implemented)
├── dl/                     data · models · training · evaluation · inference (missing)
├── configs/                run YAML + normal-road manifests    (missing)
├── backend/                FastAPI inference service           (missing)
├── frontend/               Astro landing + Streamlit prototype  (missing)
├── infra/                  docker/ + compose/                  (missing)
├── tests/                  dataset + architecture contracts    (implemented)
├── docs/                   ADRs, dataset, metrics, XAI, SDD, report, validation
└── .github/                CI/CD, CODEOWNERS, PR and issue templates
```

`docs/architecture/workspace.dsl` is the only architecture source. `assets/` was
removed with the old diagram tooling and should not return: publishable figures
live with the experiment that produced them.

## 8. Validation status

The [requirements matrix](docs/validation/requirements-matrix.md) is authoritative
and records no `implemented` requirement at this snapshot: the dataset, tests and
documentation guardrails exist; models, XAI, serving, deployment and the
commercial artefacts do not. Status words are evidence claims, not plans.

## Team

Six contributors: Emna Trabelsi, Ines Trabelsi, Hejer Mnejja, Walid Fehry,
Khaled Gannoun and Adrian Salvador Ekomo Mesi Obono. Workstreams M1–M6 are
defined in [`.github/CODEOWNERS`](.github/CODEOWNERS); owners are assigned at the
kickoff meeting. M4's metric harness is the critical path.

## Citation

Cite the dataset paper: K. Lis, K. Nakka, P. Fua and M. Salzmann, *Detecting the
Unexpected via Image Resynthesis*, ICCV 2019. BibTeX is in
[`CITATION.cff`](CITATION.cff).

## License and credits

Code is [MIT](LICENSE). **The data is not.** Images are third-party photographs
with per-image research terms; annotations are CC BY-SA 4.0. Keep
[`data/credits.txt`](data/credits.txt) with any redistributed frame.
