# Project layout, rules and shared protocol

Moved here from the README unchanged. These rules are what keeps the six models comparable.

## CRISP-DM layout
```
RoadAnomaly-CRISPDM/
├── notebooks/
│   ├── 0_RoadAnomaly_Master.ipynb    # all phases in one notebook (generated: mise run master)
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
7. **Reproducibility.** Every notebook seeds its random generators (`protocol.SEED` wherever a model is trained, evaluated or explained); the training and evaluation notebooks (4A, 4B, 4C, 5) also enable deterministic GPU ops; every notebook runs top to bottom (`mise run pipeline`).
8. **Dependencies.** Python packages with pip only (pinned in `requirements.txt`); Node is used only for the landing page.
9. **One master notebook, generated.** `notebooks/0_RoadAnomaly_Master.ipynb` puts phases 1 to 6 in one notebook, for reading and submission: each modeling part names its binôme, and the training code explains its hyper-parameters. It is built from the phase notebooks by `scripts/build_master_notebook.py` (`mise run master`, also run at the end of `mise run pipeline`) and never edited by hand; `mise run check` fails when it is out of date.
10. **Clean code.** `mise run lint` (ruff, rules in `pyproject.toml`) passes on the code and the notebooks: sorted imports, no unused names, lines of at most 120 characters, `zip(..., strict=...)` stated. The training cells explain their hyper-parameters in comments. `mise run check` runs it with the other gates.

## Shared protocol (notebooks 2 and 3)
- **Split:** 42 train / 9 val / 9 test, group-aware (scenes from the same video, photographer or article never cross splits), rebuilt identically in notebook 3.
- **Masks:** `labels_semantic.png` value 2 → anomaly (1), value 0 → background (0).
- **Metrics** (derived from the data, notebook 2 §10): per-image mean Precision, Recall, F1 = Dice, IoU (and aggregated); object recall / precision / F1 with small objects apart; AuPRC (main for score maps), AUROC, AUPRO@0.3 and FPR95; Boundary IoU (15-px band) and HD95; 95 % bootstrap intervals over images and paired bootstrap differences. Pixel accuracy is not used (90 % of the pixels are background).
- Thresholds, early stopping and model selection use the **validation split only**.

