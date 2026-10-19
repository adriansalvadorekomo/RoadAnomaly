# `infra/` — containers and local stack

Owner: **M5**.

```
infra/
├── docker/
│   ├── Dockerfile.backend    python:3.12-slim, onnxruntime, no torch, non-root
│   └── Dockerfile.frontend   node:20-alpine -> next build -> standalone runtime
└── compose/
    └── docker-compose.yml    api + web, pinned to GHCR image tags or local builds
```

## The stack

| Service | Port | Image | Notes |
|---|---|---|---|
| `api` | 8000 | `ghcr.io/adriansalvadorekomo/roadanomaly-api:<tag>` | reads `artifacts/` volume, model loaded at startup |
| `web` | 3000 | `ghcr.io/adriansalvadorekomo/roadanomaly-web:<tag>` | talks to `api` over the compose network |

```bash
make up      # docker compose -f infra/compose/docker-compose.yml up --build
make down
```

## Container rules

- **No torch in the API image.** Trained weights are exported to ONNX by
  `dl/inference/`; shipping torch would triple the image for no benefit.
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

| Surface | Target | Status |
|---|---|---|
| Local development | `docker compose` (`infra/compose/`) | `missing` |
| Frontend | Vercel | `missing` |
| Inference service | Kubernetes on Minikube (`k8s/base/` + `k8s/overlays/local/`) | `missing` |
| GitOps | Argo CD syncing the local overlay | `missing` |

Images are published to GHCR by CD on a `v*` tag. Kubernetes pulls the pinned
tag; `latest` is never deployed. See
[ADR-0004](../docs/adr/0004-vercel-and-gitops-deployment.md) and
[`docs/architecture/`](../docs/architecture/).
