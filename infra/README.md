# `infra/` — containers and local stack

Owner: **M5**.

```
infra/
├── docker/
│   ├── Dockerfile.backend    python:3.12-slim, tensorflow-cpu, non-root
│   └── Dockerfile.prototype  python:3.12-slim, streamlit, non-root
└── compose/
    └── docker-compose.yml    api + prototype, pinned to GHCR tags or local builds
```

The Astro landing page is not containerized for the serving path. Vercel builds
it from the repository's Git integration; locally it runs with `make landing`.
See [ADR-0006](../docs/adr/0006-astro-and-streamlit-frontend.md).

## The stack

| Service | Port | Image | Notes |
|---|---|---|---|
| `api` | 8000 | `ghcr.io/adriansalvadorekomo/roadanomaly-api:<tag>` | reads the `artifacts/` volume, model loaded at startup |
| `prototype` | 8501 | `ghcr.io/adriansalvadorekomo/roadanomaly-prototype:<tag>` | calls `api` over the compose network; public workload in K8s |

```bash
make up      # docker compose -f infra/compose/docker-compose.yml up --build
make down
```

## Container rules

- **Only the inference runtime ships in the API image.** Trained weights are
  exported to a SavedModel by `dl/inference/`; the image installs
  `tensorflow-cpu`, not the training dependencies. TensorFlow is heavier than
  ONNX Runtime, so multi-stage builds and CPU-only wheels are mandatory.
- **The prototype image ships Streamlit, not TensorFlow.** It is a client of
  `POST /predict` and must never load a SavedModel or import `dl/`.
- **Model artifacts are mounted read-only.** The API reads a versioned
  SavedModel and its manifest from the `artifacts/` volume; training never runs
  inside the serving container.
- **Non-root user** in both images.
- **Pinned base tags**, not `latest`, so a rebuild next week builds the same
  thing.
- Version tags in `docker-compose.yml` are pinned to a released tag
  (`v1.0.0`), matching what CD publishes. `:latest` is never deployed.
- The API image is CPU-only on purpose: the demo runs anywhere, and GPU
  inference is a training-time concern, not a serving-time one.

## Status

**No container file exists yet.** The tree above is the intended layout; the
directories appear when their first file lands. `make up` and the container
jobs in CI/CD are therefore gated and will not run.

## Deployment target (planned)

| Surface | Target | Exposure | Status |
|---|---|---|---|
| Local development | `docker compose` (`infra/compose/`) | localhost only | `missing` |
| Landing page | Vercel (Astro static build) | public | `missing` |
| Prototype | Minikube (`k8s/base/` + `k8s/overlays/local/`) | public ingress or tunnel | `missing` |
| Inference service | Minikube, ClusterIP Service | cluster-internal only | `missing` |
| GitOps | Argo CD syncing the local overlay | cluster-internal | `missing` |

Images are published to GHCR by CD on a `v*` tag. Kubernetes pulls the pinned
tags; `latest` is never deployed. The prototype is the only public workload
because it is the only surface that needs to receive browser traffic; FastAPI
stays internal. See [ADR-0004](../docs/adr/0004-vercel-and-gitops-deployment.md),
[ADR-0006](../docs/adr/0006-astro-and-streamlit-frontend.md) and
[`docs/architecture/`](../docs/architecture/).
