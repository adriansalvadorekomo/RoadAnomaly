# Architecture

Component responsibilities, data flow and deployment boundaries for
RoadAnomaly. Every diagram is labelled **current** (exists in the repository
today) or **proposed** (target state, not implemented). The matrix in
[`docs/validation/requirements-matrix.md`](../validation/requirements-matrix.md)
is the authority on status.

| Term | Meaning here |
|---|---|
| **current** | Backed by files in this repository that run today |
| **proposed** | Agreed target; no implementation yet |
| **eval-only** | The 60 RoadAnomaly frames are never used to fit weights ([ADR-0001](../adr/0001-evaluation-only-benchmark.md)) |

The high-level picture is generated from
[`architecture.json`](architecture.json) with
[archify](https://github.com/tt-a1i/archify); open
[`architecture.html`](architecture.html) for the interactive version. The PNGs
embedded in the README are exported from the same spec at 2×.

The map is intentionally tall (1090 × 1090) so five stages and twelve components
stay legible at README width. The interactive viewer scrolls on a laptop instead
of shrinking the labels below reading size; that is a deliberate trade-off, not
a missing responsive layout.

The spec is titled **RoadAnomaly End-to-End System Map**. It places RoadAnomaly
in the evaluation stage, not in the training data, and shows the serving split:
FastAPI is cluster-internal, Streamlit is the public interactive prototype and
the Astro landing page on Vercel links to it. The diagram is a target, not a
claim that those components are running.

## Current architecture (implemented)

The repository is a verified dataset, a test harness, a CI workflow and the
documentation that constrains the work. There is **no running model service**.

```mermaid
flowchart TD
  D["data/ — 60 frames, labels, credits"] --> T["tests/dataset — 6 integrity tests"]
  T --> CI["GitHub Actions CI — ruff, mypy, pytest"]
  ADR["docs/adr — protocol and stack decisions"] -.-> D
  M["docs/validation — evidence matrix"] -.-> CI
```

What runs today:

- `make data-check` re-derives every documented dataset fact.
- `make lint type test` is the same gate CI runs.
- `.github/workflows/ci.yml` runs on every pull request and every push to
  `main`.
- `.github/workflows/cd.yml` is valid but its image, smoke-test and report jobs
  are gated on files that do not exist yet.

## Target architecture (proposed)

```mermaid
flowchart LR
  subgraph data["1 · Data — normal-road only"]
    NP["Normal-road pipeline<br/>Cityscapes / BDD100K · tf.data · train/val"]
  end

  subgraph modeling["2 · Modeling — TensorFlow/Keras"]
    A["A · Autoencoder<br/>reconstruction error"]
    B["B · Resynthesis<br/>synthesize → residual"]
    C["C · Segmentation<br/>DeepLabV3+ / U-Net · MSP"]
  end

  subgraph evaluation["3 · Evaluation & promotion — eval-only"]
    RA["RoadAnomaly<br/>60 frames · never trained"]
    EV["Shared evaluation harness<br/>metrics · threshold CV"]
    REG["Model registry<br/>SavedModel + manifest"]
  end

  subgraph serving["4 · Serving & experience — Minikube + Vercel"]
    API["FastAPI inference<br/>POST /predict · cluster-internal"]
    ST["Streamlit prototype<br/>public ingress · interactive demo"]
    WEB["Astro landing page<br/>Vercel · static · no API call"]
  end

  subgraph delivery["5 · Delivery — GitHub Actions + Argo CD"]
    CI["GitHub Actions<br/>tests · GHCR images"]
    K8S["Minikube + Argo CD<br/>syncs API and prototype"]
  end

  NP --> A
  NP --> B
  NP --> C
  A --> EV
  B --> EV
  C --> EV
  RA --> EV
  EV --> REG
  REG --> API
  ST --> API
  API --> ST
  WEB -. "demo link" .-> ST
  CI --> K8S
  K8S --> API
  K8S -. "deploys" .-> ST
```

The model families are described in
[ADR-0002](../adr/0002-three-model-families.md), the TensorFlow choice in
[ADR-0005](../adr/0005-tensorflow-framework.md), and the frontend split in
[ADR-0006](../adr/0006-astro-and-streamlit-frontend.md). The deployment target is
[ADR-0004](../adr/0004-vercel-and-gitops-deployment.md).

## Component responsibilities

| Component | Responsibility | Status |
|---|---|---|
| `data/` | The evaluation benchmark: 60 frames, semantic/instance labels, per-image credits | implemented |
| `tests/dataset/` | Guards the frame ↔ label contract and every number published in the README | implemented |
| `dl/data/` | Normal-road loading, mask decoding, transforms, scene-grouped folds | missing |
| `dl/models/` | Autoencoder, resynthesis and segmentation models behind one interface | missing |
| `dl/training/` | One TensorFlow/Keras training loop for all three families | missing |
| `dl/evaluation/` | The single implementation of every metric; framework-free | missing |
| `dl/inference/` | SavedModel export and shared scoring helpers | missing |
| `configs/` | One YAML per run, shared by training and evaluation | missing |
| `backend/` | FastAPI service, `tensorflow-cpu`, `POST /predict` | missing |
| `frontend/landing/` | Astro + Tailwind static landing page on Vercel | missing |
| `frontend/prototype/` | Streamlit interactive client for FastAPI | missing |
| `infra/docker/` | API and prototype images | missing |
| `infra/compose/` | Local two-service stack (API + prototype) | missing |
| `k8s/`, `argocd/` | Local Kubernetes overlay and GitOps application | missing (documented target only) |
| `.github/workflows/` | CI on every PR; CD on tags; Vercel builds the landing page | implemented, with gated jobs |

## Data flow

1. **Training** uses normal-road corpora only (Cityscapes/BDD100K normal
   subsets, ImageNet-pretrained backbones). The anomaly is defined by absence.
2. **Evaluation** runs every one of the 60 RoadAnomaly frames, including the
   failures. Each frame has at least 0.4 % anomalous pixels, so no frame is
   dropped from the per-frame statistics.
3. **Threshold tuning**, when reported, uses scene-grouped k-fold over the
   `animals*`, `cones*`, `obstacles*`, `lost_tires*` and `vehicle*` groups. It is
   never mixed with the zero-shot column.
4. **Promotion** selects on normal-road validation, then publishes a SavedModel
   and a manifest: git SHA, config hash, dataset version, TensorFlow version,
   input spec, validation metrics and default threshold.
5. **Serving** loads the SavedModel into FastAPI and returns a score map; the
   threshold is a request parameter, not a constant.
6. **Experience** keeps the API internal. Streamlit accepts browser traffic and
   calls the API inside the cluster; the Astro landing page is static, links to
   the prototype and renders only published results.

## Inference flow (proposed)

```mermaid
sequenceDiagram
  actor U as Reviewer
  participant L as Astro landing (Vercel)
  participant S as Streamlit prototype (Minikube)
  participant A as FastAPI service (Minikube, internal)
  participant R as Model registry (SavedModel)
  U->>L: open the public page
  L-->>U: project story + published results
  L-->>U: demo link
  U->>S: open the prototype, upload or pick a frame
  S->>A: POST /predict (file, model, optional threshold)
  A->>R: load SavedModel + manifest once at startup
  A->>A: preprocess → score map → threshold → mask
  A-->>S: mask, heatmap, scores, timing
  S-->>U: overlay, threshold slider, side-by-side comparison
```

## Frontend/backend boundary

- `POST /predict` accepts `multipart/form-data`: `file`, `model`, optional
  `threshold`.
- The OpenAPI schema at `/docs` is the source of truth. The Streamlit prototype
  validates the fields it reads; it does not define its own response shapes.
- `GET /health` and `GET /models` are the only other endpoints.
- The landing page has no API client: no runtime request, no generated TypeScript
  types, no API base URL. It links to the prototype instead.
- Nothing in this boundary exists yet: `backend/app/__init__.py` is the only
  backend file, and `frontend/` contains READMEs and the prototype dependency
  file.

## CI/CD flow (implemented workflow, gated jobs)

```mermaid
flowchart LR
  PR["Pull request / push to main"] --> CI["CI<br/>ruff · mypy · pytest"]
  CI -->|green| MERGE["merge"]
  MERGE --> TAG["tag v*"]
  TAG --> CD["CD"]
  CD --> IMG["GHCR images<br/>api + prototype<br/>gated on Dockerfiles"]
  CD --> SMOKE["training smoke test<br/>gated on dl/training/train.py"]
  CD --> PAGES["report to Pages<br/>gated on docs/report/_quarto.yml"]
  MERGE --> VERCEL["Vercel<br/>builds Astro landing"]
  CI --> LAND["Astro build<br/>gated on landing/package.json"]
  CI --> PROTO["Streamlit check<br/>gated on prototype/app.py"]
```

The gates are computed by a small detection job; the optional jobs skip
cleanly until their files land.

## Local Kubernetes and GitOps flow (proposed)

```mermaid
flowchart LR
  G["Git repository<br/>k8s/base + k8s/overlays/local"] --> ARGO["Argo CD"]
  ARGO -->|sync| MIN["Minikube cluster"]
  GHCR["GHCR image tags<br/>api + prototype"] --> MIN
  MIN --> API["FastAPI inference<br/>ClusterIP"]
  MIN --> ST["Streamlit prototype<br/>public Ingress"]
  ST --> API
  V["Vercel project"] --> WEB["Astro landing page"]
  WEB -. "demo link" .-> ST
```

No manifests, Argo CD application or Vercel project exist yet. The local
developer path remains `docker compose`; see
[`infra/README.md`](../../infra/README.md) and
[ADR-0004](../adr/0004-vercel-and-gitops-deployment.md).
