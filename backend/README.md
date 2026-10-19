# `backend/` — inference API

Owner: **M5**. Stack: FastAPI + TensorFlow runtime (CPU), same language as
`dl/` so a model bug never requires switching ecosystems.

```
backend/
└── app/
    ├── main.py        FastAPI app, CORS, lifespan model loading
    ├── routes.py      /health · /models · /predict
    ├── schemas.py     pydantic request/response models (the API contract)
    ├── inference.py   artifact loading + post-processing to mask/heatmap
    └── registry.py    maps model name -> exported artifact path
```

## Contract the prototype depends on

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | liveness, returns loaded model names |
| `GET` | `/models` | available models and their input size |
| `POST` | `/predict` | image in, anomaly score map + mask + metrics out |

`POST /predict` accepts `multipart/form-data` (`file`, `model`, optional
`threshold`) and returns base64 PNG overlays plus timing. The OpenAPI schema at
`/docs` is the source of truth: the Streamlit prototype validates the fields it
reads, and the Astro landing page has no runtime API client.

## Serving notes

- Artifacts are **exported** by `dl/inference/`, not trained here. The API loads
  a TensorFlow SavedModel and its manifest; it does not import training code or
  a second model ecosystem.
- Threshold is a request parameter, not a constant, because ADR-0001 makes the
  operating point an explicit experimental choice.
- Model loading happens once in the lifespan hook, never per request.
- Preprocessing must match the training graph. The SavedModel exposes the
  serving signature and its input specification in the manifest; a contract
  test loads the exported artifact and checks the output shape and dtype.
