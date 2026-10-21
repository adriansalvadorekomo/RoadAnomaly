# 0002. Compare three model families, not one

- **Status:** Superseded by [ADR-0010](0010-model-lineup-and-evaluation-contract.md)
- **Date:** 2026-10-18
- **Deciders:** whole team

> **Superseded (2026-10-21).** ADR-0010 replaces image resynthesis with U-Net
> and fixes the current model lineup, metric contract and selection scorecard.
> This record is retained as history.

> **Framework note (ADR-0005, historical).** At that point the three-family
> decision stood; model C was to use TensorFlow-native DeepLabV3+ / U-Net
> instead of SegFormer. ADR-0010 later replaced the lineup, so this note records
> the state before that revision.
>
> **XAI note (ADR-0009/ADR-0011, historical).** Explainability was required
> evaluation evidence for the selected model, not a fourth model family. The
> method was later fixed by ADR-0011 and never changed the model comparison.

## Context

The module asks us to "experiment with suitable deep learning approaches,
including CNNs, semantic segmentation models, and transfer learning.
Autoencoders may also be explored as a complementary approach", and to
"justify your choice of models".

The assessment therefore rewards breadth with justification, not a single
tuned model. At the same time the deadline is three weeks out and six people
are working in parallel, so each approach must be independently runnable by
one person.

## Decision

Three approaches are implemented behind one shared evaluation harness, so the
comparison is a configuration change rather than three parallel projects.

**A. Autoencoder reconstruction error** — an encoder/decoder trained to
reconstruct *normal* road scenes. Anomalies reconstruct badly; the per-pixel
error is thresholded into a mask. Chosen because it needs no anomaly labels at
all, gives us a fast end-to-end baseline in week 1, and makes the failure mode
of the whole family visible (it also reconstructs anomalies well when they are
large and smooth).

**B. Image resynthesis (Lis et al., ICCV 2019)** — segment the scene, replace
the "unknown" region with a synthesised version of what the network expects to
see, and flag pixels where the original and the resynthesis disagree. Chosen
because it is the reference method of the dataset we are given, so we can
compare against a published result instead of only against ourselves.

**C. Transfer-learned segmentation** — DeepLabv3+ and SegFormer with
ImageNet/COCO-pretrained backbones, fine-tuned on normal road classes, with
anomaly score = 1 − max softmax probability (max-logit / MSP baseline).
Chosen because pretrained weights are the most reliable way to get a strong
pixel-level model with 60 evaluation images and modest compute, and because
the MSP baseline is the yardstick that the more elaborate methods must beat
to justify themselves.

All three emit the same object: a per-pixel anomaly score map. The shared
harness in `dl/evaluation/` turns any score map plus a ground-truth mask into
the same metric set, so no model can be evaluated more favourably than another.

## Alternatives considered

| Option | Why not |
|---|---|
| Only the resynthesis method | Reproduces the paper but proves nothing about alternatives; the module explicitly asks for comparison |
| A single big segmentation model, heavily tuned | Best possible single score, weakest answer to "compare the approaches investigated" |
| Diffusion- or flow-based reconstruction | Strongest published anomaly scores, but the training cost does not fit a three-week CPU/Colab budget |
| GAN discriminator scoring | Attractive, but unstable to tune in the time available; we would be reporting tuning noise |

## Consequences

**What gets easier.** Week 1 produces a working baseline (A) that de-risks the
rest. Every later model has a reference point. The report has a real
comparison table with an ablation story.

**What gets harder.** Three training pipelines to keep green in CI, three
inference paths behind the API, and the demo UI must show all three without
becoming a settings screen. Shared code in `dl/data/` and `dl/evaluation/`
becomes a coordination point: breaking it breaks everyone.

**How we would know this was wrong.** If by the end of week 2 two of the three
approaches are not producing sane score maps, we drop the weakest one and
document *why we dropped it* rather than shipping a half-tuned model.
