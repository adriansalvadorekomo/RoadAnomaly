# XAI contract

> **Status:** methods selected; implementation and artifacts missing. This file
> is a planned evidence contract, not a claim that an explanation exists.

XAI is a required Evaluation gate ([ADR-0009](adr/0009-xai-evaluation-gate.md)).
The methods are fixed by [ADR-0011](adr/0011-xai-methods-and-faithfulness.md).
It is not a fourth network, not a model-selection signal and not a promotion
input.

## Methods

| Model | Primary evidence | Secondary evidence | Target |
|---|---|---|---|
| `autoencoder` | Per-pixel reconstruction-error map | Integrated Gradients on the scalar mean reconstruction error | Where reconstruction fails; input attribution for that scalar |
| `unet` | Seg-Grad-CAM on decoder feature maps | Integrated Gradients for a chosen target pixel/class | Decoder regions supporting the prediction |
| `deeplabv3plus` | Seg-Grad-CAM per ASPP branch and decoder stage | Integrated Gradients for a chosen target pixel/class | Contribution of dilation rates and decoder stages |

### Autoencoder

- The reconstruction-error map is a **model output**, not an explanation. It
  shows where the reconstruction is poor, not why. It must be labelled as an
  error map and never as Grad-CAM or Integrated Gradients.
- Integrated Gradients explains a scalar target. The default target is the mean
  reconstruction error over the frame; the baseline (zero image or training-set
  mean), interpolation steps (default 32) and whether the result is absolute or
  signed are recorded with the artifact.
- There is no class score, so a pointing game is not applicable.

### U-Net

- Seg-Grad-CAM uses the decoder feature maps and the selected target class or
  pixel set. The bottleneck is the coarsest representation and loses
  skip-connection detail; a bottleneck result is an ablation, not the primary
  explanation.
- Integrated Gradients uses the same target and preprocessing as inference.
  The baseline and step count are recorded.
- The Vinogradova et al. Seg-Grad-CAM reference is verified: DOI
  `10.1609/aaai.v34i10.7244`.

### DeepLabV3+

- Seg-Grad-CAM is computed per ASPP branch and decoder stage so the report can
  show the contribution of each dilation rate.
- The stride-4 low-level path bypasses ASPP; the global-pooling branch is
  spatially constant. Both limits are stated next to the result.
- The same Integrated Gradients target/baseline rules apply.

## Limitations

- Grad-CAM and Seg-Grad-CAM are gradient-weighted activation maps. They show
  correlation at a coarse resolution; they are not causal explanations.
- Integrated Gradients is baseline-sensitive and can saturate. A different
  baseline changes the attribution; results are not comparable across
  baselines.
- A heatmap can look plausible while being unfaithful. The faithfulness checks
  below are required, not optional decoration.
- No method certifies safety or correctness. XAI evidence supports inspection
  and discussion; it does not promote a model.

## Faithfulness checks

These checks are report-only. They never enter the selection scorecard.

### Deletion and insertion

1. Rank input regions by attribution.
2. Delete the highest-ranked regions progressively and measure the target score
   (reconstruction error for the autoencoder; class/pixel score for
   segmentation).
3. Insert the highest-ranked regions into a neutral baseline and measure the
   same target.
4. Report the area under the deletion and insertion curves, with random-order
   and center-prior baselines. State the region size, step count and baseline.

### Pointing game

For U-Net and DeepLabV3+, take the highest-attribution point and check whether
it falls inside the target class/object region. Report the hit rate over frames
and the random-hit baseline. It is not applicable to the autoencoder.

## Evidence format

Each XAI run stores:

- model ID and immutable artifact digest;
- frame IDs, input preprocessing version and score maps;
- method, target layer/class/pixel, baseline and step count;
- per-frame heatmap and/or error-map PNGs;
- deletion/insertion and pointing-game results with baselines;
- a short written interpretation and observed failure modes;
- a link to the experiment record.

The Streamlit prototype may show an explanation panel only when these artifacts
exist and are linked to the model digest. It must not render a placeholder, a
generic saliency image or an unlabelled error map.

## Status

The method decision is resolved; V1.8 remains `in progress` because no XAI code
or artifact exists and no model has been trained. The implementation is blocked
on the model and the normal-road manifest, not on a method choice.
