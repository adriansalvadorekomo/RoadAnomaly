# `frontend/prototype/` — Streamlit interactive demo

Owner: **M6**. **Status: `missing`** — this directory contains a README and the
dependency file.

One Streamlit page that lets a reviewer upload a road frame or pick a bundled
evaluation frame, choose a model, set an optional threshold and see the result.
It calls the FastAPI service; it does not load a model.

## Contract

- `POST /predict` with `multipart/form-data`: `file`, `model` (`A`/`B`/`C`),
  optional `threshold`.
- Response fields used by the UI: `model`, `model_digest`, `threshold`,
  `score_map_png_b64`, `mask_png_b64`, `overlay_png_b64`, `pixel_stats` and
  `timing_ms`. Validate the fields before rendering them.
- `pixel_stats` (`anomaly_pixels`, `anomaly_ratio`, `mean_score`, `max_score`)
  are display statistics, **not** IoU/Dice/AUPRC. The upload has no ground truth.
- The three images are raw base64 PNGs. Decode only after checking the field is a
  string; never `eval` or inject the payload into HTML.
- API base URL: `API_BASE_URL`, default `http://localhost:8000` locally and the
  FastAPI Service DNS name inside Minikube.
- If the API is unreachable, show the error and the endpoint it tried. **Never**
  render a placeholder mask as if it were a prediction.
- Bundled samples are RoadAnomaly evaluation frames. The page repeats the
  evaluation-only caveat (ADR-0001) and links to `data/credits.txt`.

The full field table lives in
[`docs/architecture/README.md`](../../docs/architecture/README.md#frontendbackend-boundary)
and [`backend/README.md`](../../backend/README.md).

## Controls

| Control | Behaviour |
|---|---|
| Image | Upload a file or pick a bundled frame |
| Model | Select A, B or C; the API owns the model registry and the selected alias |
| Threshold | Slider; changing it re-renders the mask by thresholding the cached `score_map_png_b64` locally, otherwise re-calls the API. Show the threshold that produced the displayed mask |
| Compare | Optional tab that sends the same frame through all three models and shows score maps, masks and pixel statistics side by side |
| XAI | Only after [ADR-0009](../../docs/adr/0009-xai-evaluation-gate.md) has a chosen method and explanation artifacts exist; otherwise the tab is absent, not a placeholder |

The model selector is a comparison control, not a promotion control. Choosing B
does not change `selected.json`.

## XAI panel (blocked, G1)

The method is undecided. When it lands, the panel must show the explanation
artifact linked to the `model_digest` and the experiment record, plus a short
interpretation. It must not invent a heatmap from the score map and call it
Grad-CAM. Until then, V1.8 stays `blocked` and the panel does not render.

## Run

```bash
pip install -r requirements/prototype.txt
streamlit run frontend/prototype/app.py --server.port 8501
```

Inside Minikube, the app reaches FastAPI at the cluster Service DNS name, not
`localhost`. The Streamlit Service is exposed through an ingress or tunnel; see
[`infra/README.md`](../../infra/README.md) and ADR-0006.
