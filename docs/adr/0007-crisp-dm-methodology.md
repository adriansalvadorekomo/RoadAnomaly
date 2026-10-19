# 0007. Use CRISP-DM as the project methodology

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** whole team

## Context

The module assesses both the deep-learning work and the process used to reach
it. The repository previously described a custom five-stage pipeline (data,
modeling, evaluation/promotion, serving, delivery). That vocabulary was useful
for the architecture diagram, but it hid two things a reviewer needs to see:

1. **Evaluation is not one phase.** Selection on normal-road validation,
   held-out scoring on RoadAnomaly and explainability are separate activities
   with different evidence and different promotion rights.
2. **Deployment is part of the method, not an afterthought.** Export, model
   registration, image publication, GitOps and the serving surfaces all have
   decisions that can invalidate a result if they are improvised late.

The project is iterative: a failed evaluation can send work back to data
preparation or modeling, and a deployment finding can reopen the business
constraints. A waterfall description would be inaccurate.

## Decision

Use **CRISP-DM** as the project methodology:

| Phase | What it owns in this repository | Evidence |
|---|---|---|
| 1. Business understanding | Objectives, success criteria, evaluation-only protocol, scope and non-goals | `README.md` §1, [ADR-0001](0001-evaluation-only-benchmark.md) |
| 2. Data understanding | RoadAnomaly dataset facts and EDA; normal-road source audit and licence review | `tests/dataset/`, `data/readme.md`, `dl/notebooks/` (missing) |
| 3. Data preparation | Normal-road loading, decoding, augmentation, scene-grouped train/validation splits and a pinned dataset manifest | `dl/data/` (missing), `configs/` (empty) |
| 4. Modeling | Three Keras families behind one interface and one training loop | [ADR-0002](0002-three-model-families.md), [ADR-0005](0005-tensorflow-framework.md) |
| 5. Evaluation | Shared metric harness, normal-road selection, RoadAnomaly held-out scoring, threshold regimes and XAI | `dl/evaluation/` (missing), [ADR-0008](0008-promotion-and-model-registry.md), [ADR-0009](0009-xai-evaluation-gate.md) |
| 6. Deployment | SavedModel export and registry, FastAPI, Streamlit, Astro/Vercel, containers, Minikube and Argo CD | [ADR-0004](0004-vercel-and-gitops-deployment.md), [ADR-0006](0006-astro-and-streamlit-frontend.md) |

The phases are **iterative and evidence-gated**, not a one-way waterfall:

- Evaluation may return work to data preparation or modeling.
- Deployment feedback may reopen business understanding, but it never triggers
  automatic retraining on RoadAnomaly.
- The phase boundary is a documentation and review boundary; it is not a new
  runtime component.

This ADR does not change the evaluation-only protocol. It makes that protocol a
gate in phase 1 and phase 5 rather than a footnote.

## Alternatives considered

| Option | Why not |
|---|---|
| Keep the custom five-stage map | It conflated benchmark scoring with selection and made deployment look optional |
| CRISP-ML(Q) | A good extension, but it adds quality-assurance vocabulary the module does not ask for and the team would have to maintain |
| TDSP | More prescriptive about team roles and tooling than a three-week, six-person module project needs |
| Ad-hoc / Kanban only | Describes tasks, not the analytical lifecycle the report must justify |

## Consequences

**What gets easier.** The report can map each section to a recognised phase, and
the architecture diagram can show where selection, held-out scoring, XAI and
deployment sit. Reviewers can ask "which phase produced this evidence?" instead
of inferring a pipeline from a diagram.

**What gets harder.** Every experiment record must say which phase it belongs to
and whether its metric was a selection signal or a held-out report. A result
cannot be moved between those categories after the fact.

**How we would know this was wrong.** If the module required a different
methodology, or if the team could not map a required deliverable to one of the
six phases without inventing a seventh, this decision should be revisited.
