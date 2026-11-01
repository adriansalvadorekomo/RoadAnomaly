# RoadAnomaly — pixel-level detection of unexpected road obstacles (CRISP-DM)

ESPRIT · Deep Learning module · Group of 6 · **Final submission: 8 November 2026**

Goal: identify and localise, **at the pixel level**, unexpected objects on the road (animals, rocks, cones, lost tyres, …) in the [RoadAnomaly](data/raw/RoadAnomaly/readme.md) dataset (Lis et al., ICCV 2019). Three approaches are trained on the same shared split, evaluated once on the same frozen test set, explained with XAI, and served through an API and a demo.

| Binôme | Members | Approach | Notebook |
|---|---|---|---|
| A | Ines · Emna | DeepLabV3+ with transfer learning (frozen ImageNet ResNet50) | [`4_Modeling/A_DeepLabV3Plus.ipynb`](notebooks/4_Modeling/A_DeepLabV3Plus.ipynb) |
| B | Khaled · Adrian | Convolutional autoencoders: pixel AE (baseline) and feature-space AE on frozen VGG16 (final) | [`4_Modeling/B_Autoencoder.ipynb`](notebooks/4_Modeling/B_Autoencoder.ipynb) |
| C | Hejer · Walid | CNN baseline (Hejer), U-Net from scratch and U-Net with ImageNet ResNet50 encoder (Walid) | [`4_Modeling/C_CNN_UNet.ipynb`](notebooks/4_Modeling/C_CNN_UNet.ipynb) |

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
│   └── 6_XAI.ipynb                   # Seg-Grad-CAM, error maps, deletion / insertion
├── src/roadanomaly/                  # shared code (pip install -e .), imported everywhere
│   ├── protocol.py                   #   seed, resolution, object limits, bootstrap settings
│   ├── data_pipeline.py              #   paths, frames + masks, split manifest, tf.data loader
│   ├── splitting.py                  #   how the split was made, and its checks
│   ├── normal_regions.py             #   anomaly-free patches / feature cells (Binôme B)
│   ├── postprocessing.py             #   score map → mask (smoothing, z-score, threshold)
│   ├── metrics.py · evaluation.py    #   pixel / object / boundary metrics, the shared report
│   ├── inference.py                  #   shared model format + Predictor (notebooks, API, demo)
│   ├── xai.py                        #   Grad-CAM / Seg-Grad-CAM, deletion / insertion
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
| `mise run pipeline` | execute notebooks 2 → 6 in order (trains the models, evaluates, explains) |
| `mise run notebook <path>` | execute one notebook in place |
| `mise run models` / `evaluate <model> [split]` | list the trained models / evaluate one from the command line |
| `mise run api` / `app` / `landing` | FastAPI on :8000, Streamlit demo on :8501, landing page on :4321 |
| `mise run docker:build` / `docker:up` | build and start the API + demo containers |
| `mise run gpu` / `check` / `clean` | GPU check, repository hygiene, remove caches |

The modeling notebooks download ImageNet weights once into `~/.keras/models` (ResNet50 for A and C, VGG16 / VGG19 for B; about 250 MB); their first run needs internet.

### GPU notes (RTX 4060 8 GB and RTX 2060 6 GB)
- **TensorFlow is pinned to 2.20.0.** The 2.21.0 wheel cannot find `libcusolver` and silently runs on CPU. On Windows, TensorFlow runs on CPU (use WSL2 for the GPU).
- The **RTX 2060 (6 GB) is the reference budget.** At `IMG_SIZE = (352, 640)`: U-Net trains with batch 8, DeepLabV3+ with batch ≤ 4 (`python scripts/gpu_memory_check.py deeplab 352 640 4`).
- Mixed precision: `setup_gpu(mixed_precision=True)` (float16, never bfloat16), and `jit_compile=False` when compiling.

## Shared protocol (notebooks 2 and 3)
- **Split:** 42 train / 9 val / 9 test, group-aware (scenes from the same video, photographer or article never cross splits), rebuilt identically in notebook 3.
- **Masks:** `labels_semantic.png` value 2 → anomaly (1), value 0 → background (0).
- **Metrics** (derived from the data, notebook 2 §10): per-image mean Precision, Recall, F1 = Dice, IoU (and aggregated); object recall / precision / F1 with small objects apart; AuPRC (main for score maps), AUROC, AUPRO@0.3 and FPR95; Boundary IoU (15-px band) and HD95; 95 % bootstrap intervals over images and paired bootstrap differences. Pixel accuracy is not used (90 % of the pixels are background).
- Thresholds, early stopping and model selection use the **validation split only**.

## Results (frozen test split, notebook 5)
RESULTS_PLACEHOLDER

## Deployment
- **API** (`deployment/api/main.py`): `GET /health`, `GET /models`, `POST /predict` (image → mask, overlay, score map, statistics), `POST /explain` (Grad-CAM). Interactive docs at `http://localhost:8000/docs`.
- **Demo** (`deployment/app/streamlit_app.py`): upload an image or pick a validation example, compare models side by side, Grad-CAM on demand, test results tab.
- **Landing page** (`deployment/landing/`, Astro): static page whose numbers are read from `reports/results/test_results.json` at build time.
- **Docker:** `docker compose -f deployment/docker-compose.yml up --build` starts the API and the demo (CPU TensorFlow; `models/` mounted read-only).
- **Video:** `python scripts/infer_video.py video.mp4 --model B_feature_ae` writes an overlay video and prints the measured latency and FPS.

## Dataset and licences
RoadAnomaly by K. Lis, K. Nakka, P. Fua and M. Salzmann, *Detecting the Unexpected via Image Resynthesis*, ICCV 2019. The images belong to their authors and are provided for research purposes; sources and licences are in [`data/raw/RoadAnomaly/credits.txt`](data/raw/RoadAnomaly/credits.txt). The annotations are CC BY-SA 4.0.
