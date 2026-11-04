"""Explainability tools shared by notebook 6, the API and the demo (CRISP-DM Evaluation, XAI part).

Every model is explained by a pair (see `explain`):
- WHERE, spatial localisation: Grad-CAM / Grad-CAM++ of a fixed scalar target;
- WHAT, feature attribution: exact Shapley values (SHAP) over five interpretable image
  factors (colour, fine texture, brightness and contrast, the obstacle itself, the scene).

- grad_cam: Grad-CAM (Selvaraju et al., 2017) or Grad-CAM++ (Chattopadhay et al., 2018) of a fixed
  scalar target with respect to one layer's activations. For segmentation, the target is the mean anomaly logit inside a
  fixed region (Seg-Grad-CAM, Vinogradova et al., 2020; Binôme A). For an autoencoder, the
  target is the mean reconstruction error inside a fixed region (Binôme B).
- deletion_insertion: a faithfulness check (Petsiuk et al., 2018). Image blocks are ranked
  by the attribution map; deleting the top blocks should lower the target faster than a
  random order, and inserting them back should raise it faster.

An error map is a detection map (where the reconstruction fails), not an attribution: it
says where, not why. Grad-CAM maps are descriptive and never used to select a model.
"""
import keras
import numpy as np
import tensorflow as tf
from scipy import ndimage

_inspectors = {}   # (model id, layer, output) -> keras.Model, built once


def _inspector(model, layer_name, output_name):
    key = (id(model), layer_name, output_name)
    if key not in _inspectors:
        output = model.output if output_name is None else model.get_layer(output_name).output
        _inspectors[key] = keras.Model(model.inputs, [model.get_layer(layer_name).output, output])
    return _inspectors[key]


def grad_cam(model, x, layer_name, target_fn, output_name=None, size=None, method="gradcam"):
    """Positive Grad-CAM ("gradcam") or Grad-CAM++ ("gradcam++") map of target_fn(x, output) for one input x.

    target_fn(inputs, outputs) must return a scalar tensor. Grad-CAM weights each channel by its mean
    gradient; Grad-CAM++ by a pixel-wise weighted mean of the positive gradients, which localises
    several instances and whole objects better. The map is resized to `size` (default: the input's
    height and width) and divided by its maximum; returns (map in [0, 1], raw maximum).
    A raw maximum of 0 means no positive evidence.
    """
    if method not in ("gradcam", "gradcam++"):
        raise ValueError(f"method must be 'gradcam' or 'gradcam++', got {method!r}")
    inputs = tf.convert_to_tensor(np.asarray(x, dtype=np.float32)[None])
    with tf.GradientTape() as tape:
        activations, outputs = _inspector(model, layer_name, output_name)(inputs, training=False)
        target = target_fn(inputs, outputs)
    gradients = tape.gradient(target, activations)
    if gradients is None:
        raise RuntimeError(f"no gradient reaches layer {layer_name}")
    if method == "gradcam":
        weights = tf.reduce_mean(gradients, axis=(1, 2), keepdims=True)   # one weight per channel
    else:   # Grad-CAM++: alpha = g^2 / (2 g^2 + sum(A) g^3), weights = sum(alpha * relu(g))
        g2, g3 = tf.square(gradients), tf.pow(gradients, 3)
        denominator = 2.0 * g2 + tf.reduce_sum(activations, axis=(1, 2), keepdims=True) * g3
        alpha = tf.math.divide_no_nan(g2, tf.where(tf.abs(denominator) > 1e-12, denominator, tf.ones_like(denominator)))
        weights = tf.reduce_sum(alpha * tf.nn.relu(gradients), axis=(1, 2), keepdims=True)
    cam = tf.nn.relu(tf.reduce_sum(weights * activations, axis=-1))[0]
    size = size or inputs.shape[1:3]
    cam = tf.image.resize(cam[..., None], size, method="bilinear")[..., 0].numpy()
    raw_max = float(cam.max())
    return (cam / raw_max if raw_max > 0 else cam).astype(np.float32), raw_max


def region_mean(values, region):
    """Mean of a (1, H, W) tensor inside a fixed binary (H, W) region."""
    region = tf.convert_to_tensor(np.asarray(region, dtype=np.float32))
    return tf.reduce_sum(values[0] * region) / tf.reduce_sum(region)


def logit_target(region):
    """Seg-Grad-CAM target: mean anomaly logit inside `region` (logits avoid sigmoid saturation)."""
    return lambda inputs, logits: region_mean(logits[..., 0], region)


def reconstruction_target(region):
    """Autoencoder target: mean squared reconstruction error (over channels) inside `region`."""
    return lambda inputs, reconstruction: region_mean(
        tf.reduce_mean(tf.square(inputs - reconstruction), axis=-1), region)


def block_order(heatmap, block):
    """Indices of the (block x block) image blocks, highest mean attribution first."""
    rows, cols = heatmap.shape[0] // block, heatmap.shape[1] // block
    means = heatmap[:rows * block, :cols * block].reshape(rows, block, cols, block).mean(axis=(1, 3))
    return np.argsort(-means.ravel(), kind="stable"), (rows, cols)


DELETION_FRACTIONS = np.linspace(0, 1, 6)   # share of the blocks deleted / inserted at each step


def deletion_insertion(score_fn, image, heatmap, block=32, fractions=DELETION_FRACTIONS,
                       blur_sigma=8, random_seeds=(1337, 1338, 1339)):
    """Deletion and insertion curves of score_fn for the attribution order and random orders.

    score_fn(batch (N, H, W, 3)) -> (N,) scores of the fixed target. The baseline is a
    Gaussian blur of the image (spatial sigma `blur_sigma`): deleted blocks are replaced by
    the blurred image, inserted blocks are restored on top of it.
    Returns {"attribution": {"deletion": [...], "insertion": [...]}, "random_i": {...}}.
    """
    image = np.asarray(image, dtype=np.float32)
    baseline = np.clip(ndimage.gaussian_filter(image, sigma=(blur_sigma, blur_sigma, 0)), 0, 1).astype(np.float32)
    order, (rows, cols) = block_order(heatmap, block)
    n_blocks = rows * cols

    def curves(block_order_):
        deletion, insertion = [], []
        for fraction in fractions:
            chosen = np.zeros(n_blocks, dtype=bool)
            chosen[block_order_[:int(round(fraction * n_blocks))]] = True
            chosen = np.kron(chosen.reshape(rows, cols), np.ones((block, block), dtype=bool))
            selected = np.zeros(image.shape[:2], dtype=bool)
            selected[:chosen.shape[0], :chosen.shape[1]] = chosen
            selected = selected[..., None]
            scores = score_fn(np.stack([np.where(selected, baseline, image), np.where(selected, image, baseline)]))
            deletion.append(float(scores[0]))
            insertion.append(float(scores[1]))
        return {"deletion": deletion, "insertion": insertion}

    results = {"attribution": curves(order)}
    for i, seed in enumerate(random_seeds, start=1):
        results[f"random_{i}"] = curves(np.random.default_rng(seed).permutation(n_blocks))
    for result in results.values():
        result["deletion_auc"] = float(np.trapezoid(result["deletion"], fractions))
        result["insertion_auc"] = float(np.trapezoid(result["insertion"], fractions))
    return results


def default_segmentation_layer(model, logits_layer="anomaly_logits"):
    """Last layer before `logits_layer` with a spatial, multi-channel output (e.g. DeepLabV3+ 'decoder_2').

    Lets the same Seg-Grad-CAM code explain any segmentation model of the shared format (A, C)
    without knowing its layer names; a config.json may still name the layer explicitly.
    """
    names = [layer.name for layer in model.layers]
    for layer in reversed(model.layers[:names.index(logits_layer)]):
        shape = getattr(layer, "output", None) is not None and layer.output.shape
        if shape and len(shape) == 4 and shape[-1] and shape[-1] > 1:
            return layer.name
    raise ValueError(f"no multi-channel spatial layer before {logits_layer!r}")


# ---------------------------------------------------------------------------------------------------
# WHAT: exact Shapley values over interpretable image factors
# ---------------------------------------------------------------------------------------------------
# Each factor is a property of the image that can be removed by a defined transform. A coalition S is
# the set of factors kept; every factor outside S is removed (in the fixed order below), and the model's
# scalar target on the fixed region is recomputed. With 5 factors, the 2^5 = 32 coalitions are all
# evaluated, so the Shapley values are exact and add up to v(all kept) - v(all removed) (efficiency).

FACTORS = ("colour", "texture", "contrast", "object", "context")
FACTOR_LABELS = {
    "colour": "Colour", "texture": "Fine texture", "contrast": "Brightness and contrast",
    "object": "The obstacle itself", "context": "The surrounding scene",
}
FACTOR_REMOVAL = {
    "colour": "replaced by its grey luminance",
    "texture": "fine detail blurred away (Gaussian, sigma 2 px)",
    "contrast": "contrast flattened to 35 % around the image mean",
    "object": "the region (dilated 6 px) filled with a heavy blur of its surroundings",
    "context": "everything outside the region replaced by a heavy blur",
}
REGION_MARGIN = 6   # px around the region that belong to the obstacle when it is removed
HEAVY_BLUR = 12     # sigma (px) of the blur that stands in for removed content


def _blur(image, sigma):
    return ndimage.gaussian_filter(image, sigma=(sigma, sigma, 0))


def remove_factors(image, region, removed):
    """The image with every factor in `removed` taken out, in the fixed order of FACTORS."""
    out = np.asarray(image, dtype=np.float32).copy()
    zone = ndimage.binary_dilation(np.asarray(region, bool), iterations=REGION_MARGIN)
    if "colour" in removed:
        grey = out @ np.array([0.299, 0.587, 0.114], np.float32)
        out = np.repeat(grey[..., None], 3, axis=-1)
    if "texture" in removed:
        out = _blur(out, 2)
    if "contrast" in removed:
        mean = out.mean(axis=(0, 1), keepdims=True)
        out = mean + 0.35 * (out - mean)
    if "object" in removed:
        out = np.where(zone[..., None], _blur(out, HEAVY_BLUR), out)
    if "context" in removed:
        out = np.where(zone[..., None], out, _blur(out, HEAVY_BLUR))
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def factor_shapley(score_fn, image, region, factors=FACTORS):
    """Exact Shapley values of the factors for score_fn on one image and a fixed region.

    score_fn(batch (N, H, W, 3)) -> (N,) target values. Returns a dict with the value of each
    factor ("phi"), v(all kept) ("full"), v(all removed) ("base") and the efficiency gap
    |sum(phi) - (full - base)|, which is 0 up to float error.
    """
    from itertools import combinations
    from math import factorial

    k = len(factors)
    coalitions = [frozenset(c) for r in range(k + 1) for c in combinations(factors, r)]
    batch = np.stack([remove_factors(image, region, set(factors) - set(c)) for c in coalitions])
    value = dict(zip(coalitions, np.asarray(score_fn(batch), dtype=np.float64), strict=True))
    phi = {}
    for f in factors:
        total = 0.0
        for coalition in coalitions:
            if f in coalition:
                continue
            weight = factorial(len(coalition)) * factorial(k - len(coalition) - 1) / factorial(k)
            total += weight * (value[coalition | {f}] - value[coalition])
        phi[f] = float(total)
    full, base = float(value[frozenset(factors)]), float(value[frozenset()])
    return {"phi": phi, "full": full, "base": base, "efficiency_gap": abs(sum(phi.values()) - (full - base)),
            "evaluations": len(coalitions)}


# ---------------------------------------------------------------------------------------------------
# One explanation per model: the region, WHERE (Grad-CAM family) and WHAT (factor SHAP)
# ---------------------------------------------------------------------------------------------------

def _cells(region, shape):
    """Pixel region -> region of feature cells (a cell counts when at least half of it is in the region)."""
    resized = tf.image.resize(np.asarray(region, np.float32)[..., None], shape, method="area").numpy()[..., 0]
    return resized >= 0.5 if (resized >= 0.5).any() else resized > 0


def target_score_fn(predictor, region):
    """batch of images in [0, 1] -> the model's scalar target on the fixed region, per image.

    Segmentation: mean anomaly logit (before the sigmoid, so it does not saturate). Autoencoders: mean
    raw reconstruction error (per pixel for the pixel AE, per 16-px cell for the feature AE).
    """
    if predictor.model_type == "segmentation":
        logits = _inspector(predictor.model, "anomaly_logits", None)
        return lambda batch: logits.predict(batch, batch_size=8, verbose=0)[0][..., 0][:, region].mean(axis=1)
    if predictor.model_type == "pixel_autoencoder":
        return lambda batch: predictor.raw_maps(batch)[:, region].mean(axis=1)
    def feature_score(batch):
        raw = predictor.raw_maps(batch)
        return raw[:, _cells(region, raw.shape[1:3])].mean(axis=1)
    return feature_score


def explanation_region(predictor, image):
    """The fixed region every explanation targets: the model's predicted mask, or its top 1 % scores."""
    out = predictor.predict(image)
    mask, scores = out["masks"][0].astype(bool), out["scores"][0]
    return (mask if mask.any() else scores >= np.quantile(scores, 0.99)), out


def where_map(predictor, image, region, method="gradcam++"):
    """WHERE: the Grad-CAM family map of the model's target on the region, at the image size."""
    image = np.asarray(image, np.float32)
    if predictor.model_type == "segmentation":
        layer = predictor.config.get("xai", {}).get("layer") or default_segmentation_layer(predictor.model)
        return grad_cam(
            predictor.model, image, layer, logit_target(region), output_name="anomaly_logits", method=method
        )
    if predictor.model_type == "pixel_autoencoder":
        return grad_cam(predictor.model, image, "code", reconstruction_target(region), method=method)
    features = predictor.features(image[None])[0]
    return grad_cam(predictor.model, features, "code", reconstruction_target(_cells(region, features.shape[:2])),
                    size=image.shape[:2], method=method)


def explain(predictor, image, method="gradcam++"):
    """The pair of explanations of one model on one image (H, W, 3) in [0, 1].

    Returns {"region", "scores", "mask", "where" (map in [0, 1]), "where_method", "what" (factor_shapley)}.
    """
    region, out = explanation_region(predictor, image)
    cam, _ = where_map(predictor, image, region, method)
    what = factor_shapley(target_score_fn(predictor, region), image, region)
    return {"region": region, "scores": out["scores"][0], "mask": out["masks"][0].astype(bool),
            "where": cam, "where_method": method, "what": what}


def describe_what(what, model_name="The model"):
    """One plain sentence about the largest Shapley contributions, for interfaces and reports."""
    ranked = sorted(what["phi"].items(), key=lambda kv: -abs(kv[1]))
    top, second = ranked[0], ranked[1]
    share = abs(top[1]) / max(sum(abs(v) for v in what["phi"].values()), 1e-12)
    direction = "raises" if top[1] > 0 else "lowers"
    return (f"{model_name} relies most on {FACTOR_LABELS[top[0]].lower()}, which {direction} its anomaly score "
            f"by {_number(abs(top[1]))} ({100 * share:.0f} % of the total attribution), then on "
            f"{FACTOR_LABELS[second[0]].lower()} ({'+' if second[1] >= 0 else '−'}{_number(abs(second[1]))}).")


def _number(x):
    """Three significant digits, without scientific notation for the usual ranges (0.0123, 2.97, 22.7)."""
    return f"{x:#.3g}".rstrip(".") if 1e-3 <= x < 1e4 else f"{x:.2e}"
