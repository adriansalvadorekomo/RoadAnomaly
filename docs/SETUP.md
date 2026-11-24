# Setup, training and hardware

Moved here from the README unchanged: everything needed to install, train and run RoadAnomaly locally. The README keeps the short version.

## Setup (pip only)
Python 3.10–3.12 and, for the GPU, an NVIDIA driver for CUDA 12 (the CUDA libraries come from pip on Linux).
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                   # makes `import roadanomaly` work everywhere
python -m ipykernel install --user --name roadanomaly --display-name "Python (roadanomaly)"
```
With [mise](https://mise.jdx.dev) the same is `mise run setup`. **`mise run help`** lists every task grouped by purpose, with its arguments; `mise run help <task>` shows one in full, including the plain shell command to run it without mise. Main tasks:

| Task | What it does |
|---|---|
| `mise run help` (`help <task>`) | every project command, grouped by purpose (read from `mise.toml`, so it is always up to date) |
| `mise run setup` / `setup:deploy` | create `.venv`, install the pinned packages, register the kernel / install the API, demo and landing dependencies |
| `mise run test` (`test:fast`) | run the test suite (without the 20 s split regeneration) |
| `mise run train` (`train:a` / `train:b` / `train:c`) | train the six models (notebooks 4A, 4B, 4C) and save them in `models/`; needs the data split of the repo only, about 20 minutes on a laptop RTX 4060 (see *Training time* below) |
| `mise run pipeline` | execute notebooks 2 → 6 in order (trains the models, evaluates, explains), then rebuild the master notebook |
| `mise run master` | rebuild `notebooks/0_RoadAnomaly_Master.ipynb` (all phases in one notebook) from the phase notebooks |
| `mise run notebook <path>` | execute one notebook in place |
| `mise run models` / `evaluate <model> [split]` | list the trained models / evaluate one from the command line |
| `mise run api` / `app` / `landing` | FastAPI on :8000, Streamlit demo on :8501, landing page on :4321 |
| `mise run product` | the RoadAnomaly product (customer MVP, in French) on :8502 |
| `mise run landing:build` / `landing:preview` / `landing:deploy` | build the landing page, serve the build on :4329, deploy it to Vercel (`landing:deploy:preview` for a preview URL) |
| `mise run docker:build` / `docker:up` | build and start the API, demo, product and landing containers |
| `mise run lint` | ruff on the code and the notebooks (`ruff check . --fix` sorts the imports) |
| `mise run gpu` / `check` / `clean` | GPU check, quality gate (no absolute paths, master notebook up to date, lint clean), remove caches |

The modeling notebooks download ImageNet weights once into `~/.keras/models` (ResNet50 for A and C, VGG16 / VGG19 for B; about 250 MB); their first run needs internet.

### Get the trained models, then explain and serve them
`models/` is git-ignored, so a fresh clone has no trained model. Either run `mise run train`, or copy the `models/` folder from a teammate. `mise run models` lists what is there; with the models in place, `mise run notebook notebooks/5_Evaluation.ipynb`, `mise run api`, `mise run app`, `mise run product` and `mise run docker:up` all work.

**Training time** (measured from the notebooks' own cell timestamps, RTX 4060 Laptop GPU, TensorFlow 2.20, without the one-off ImageNet download of about 250 MB):

| Task | Notebook | Time | Where it goes |
|---|---|---|---|
| `train:a` | 4A DeepLabV3+ | about 35 s | training, 16 epochs: 25 s |
| `train:b` | 4B autoencoders | about 12.4 min | pixel AE, four loss variants: 7.7 min; VGG depth study: 3.5 min; ablation: 35 s |
| `train:c` | 4C CNN and U-Nets | about 6.5 min | CNN (80 epochs): 2.0 min; U-Net (50 epochs): 1.7 min; U-Net ResNet50 (46 epochs + flip check): 2.6 min |
| `train` | all three | **about 20 min** | |

Other hardware (CPU, RTX 2060, Colab) has not been measured.

**No GPU?** Nothing breaks: `setup_gpu()` prints "No GPU found: running on CPU" and the code runs on the CPU (on Windows, TensorFlow has no GPU support: use WSL2). Training is then slower (not measured here), so train one binôme at a time (`train:a`, `train:b`, `train:c`) or copy the models. Scores can differ in the last digits across hardware, and the latency figures (RTX 4060) will be higher; the demo and the API in Docker already use CPU TensorFlow.

> **Tip: no graphics card, or not an NVIDIA RTX?** The code does not need one.
> - **Only want to see the results or run the demo?** No training needed: `mise run docker:up` (CPU) with a copy of the `models/` folder from a teammate, or just open the landing page.
> - **Need to train?** Pick the cheapest option that works for you:
>   1. **CPU:** `mise run train:a`, `train:b` or `train:c` one at a time (slow, but it works; leave the machine plugged in).
>   2. **A free cloud GPU** (Google Colab or Kaggle notebooks give an NVIDIA GPU): clone the repo there, `pip install -r requirements.txt && pip install -e .`, run a modeling notebook, then download the `models/<name>/` folder it produced. We have not tested this route ourselves.
>   3. **Windows:** TensorFlow 2.20 only uses an NVIDIA GPU under WSL2; on native Windows it runs on the CPU.
> - **AMD or Apple GPU:** the pinned TensorFlow 2.20 build here targets NVIDIA CUDA, so these cards are not used and the code falls back to the CPU. (Vendor plug-ins exist, `tensorflow-rocm` and `tensorflow-metal`, but they need other TensorFlow versions and we have not tried them.)
> - **A smaller NVIDIA card (under 6 GB)?** If training runs out of memory, lower the batch size in the modeling notebook (`BATCH_SIZE` in notebook 4A, `PIXEL_BATCH_SIZE` in 4B, the `batch_size` argument of `train(...)` in 4C); the results then differ a little from the reported ones.
> - Whatever you use, `mise run gpu` shows what TensorFlow can see.

### VS Code
Open the **repository root** (`code RoadAnomaly-CRISPDM`), not a subfolder such as `notebooks/`: only then does VS Code read the workspace settings (`.vscode/settings.json`: the `.venv` interpreter, pip instead of uv, pytest) and Pylance read `pyproject.toml` (type checking in `basic` mode, with the rules that only flag working TensorFlow / NumPy code turned off). If you open `notebooks/` on its own, `notebooks/pyrightconfig.json` still gives Pylance the project's rules (it extends `pyproject.toml`), but the interpreter and the other workspace settings then have to be chosen by hand; without a project configuration, Pylance would apply your personal settings, e.g. a global `strict` mode, and show many false errors. For notebooks, pick the kernel **Python (roadanomaly)**, the same `.venv` registered by `mise run setup`, so that the notebooks' metadata stays unchanged. The recommended extensions are listed in `.vscode/extensions.json` (Python, Pylance, Jupyter, Ruff, Astro, TOML).

### GPU notes (RTX 4060 8 GB and RTX 2060 6 GB)
- **TensorFlow is pinned to 2.20.0.** The 2.21.0 wheel cannot find `libcusolver` and silently runs on CPU. On Windows, TensorFlow runs on CPU (use WSL2 for the GPU).
- The **RTX 2060 (6 GB) is the reference budget.** At `IMG_SIZE = (352, 640)` a U-Net fits batch 8 and DeepLabV3+ batch ≤ 4 (`python scripts/gpu_memory_check.py deeplab 352 640 4`). The trained models used batch 2 (A), 4 (C CNN and U-Net) and 8 (C U-Net ResNet50, 4.6 GB peak).
- Mixed precision: `setup_gpu(mixed_precision=True)` (float16, never bfloat16), and `jit_compile=False` when compiling.

