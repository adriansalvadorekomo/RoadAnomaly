"""RoadAnomaly inference API (FastAPI).

Endpoints (FR, section 6):
- GET  /health   liveness + the models that are loaded
- GET  /models   description of every model (binôme, type, validation scores, post-processing)
- POST /predict  image file -> anomaly mask (+ optional overlay and score map as base64 PNG) and statistics
- POST /explain  image file -> Grad-CAM heatmap of the predicted region (base64 PNG)

Run: `mise run api` (or `uvicorn deployment.api.main:app --port 8000`); interactive docs at /docs.
"""
import base64

from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from deployment import service

app = FastAPI(title="RoadAnomaly API", version="1.0.0",
              description="Pixel-level detection of unexpected obstacles on the road (ESPRIT, CRISP-DM project).")


def _b64_png(array):
    return base64.b64encode(service.png_bytes(array)).decode("ascii")


def _model_or_404(model):
    names = service.model_names()
    if not names:
        raise HTTPException(503, "no trained model in models/: run the modeling notebooks first")
    model = model or names[-1]
    if model not in names:
        raise HTTPException(404, f"unknown model {model!r}; available: {names}")
    return model


async def _read_image(file: UploadFile):
    try:
        return service.decode_image(await file.read())
    except service.InputError as error:
        raise HTTPException(422, str(error)) from error


@app.get("/health")
def health():
    return {"status": "ok", "models": service.model_names()}


@app.get("/models")
def models():
    return {name: service.model_info(name) for name in service.model_names()}


@app.post("/predict")
async def predict(file: UploadFile = File(..., description="RGB image (JPEG, PNG or WebP)"),
                  model: str | None = Query(None, description="model name from /models (default: last)"),
                  include_images: bool = Query(True, description="return overlay and score map as base64 PNG")):
    model = _model_or_404(model)
    result = service.analyse(model, await _read_image(file))
    response = {"stats": result["stats"], "mask_png": _b64_png(result["mask"].astype("uint8") * 255)}
    if include_images:
        response["overlay_png"] = _b64_png(service.overlay(result["image"], result["mask"]))
        response["score_map_png"] = _b64_png(service.heatmap_rgb(result["scores"]))
    return response


@app.post("/explain")
async def explain(file: UploadFile = File(...), model: str | None = Query(None)):
    model = _model_or_404(model)
    result, cam = service.explain(model, await _read_image(file))
    return {"stats": result["stats"], "target": "Grad-CAM of the predicted region",
            "note": "descriptive explanation, not a causal proof; an error map is a detection map",
            "heatmap_png": _b64_png(service.blend(result["image"], service.heatmap_rgb(cam, "jet")))}
