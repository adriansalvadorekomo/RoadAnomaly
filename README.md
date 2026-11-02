# RoadAnomaly — pixel-level detection of unexpected road obstacles (CRISP-DM)

ESPRIT · Deep Learning module · Group of 6 · **Final submission: 8 November 2026**

**Authors:** Ines Trabelsi, Emna Trabelsi, Khaled Gannoun, Adrian Salvador Ekomo Mesi Obono, Hejer Mnejja, Walid Fehry

Goal: identify and localise, **at the pixel level**, unexpected objects on the road (animals, rocks, cones, lost tyres, …) in the [RoadAnomaly](data/raw/RoadAnomaly/readme.md) dataset (Lis et al., ICCV 2019). Three approaches are trained on the same shared split, evaluated once on the same frozen test set, explained with XAI, and served through an API and a demo.

| Binôme | Members | Approach | Notebook |
|---|---|---|---|
| A | Ines Trabelsi · Emna Trabelsi | DeepLabV3+ with transfer learning (frozen ImageNet ResNet50) | [`4_Modeling/A_DeepLabV3Plus.ipynb`](notebooks/4_Modeling/A_DeepLabV3Plus.ipynb) |
| B | Khaled Gannoun · Adrian Salvador Ekomo Mesi Obono | Convolutional autoencoders: pixel AE (baseline) and feature-space AE on frozen VGG16 (final) | [`4_Modeling/B_Autoencoder.ipynb`](notebooks/4_Modeling/B_Autoencoder.ipynb) |
| C | Hejer Mnejja · Walid Fehry | CNN baseline (Hejer), U-Net from scratch and U-Net with ImageNet ResNet50 encoder (Walid) | [`4_Modeling/C_CNN_UNet.ipynb`](notebooks/4_Modeling/C_CNN_UNet.ipynb) |

## TL;DR
**The problem.** A car's camera network knows a closed list of things: road, car, person, sign. Put a cow on the road and it still has to answer with one of its words, so it may call the cow "road". We want a network that says instead *"these pixels are something I did not expect"*: a mask that tells a driver-assistance system **where** the obstacle is and **how big**, without knowing **what** it is.

**What we did.** Six models from three ideas, trained on the same 42 photographs, chosen on the same 9 validation photographs, and judged **once** on 9 sealed test photographs (22 obstacles):
- **A, learn the masks with borrowed eyes:** DeepLabV3+ on a frozen ResNet50 that already learned to see on ImageNet.
- **B, learn only what a normal road looks like:** an autoencoder copies normal road; what it cannot copy is the alarm. First on pixels, then on VGG16 features.
- **C, learn the masks from scratch, then with borrowed eyes:** a CNN, a U-Net (skip connections keep the details), and a U-Net with an ImageNet ResNet50 encoder.

**What we found.**
1. **Three-way tie at the top.** DeepLabV3+ (F1 0.739), the pretrained U-Net (0.708) and the feature autoencoder (0.623) cannot be separated on 9 photographs (their paired 95 % intervals cross zero), and each beats the other three models.
2. **Pretrained ImageNet features are the dividing line.** The three models that see through an ImageNet network score F1 ≥ 0.62; the three that learned to see from our 42 photographs alone score ≤ 0.45. Even the autoencoder's success mostly comes from the VGG16 features: a model with no autoencoder at all, on the same features, scores about the same, and we say so.
3. **They fail differently, and that decides the use.** The supervised models find the most obstacles (20/22 for DeepLabV3+) but sprinkle small false alarms (38 of its 67 blobs). The feature autoencoder raises fewer, surer warnings (12 of 22 right) and is the **only model that passes all four business tests**.
4. **Every warning can be explained twice.** *Where* (Grad-CAM++, a flashlight on the image regions that raised the score; faithful for 5 of 6 models) and *what* (exact SHAP, a fair split of the score between five image factors). Brightness and contrast is the main factor for four models; DeepLabV3+ leans on the surrounding scene, the pixel autoencoder on the obstacle itself.
5. **Fast enough for video:** 13–48 ms per photograph on a laptop RTX 4060.

**Recommendation.** DeepLabV3+ by default (the API and the video script use it); the feature autoencoder where a false alarm is expensive. **Limits:** 9 test photographs (one photo moves a mean by about 11 %), no small obstacle in the test split, and RoadAnomaly is used here for both training and testing, so these are not out-of-distribution benchmark scores.

## CRISP-DM layout
```
RoadAnomaly-CRISPDM/
├── notebooks/
│   ├── 1_Business_Understanding.md   # problem, objectives, success criteria, plan
│   ├── 2_Data_Understanding.ipynb    # EDA → evaluation protocol derived from the data
│   ├── 3_Data_Preparation.ipynb      # frozen split (rebuilt + checked), loader, conventions
│   ├── 4_Modeling/                   # one notebook per binôme, validation only
│   │   ├── A_DeepLabV3Plus.ipynb
│   │   ├── B_Autoencoder.ipynb
│   │   └── C_CNN_UNet.ipynb
│   ├── 5_Evaluation.ipynb            # the only use of the test split: all models, once
│   └── 6_XAI.ipynb                   # paired XAI: Grad-CAM++ (where) + exact SHAP (what), faithfulness
├── src/roadanomaly/                  # shared code (pip install -e .), imported everywhere
│   ├── protocol.py                   #   seed, resolution, object limits, bootstrap settings
│   ├── data_pipeline.py              #   paths, frames + masks, split manifest, tf.data loader
│   ├── splitting.py                  #   how the split was made, and its checks
│   ├── normal_regions.py             #   anomaly-free patches / feature cells (Binôme B)
│   ├── postprocessing.py             #   score map → mask (smoothing, z-score, threshold)
│   ├── metrics.py · evaluation.py    #   pixel / object / boundary metrics, the shared report
│   ├── inference.py                  #   shared model format + Predictor (notebooks, API, demo)
│   ├── xai.py                        #   Grad-CAM / Grad-CAM++, exact Shapley factors, deletion / insertion
│   ├── gpu.py
│   ├── losses.py                     #   BCE + Dice, focal, focal-Tversky
│   └── models/                       #   deeplabv3plus · autoencoder · feature_ae · cnn · unet
├── data/
│   ├── raw/RoadAnomaly/              # 60 images + masks (tracked; credits.txt = licences)
│   ├── interim/  processed/          # caches (git-ignored)
├── models/                           # trained models, one folder each (git-ignored)
├── splits/split_manifest.csv         # frozen train / val / test split
├── reports/{figures,results}/        # figures and the evaluation results (results/ is tracked)
├── deployment/                       # api/ (FastAPI) · app/ (Streamlit) · landing/ (Astro) · Docker
├── scripts/                          # evaluate.py · infer_video.py · gpu_memory_check.py
├── tests/                            # pytest: metrics, split, inference contract, XAI, API
├── archive/                          # earlier explorations, kept as run (see archive/README.md)
└── mise.toml                         # project tasks (mise run …)
```

## Rules of the project
1. **No duplicated code.** Notebooks, scripts and apps import from `src/roadanomaly`; a helper used twice moves there.
2. **One model format.** Every final model is a folder `models/<name>/` with `model.keras` + `config.json` (model type, input size, every post-processing setting chosen on validation, validation scores, training settings, environment) — written by `inference.save_artifact`. `inference.Predictor` turns any of them into score maps and masks; notebook 5, the API and the demo all use it, and `mise run test` checks that each saved model reproduces its validation AuPRC.
3. **The test split exists once.** `splits/split_manifest.csv` is checked (and rebuilt identically) in notebook 3, never rewritten. Only notebook 5 loads the test images, once; earlier looks are disclosed there.
4. **Normal-region extraction** for the autoencoders lives in `src/roadanomaly/normal_regions.py`, not in the shared notebooks.
5. **`archive/`** holds earlier explorations; nothing in the pipeline imports from it.
6. **Paths** come from `data_pipeline.py` (repository-relative); no absolute or OS-specific path in code or saved outputs (`mise run check`).
7. **Reproducibility.** Every notebook sets the seed (`protocol.SEED`) and enables deterministic ops, and runs top to bottom (`mise run pipeline`).
8. **Dependencies.** Python packages with pip only (pinned in `requirements.txt`); Node is used only for the landing page.

## Setup (pip only)
Python 3.10–3.12 and, for the GPU, an NVIDIA driver for CUDA 12 (the CUDA libraries come from pip on Linux).
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                   # makes `import roadanomaly` work everywhere
python -m ipykernel install --user --name roadanomaly --display-name "Python (roadanomaly)"
```
With [mise](https://mise.jdx.dev) the same is `mise run setup`. Main tasks (`mise tasks` lists all):

| Task | What it does |
|---|---|
| `mise run setup` / `setup:deploy` | create `.venv`, install the pinned packages, register the kernel / install the API, demo and landing dependencies |
| `mise run test` (`test:fast`) | run the test suite (without the 20 s split regeneration) |
| `mise run train` (`train:a` / `train:b` / `train:c`) | train the six models (notebooks 4A, 4B, 4C) and save them in `models/`; needs the data split of the repo only, much faster with a GPU (see *No GPU?* below) |
| `mise run pipeline` | execute notebooks 2 → 6 in order (trains the models, evaluates, explains) |
| `mise run notebook <path>` | execute one notebook in place |
| `mise run models` / `evaluate <model> [split]` | list the trained models / evaluate one from the command line |
| `mise run api` / `app` / `landing` | FastAPI on :8000, Streamlit demo on :8501, landing page on :4321 |
| `mise run landing:build` / `landing:preview` / `landing:deploy` | build the landing page, serve the build on :4329, deploy it to Vercel (`landing:deploy:preview` for a preview URL) |
| `mise run docker:build` / `docker:up` | build and start the API + demo containers |
| `mise run gpu` / `check` / `clean` | GPU check, repository hygiene, remove caches |

The modeling notebooks download ImageNet weights once into `~/.keras/models` (ResNet50 for A and C, VGG16 / VGG19 for B; about 250 MB); their first run needs internet.

### Get the trained models, then explain and serve them
`models/` is git-ignored, so a fresh clone has no trained model. Either run `mise run train`, or copy the `models/` folder from a teammate. `mise run models` lists what is there; with the models in place, `mise run notebook notebooks/5_Evaluation.ipynb`, `mise run api`, `mise run app` and `mise run docker:up` all work.

**No GPU?** Nothing breaks: `setup_gpu()` prints "No GPU found: running on CPU" and the code runs on the CPU (on Windows, TensorFlow has no GPU support: use WSL2). Training is then much slower (DeepLabV3+ and the U-Net ResNet50 are the slowest), so train one binôme at a time (`train:a`, `train:b`, `train:c`) or copy the models. Scores can differ in the last digits across hardware, and the latency figures (RTX 4060) will be higher; the demo and the API in Docker already use CPU TensorFlow.

> **Tip: no graphics card, or not an NVIDIA RTX?** The code does not need one.
> - **Only want to see the results or run the demo?** No training needed: `mise run docker:up` (CPU) with a copy of the `models/` folder from a teammate, or just open the landing page.
> - **Need to train?** Pick the cheapest option that works for you:
>   1. **CPU:** `mise run train:a`, `train:b` or `train:c` one at a time (slow, but it works; leave the machine plugged in).
>   2. **A free cloud GPU** (Google Colab or Kaggle notebooks give an NVIDIA GPU): clone the repo there, `pip install -r requirements.txt && pip install -e .`, run a modeling notebook, then download the `models/<name>/` folder it produced. We have not tested this route ourselves.
>   3. **Windows:** TensorFlow 2.20 only uses an NVIDIA GPU under WSL2; on native Windows it runs on the CPU.
> - **AMD or Apple GPU:** the pinned TensorFlow 2.20 build here targets NVIDIA CUDA, so these cards are not used and the code falls back to the CPU. (Vendor plug-ins exist, `tensorflow-rocm` and `tensorflow-metal`, but they need other TensorFlow versions and we have not tried them.)
> - **A smaller NVIDIA card (under 6 GB)?** If training runs out of memory, lower the batch size in the modeling notebook (`BATCH_SIZE` in notebook 4A, `PIXEL_BATCH_SIZE` in 4B, the `batch_size` argument of `train(...)` in 4C); the results then differ a little from the reported ones.
> - Whatever you use, `mise run gpu` shows what TensorFlow can see.

### GPU notes (RTX 4060 8 GB and RTX 2060 6 GB)
- **TensorFlow is pinned to 2.20.0.** The 2.21.0 wheel cannot find `libcusolver` and silently runs on CPU. On Windows, TensorFlow runs on CPU (use WSL2 for the GPU).
- The **RTX 2060 (6 GB) is the reference budget.** At `IMG_SIZE = (352, 640)` a U-Net fits batch 8 and DeepLabV3+ batch ≤ 4 (`python scripts/gpu_memory_check.py deeplab 352 640 4`). The trained models used batch 2 (A), 4 (C CNN and U-Net) and 8 (C U-Net ResNet50, 4.6 GB peak).
- Mixed precision: `setup_gpu(mixed_precision=True)` (float16, never bfloat16), and `jit_compile=False` when compiling.

## Shared protocol (notebooks 2 and 3)
- **Split:** 42 train / 9 val / 9 test, group-aware (scenes from the same video, photographer or article never cross splits), rebuilt identically in notebook 3.
- **Masks:** `labels_semantic.png` value 2 → anomaly (1), value 0 → background (0).
- **Metrics** (derived from the data, notebook 2 §10): per-image mean Precision, Recall, F1 = Dice, IoU (and aggregated); object recall / precision / F1 with small objects apart; AuPRC (main for score maps), AUROC, AUPRO@0.3 and FPR95; Boundary IoU (15-px band) and HD95; 95 % bootstrap intervals over images and paired bootstrap differences. Pixel accuracy is not used (90 % of the pixels are background).
- Thresholds, early stopping and model selection use the **validation split only**.

## Results (frozen test split, notebook 5)
Nine test photographs, 22 obstacles, evaluated once with thresholds fixed on validation (`reports/results/`, notebook 5). F1 is the per-image mean with its 95 % bootstrap interval; chance AuPRC is 0.086.

| Binôme | Model | AuPRC | F1 = Dice [95 % CI] | Obstacles found | False alarms / blobs | ms / photo (RTX 4060) | Business criteria |
|---|---|---|---|---|---|---|---|
| A | DeepLabV3+ (frozen ResNet50) | **0.755** | **0.739** [0.62, 0.84] | 20/22 | 38/67 | 21 | 3 / 4 |
| C | U-Net with ImageNet ResNet50 | 0.687 | 0.708 [0.59, 0.81] | 16/22 | 64/93 | 48 | 3 / 4 |
| B | Feature-space autoencoder (VGG16) | 0.631 | 0.623 [0.51, 0.73] | 16/22 | **10/22** | 40 | **4 / 4** |
| C | U-Net from scratch | 0.378 | 0.447 [0.35, 0.54] | 10/22 | 80/117 | 16 | 2 / 4 |
| C | CNN baseline | 0.353 | 0.340 [0.23, 0.44] | 9/22 | 155/219 | 13 | 2 / 4 |
| B | Pixel autoencoder (baseline) | 0.178 | 0.248 [0.12, 0.39] | 16/22 | 40/45 | 26 | 2 / 4 |

The top three are not separated by the paired bootstrap (for example DeepLabV3+ − U-Net ResNet50 = +0.030 [−0.010, 0.081]); each of them is established as better than the bottom three. Only the feature autoencoder meets all four business criteria (`notebooks/1_Business_Understanding.md`, section 4). Earlier looks at the test set are disclosed in notebook 5.

## Explanations (notebook 6)
Every model is explained by two methods, always together and on the same target: its score on the region it flagged (mean anomaly logit for the segmentation models, mean reconstruction error for the autoencoders).

- **Where — Grad-CAM++** (Grad-CAM available): which part of the image that score comes from. It is the default because it is the more faithful map under the deletion / insertion test: it beats random orders for 5 of the 6 models, and fixes the feature autoencoder, where plain Grad-CAM does worse than random (deletion area 65.5 vs 31.3 → 29.9). Neither method passes for the U-Net from scratch.
- **What — exact SHAP over five image factors**: colour, fine texture, brightness and contrast, the obstacle itself, the surrounding scene. Each factor has a stated removal transform (`xai.FACTOR_REMOVAL`); the score is recomputed for all 2⁵ = 32 combinations, so the Shapley values are exact and add up to the score change (largest gap over 54 explanations below 1e-13, float rounding).

| Model | Colour | Fine texture | Brightness & contrast | The obstacle | The scene |
|---|---|---|---|---|---|
| DeepLabV3+ | 14 % | 5 % | 30 % | 20 % | **31 %** |
| Feature autoencoder | 12 % | 24 % | **37 %** | 22 % | 6 % |
| Pixel autoencoder | 7 % | 20 % | 34 % | **38 %** | 0 % |
| CNN baseline | 18 % | 2 % | **63 %** | 17 % | 1 % |
| U-Net | 19 % | 5 % | **54 %** | 17 % | 5 % |
| U-Net ResNet50 | 15 % | 14 % | **39 %** | 22 % | 11 % |

Mean share of each model's Shapley attribution over the nine validation photographs (`reports/results/xai_summary.json`). Explanations describe the models; none of them was used to choose a model or a threshold.

## Deployment
- **API** (`deployment/api/main.py`, default model `A_deeplabv3plus`): `GET /health`, `GET /models`, `POST /predict` (image → mask, overlay, score map, statistics), `POST /explain?model=…&method=gradcampp|gradcam` (the paired explanation: a Grad-CAM++ / Grad-CAM heatmap as base64 PNG, and the exact Shapley value of each image factor with its efficiency check and a one-sentence summary). Interactive docs at `http://localhost:8000/docs`.
- **Demo** (`deployment/app/streamlit_app.py`): upload an image or pick a validation example, Detect (every model side by side), Explain (where + what for one model), Compare (detections and factor shares of all models), Test results and Method tabs. Theme in `.streamlit/config.toml`.
- **Landing page** (`deployment/landing/`, Astro): static page whose numbers are read from `reports/results/test_results.json` and `xai_summary.json` at build time.
- **Docker:** `docker compose -f deployment/docker-compose.yml up --build` starts the API and the demo (CPU TensorFlow; `models/` mounted read-only).
- **Video:** `python scripts/infer_video.py video.mp4` (DeepLabV3+ by default, or `--model B_feature_ae`) writes an overlay video and prints the measured latency and FPS.

## Dataset and licences
RoadAnomaly by K. Lis, K. Nakka, P. Fua and M. Salzmann, *Detecting the Unexpected via Image Resynthesis*, ICCV 2019. The images belong to their authors and are provided for research purposes; sources and licences are in [`data/raw/RoadAnomaly/credits.txt`](data/raw/RoadAnomaly/credits.txt). The annotations are CC BY-SA 4.0.
