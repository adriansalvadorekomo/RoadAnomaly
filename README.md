# RoadAnomaly — Road anomaly segmentation (CRISP-DM)

ESPRIT · Deep Learning module · Group of 6 · **Final submission: 8 November 2026**

Goal: identify and localise, **at the pixel level**, unexpected objects on the road (animals, rocks, cones, lost tyres, …) in the [RoadAnomaly](datasets/RoadAnomaly/readme.md) dataset (Lis et al., ICCV 2019). The three approaches below are trained on the same shared split and compared on the same frozen test set.

| Binôme | Members | Approach |
|---|---|---|
| A | Ines · Emna | DeepLabV3+ with transfer learning |
| B | Khaled · Adrian | Convolutional autoencoder (reconstruction error) |
| C | Hejer · Walid | CNN baseline + U-Net |

## Repository layout
```
RoadAnomaly-CRISPDM/
├── datasets/RoadAnomaly/        # 60 images + pixel masks (readme.md, credits.txt = licences)
├── notebooks/                   # one notebook per CRISP-DM step, numbered
│   └── 01_Data_Understanding.ipynb
├── src/roadanomaly/             # shared code, installed with `pip install -e .`
│   ├── data_pipeline.py         #   frame loading, binary masks, split loading, tf.data DataLoader
│   ├── metrics.py               #   pixel + object metrics, bootstrap intervals
│   └── gpu.py                   #   GPU setup (memory growth, mixed precision)
├── splits/split_manifest.csv    # frozen train / val / test split (group-aware)
├── reports/figures/             # figures saved by the notebooks
├── scripts/gpu_memory_check.py  # checks that a resolution / batch size fits a 6 GB GPU
├── requirements.txt             # pinned versions
└── pyproject.toml               # makes src/roadanomaly installable
```
Notebook naming: `NN_<Step>.ipynb` for shared steps, and `NN_<Binôme>_<Model>.ipynb` for model notebooks (e.g. `02_B_Autoencoder.ipynb`). Model weights (`*.keras`), `checkpoints/` and `logs/` are git-ignored.

## Setup (pip only)
Requires Python 3.10–3.12 and an NVIDIA driver for CUDA 12. The CUDA libraries themselves come from pip.
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                   # makes `import roadanomaly` work in every notebook
python -m ipykernel install --user --name roadanomaly --display-name "Python (roadanomaly)"
```
Check the GPU:
```bash
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

### GPU notes (RTX 4060 8 GB and RTX 2060 6 GB)
- **TensorFlow is pinned to 2.20.0.** The 2.21.0 wheel cannot find `libcusolver` and silently runs on CPU.
- The **RTX 2060 (6 GB) is the reference budget.** At the shared resolution `IMG_SIZE = (352, 640)`: U-Net trains with batch 8 and DeepLabV3+ (ResNet50) with batch 4. Check your own configuration with:
  `python scripts/gpu_memory_check.py deeplab 352 640 4`
- Use `setup_gpu(mixed_precision=True)` for float16 (both cards support it). Never use bfloat16, which the 2060 does not support.
- Compile with `jit_compile=False` when using mixed precision. TF 2.20's XLA fails on some graphs with "Seen floating point types of different precisions".

## Shared protocol (from `notebooks/01_Data_Understanding.ipynb`)
- **Split:** 42 train / 9 val / 9 test. Scenes from the same video, photographer or article never cross splits. The **test split is used once**, for the final comparison.
- **Masks:** `labels_semantic.png` value 2 → anomaly (1), value 0 → background (0).
- **Metrics:** chosen from the data analysis (section 12 of the notebook):
  - pixel Precision, Recall, F1, IoU and Dice as the per-image mean;
  - object-level recall, precision and F1;
  - AuPRC for score maps;
  - bootstrap intervals on test.
  
  Pixel accuracy is not used: 90 % of the pixels are background.
- Thresholds, early stopping and model selection use the **validation split only**.

## Dataset and licences
RoadAnomaly by K. Lis, K. Nakka, P. Fua and M. Salzmann, *Detecting the Unexpected via Image Resynthesis*, ICCV 2019. The images belong to their authors and are provided for research purposes; sources and licences are in [`datasets/RoadAnomaly/credits.txt`](datasets/RoadAnomaly/credits.txt). The annotations are CC BY-SA 4.0.
