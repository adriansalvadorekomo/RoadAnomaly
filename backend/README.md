# `backend/` — inference API

> **Status: `missing`.** This is the target contract; only a package stub exists.
> There is no FastAPI app, model artifact or container yet.

Owner: **M5**. Stack: FastAPI + TensorFlow runtime (CPU), same language as
`dl/` so a model bug never requires switching ecosystems.

```
backend/
└── app/
    ├── main.py        FastAPI app, lifespan model loading, no wildcard CORS
    ├── routes.py      /health · /models · /predict
    ├── schemas.py     pydantic request/response models (the API contract)
    ├── inference.py   artifact loading + post-processing to mask/heatmap
    └── registry.py    maps model id -> path/digest in the mounted bundle
```

## Contract the prototype depends on

The full field table and example live in
[`docs/architecture/README.md`](../docs/architecture/README.md#planned-api-and-frontend-boundary).
This page repeats the parts the backend must not change silently.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | liveness; returns `status`, loaded `models` and `artifact_digest` |
| `GET` | `/models` | array of `{id, input_size, default_threshold, digest}` |
| `POST` | `/predict` | image in; score map, mask, overlay, pixel statistics and timing out |

`POST /predict` is `multipart/form-data`:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `file` | image file | yes | RGB road frame |
| `model` | `"autoencoder" \| "unet" \| "deeplabv3plus"` | yes | Candidate id present in the mounted bundle |
| `threshold` | float in `[0, 1]` | no | Overrides the manifest default; the response echoes it |

The response is JSON:

```json
{
  "model": "autoencoder",
  "model_digest": "sha256:6f1c...",
  "threshold": 0.62,
  "input": {"width": 1280, "height": 720},
  "score_map_png_b64": "iVBORw0KGgo...",
  "mask_png_b64": "iVBORw0KGgo...",
  "overlay_png_b64": "iVBORw0KGgo...",
  "pixel_stats": {
    "anomaly_pixels": 12345,
    "anomaly_ratio": 0.0134,
    "mean_score": 0.18,
    "max_score": 0.97
  },
  "timing_ms": {"preprocess": 12, "inference": 341, "postprocess": 19, "total": 372}
}
```

The three PNG fields are raw base64 (no `data:` prefix). `score_map_png_b64` is
an 8-bit grayscale score map so the prototype can re-threshold locally;
`mask_png_b64` is the binary mask at the echoed threshold; `overlay_png_b64` is
for display.

**`pixel_stats` are not evaluation metrics.** An upload has no ground truth, so
the API must not compute or return IoU, Dice, AUROC or AUPRO. Those live only in
`dl/evaluation/` and `docs/experiments/`.

Error responses use a JSON body `{"detail": "..."}`:

| Status | When |
|---|---|
| `400` | unreadable image, unknown model id, threshold outside `[0, 1]` |
| `503` | the registry bundle or requested SavedModel is unavailable |
| `500` | an unexpected inference failure; do not return a fake mask |

`GET /health` returns
`{"status": "ok", "models": ["autoencoder", "unet", "deeplabv3plus"], "selected": "autoencoder", "artifact_digest": "sha256:..."}`.
`GET /models` reads the same manifests and never guesses a default threshold.

## Serving notes

- Artifacts are **exported** by `dl/inference/`, not trained here. The API loads
  a TensorFlow SavedModel and its manifest from the read-only registry mount; it
  does not import training code or a second model ecosystem.
- The selected model is loaded in the lifespan hook. All three candidates are
  present in the bundle for the comparison UI; each is loaded once and cached.
  A request never triggers training, a download or a reload.
- Startup fails if the bundle or `selected.json` is missing. Returning a
  different model under the same name is worse than refusing to start.
- Threshold is a request parameter, not a constant, because the operating point
  is an explicit experimental choice. The default comes from the selected
  model's manifest and normal-road validation, never from RoadAnomaly.
- Preprocessing must match the training graph. The manifest records the input
  spec and preprocessing version; an integration test loads the exported artifact
  and checks output shape and dtype before the API is considered deployable.
- FastAPI is cluster-internal. The Streamlit server calls it; the browser does
  not. A wildcard CORS policy is therefore unnecessary and should not be added
  "just in case".
