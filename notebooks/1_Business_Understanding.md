# 1 · Business Understanding — RoadAnomaly

**CRISP-DM phase 1.** Next: [`2_Data_Understanding.ipynb`](2_Data_Understanding.ipynb)

ESPRIT · Deep Learning module · Group of 6 · Final submission **8 November 2026**.
Operative plan: the group's framing and allocation document (FR, *Fiche officielle de cadrage et de répartition*).

> **TL;DR.** A car's camera network knows a closed list of things (road, car, person…). Put a cow on the road and it still has to pick one of its words, so it may call the cow "road". We want a network that instead says *"these pixels are something I did not expect"*: a mask, so a driver-assistance system knows **where** the obstacle is and **how big**, without knowing **what** it is.
>
> - **Four business goals:** find the obstacles (BO1), without crying wolf (BO2), explain every warning (BO3), and show it running fast enough for video (BO4).
> - **Four pass / fail tests, fixed before the test set was opened** (section 4): beat a trivial detector (SC1), more right warnings than wrong ones (SC2), find at least half the obstacles (SC3), under 100 ms per photo (SC4).
> - **Three approaches, one per pair of students:** learn the masks with a pretrained DeepLabV3+ (A), learn only what a normal road looks like and flag what cannot be rebuilt (B, autoencoders), and learn the masks with a CNN and two U-Nets (C).
> - **Outcome** (notebooks 5 and 6): DeepLabV3+, the pretrained U-Net and the feature autoencoder are statistically tied at the top (test F1 0.74, 0.71, 0.62 on 9 photographs). Only the feature autoencoder passes all four tests: the others find more obstacles but raise too many false alarms (SC2). BO3 is met with a paired explanation, *where* (Grad-CAM++) and *what* (exact SHAP), for every model.

---

## 1. The problem

A camera-based perception system on a vehicle labels every pixel of the road scene (road, car, pedestrian, sign…). It is trained on a **closed list of classes**. When something that is not on the list appears on the road, it has no class to fall into:
- a cow;
- a fallen rock;
- a lost tyre;
- a traffic cone in an unusual place.

The network then forces it into a known class, often with high confidence. A boulder labelled as "road" is not braked for.

**Business question.** Can we flag, **at the pixel level**, the regions of a road image that contain an unexpected obstacle? A pixel-level answer gives a downstream system two things:
- its **location and extent** (where to steer, how close it is);
- a signal it can use without knowing *what* the obstacle is.

**Stakeholders.**
- Road-safety and driver-assistance teams: the consumers of the warning.
- The course team: assessment of the method.
- The six group members: their deliverables are in section 5.

## 2. Business objectives

| # | Objective | Why it matters |
|---|---|---|
| BO1 | **Find the obstacles**: localise as many annotated obstacles as possible, including small ones | A missed obstacle is the costly error (collision) |
| BO2 | **Keep false alarms low** | Frequent false alarms cause unnecessary braking and teach the driver to ignore the warning |
| BO3 | **Explain the warnings**: show which image regions drive a prediction | An operator must be able to trust or challenge a warning; it is also required to discuss failures honestly |
| BO4 | **Demonstrate it**: a usable demo (image in, mask and explanation out) that runs fast enough for frame-by-frame video | Communicates the result; measures latency instead of promising real time |

## 3. Data mining goals (translation into Deep Learning tasks)

**Task.** Binary semantic segmentation, "anomaly" vs "background", on the RoadAnomaly dataset (Lis et al., ICCV 2019):
- 60 images at 1280×720;
- pixel masks in which value 2 means anomaly.

Three complementary approaches, one per binôme (FR):

| Binôme | Members | Approach | Learns from |
|---|---|---|---|
| A | Ines Trabelsi · Emna Trabelsi | **DeepLabV3+** with transfer learning (ImageNet ResNet50 encoder, ASPP, decoder) | annotated masks (supervised) |
| B | Khaled Gannoun · Adrian Salvador Ekomo Mesi Obono | **Convolutional autoencoder**: reconstruction error as anomaly score (pixel AE baseline, feature-space AE final) | normal regions only (unsupervised idea) |
| C | Hejer Mnejja · Walid Fehry | **CNN baseline + U-Nets** (from scratch, and with an ImageNet ResNet50 encoder) | annotated masks (supervised) |

All three produce a **score map** (probability or reconstruction error). A threshold chosen on validation turns it into a **binary mask**, so the three are compared on the same footing.

## 4. Success criteria

Fixed on 2026-11-01, before the shared test evaluation of notebook 5 (the earlier test looks are disclosed there).

**Data mining criteria.** The protocol was derived from the data in notebook 2, section 10, never chosen in advance:
- **Teacher's required metrics:** pixel Precision, Recall, F1, IoU and Dice, as the per-image mean and aggregated.
- **Score maps:** AuPRC is the main ranking metric (chance = prevalence). AUROC and AUPRO@0.3 are reported with their chance levels, and FPR95 too.
- **Object level:** object recall / precision / F1, with small and large objects reported separately.
- **Boundaries:** Boundary IoU and HD95 in px.
- **Uncertainty:** 95 % bootstrap intervals over the 9 test images, and paired bootstrap differences between models.
- **Validation discipline:** thresholds, early stopping and model selection on validation only; the test split is used once.

**Business success criteria**, checked per model in notebook 5, section 6:

| # | Criterion | Measured as | Linked to |
|---|---|---|---|
| SC1 | Clearly better than a trivial detector | lower bound of the 95 % CI of the per-image F1 > F1 of "everything is anomaly" | BO1, BO2 |
| SC2 | A warning is more often right than wrong | object precision over all predicted blobs > 0.5 | BO2 |
| SC3 | Most obstacles are found | object recall over all annotated obstacles ≥ 0.5 | BO1 |
| SC4 | Demonstrable on video | inference < 100 ms per image on a laptop GPU (≥ 10 images/s) | BO4 |

BO3 has no numeric threshold. It is judged in notebook 6, where every model gets a paired explanation of the same number (its score on the region it flagged): **where** the score comes from (Grad-CAM++) and **what** it is made of (exact Shapley values over five image factors). Each half is checked:
- the map is faithful when deleting / inserting the blocks it ranks first moves the score faster than random orders;
- the Shapley values are exact when they add up to the score change (the efficiency identity).

The BU report's ideal of finding "100 % of obstacles" is not a realistic success criterion on 60 images. It stays the direction of improvement.

## 5. Scope and deliverables (FR)

**Required by the teacher.** We also produce the visualisations, the critical analysis and the technical report.

| CRISP-DM phase | Deliverable |
|---|---|
| Data Understanding | EDA, visual examples and label table: [`2_Data_Understanding.ipynb`](2_Data_Understanding.ipynb) |
| Data Preparation | split manifest, DataLoader and evaluation protocol: [`3_Data_Preparation.ipynb`](3_Data_Preparation.ipynb) |
| Modeling | CNN / segmentation / transfer learning: [`4_Modeling/`](4_Modeling/) (one notebook per binôme) |
| Evaluation | metrics on the frozen test split: [`5_Evaluation.ipynb`](5_Evaluation.ipynb) |

**Group extensions** (FR: not explicit requirements):
- XAI: [`6_XAI.ipynb`](6_XAI.ipynb).
- Deployment in [`../deployment/`](../deployment/):
  - FastAPI with `/health`, `/models`, `/predict` and `/explain`;
  - a Streamlit demo;
  - an Astro landing page;
  - Docker / Compose.
- Video inference with latency.
- A commercial video.

YOLO-style detectors are out of scope: they give boxes, not pixel masks.

## 6. Resources, constraints and risks

| Item | Situation | Consequence / mitigation |
|---|---|---|
| Data volume | 60 images, split 42 / 9 / 9 (group-aware) | Small evaluation sets: intervals, per-image results, no winner declared when intervals overlap |
| No normal image | every image contains an anomaly (notebook 2, §5) | The autoencoder learns "normal" from anomaly-free **regions** of the train images; external normal data only with explicit authorisation (FR) |
| Near-duplicate scenes | frames from the same video or article (notebook 2, §8) | Group-aware split, regenerated and checked in notebook 3 |
| Licences | images belong to their authors; annotations are CC BY-SA 4.0 | Research use only; sources in `data/raw/RoadAnomaly/credits.txt`; the dataset is cited |
| Compute | RTX 4060 8 GB and RTX 2060 6 GB (reference budget) | 352×640 working resolution; DeepLabV3+ batch ≤ 4; mixed precision float16 only |
| Pretrained weights | ImageNet weights are used by A (ResNet50 encoder), B (VGG16 features; VGG19 inside the pixel AE's loss) and C (ResNet50 encoder of the pretrained U-Net) | External knowledge, stated in the report; to be confirmed as allowed for Binôme B |
| Test contamination | some test images were scored during development (disclosed in notebook 5) | No change made on test evidence; disclosure instead of a hidden re-split |
| Framing | RoadAnomaly is an out-of-distribution benchmark in the literature (models trained elsewhere, tested here) | Here it is used for training and testing on 60 images; results are not comparable to OoD leaderboards, and generalisation to unseen anomaly types is not shown |

## 7. Project plan

The FR schedule, with milestones.

| Dates | Milestone | Owner |
|---|---|---|
| 20–22 Oct | EDA, masks, splits and protocol (notebooks 2–3) | all |
| 23–25 Oct | Model-specific pipelines and architectures | each binôme |
| 26–31 Oct | Training, validation, checkpoints (notebooks 4) | each binôme |
| 1–3 Nov | Final evaluation, XAI and comparison (notebooks 5–6) | all |
| 4–5 Nov | Application, Docker, inference video | all (API / Docker / video: Binôme B) |
| 6–7 Nov | Report, commercial video, rehearsal | all |
| 8 Nov | **Final submission** | all |

## 8. References

- K. Lis, K. Nakka, P. Fua, M. Salzmann. *Detecting the Unexpected via Image Resynthesis.* ICCV 2019 (the RoadAnomaly dataset).
- R. Chan et al. *SegmentMeIfYouCan: A Benchmark for Anomaly Segmentation.* NeurIPS Datasets and Benchmarks 2021 (component-level metrics, FPR95).
- R. Wirth, J. Hipp. *CRISP-DM: Towards a Standard Process Model for Data Mining.* 2000.
- L.-C. Chen et al. *Encoder-Decoder with Atrous Separable Convolution for Semantic Image Segmentation (DeepLabV3+).* ECCV 2018.
- O. Ronneberger, P. Fischer, T. Brox. *U-Net: Convolutional Networks for Biomedical Image Segmentation.* MICCAI 2015.
- P. Bergmann et al. *MVTec AD — A Comprehensive Real-World Dataset for Unsupervised Anomaly Detection.* CVPR 2019 (per-region overlap, AUPRO).
- T. Defard et al. *PaDiM: a Patch Distribution Modeling Framework for Anomaly Detection and Localization.* ICPR 2021 (Gaussian control of Binôme B).
- B. Cheng et al. *Boundary IoU: Improving Object-Centric Image Segmentation Evaluation.* CVPR 2021.
- R. R. Selvaraju et al. *Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization.* ICCV 2017.
- A. Chattopadhay, A. Sarkar, P. Howlader, V. N. Balasubramanian. *Grad-CAM++: Generalized Gradient-Based Visual Explanations for Deep Convolutional Networks.* WACV 2018.
- S. M. Lundberg, S.-I. Lee. *A Unified Approach to Interpreting Model Predictions.* NeurIPS 2017 (SHAP); L. S. Shapley. *A Value for n-Person Games.* 1953.
- V. Petsiuk, A. Das, K. Saenko. *RISE: Randomized Input Sampling for Explanation of Black-box Models.* BMVC 2018 (deletion / insertion).
- For Seg-Grad-CAM (Vinogradova et al., 2020), FR asks the team to verify the reference before academic citation.
