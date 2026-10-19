# `prototypes/` — intended experimental workflow

> **Status: intended, not implemented.** No prototype application exists here
> yet. The steps below define the order in which experimental work is expected
> to happen and where each artefact belongs. Nothing in this file is evidence
> that a step is complete.

The graded work is the deep learning study; prototypes are how a result becomes
visible before it is promoted into `dl/`, `backend/` or `frontend/`.

| # | Step | Output | Where it belongs | Status |
|---|---|---|---|---|
| 1 | Dataset comprehension | EDA notebook: masks, class vocabulary, scale and coverage distributions | `dl/notebooks/01_dataset_eda.ipynb` | missing |
| 2 | Data preparation | loader, normal-road corpora, scene-grouped folds | `dl/data/` | missing |
| 3 | Model selection and training | models A/B/C behind one interface; one YAML per run | `dl/models/`, `dl/training/`, `configs/` | missing |
| 4 | Evaluation and comparison | shared metric harness, per-frame table, failure analysis | `dl/evaluation/`, `docs/experiments/` | missing |
| 5 | Explainable AI (XAI) | saliency, occlusion or error maps plus a written justification of the method | `dl/inference/`, report | blocked — no trained model and no recorded method decision (gap G1) |
| 6 | Image and video inference | single-frame and sequence scoring, latency measurement | `dl/inference/`, `backend/` | missing |
| 7 | Streamlit prototype (accepted in ADR-0006) | interactive one-result UI | `frontend/prototype/` | missing |
| 8 | Integration with backend and deployment | export → API → Astro landing + Streamlit prototype → Vercel / Kubernetes | `backend/`, `frontend/`, `infra/`, `k8s/` | blocked on steps 2–6 |

## Rules

- A prototype may be ugly; it may not invent a number. Every displayed metric
  must come from an experiment file.
- Anything that survives validation moves into `dl/` (logic) or `frontend/`
  (UI). The API never imports from `prototypes/`.
- The frontend split is accepted in
  [ADR-0006](../docs/adr/0006-astro-and-streamlit-frontend.md): an Astro landing
  page on Vercel and a Streamlit prototype. Do not add either application as
  part of a documentation or structure change; implementation follows the ADR
  and the evidence bar in the requirements matrix.
- Step 5 is required by the technical validation. It is `blocked` on trained
  models, and it is also missing a method decision; both facts are tracked in
  [`docs/validation/requirements-matrix.md`](../docs/validation/requirements-matrix.md).
