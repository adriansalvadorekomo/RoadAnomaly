# 0005. TensorFlow/Keras for training and inference

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** whole team

> **Supersedes in part:** the TorchScript/ONNX artifact and ONNX Runtime clauses
> in [ADR-0003](0003-monorepo-and-serving-stack.md) and the SegFormer option in
> [ADR-0002](0002-three-model-families.md). It does not change ADR-0001, the
> evaluation-only protocol, or the three-model-family decision.

## Context

The repository was scaffolded around PyTorch, TorchScript/ONNX export and ONNX
Runtime. No model, training loop or inference service exists yet, so there is no
code to port. The team has decided to use TensorFlow/Keras instead.

The project needs three model families (ADR-0002), ImageNet-pretrained
backbones, CPU inference in a FastAPI container, and an artifact that a reviewer
can reproduce. SegFormer is PyTorch-first; the TensorFlow-native segmentation
baseline is DeepLabV3+ with a MobileNetV2 or EfficientNet backbone, with U-Net
or FCN as the fallback.

## Decision

- **Framework:** TensorFlow 2.21 / Keras 3 on Python 3.12. Training and
  evaluation use `tf.data`, Keras layers and `tf.distribute` where needed.
- **Model families:** A autoencoder, B image resynthesis and C transfer-learned
  segmentation stay as decided. C uses TensorFlow-native DeepLabV3+ / U-Net,
  not SegFormer. The resynthesis family is implemented in Keras.
- **Metrics stay framework-agnostic.** `dl/evaluation/metrics.py` consumes NumPy
  score maps and ground-truth masks; it does not import TensorFlow.
- **Export:** a TensorFlow **SavedModel** with a documented serving signature,
  plus a `manifest.json` containing the git SHA, config hash, normal-road dataset
  manifest ID and split hash, TensorFlow version, input spec, normal-road
  validation metrics, default threshold and artifact digest. There is no
  TorchScript or ONNX step.
- **Registry:** export produces all three candidate SavedModels and manifests;
  `selected.json` points at the candidate chosen on normal-road validation. The
  release bundle is published as an OCI artifact to GHCR and mounted read-only
  by the API. RoadAnomaly metrics stay in `docs/experiments/` and never enter
  the selection fields. See [ADR-0008](0008-promotion-and-model-registry.md).
- **Serving:** FastAPI loads the selected SavedModel once at startup with
  `tensorflow-cpu`; `POST /predict` accepts a threshold as a request parameter.
  TensorFlow Serving and TFLite are not part of the initial target.
- **Dependencies:** `requirements/dl.txt` installs `tensorflow==2.21.*` for
  training; `requirements/api.txt` installs `tensorflow-cpu==2.21.*` for the
  service. Framework-free API dependencies live in `requirements/api-base.txt`
  so the local `make install` can install TensorFlow once without also pulling
  `tensorflow-cpu`. `requirements/dev.txt` stays TensorFlow-free so lint,
  type-checking and dataset tests remain fast. `tensorflow` and `tensorflow-cpu`
  must never be installed into the same environment.
- **CI:** the fast quality job stays TensorFlow-free. The optional ML smoke job
  and the CD training smoke test install the TensorFlow training requirements
  and run a tiny CPU job; full training is never part of pull-request CI.

## Alternatives considered

| Option | Why not |
|---|---|
| Keep PyTorch (the original scaffold) | Contradicts the team decision; the scaffold has no model code, so the cost of switching now is documentation, dependencies and the artifact contract |
| TensorFlow Serving | Production-realistic, but it adds a second service to operate; FastAPI already owns the API contract and the demo runs on one machine |
| TFLite runtime only | Smaller API image, but conversion and operator coverage add a model-specific failure mode; keep it as a later optimization if the image becomes a problem |
| SegFormer via a TensorFlow port | Adds a second model ecosystem and a non-Keras training path; DeepLabV3+ / U-Net are native and sufficient for the comparison |
| JAX | Strong research stack, but the team wants TensorFlow/Keras and the pretrained-backbone path is simpler here |

## Consequences

**What gets easier.** One framework for models and serving. Keras Applications
and TensorFlow Hub provide pretrained backbones. SavedModel is the native
artifact, so the API does not need an export conversion framework. FastAPI
remains the only application service.

**What gets harder.** The API image grows because it ships `tensorflow-cpu`;
multi-stage builds and a CPU-only image keep it bounded. TensorFlow
determinism requires explicit seeds and `enable_op_determinism()`. The
resynthesis family has fewer TensorFlow reference implementations than
PyTorch, so it carries the most schedule risk. The manifest must record the
TensorFlow version and the exact checkpoint source.

**How we would know this was wrong.** If the three models cannot produce CPU
score maps within the demo budget, or TensorFlow cannot be pinned reproducibly
in CI, revisit TFLite or TensorFlow Serving — not PyTorch — unless the team
explicitly reverses this decision.
