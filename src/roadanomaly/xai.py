"""Explainability tools shared by notebook 6 (CRISP-DM Evaluation, XAI part).

- grad_cam: Grad-CAM of a fixed scalar target with respect to one layer's activations
  (Selvaraju et al., 2017). For segmentation, the target is the mean anomaly logit inside a
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


def grad_cam(model, x, layer_name, target_fn, output_name=None, size=None):
    """Positive Grad-CAM map of target_fn(x, output) for one input x (without batch axis).

    target_fn(inputs, outputs) must return a scalar tensor. The map is resized to `size`
    (default: the input's height and width) and divided by its maximum; returns
    (map in [0, 1], raw maximum). A raw maximum of 0 means no positive evidence.
    """
    inputs = tf.convert_to_tensor(np.asarray(x, dtype=np.float32)[None])
    with tf.GradientTape() as tape:
        activations, outputs = _inspector(model, layer_name, output_name)(inputs, training=False)
        target = target_fn(inputs, outputs)
    gradients = tape.gradient(target, activations)
    if gradients is None:
        raise RuntimeError(f"no gradient reaches layer {layer_name}")
    weights = tf.reduce_mean(gradients, axis=(1, 2), keepdims=True)   # one weight per channel
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


def deletion_insertion(score_fn, image, heatmap, block=32, fractions=np.linspace(0, 1, 6),
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
