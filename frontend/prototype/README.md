# `frontend/prototype/` — Streamlit interactive demo

Owner: **M6**. **Status: `missing`** — this directory contains a README and the
dependency file.

One Streamlit page that lets a reviewer upload a road frame or pick a bundled
evaluation frame, choose a model, set an optional threshold and see the result.
It calls the FastAPI service; it does not load a model.

## Contract

- `POST /predict` with `multipart/form-data`: `file`, `model`, optional
  `threshold`.
- Response fields used by the UI: mask, heatmap or score map, scalar scores,
  timing and the model identifier. Validate the fields before rendering them.
- API base URL: `API_BASE_URL`, default `http://localhost:8000`.
- If the API is unreachable, show the error and the endpoint it tried. **Never**
  render a placeholder mask as if it were a prediction.
- Bundled samples are RoadAnomaly evaluation frames. The page repeats the
  evaluation-only caveat (ADR-0001) and links to `data/credits.txt`.

## Controls

| Control | Behaviour |
|---|---|
| Image | Upload a file or pick a bundled frame |
| Model | Select A, B or C; the API owns the model registry |
| Threshold | Slider; changing it re-renders the mask from the cached score map when possible, otherwise re-calls the API |
| Compare | Optional tab that sends the same frame through all three models and shows the scores side by side |

## Run

```bash
pip install -r requirements/prototype.txt
streamlit run frontend/prototype/app.py --server.port 8501
```

Inside Minikube, the app reaches FastAPI at the cluster Service DNS name, not
`localhost`. The Streamlit Service is exposed through an ingress or tunnel; see
[`infra/README.md`](../../infra/README.md) and ADR-0006.
