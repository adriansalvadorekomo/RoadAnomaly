"""The API contract, on a small synthetic model saved in the shared format."""
import base64
import io

import numpy as np
import pytest
from PIL import Image

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from deployment import service  # noqa: E402
from deployment.api.main import app  # noqa: E402


@pytest.fixture
def client(segmentation_dir, monkeypatch):
    monkeypatch.setattr(service.dp, "MODELS_DIR", segmentation_dir.parent)
    service.get_predictor.cache_clear()
    return TestClient(app)


def _png(width=80, height=50):
    buffer = io.BytesIO()
    Image.fromarray(np.random.default_rng(0).integers(0, 255, (height, width, 3), dtype=np.uint8)).save(buffer, "PNG")
    return buffer.getvalue()


def test_health_and_models(client):
    assert client.get("/health").json() == {"status": "ok", "models": ["seg"]}
    info = client.get("/models").json()["seg"]
    assert info["model_type"] == "segmentation" and "model_file" not in info


def test_predict_any_image_size(client):
    response = client.post("/predict?model=seg", files={"file": ("road.png", _png(), "image/png")})
    assert response.status_code == 200
    body = response.json()
    mask = np.asarray(Image.open(io.BytesIO(base64.b64decode(body["mask_png"]))))
    assert mask.shape == (32, 64) and set(np.unique(mask)) <= {0, 255}
    assert {"anomaly_percent", "blobs", "latency_ms"} <= set(body["stats"]) and "overlay_png" in body


def test_explain(client):
    response = client.post("/explain?model=seg", files={"file": ("road.png", _png(), "image/png")})
    assert response.status_code == 200 and response.json()["heatmap_png"]


def test_bad_inputs_are_rejected_clearly(client):
    assert client.post("/predict", files={"file": ("x.txt", b"not an image", "text/plain")}).status_code == 422
    assert client.post("/predict", files={"file": ("e.png", b"", "image/png")}).status_code == 422
    assert client.post("/predict?model=nope", files={"file": ("r.png", _png(), "image/png")}).status_code == 404
