# 0004. Vercel frontend and GitOps inference deployment

- **Status:** Accepted (target state; implementation not started)
- **Date:** 2026-10-19
- **Deciders:** whole team
- **Supersedes in part:** [ADR-0003](0003-monorepo-and-serving-stack.md) —
  deployment clause only. The stack choices in ADR-0003 stand.

> **Framework note (ADR-0005).** The inference runtime is TensorFlow
> (`tensorflow-cpu` + SavedModel), not ONNX Runtime. The Vercel, Kubernetes and
> Argo CD target is unchanged.
>
> **Frontend note (ADR-0006).** Vercel hosts the Astro landing page. The
> Streamlit prototype and FastAPI run in Minikube; the prototype is the only
> public workload and calls FastAPI over the cluster network. The Vercel page
> links to the prototype instead of calling the Minikube API directly.

## Context

ADR-0003 chose a local `docker compose up` as the deployment target and
rejected Kubernetes as operational cost with no benefit for a course demo.

The project now has to document — and eventually demonstrate — a deployment
workflow that goes beyond a laptop: the frontend is expected to run on Vercel,
and the inference service on Kubernetes locally (Minikube) with Argo CD
performing GitOps synchronisation.

Nothing in this decision is implemented yet: there are no Dockerfiles, no
manifests, no Argo CD application and no Vercel project at this commit. The
point of the ADR is to make the target explicit before files appear, and to
record that it supersedes the "compose only" clause of ADR-0003 rather than
silently contradicting it.

## Decision

1. **Frontend: Vercel.** The Next.js dashboard is deployed to Vercel. The API
   base URL is an environment variable; no backend URL is hard-coded.
   *(Superseded by ADR-0006: the Vercel workload is now the Astro landing page;
   the Streamlit prototype runs in Minikube.)*
2. **Inference service: Kubernetes, locally Minikube.** Manifests live in
   `k8s/base/` (Deployment, Service, ConfigMap) with a
   `k8s/overlays/local/` overlay for Minikube.
3. **GitOps: Argo CD.** The Argo CD application watches this repository and
   syncs the local overlay. A cluster change is a commit, not a manual edit.
4. **Images: GHCR.** The existing CD workflow publishes `-api` and `-web`
   images on tags. *(Now `-api` and `-prototype`; see ADR-0006.)* Kubernetes
   pulls the pinned tag; `latest` is never deployed.
5. **Local developer path: `docker compose`.** `infra/compose/` remains the
   fastest way to run both services on a laptop. Kubernetes is the demo target,
   not a requirement for contributing.

## Alternatives considered

| Option | Why not |
|---|---|
| Keep compose as the only target (ADR-0003) | Does not meet the deployment workflow the module asks us to document; leaves the GitOps story empty |
| Managed cloud Kubernetes | Cost and credentials for a three-week project; Minikube demonstrates the same manifests locally |
| Vercel for the FastAPI service too | Vercel is built for serverless/Next.js; a long-running ONNX inference container does not fit its deployment model |
| Argo CD only, without a local cluster | Nothing to sync to during the demo; Minikube makes the flow reproducible on one machine |

## Consequences

**What gets easier.** The deployment story becomes reviewable in Git: manifests,
overlay and Argo CD application are versioned with the code. The frontend gets
preview deployments per pull request. The GHCR images already produced by CD
become the deployment artefact.

**What gets harder.** Three new surfaces to operate (Vercel project, Minikube,
Argo CD) on top of the compose stack. Manifests can drift from the images if
the tag is not pinned. The team must decide who owns the cluster and the Vercel
project before the demo.

**Status.** `missing` until the first Dockerfile lands. Tracked as G8 in
[`docs/validation/requirements-matrix.md`](../validation/requirements-matrix.md).

**How we would know this was wrong.** If Minikube or Argo CD cannot be made
reproducible on the demo machine by the end of week 2, the fallback is the
compose stack, recorded here as a reversal rather than an unspoken failure.
