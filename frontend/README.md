# `frontend/` — landing page and prototype

Owner: **M6**.

Two surfaces, two jobs, one backend:

| Path | Stack | Runs on | Job |
|---|---|---|---|
| `landing/` | Astro + Tailwind | **Vercel** | Public project/results page; links to the demo, report and repository |
| `prototype/` | Streamlit | **Minikube** (or `docker compose`) | Upload/pick a frame, call FastAPI, show overlay/heatmap/scores |

The backend is FastAPI in [`backend/`](../backend/). The landing page does **not**
call the API; it links to the Streamlit prototype. The prototype calls the API
inside the cluster, so the browser never needs a route to the inference service.
See [ADR-0006](../docs/adr/0006-astro-and-streamlit-frontend.md).

## Rules

- **Never fake a result.** If the API is unavailable, the prototype says so. A
  placeholder mask that happens to look plausible is worse than an error state.
- **The landing page renders published results only.** Numbers come from
  `docs/experiments/` at build time and stay out of the page until the
  experiment file exists. An empty table is the honest default.
- **The prototype is a client, not a model runtime.** It must not import
  TensorFlow or load a SavedModel; that is the API's job.
- **Sample frames are evaluation data.** The bundled RoadAnomaly images are
  shown for evaluation/demo only; the UI repeats the ADR-0001 caveat and the
  attribution in [`data/credits.txt`](../data/credits.txt).
- **The API contract is the OpenAPI schema** at `/docs`. The prototype validates
  the fields it reads; the landing page has no runtime API types to generate.
  `pixel_stats` are display statistics, not IoU/Dice/AUROC/AUPRO.
- **XAI is gated.** The prototype shows an explanation panel only when
  explanation artifacts exist for the model digest (ADR-0009/ADR-0011). It must
  not label a score map as Grad-CAM, Seg-Grad-CAM or Integrated Gradients.

## Local commands

```bash
make landing     # Astro dev server on :4321
make prototype   # Streamlit on :8501
```

The Streamlit app reads `API_BASE_URL` (default `http://localhost:8000`).
`make install` installs `requirements/prototype.txt` alongside the Python
training and API dependencies.
