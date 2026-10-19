# 0006. Astro landing page and Streamlit prototype

- **Status:** Accepted (target state; implementation not started)
- **Date:** 2026-10-19
- **Deciders:** whole team
- **Supersedes in part:** the frontend clauses of
  [ADR-0003](0003-monorepo-and-serving-stack.md) and
  [ADR-0004](0004-vercel-and-gitops-deployment.md).

> The backend remains FastAPI ([ADR-0003](0003-monorepo-and-serving-stack.md))
> and the model runtime remains TensorFlow/Keras
> ([ADR-0005](0005-tensorflow-framework.md)). This record changes the frontend
> surfaces only.

## Context

ADR-0003 chose a single Next.js dashboard (Tailwind + shadcn/ui) that would
upload a frame, call the API and render overlays, heatmaps and a comparison.
ADR-0004 put that dashboard on Vercel and the inference service on
Kubernetes/Minikube with Argo CD.

The deliverable actually has two surfaces with different jobs:

1. A **public landing and results page** that explains the project, links to the
   report and the demo, and is fast, indexable and cheap to host. It does not
   need a live model call.
2. An **interactive prototype** where a reviewer uploads or picks a frame, runs
   the selected model, moves the threshold and sees the overlay and heatmap.
   This is a demo tool, not a production UI.

Building both as one Next.js application means writing a custom upload flow,
state management and chart layer before the prototype can be evaluated. Astro
builds the first surface as static HTML with almost no client JavaScript;
Streamlit gives the second surface a working upload, slider and image layout
with very little code. The team values an honest, working prototype over a
custom UI for its own sake.

There is also a network constraint. A Vercel deployment cannot call a FastAPI
service running on a developer's Minikube cluster on `localhost`. Keeping the
browser-facing demo inside the cluster, where it can reach the API service,
removes that constraint without exposing the inference API publicly.

## Decision

1. **Landing page: Astro + Tailwind** in `frontend/landing/`. It builds to static
   files and is deployed to **Vercel**. It makes no runtime API call. Metrics and
   examples are read from `docs/experiments/` at build time and are rendered only
   when they trace to a committed experiment record; an empty results table
   stays empty. It links to the Streamlit prototype, the technical report and
   the repository.
2. **Interactive prototype: Streamlit** in `frontend/prototype/`. It can upload
   a frame or pick a bundled evaluation frame, select a model, set an optional
   threshold and call the FastAPI `POST /predict` endpoint. It renders the
   overlay, heatmap, scores and timing. It contains no model code and never
   fabricates a result when the API is unavailable.
3. **Backend: FastAPI stays the only inference service.** It loads the
   TensorFlow SavedModel, owns preprocessing and returns the score map, mask and
   timing. The prototype is a client, not a second model runtime.
4. **Target topology.** The Astro landing page runs on Vercel. The Streamlit
   prototype and FastAPI run in Minikube (and in `docker compose` locally). The
   prototype is the only public workload, exposed through an ingress tunnel or a
   public cluster; FastAPI stays cluster-internal. The Vercel page links to the
   prototype's public URL and never calls the Minikube API directly.
5. **CI/CD.** The Astro build is gated on `frontend/landing/package.json`. A
   separate gated CI job installs the prototype dependencies and syntax-checks
   the Streamlit app; the main Python quality job stays focused on `dl/`,
   `backend/` and `tests/`. CI and CD build the API and prototype images; CD
   publishes them to GHCR, and Argo CD syncs both workloads. Vercel builds the
   landing page from the repository's Git integration, not from a GHCR image.

## Alternatives considered

| Option | Why not |
|---|---|
| One Next.js dashboard for both surfaces | More custom UI work than the prototype justifies; still leaves the Vercel-to-Minikube reachability problem |
| Gradio instead of Streamlit | The same class of tool; the team is already using Streamlit and it has a straightforward image/slider layout |
| Streamlit Community Cloud for the prototype | Public hosting is convenient, but it requires a publicly reachable FastAPI and adds cold starts and a second hosting account; acceptable as a later fallback, not the target |
| Server-rendered HTML from FastAPI (Jinja) | Keeps one runtime but gives up the interactive upload/threshold experience that the prototype exists to demonstrate |
| Next.js landing page only, no prototype | The technical validation needs reviewers to run the selected model; a static page cannot show the overlay or threshold behaviour |

## Consequences

**What gets easier.** The landing page is static, fast and cheap to host. The
prototype is small, Python-only and reuses the API contract. The public demo
path is browser → Streamlit → FastAPI, so the inference service never needs a
public IP. There is no TypeScript client to keep in sync with the API because
the landing page does not call it.

**What gets harder.** There are two frontend runtimes: Astro/Node for the
landing page and Streamlit/Python for the prototype. The prototype looks like
Streamlit, not a bespoke product, and has limited routing and layout control.
The landing page cannot show live inference results; it links to the prototype
instead. The OpenAPI schema remains the contract, but the Streamlit client must
validate responses explicitly rather than relying on generated TypeScript types.

**How we would know this was wrong.** If the prototype needs authentication,
multi-page navigation or a branded interface that Streamlit cannot deliver, or
if reviewers cannot reach the public prototype through the chosen ingress, add a
small Next.js client for the prototype and keep Astro for the landing page.
Revisit hosting before adding a second inference service.
