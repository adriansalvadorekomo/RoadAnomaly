"""Entraîne l'autoencodeur du binôme B et calibre ses scores sur validation."""

from __future__ import annotations

import argparse
import json
import os
import platform
from pathlib import Path

import keras
import numpy as np
import tensorflow as tf
from sklearn.metrics import average_precision_score

from roadanomaly import data_pipeline as dp, metrics
from roadanomaly.autoencoder import (
    anomaly_scores,
    build_autoencoder,
    compile_reconstruction_loss,
    extract_normal_patches,
    reconstruction_error_maps,
)
from roadanomaly.gpu import setup_gpu

IMG_SIZE = (352, 640)
PATCH_SIZE = 64
PATCH_STRIDE = 32
MASK_MARGIN = 4
ENCODER_FILTERS = (32, 64, 128, 256)
CODE_CHANNELS = 2
LEARNING_RATE = 1e-3
BATCH_SIZE = 64
PATIENCE = 8
MIN_OBJECT_PX = 4
SIGMA_CANDIDATES = (0, 2, 4, 8, 16)
THRESHOLD_QUANTILES = np.linspace(0.50, 0.995, 60)


def parse_args() -> argparse.Namespace:
    """Construit les options de la ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=dp.DATA_DIR)
    parser.add_argument("--manifest", type=Path, default=dp.MANIFEST_PATH)
    parser.add_argument("--model-output", type=Path, default=dp.REPO_ROOT / "models" / "B_autoencoder.keras")
    parser.add_argument("--config-output", type=Path, default=dp.REPO_ROOT / "models" / "B_best_config.json")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--loss", choices=("mse", "mae", "ssim"), default="mse")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    keras.utils.set_random_seed(args.seed)
    tf.config.experimental.enable_op_determinism()
    device_name = setup_gpu()

    train_frames, x_train, y_train = dp.load_split(
        "train", IMG_SIZE, manifest_path=args.manifest, data_dir=args.data_dir
    )
    val_frames, x_val, y_val = dp.load_split(
        "val", IMG_SIZE, manifest_path=args.manifest, data_dir=args.data_dir
    )
    p_train = extract_normal_patches(x_train, y_train, PATCH_SIZE, PATCH_STRIDE, MASK_MARGIN)
    p_val = extract_normal_patches(x_val, y_val, PATCH_SIZE, PATCH_STRIDE, MASK_MARGIN)

    def augment_patch(patch: tf.Tensor) -> tuple[tf.Tensor, tf.Tensor]:
        patch = tf.image.random_flip_left_right(patch)
        return patch, patch

    train_dataset = (
        tf.data.Dataset.from_tensor_slices(p_train)
        .shuffle(len(p_train), seed=args.seed)
        .map(augment_patch, num_parallel_calls=tf.data.AUTOTUNE)
        .batch(args.batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )
    val_dataset = tf.data.Dataset.from_tensor_slices((p_val, p_val)).batch(args.batch_size)

    model = build_autoencoder(ENCODER_FILTERS, CODE_CHANNELS)
    compile_reconstruction_loss(model, args.loss, LEARNING_RATE)
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=PATIENCE, restore_best_weights=True
        )
    ]
    history = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=args.epochs,
        callbacks=callbacks,
        verbose=2,
    )
    model.save(args.model_output)

    _, raw_errors = reconstruction_error_maps(model, x_val)
    ground_truth = y_val[..., 0].astype(bool)
    sigma_rows = []
    for sigma in SIGMA_CANDIDATES:
        scores = anomaly_scores(raw_errors, sigma)
        auprc = average_precision_score(ground_truth.ravel(), scores.ravel())
        sigma_rows.append((float(auprc), sigma, scores))
    _, selected_sigma, val_scores = max(sigma_rows, key=lambda row: row[0])

    candidates = np.quantile(val_scores, THRESHOLD_QUANTILES)
    f1_by_threshold = []
    for threshold in candidates:
        masks = np.stack(
            [
                metrics.remove_small_components(score >= threshold, MIN_OBJECT_PX)
                for score in val_scores
            ]
        )
        f1_by_threshold.append(
            metrics.evaluate_masks(list(ground_truth), list(masks))["per_image_mean"]["f1"]
        )
    selected_threshold = float(candidates[int(np.argmax(f1_by_threshold))])
    val_masks = np.stack(
        [
            metrics.remove_small_components(score >= selected_threshold, MIN_OBJECT_PX)
            for score in val_scores
        ]
    )
    val_pixel = metrics.evaluate_masks(list(ground_truth), list(val_masks))
    val_per_image = []
    for frame, truth, score, pixel_scores in zip(
        val_frames, ground_truth, val_scores, val_pixel["per_image"]
    ):
        val_per_image.append(
            {
                "frame": frame,
                "auprc": float(average_precision_score(truth.ravel(), score.ravel())),
                **pixel_scores,
            }
        )
    model_path_relative = Path(
        os.path.relpath(
            Path(args.model_output).resolve(),
            start=Path(args.config_output).resolve().parent,
        )
    )
    config = {
        "artifact_version": 1,
        "model_path": str(model_path_relative),
        "preprocessing": {
            "image_size_height_width": list(IMG_SIZE),
            "image_channels": "RGB",
            "image_dtype_range": "float32 [0, 1]",
            "image_resize": "bilinear",
            "mask_resize": "nearest",
        },
        "architecture": {
            "name": "convolutional_autoencoder",
            "encoder_filters": list(ENCODER_FILTERS),
            "code_channels": CODE_CHANNELS,
            "code_activation": "linear",
            "output_activation": "sigmoid",
        },
        "training": {
            "seed": args.seed,
            "loss": args.loss,
            "optimizer": "Adam",
            "learning_rate": LEARNING_RATE,
            "batch_size": args.batch_size,
            "maximum_epochs": args.epochs,
            "epochs_ran": len(history.history["loss"]),
            "best_epoch": int(np.argmin(history.history["val_loss"])) + 1,
            "best_validation_loss": float(min(history.history["val_loss"])),
            "patch_size": PATCH_SIZE,
            "patch_stride": PATCH_STRIDE,
            "mask_margin": MASK_MARGIN,
            "train_normal_patches": int(len(p_train)),
            "validation_normal_patches": int(len(p_val)),
        },
        "postprocessing": {
            "pixel_error": "mean squared RGB reconstruction error",
            "sigma": int(selected_sigma),
            "per_image_z_score": True,
            "threshold": selected_threshold,
            "threshold_objective": "validation per-image mean F1",
            "min_component_px": MIN_OBJECT_PX,
        },
        "validation": {
            "frames": list(val_frames),
            "auprc": float(average_precision_score(ground_truth.ravel(), val_scores.ravel())),
            "per_image_mean": val_pixel["per_image_mean"],
            "per_image": val_per_image,
        },
        "environment": {
            "python": platform.python_version(),
            "tensorflow": tf.__version__,
            "keras": keras.__version__,
            "device": device_name,
            "deterministic_ops": True,
        },
    }
    args.config_output.parent.mkdir(parents=True, exist_ok=True)
    args.config_output.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"Modèle sauvegardé : {args.model_output}")
    print(f"Configuration sauvegardée : {args.config_output}")
    print(
        f"Validation: AuPRC={config['validation']['auprc']:.6f}, "
        f"F1 moyen={val_pixel['per_image_mean']['f1']:.6f}, "
        f"sigma={selected_sigma}, seuil={selected_threshold:.6f}"
    )


if __name__ == "__main__":
    main()
