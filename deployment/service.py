"""Inference service shared by the FastAPI server and the Streamlit demo.

It wraps roadanomaly.inference.Predictor (the same code path as notebook 5) and adds what an
interface needs: decoding of uploaded files, coloured overlays, per-image statistics, Grad-CAM
on demand and timing. Models are loaded once and cached.
"""
import io
import os
import time
from functools import lru_cache

import matplotlib
import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
from scipy import ndimage

from roadanomaly import data_pipeline as dp, xai
from roadanomaly.gpu import setup_gpu
from roadanomaly.inference import Predictor, available_models, prepare_image
from roadanomaly.metrics import EIGHT_CONNECTED

# Cap the GPU memory of each serving process (API and demo can then share one card with a notebook).
# ROADANOMALY_GPU_MEMORY_MB=0 switches to on-demand growth without a cap.
GPU_MEMORY_MB = int(os.environ.get("ROADANOMALY_GPU_MEMORY_MB", "2048"))
setup_gpu(memory_limit_mb=GPU_MEMORY_MB or None)

MAX_UPLOAD_BYTES = 15 * 1024 * 1024        # 15 MB
MAX_SIDE_PX = 8000


class InputError(ValueError):
    """The uploaded file is not a usable image (message is safe to show to the user)."""


def model_names():
    """Names of the models available in models/ (shared format)."""
    return available_models(dp.MODELS_DIR)


@lru_cache(maxsize=None)
def get_predictor(name):
    if name not in model_names():
        raise KeyError(f"unknown model {name!r}; available: {model_names()}")
    return Predictor(dp.MODELS_DIR / name)


def model_info(name):
    """Public description of a model: no file paths, only what a client needs."""
    config = get_predictor(name).config
    keys = ("name", "binome", "title", "model_type", "input", "postprocessing", "validation")
    return {key: config.get(key) for key in keys}


def decode_image(data: bytes):
    """Bytes of an uploaded file -> RGB uint8 array, with clear errors for bad input."""
    if not data:
        raise InputError("empty file")
    if len(data) > MAX_UPLOAD_BYTES:
        raise InputError(f"file larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as error:
        raise InputError("not a readable image (JPEG, PNG or WebP expected)") from error
    if max(image.size) > MAX_SIDE_PX:
        raise InputError(f"image side larger than {MAX_SIDE_PX} px")
    return np.asarray(image.convert("RGB"))


def analyse(name, image_rgb):
    """Run one model on one RGB image (any size). Returns the arrays and summary statistics."""
    predictor = get_predictor(name)
    x = prepare_image(image_rgb, predictor.image_size)
    start = time.perf_counter()
    out = predictor.predict(x)
    elapsed = 1000 * (time.perf_counter() - start)
    mask, scores = out["masks"][0].astype(bool), out["scores"][0]
    _, n_blobs = ndimage.label(mask, structure=EIGHT_CONNECTED)
    return {"image": x, "mask": mask, "scores": scores,
            "stats": {"model": name, "anomaly_percent": float(100 * mask.mean()), "blobs": int(n_blobs),
                      "max_score": float(scores.max()), "threshold": predictor.threshold,
                      "latency_ms": float(elapsed), "image_size": list(predictor.image_size)}}


def explain(name, image_rgb):
    """Grad-CAM heatmap (H, W) in [0, 1] of the predicted region (or the top 1 % scores if empty)."""
    predictor = get_predictor(name)
    result = analyse(name, image_rgb)
    region = result["mask"] if result["mask"].any() else result["scores"] >= np.quantile(result["scores"], 0.99)
    if predictor.model_type == "segmentation":
        layer = predictor.config.get("xai", {}).get("layer") or xai.default_segmentation_layer(predictor.model)
        cam, _ = xai.grad_cam(predictor.model, result["image"], layer, xai.logit_target(region),
                              output_name="anomaly_logits")
    elif predictor.model_type == "pixel_autoencoder":
        cam, _ = xai.grad_cam(predictor.model, result["image"], "code", xai.reconstruction_target(region))
    else:
        features = predictor.features(result["image"][None])[0]
        cells = tf.image.resize(region.astype("float32")[..., None], features.shape[:2], method="area").numpy()[..., 0]
        cells = cells >= 0.5 if (cells >= 0.5).any() else cells > 0
        cam, _ = xai.grad_cam(predictor.model, features, "code", xai.reconstruction_target(cells),
                              size=predictor.image_size)
    return result, cam


def overlay(image, mask, color=(255, 40, 40), alpha=0.5):
    """uint8 RGB image with the mask painted in `color` and its outline drawn."""
    base = (np.asarray(image) * 255).astype(np.uint8) if np.asarray(image).dtype != np.uint8 else np.asarray(image)
    out = base.astype(np.float32)
    out[mask] = (1 - alpha) * out[mask] + alpha * np.array(color, np.float32)
    edge = mask & ~ndimage.binary_erosion(mask, iterations=2)
    out[edge] = color
    return out.astype(np.uint8)


def heatmap_rgb(values, cmap="inferno"):
    """(H, W) array -> uint8 RGB with a matplotlib colour map (values rescaled to [0, 1])."""
    values = np.asarray(values, dtype=np.float32)
    span = values.max() - values.min()
    values = (values - values.min()) / span if span > 0 else np.zeros_like(values)
    return (matplotlib.colormaps[cmap](values)[..., :3] * 255).astype(np.uint8)


def blend(image, heat_rgb, alpha=0.45):
    base = (np.asarray(image) * 255).astype(np.float32)
    return ((1 - alpha) * base + alpha * heat_rgb.astype(np.float32)).astype(np.uint8)


def png_bytes(array):
    buffer = io.BytesIO()
    Image.fromarray(array).save(buffer, format="PNG")
    return buffer.getvalue()
