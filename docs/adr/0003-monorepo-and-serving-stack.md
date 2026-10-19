# 0003. Monorepo, FastAPI + Next.js, GHCR delivery

- **Status:** Accepted; deployment clause superseded by
  [ADR-0004](0004-vercel-and-gitops-deployment.md)
- **Date:** 2026-10-18
- **Deciders:** whole team

> **Superseded in part.** The stack choices below stand. The sentence that
> makes local `docker compose` the only deployment target is replaced by
> Vercel (frontend) and Kubernetes/Minikube + Argo CD (inference service) in
> [ADR-0004](0004-vercel-and-gitops-deployment.md). `docker compose` remains the
> local developer path.
>
> **Framework note (ADR-0005).** The serving artifact is a TensorFlow SavedModel
> loaded by FastAPI with `tensorflow-cpu`; the TorchScript/ONNX and ONNX Runtime
> references below are historical. The FastAPI and monorepo decisions stand.
>
> **Frontend note (ADR-0006).** The single Next.js dashboard is replaced by an
> Astro landing page on Vercel plus a Streamlit prototype. FastAPI remains the
> only inference service. The Next.js alternatives below are historical; the
> Streamlit prototype is the accepted choice.

## Context

The graded deliverables are the code, the methodology, the evaluation and a
technical report. On top of that the team wants the work to be demonstrable:
a dashboard where a reviewer uploads a road image and sees the anomaly mask,
backed by an API that runs the trained models.

Six people, three weeks, one Git remote. Every extra runtime is a cost paid by
whoever has the least time that week.

## Decision

**One repository** containing `dl/`, `backend/`, `frontend/`, `infra/` and
`docs/`, with the dataset committed directly to git (15 MB — small enough that
a clone reproduces the project, and the dataset is the subject of the report,
so it belongs in the history).

**Backend: FastAPI** serving `POST /predict`, with models loaded from exported
TorchScript/ONNX artifacts. Same language as the model code, so a model bug never
requires switching ecosystems, and the OpenAPI schema documents the contract
for the frontend for free.

**Frontend: Next.js + Tailwind + shadcn/ui** — upload, mask overlay, heatmap,
and a side-by-side comparison of the three methods. Server components let the
dashboard render the first screen without a client round-trip.

**Delivery: GitHub Actions → GHCR → docker-compose.** CI (lint, types, tests,
dataset integrity) runs on every pull request and needs no secrets and no GPU,
so it can never be the reason a contributor is blocked. CD runs only on a
`v*` tag: images are pushed to GHCR, the training smoke test re-runs, and the
report is published to GitHub Pages. Deployment target is a local
`docker compose up` on the machine that will demo it.

## Alternatives considered

| Option | Why not |
|---|---|
| Separate repos for the models, API and frontend | Three remotes, three CI configurations, and version skew between a model artifact and the API that loads it — for a project whose whole point is that the pieces line up |
| Streamlit/Gradio instead of a Next.js dashboard | Far less work, and honest about where the value is; rejected because the deliverable includes a real frontend and the team has the capacity |
| TorchServe/Triton as a model server | More production-realistic, but an extra service to operate; FastAPI + ONNX Runtime covers a single-user demo |
| Git LFS or DVC for the dataset | Adds a dependency and a failure mode for 15 MB that git handles without complaint |
| Kubernetes / cloud deployment | Operational cost with no benefit for a course demonstration |
| Pushing images on every merge to `main` | Deploys unreviewed states; tags make the deployed revision a deliberate act |

## Consequences

**What gets easier.** One clone and `make install` gives a contributor
everything. `docker compose up` reproduces the demo. CI is fast and
fork-friendly. The architecture diagram is one picture of one system.

**What gets harder.** `main` must stay green across three toolchains, so
unrelated changes can break the build for everyone. The dataset in git means
the clone is 15 MB rather than a few hundred kilobytes. The API and the
dashboard share a contract that lives in two languages — the OpenAPI schema is
the seam, and it must be updated deliberately rather than by hand.

**How we would know this was wrong.** If CI on `main` is red for more than a
day, or if the dataset grows past ~200 MB (a second anomaly dataset), we
revisit: split the repositories, move the data to DVC, and record the reversal
here.
