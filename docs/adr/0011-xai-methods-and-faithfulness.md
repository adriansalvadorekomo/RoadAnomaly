# 0011. XAI methods and faithfulness checks

- **Status:** Accepted (methods selected; implementation not started)
- **Date:** 2026-10-21
- **Deciders:** whole team
- **Amends:** [ADR-0009](0009-xai-evaluation-gate.md) (placement and gate unchanged)
- **Related:** [ADR-0010](0010-model-lineup-and-evaluation-contract.md)

## Context

ADR-0009 fixed XAI as an Evaluation gate: it consumes the selected model and
its score maps, produces per-frame evidence plus a written justification, and
never promotes a model. It deliberately left the method open because no model
existed.

The revised model lineup makes the method choice concrete. The autoencoder has
no class score, only a reconstruction error. U-Net and DeepLabV3+ expose
multi-scale feature maps and class logits at different depths. A single
method applied blindly to all three would either be undefined for the
autoencoder or hide the architecture-specific evidence.

The Seg-Grad-CAM citation was checked before adoption. The reference is
Vinogradova, Dibrov and Myers,
"Towards Interpretable Semantic Segmentation via Gradient-Weighted Class
Activation Mapping" (AAAI-20 student abstract), DOI
`10.1609/aaai.v34i10.7244`. It is verified.

## Decision

XAI remains one shared evaluation activity, not a fourth network. The methods
are fixed per model family:

| Model | Primary explanation | Secondary explanation | What it explains |
|---|---|---|---|
| `autoencoder` | Per-pixel reconstruction-error map | Integrated Gradients on the scalar mean reconstruction error | Where the reconstruction fails, and which input pixels contribute to that scalar |
| `unet` | Seg-Grad-CAM on decoder feature maps | Integrated Gradients for a chosen target pixel | Which decoder regions support the predicted class/score |
| `deeplabv3plus` | Seg-Grad-CAM per ASPP branch and decoder stage | Integrated Gradients for a chosen target pixel | Contribution of each dilation rate and decoder stage |

### Method rules

- The reconstruction-error map is a model output, **not an explanation**. It
  shows where the model is surprised, not why. It may be displayed beside a
  heatmap but must not be labelled as Grad-CAM or Integrated Gradients.
- Integrated Gradients uses a declared baseline (zero image or training-set
  mean), a declared number of steps (default 32), and a target scalar or pixel.
  The report records the baseline and step count; results are not comparable
  across different baselines.
- Seg-Grad-CAM uses the selected target layer, the target class/pixel set and
  the same input preprocessing as inference. U-Net's decoder is the primary
  target because the bottleneck discards skip-connection detail; a bottleneck
  comparison is an ablation, not the primary result. DeepLabV3+'s stride-4
  low-level path bypasses ASPP and its global-pooling branch is spatially
  constant; both limits are stated with the result.
- Grad-CAM and Integrated Gradients show gradient/attribution correlation.
  They are coarse, baseline-sensitive and not causal explanations. No claim of
  causation, safety certification or model correctness follows from a heatmap.
- XAI never changes weights, thresholds, the selected alias or the registry.
  It has no promotion right.

### Faithfulness checks

Every XAI result is accompanied by a separate report-only check:

1. **Deletion/insertion.** Rank input regions by attribution, progressively
   remove or insert them, and measure the target score. Report the area under
   the deletion and insertion curves with a random-order and center-prior
   baseline. For the autoencoder, the target is the reconstruction error; for
   segmentation, it is the selected class/pixel score.
2. **Pointing game.** For U-Net and DeepLabV3+, the highest-attribution point
   must fall inside the target class/object region. Report hit rate over frames
   and the random-hit baseline. It is not applicable to the autoencoder because
   there is no class score.

The XAI check is evidence about the explanation, not a model metric. It never
enters the selection scorecard and never appears in `selected.json`.

### Evidence format

Each XAI run stores, under the experiment record:

- the model ID and immutable artifact digest;
- the frame IDs and score maps used;
- the method, target layer/class/pixel, baseline and step count;
- per-frame heatmap and/or error-map PNGs;
- deletion/insertion and pointing-game results with baselines;
- a short written interpretation and the observed failure modes.

The Streamlit prototype may show an explanation panel only when these artifacts
exist and are linked to the model digest. It must not render a placeholder, a
generic saliency image or an unlabelled error map.

## Consequences

**What gets easier.** V1.8 has a concrete method, a citation, a faithfulness
check and an artifact schema. The autoencoder and segmentation branches no
longer share a method that is undefined for one of them.

**What gets harder.** Integrated Gradients adds compute and baseline choices;
Seg-Grad-CAM requires layer selection and careful target definition. Both need
a trained model before they can produce evidence. V1.8 therefore moves from
`blocked` on a method decision to `in progress`: the justification exists, but
the implementation and artifacts do not.

**How we would know this was wrong.** If deletion/insertion cannot distinguish
the method from a random baseline, or if the selected model's gradients are
unavailable or numerically unstable, the method decision is reopened rather
than shipping an unverified visual.

## References

- R. R. Selvaraju et al., "Grad-CAM: Visual Explanations from Deep Networks via
  Gradient-Based Localization", ICCV 2017,
  DOI `10.1109/ICCV.2017.74`.
- K. Vinogradova, A. Dibrov, G. Myers, "Towards Interpretable Semantic
  Segmentation via Gradient-Weighted Class Activation Mapping", AAAI-20,
  DOI `10.1609/aaai.v34i10.7244`.
- M. Sundararajan, A. Taly, Q. Yan, "Axiomatic Attribution for Deep Networks",
  ICML 2017.
- V. Petsiuk, A. Das, K. Saenko, "RISE: Randomized Input Sampling for
  Explanation of Black-box Models", BMVC 2018 (deletion/insertion protocol).
