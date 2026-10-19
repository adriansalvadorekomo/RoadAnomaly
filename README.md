<div align="center">

# RoadAnomaly — Pixel-Level Road Anomaly Detection

*Deep Learning module project · TensorFlow/Keras, CNNs, image resynthesis, transfer learning and autoencoders*

**Finding the unexpected on the road: animals, cones, boulders, debris and other
objects that a driving perception stack was never trained to expect.**

[![CI](https://github.com/adriansalvadorekomo/RoadAnomaly/actions/workflows/ci.yml/badge.svg)](https://github.com/adriansalvadorekomo/RoadAnomaly/actions/workflows/ci.yml)
[![CD](https://github.com/adriansalvadorekomo/RoadAnomaly/actions/workflows/cd.yml/badge.svg)](https://github.com/adriansalvadorekomo/RoadAnomaly/actions/workflows/cd.yml)
[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Data: CC BY-SA 4.0](https://img.shields.io/badge/annotations-CC%20BY--SA%204.0-lightgrey.svg)](data/credits.txt)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab.svg)](pyproject.toml)
[![TensorFlow 2.21](https://img.shields.io/badge/TensorFlow-2.21-FF6F00?logo=tensorflow&logoColor=white)](docs/adr/0005-tensorflow-framework.md)
[![Node 20+](https://img.shields.io/badge/node-20%2B-339933.svg)](frontend/)
[![Code style: ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](pyproject.toml)

</div>

---

> **How to read the status words.** `implemented` means a file or command in
> this repository proves the capability. `in progress` means partial evidence
> exists. `missing` means nothing exists yet. `blocked` means a named dependency
> must land first. The authority is
> [`docs/validation/requirements-matrix.md`](docs/validation/requirements-matrix.md);
> a sentence in this README is never the evidence for its own claim.

## 1. Overview and objectives

A segmentation model trained on Cityscapes or BDD100K predicts a closed set of
classes: road, car, pedestrian, sky. Anything else — a deer on the asphalt, a
ladder that fell off a truck, a boulder around a bend — is either absorbed into
the nearest known class or ignored, and at 50 km/h "ignored" is an incident.

Road anomaly detection reframes this as **per-pixel out-of-distribution
detection**: produce a score map where high values mean *this pixel does not
belong to anything I was trained to recognise*. The model is never given an
"anomaly" class to learn. It is given normal driving scenes and has to notice
when the world stops matching them.

| # | Objective | What would prove it | Status |
|---|---|---|---|
| O1 | Understand the benchmark and freeze an honest protocol | Verified dataset report, EDA notebook, ADR-0001 | `in progress` — facts verified, no EDA notebook |
| O2 | Implement three general model families | A/B/C behind one interface, trained and reproducible | `missing` |
| O3 | Compare them behind one metric harness | Results table populated from `docs/experiments/` | `missing` |
| O4 | Explain the selected model (XAI) | Saliency/occlusion maps plus a written justification | `blocked` — no model, no method decision (G1) |
| O5 | Serve the selected model | FastAPI + Streamlit prototype + Astro landing + containers + deployment | `missing` |
| O6 | Make the commercial case | BMC, 4Ps, teaser, commercial report | `missing` |

## 2. Current architecture (implemented)

At this commit the repository is a **verified dataset and its guard rails**,
not a running system. There is no model, API, frontend or container. The full
component view is in [`docs/architecture/README.md`](docs/architecture/README.md).

| Component | State | Evidence |
|---|---|---|
| Dataset (60 frames + labels + credits) | `implemented` | `data/`, tracked in git (15 MB) |
| Dataset contract tests | `implemented` | 6 tests in `tests/dataset/` |
| Lint, types and test gate | `implemented` | `ruff`, `mypy`, `pytest`; `.github/workflows/ci.yml` |
| Decision records and protocol | `implemented` | `docs/adr/0001`–`0006` |
| Scaffold, Makefile, templates | `implemented` | `Makefile`, `.github/` |
| Models, training, metrics, inference | `missing` | `dl/` holds directories only |
| Backend, frontend, containers | `missing` | backend stub, frontend READMEs, no Dockerfiles |
| Deployment (compose, Kubernetes, Vercel) | `missing` | target documented in ADR-0004 |

The only executable pipeline today is CI: lint, type-check and the six dataset
tests. That is deliberate — the protocol and the data contract were frozen
before any model code existed.

## 3. Target architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/architecture-dark.png">
  <img alt="RoadAnomaly end-to-end system map: normal-road data and three TensorFlow models, shared evaluation, FastAPI serving, a Streamlit prototype, an Astro landing page on Vercel, and GitHub Actions with Argo CD delivery" src="assets/architecture.png" width="100%">
</picture>

**This is the target, not the current state.** Five stages, one system:

- **Data** (`missing`) — normal-road corpora feed a TensorFlow/Keras `tf.data`
  pipeline with scene-grouped train/validation splits. RoadAnomaly is never a
  training input. See [ADR-0001](docs/adr/0001-evaluation-only-benchmark.md).
- **Modeling** (`missing`) — three families are compared behind one interface:
  A autoencoder, B image resynthesis and C DeepLabV3+ / U-Net. See
  [ADR-0002](docs/adr/0002-three-model-families.md) and
  [ADR-0005](docs/adr/0005-tensorflow-framework.md).
- **Evaluation and promotion** (`missing`) — one metric harness scores all three
  models, selects on normal-road validation and promotes a TensorFlow SavedModel
  plus a manifest. The 60 RoadAnomaly frames are scored held-out only, and
  threshold tuning is reported separately from the zero-shot column.
- **Serving and experience** (`missing`) — FastAPI loads the SavedModel and
  exposes `POST /predict`; the Streamlit prototype is the public interactive
  demo; the Astro landing page on Vercel presents the project, links to the
  prototype and renders only published results. Streamlit calls FastAPI inside
  the cluster, so the browser never needs a route to the inference API.
- **Delivery** (`implemented` workflow, `missing` deployment) — GitHub Actions
  gates every pull request and publishes tagged API and prototype images to
  GHCR. Argo CD syncs Minikube; Vercel builds the Astro landing page through its
  Git integration. The target is recorded in
  [ADR-0004](docs/adr/0004-vercel-and-gitops-deployment.md) and
  [ADR-0006](docs/adr/0006-astro-and-streamlit-frontend.md).

Read the labels literally: the diagram is a target, not a claim that the model,
API, prototype, landing page or cluster is running. `docker compose` is the
local path; Minikube, Argo CD and Vercel are the demo target.

The diagram is generated from
[`docs/architecture/architecture.json`](docs/architecture/architecture.json)
with [archify](https://github.com/tt-a1i/archify); open
[`architecture.html`](docs/architecture/architecture.html) for the interactive
version (pan, zoom, dark mode, guided tours). Regenerate it from the spec rather
than editing the HTML — the HTML is a build artifact.

## 4. Dataset and evaluation protocol

`data/` is tracked in this repository (15 MB) so a clone is reproducible. Every
number in this table is asserted by
[`tests/dataset/test_dataset_integrity.py`](tests/dataset/test_dataset_integrity.py) —
if the dataset is ever swapped, CI fails rather than letting the documentation
drift.

| Property | Value |
|---|---|
| Images | **60** frames, `data/frames/*.webp`, all **1280 × 720**, RGB |
| Index | `data/frame_list.json` — frame order used by every loader |
| Annotation dirs | **60** — one `<frame>.labels/` per frame, so the pairing is exact |
| Semantic masks | `labels_semantic.png`, uint8, **{0 = normal, 2 = anomaly}** in all 60 |
| Colour masks | `labels_semantic_color.png` — black = normal, orange `#FF4500` = anomaly |
| Instance masks | `labels_instance.png` in **46** frames; pixel value = instance id |
| Instances | **201** bounding regions, **all `cls = 2`** (one anomaly class, no sub-labels) |
| Semantic-only frames | **14** — e.g. `animals06`, `cones07`, `obstacles01/02`, annotated but with no instance masks |
| Anomaly coverage | **9.8 %** of all pixels; per frame: **0.4 % → 42.3 %** (median 6.6 %) |
| Object scale | median instance ≈ **87 × 87 px**, but **35 of 201 instances** are smaller than 32 × 32 px |
| Categories | animals 31 · obstacles 15 · cones 8 · lost_tires 3 · vehicle 3 |
| Attribution | [`data/credits.txt`](data/credits.txt) — per-image author, source and licence |

**Category distribution** (by frame-name prefix, the natural scene grouping):

```
animals     31  ███████████████████████████████
obstacles   15  ███████████████
cones        8  ████████
lost_tires   3  ███
vehicle      3  ███
```

**Inside a label directory.** The annotation tooling (the authors' own
[LabelGrab](https://github.com/cvlab-epfl/LabelGrab)) left three kinds of file.
We use the first two:

- `labels_semantic.png` / `_color.png` / `labels_instance.png`, `index.json` —
  **used**: masks, instance ids, and per-instance `crop_rect` / `roi_rect` boxes.
- `instance_XXX_gc_mask.png` + `instance_XXX_gc_state.npy` — **not used**: the
  GrabCut editor's saved state (a `(2, 65)` float array per instance), kept in
  the repository for provenance only. The loader never reads it.

`data/readme.md` is the original authors' own description of the format and is
the authority if this table and that file ever disagree.

### Why this dataset is genuinely hard

- **Long tail of scale.** 17 % of instances are under 32 × 32 px, while in some
  frames the anomaly covers more than 40 % of the image. A single operating
  threshold cannot serve both, which is why the results section reports
  per-frame distributions and not just means.
- **Coverage is wildly uneven.** 6 frames contain under 1 % anomalous pixels.
  A model that predicts "all normal" scores well on those and terribly overall;
  a single aggregate number hides exactly the failure that matters.
- **Single class, no hierarchy.** `cls = 2` for every instance means we can
  measure *localisation* but not *recognition* — we cannot claim to know a deer
  from a cone, and we do not try to.

### The constraint that shapes everything

> **RoadAnomaly is an evaluation-only benchmark. We never fit weights on its 60
> frames.**

Every pixel in every mask is either normal or an anomaly, and the masks contain
nothing else — there is no image in this dataset without something abnormal in
it. So the usual "random split, train, report test metrics" recipe is
unavailable: any model trained here would be tested on its own training set.

The protocol, recorded in full in
[**ADR-0001**](docs/adr/0001-evaluation-only-benchmark.md):

1. **Train on normal** — Cityscapes/BDD100K normal subsets and ImageNet-pretrained
   backbones. The anomaly is defined by absence, never shown as a class.
2. **Report all 60 frames** — including the ones we fail on, with the per-frame
   IoU distribution published, not just the mean.
3. **Split only for tuning** — scene-grouped k-fold (the `animals*`, `cones*`,
   `obstacles*` prefixes) so one source image never spans two folds.
4. **Two regimes, labelled honestly** — *zero-shot* (nothing tuned) and
   *threshold-tuned* (one scalar chosen on held-out folds). Never in the same
   column.

This is the single most important design decision in the project, and the one
we expect to be challenged on in the defence. It is written down before any
model code exists, deliberately.

### Licensing — read before publishing figures

The code in this repository is MIT. The data is not: images are third-party
photographs provided for research use with per-image terms
(`data/credits.txt`), and the annotations are **CC BY-SA 4.0**. Republishing
frames in a paper, figure or slide deck requires the attribution in that file
to travel with them. See [`LICENSE`](LICENSE) for the full carve-out.

## 5. Model approaches

**Status: `missing`.** Three approaches behind **one shared scoring harness**, so
the comparison is a config change rather than three parallel projects. Rationale
and rejected alternatives are in
[**ADR-0002**](docs/adr/0002-three-model-families.md).

| | Approach | Anomaly score | Why this one |
|---|---|---|---|
| **A** | **Autoencoder reconstruction error** | per-pixel \|x − x̂\|, thresholded | Needs no anomaly labels at all. Fastest path to a real end-to-end number, and its failure mode is instructive: large smooth anomalies reconstruct too well |
| **B** | **Image resynthesis** (Lis et al., ICCV 2019) | disagreement between the input and a resynthesis of it | The dataset's own reference method, so we can compare against a published result instead of only against ourselves |
| **C** | **Transfer-learned segmentation** — DeepLabv3+ / U-Net (TensorFlow-native) | 1 − max softmax (MSP baseline) | Pretrained weights are the most reliable route to a strong pixel-level model with 60 evaluation images; MSP is the yardstick the elaborate methods must beat to justify themselves |

```python
# Every model implements the same three-part interface — that is the whole
# contract that makes the comparison fair.
model = build(config)                       # -> keras.Model
scores = model.predict(batch)               # -> per-pixel anomaly score map in [0, 1]
model.export(saved_model_dir)               # -> SavedModel with a serving signature
```

The API loads the exported SavedModel with `tf.saved_model.load`; there is no
TorchScript or ONNX step (ADR-0005).

`dl/evaluation/` turns *any* score map plus a ground-truth mask into *the same*
metric set. No model can be evaluated more favourably than another, and a
metric is implemented exactly once, in one file, for all three.

**Explainability (XAI) is required by the technical validation and is not yet
planned.** No saliency, occlusion, Grad-CAM or SHAP method has been chosen, and
there is no record of the decision. It is tracked as gap G1 in the validation
matrix; the method and its justification must be written down before it can be
implemented.

## 6. Development workflow

```bash
git clone https://github.com/adriansalvadorekomo/RoadAnomaly.git
cd RoadAnomaly

make install            # venv + dev, deep learning, API and prototype dependencies
make data-check         # verify the dataset contract (fast, no GPU)
make lint type test     # what CI runs
```

| Target | Purpose | Status |
|---|---|---|
| `make install` | Create `.venv` and install local dev, training, API and prototype dependencies | `implemented` |
| `make data-check` | Six dataset integrity tests | `implemented` |
| `make lint` / `make fmt` | Ruff lint and format | `implemented` |
| `make type` | Mypy over `dl`, `backend`, `tests` | `implemented` |
| `make test` | Full pytest suite | `implemented` |
| `make train CONFIG=configs/ae.yaml` | Training loop | `missing` — `dl/training/train.py` |
| `make eval CKPT=artifacts/best.keras` | Shared evaluation | `missing` — `dl/evaluation/evaluate.py` |
| `make export CKPT=artifacts/best.keras` | SavedModel export | `missing` — `dl/inference/export_savedmodel.py` |
| `make serve` | FastAPI on `:8000` | `missing` — `backend/app/main.py` |
| `make landing` | Astro landing page on `:4321` | `missing` — `frontend/landing/package.json` |
| `make prototype` | Streamlit prototype on `:8501` | `missing` — `frontend/prototype/app.py` |
| `make up` / `make down` | Local compose stack (API + prototype) | `missing` — `infra/compose/docker-compose.yml` |

The dataset is already in the repository; there is no download step.
**Requirements:** Python 3.10+; Node 20+ only for the Astro landing page.
Training is happiest with a GPU, but every model runs CPU-only at reduced
throughput; `requirements/dl.txt` documents the TensorFlow CPU package and
Apple Silicon note. The local `make install` uses `requirements/api-base.txt`
instead of `tensorflow-cpu`, so TensorFlow is installed exactly once.

## 7. Testing and code quality

**Status: `implemented` for the dataset tier.**

| Tier | Scope | Status |
|---|---|---|
| `tests/dataset/` | Frame ↔ label contract, mask vocabulary, instance consistency | `implemented` — 6 tests |
| `tests/unit/` | Pure functions: metrics, mask decoding, thresholding | `missing` — appears with the first model module |
| `tests/integration/` | API contract, artifact loading, end-to-end inference | `missing` — appears with the backend |

The dataset tests are the interesting ones: they re-derive every documented
fact — 60 frames, the `{0, 2}` label vocabulary, 201 instances, 46
instance-annotated directories, 14 semantic-only ones — and fail the build if
the data and the documentation disagree. Documentation that cannot rot is worth
more than documentation that is merely correct today.

`ruff check`, `ruff format --check` and `mypy` run over the whole repository
(Markdown excluded from formatting so the illustrative snippets keep their
alignment). CI runs the same commands; see
[`tests/README.md`](tests/README.md) for the tier contract and
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the suppression rule.

## 8. Docker and local development

**Status: `missing`.** There are no Dockerfiles and no compose file. The
intended layout is documented in [`infra/README.md`](infra/README.md):

```
infra/
├── docker/
│   ├── Dockerfile.backend    python:3.12-slim, tensorflow-cpu, non-root
│   └── Dockerfile.prototype  python:3.12-slim, streamlit, non-root
└── compose/
    └── docker-compose.yml    api + prototype, pinned to GHCR tags or local builds
```

When the files land, `make up` starts the API on `:8000` and the Streamlit
prototype on `:8501`. The API image is CPU-only and ships only `tensorflow-cpu`:
the SavedModel is exported by `dl/inference/`, and training dependencies stay out
of the serving container. The Astro landing page is not containerized for the
serving path — Vercel builds it, and `make landing` runs it locally on `:4321`.

## 9. Planned CI/CD workflow with GitHub Actions

**Status: CI `implemented`; CD workflow `implemented`, deployment `blocked` on
missing images and report.** The workflows are in `.github/workflows/`.

| Trigger | What runs | Status |
|---|---|---|
| Every PR and push to `main` | **CI** — ruff lint, ruff format check, mypy, 6 dataset-integrity tests | `implemented` |
| Every PR and push to `main` | Astro landing build, Streamlit syntax check and container builds, gated on `frontend/landing/package.json`, the prototype and the Dockerfiles | `blocked` — files missing, jobs skip cleanly |
| Tag `v*` | **CD** — publish `-api` and `-prototype` images to GHCR, re-run the TensorFlow training smoke test, publish the report to GitHub Pages | `blocked` — Dockerfiles, `dl/training/train.py` and `docs/report/_quarto.yml` missing |

The optional jobs are gated by a small `changes` job that checks for the files
and exposes the result as a job output. This is deliberate: job-level
`if: hashFiles(...)` is invalid GitHub Actions syntax (the function only exists
in a step), and using it made both workflows fail to parse with zero jobs. The
gates are a fix, not a feature.

## 10. Planned Kubernetes, Minikube and Argo CD workflow

**Status: `missing`.** The target is documented in
[**ADR-0004**](docs/adr/0004-vercel-and-gitops-deployment.md) and
[`docs/architecture/`](docs/architecture/README.md); no manifests exist.

1. CD publishes pinned `-api` and `-prototype` image tags to GHCR.
2. `k8s/base/` holds the API and prototype Deployments, Services, ConfigMap and
   the prototype Ingress; `k8s/overlays/local/` targets Minikube. FastAPI is a
   ClusterIP Service; only the Streamlit prototype is exposed.
3. An Argo CD application watches this repository and syncs the local overlay,
   so a cluster change is a commit rather than a manual edit.
4. Vercel deploys the Astro landing page from its Git integration and links to
   the public prototype URL.
5. `docker compose` remains the local developer path (API + prototype).
   Kubernetes is the demo target, not a requirement for contributing.

**Reachability, solved by topology.** A Vercel page cannot call a Minikube API on
`localhost`. The landing page is static and makes no API call; the browser opens
Streamlit, and Streamlit calls FastAPI inside the cluster. For a public demo,
expose **Streamlit** through an ingress tunnel (for example Cloudflare Tunnel or
ngrok) or a public cluster; FastAPI stays internal. Do not expose the inference
API just to make the landing page work.

The fallback is explicit: if Minikube or Argo CD cannot be made reproducible by
the end of week 2, the demo runs on compose and the reversal is recorded in
ADR-0004 rather than left unspoken.

## 11. Frontend: Astro landing page and Streamlit prototype

**Status: `missing`.** `frontend/` contains READMEs only. The target is two
surfaces, not one dashboard:

| Surface | Stack | Runs on | Purpose |
|---|---|---|---|
| **Landing** | Astro + Tailwind | **Vercel** | Project story, published results, links to the demo, report and repository |
| **Prototype** | Streamlit | **Minikube** (or compose) | Upload or pick a frame, choose a model, set a threshold, see overlay/heatmap/scores |

The landing pages are `/` (story and status), `/results` (published comparison,
empty until experiments land) and `/about` (protocol, ADR-0001 caveat, credits).
The demo button points at the public Streamlit URL. The prototype is the only
surface that calls FastAPI, and it does so from inside the cluster.

The rules are narrow on purpose: the landing page makes no runtime API call and
renders only numbers that trace to `docs/experiments/`; the prototype contains no
model code, shows an explicit error when the API is unreachable and never draws a
placeholder mask. The API contract remains the OpenAPI schema at `/docs`; the
Streamlit client validates the fields it reads. No Vercel project, Astro app or
Streamlit app exists yet. See
[ADR-0006](docs/adr/0006-astro-and-streamlit-frontend.md).

## 12. Technical and commercial validation

The module grades two independent validations. The full traceability matrix —
every requirement, its evidence, its file and its status — is
[`docs/validation/requirements-matrix.md`](docs/validation/requirements-matrix.md).
This table is only a summary; the matrix is the authority.

| Validation | Weight | `implemented` | `in progress` | `missing` | `blocked` |
|---|---:|---:|---:|---:|---:|
| Technical (W9) | 60 % | 0 | 1 | 5 | 2 |
| Commercial (W10) | 40 % | 0 | 4 | 9 | 2 |
| **Both** | 100 % | **0** | **5** | **14** | **4** |

The zeros are the honest state at this commit. In particular:

- **XAI is not planned** (gap G1). It is not in ADR-0002 or the roadmap, and no
  method has been chosen. This is a technical-validation requirement, not an
  optional extra.
- **No model exists**, so the comparison, the selected-model deployment and the
  commercial demo are all downstream of the same dependency.
- **No commercial artefact exists** — no canvas, no 4Ps, no penetration
  strategy, no logo/flyer, no teaser and no report.
- **Ownership is unassigned**; every CODEOWNERS path routes to the repository
  owner until the kickoff meeting.

## 13. Limitations and pending work

**Scientific limitations.**

- **60 evaluation frames** mean every metric has a wide confidence interval.
  Results are reported as per-frame distributions, and differences smaller than
  the spread are not argued about.
- **One anomaly class** means localisation is measurable but recognition is not.
- **No anomaly training data** by construction; the protocol is zero-shot or
  threshold-tuned on held-out folds, and the two regimes are never mixed.

**Implementation gaps.** No loader, model, training loop, metric harness,
experiment record, API, Astro landing page, Streamlit prototype, container,
Kubernetes manifest, Argo CD application or Vercel project exists. The results
table stays empty until a number can be traced to `docs/experiments/`.

**Commercial gaps.** No introduction, context, existing/deployed-solutions
survey, Business Model Canvas, 4Ps, penetration strategy, brand assets, teaser
or complete report exists. The plan and statuses are in
[`docs/report/README.md`](docs/report/README.md).

**People.** Workstream ownership is assigned at the kickoff meeting; until then
the tables describe roles, not people. The one edit that turns review routing on
is replacing the placeholder handles in [`.github/CODEOWNERS`](.github/CODEOWNERS).

**Risks, named.** *Compute:* three models on limited GPUs — mitigated by model A
being cheap and C using pretrained backbones. *Scope:* the experience layer is
week 3 work; if week 2 slips, the Astro landing page is reduced to a single
static page and the Streamlit prototype carries the demo. The graded deliverable
is the deep learning work and the report. *Time:* three weeks for six people,
with the commercial validation landing after the technical one.

| Week | Dates | Goal | Milestone |
|---|---|---|---|
| **1** | Oct 19–25 | Foundations | Dataset loader + EDA; harness interface frozen; **autoencoder baseline producing a real number**; CI green |
| **2** | Oct 26 – Nov 1 | The comparison | Resynthesis and segmentation models; threshold selection; ablations; per-frame and failure analysis |
| **3** | Nov 2–8 | Deliverables | FastAPI + Astro landing page + Streamlit prototype + compose; report written and rendered; README results table filled; reproducibility pass on a clean clone; tag `v1.0.0` |

---

## Repository map

```
RoadAnomaly/
├── README.md               this file
├── AGENTS.md               instructions for coding agents
├── CONTRIBUTING.md         branching, review and suppression rules
├── Makefile                developer targets (status table in §6)
├── pyproject.toml          ruff, mypy, pytest and coverage configuration
├── requirements/           dev · dl · api-base · api · prototype sets
├── data/                   60 frames + labels + credits        (implemented)
├── dl/
│   ├── data/               loader, mask decoding, splits        (missing)
│   ├── models/             autoencoder · resynthesis · seg      (missing)
│   ├── training/           one loop for all three models        (missing)
│   ├── evaluation/         metrics.py — defined once            (missing)
│   ├── inference/          SavedModel export + scoring          (missing)
│   └── notebooks/          EDA and result narratives            (missing)
├── configs/                one YAML per experiment              (missing)
├── backend/                FastAPI inference service            (missing — stub)
├── frontend/               Astro landing + Streamlit prototype  (missing — READMEs)
├── prototypes/             intended experimental workflow       (README only)
├── tests/
│   ├── dataset/            frame ↔ label contract (6 tests)     (implemented)
│   ├── unit/               pure functions                       (missing)
│   └── integration/        API and artifact contracts           (missing)
├── infra/                  README; docker/ + compose/ planned   (missing)
├── docs/
│   ├── architecture/       archify spec, HTML and Mermaid docs
│   ├── adr/                0001–0006
│   ├── experiments/        one file per run set                 (empty log)
│   ├── report/             technical outline + commercial plan  (outline only)
│   └── validation/         requirements traceability matrix
├── assets/                 generated README images
└── .github/                CI/CD, CODEOWNERS, PR and issue templates
```

`k8s/` and `argocd/` do not exist yet. Creating them empty would imply a
deployment that is not there; they are documented as the target in §10 and
ADR-0004. Each existing directory has its own README explaining what belongs in
it.

## Reproducibility

```bash
# Every published number must be reproducible from these three things:
#   1. the commit          2. the config in configs/         3. this command
make train CONFIG=configs/<name>.yaml
make eval  CKPT=artifacts/<name>.keras
```

- **Seeds are fixed and recorded** in the config; data-loader worker seeding is
  explicit, not inherited from the clock.
- **Notebook outputs are stripped before commit.** `.gitattributes` declares the
  `nbstripout` filter; each clone runs `nbstripout --install` once (see
  [`CONTRIBUTING.md`](CONTRIBUTING.md)) so diffs show code changes, not image
  bytes.
- **Artefacts are not committed.** Checkpoints, SavedModel exports and run logs
  are regenerated; `artifacts/` is ignored.
- **The environment is pinned** by `requirements/*.txt` and, in CI, by the exact
  Python/Node versions in `.github/workflows/`. The manifest records the exact
  TensorFlow version used for each artifact.
- **TensorFlow determinism:** the training entrypoint calls
  `tf.keras.utils.set_random_seed(seed)` and
  `tf.config.experimental.enable_op_determinism()`. Where cuDNN or reduction
  kernels still shift metrics in the third decimal, the experiment file records
  the observed spread rather than pretending it is zero.

## Team

**Six contributors**, equal contribution — the list order below is not a
ranking.

| Contributor |
|---|
| Emna Trabelsi |
| Ines Trabelsi |
| Hejer Mnejja |
| Walid Fehry |
| Khaled Gannoun |
| Adrian Salvador Ekomo Mesi Obono |

The project is split into six workstreams so that each has exactly one owner
and no file has two. **Owners are assigned at the kickoff meeting** — until
then every path is reviewed by the repository owner (see
[`.github/CODEOWNERS`](.github/CODEOWNERS)).

| | Workstream | Scope | Also responsible for |
|---|---|---|---|
| **M1** | Data & protocol | `dl/data/`, `tests/`, splits | EDA notebook 01, keeping ADR-0001 true in code |
| **M2** | Model A — autoencoder | `dl/models/autoencoder.py`, `dl/training/` | Baseline end-to-end in week 1 |
| **M3** | Model B — resynthesis | `dl/models/resynthesis.py` | Faithfulness to Lis et al. and what we deviate from |
| **M4** | Model C + metrics | `dl/models/segmentation.py`, `dl/evaluation/` | The shared harness everyone depends on — frozen in week 1 |
| **M5** | Backend & delivery | `backend/`, `infra/`, `.github/workflows/` | Compose stack, images, CI/CD |
| **M6** | Frontend & report | `frontend/`, `docs/`, `assets/` | Astro landing, Streamlit prototype, README, diagram, report assembly |

Everyone writes their own section of the report. **M4's harness is the critical
path**: it is the interface the other two models plug into, so its signature is
frozen in week 1 and changes to it need M2, M3 and M4 to agree.

## Citation

Cite the dataset paper as the authors request, in their own BibTeX key:

```bibtex
@inproceedings{DetectingTheUnexpected2019,
  title     = {Detecting the Unexpected via Image Resynthesis},
  author    = {Krzysztof Lis and Krishna Nakka and Pascal Fua and Mathieu Salzmann},
  booktitle = {International Conference on Computer Vision},
  year      = {2019},
  url       = {https://infoscience.epfl.ch/record/269093?ln=en}
}
```

Also available as [arXiv:1904.07595](https://arxiv.org/abs/1904.07595).
Machine-readable metadata for this repository is in [`CITATION.cff`](CITATION.cff).

## License and credits

Code is [MIT](LICENSE). **The data is not.** Images are third-party photographs
provided for research purposes with per-image terms, and the annotations are
CC BY-SA 4.0. [`data/credits.txt`](data/credits.txt) lists the author, source and
licence of every frame — keep it intact in any redistribution, and carry the
attribution with any figure you publish.
