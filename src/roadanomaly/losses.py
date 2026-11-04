"""Segmentation losses for the supervised models (Binôme C), written for Keras models that output
anomaly probabilities (float32 sigmoid) of shape (N, H, W, 1).

About 10 % of the pixels are anomalous (notebook 2, section 5), so plain binary cross-entropy is
dominated by the background:
- Dice loss (overlap of the whole mask) counterbalances the imbalance (Hejer, Walid's U-Net);
- focal loss down-weights the easy background pixels (Lin et al., 2017);
- Tversky loss weights false negatives more than false positives (beta > alpha) to raise recall;
  its focal form raises it to the power gamma (Abraham & Khan, 2019) (Walid's improved U-Net).
"""
import keras
from keras import ops

EPS = 1.0   # smoothing of the Dice / Tversky ratios (1 pixel), as in Binôme C's original code


def _flat(y_true, y_pred):
    """Per-image flattened float32 tensors, probabilities clipped away from 0 and 1."""
    y_true = ops.reshape(ops.cast(y_true, "float32"), (ops.shape(y_true)[0], -1))
    y_pred = ops.reshape(ops.cast(y_pred, "float32"), (ops.shape(y_pred)[0], -1))
    return y_true, ops.clip(y_pred, keras.backend.epsilon(), 1 - keras.backend.epsilon())


def dice_loss(y_true, y_pred):
    """1 - soft Dice per image, averaged over the batch."""
    t, p = _flat(y_true, y_pred)
    dice = (2 * ops.sum(t * p, axis=1) + EPS) / (ops.sum(t, axis=1) + ops.sum(p, axis=1) + EPS)
    return 1 - ops.mean(dice)


def bce_dice_loss(y_true, y_pred):
    """Binary cross-entropy + Dice loss."""
    t, p = _flat(y_true, y_pred)
    return ops.mean(keras.losses.binary_crossentropy(t[..., None], p[..., None])) + dice_loss(y_true, y_pred)


def focal_loss(y_true, y_pred, gamma=2.0):
    """Mean focal loss: cross-entropy scaled by (1 - p_t) ** gamma."""
    t, p = _flat(y_true, y_pred)
    p_t = t * p + (1 - t) * (1 - p)
    return ops.mean(-((1 - p_t) ** gamma) * ops.log(p_t))


def focal_tversky_loss(y_true, y_pred, alpha=0.3, beta=0.7, gamma=0.75):
    """(1 - Tversky index) ** gamma per image, averaged; beta > alpha penalises missed pixels more."""
    t, p = _flat(y_true, y_pred)
    tp = ops.sum(t * p, axis=1)
    fp = ops.sum((1 - t) * p, axis=1)
    fn = ops.sum(t * (1 - p), axis=1)
    tversky = (tp + EPS) / (tp + alpha * fp + beta * fn + EPS)
    return ops.mean((1 - tversky) ** gamma)


def focal_plus_tversky_loss(y_true, y_pred):
    """Walid's loss for the pretrained U-Net: focal + focal-Tversky."""
    return focal_loss(y_true, y_pred) + focal_tversky_loss(y_true, y_pred)
