"""RoadAnomaly demo (Streamlit): upload a road image, choose models, see masks, scores and explanations.

Run: `mise run app` (or `streamlit run deployment/app/streamlit_app.py`).
The demo calls the same inference service as the API (deployment/service.py).
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # make `deployment` importable
from deployment import service  # noqa: E402
from roadanomaly import data_pipeline as dp  # noqa: E402

RESULTS = dp.REPO_ROOT / "reports" / "results"

st.set_page_config(page_title="RoadAnomaly — obstacle detection", page_icon="🚧", layout="wide")


@st.cache_data(show_spinner=False)
def example_frames():
    """Validation images offered as examples (the test split stays out of the demo)."""
    return [row["frame"] for row in dp.read_manifest() if row["split"] == "val"]


@st.cache_data(show_spinner=False)
def load_example(frame):
    image, mask = dp.load_frame(frame)
    return image, mask.astype(bool)


# ------------------------------------------------------------------ sidebar
st.sidebar.title("RoadAnomaly")
st.sidebar.caption("Pixel-level detection of unexpected obstacles on the road · ESPRIT Deep Learning · CRISP-DM")
names = service.model_names()
if not names:
    st.error("No trained model found in `models/`. Run the modeling notebooks (`mise run pipeline`) first.")
    st.stop()
titles = {name: f"{service.model_info(name)['binome']} · {service.model_info(name)['title']}" for name in names}
chosen = st.sidebar.multiselect("Models", names, default=names, format_func=titles.get)
source = st.sidebar.radio("Image", ["Example (validation split)", "Upload"], horizontal=True)
show_xai = st.sidebar.toggle("Explain (Grad-CAM)", value=False,
                             help="Heatmap of what drives the predicted region. Descriptive, not causal.")

ground_truth = None
if source == "Upload":
    upload = st.sidebar.file_uploader("Road image", type=["jpg", "jpeg", "png", "webp"])
    if upload is None:
        st.info("Upload a road image, or switch to the examples in the sidebar.")
        st.stop()
    try:
        image = service.decode_image(upload.getvalue())
    except service.InputError as error:
        st.error(f"This file cannot be used: {error}")
        st.stop()
else:
    frame = st.sidebar.selectbox("Example", example_frames())
    image, ground_truth = load_example(frame)

# ------------------------------------------------------------------ main
detect_tab, results_tab, about_tab = st.tabs(["Detection", "Test results", "About"])

with detect_tab:
    if not chosen:
        st.warning("Choose at least one model in the sidebar.")
        st.stop()
    top = st.columns(2 if ground_truth is not None else 1)
    top[0].image(image, caption="Input image", width="stretch")
    if ground_truth is not None:
        top[1].image(service.overlay(image, ground_truth, color=(40, 220, 90)),
                     caption="Ground truth (annotation)", width="stretch")

    for name in chosen:
        with st.spinner(f"Running {titles[name]}…"):
            result, cam = service.explain(name, image) if show_xai else (service.analyse(name, image), None)
        stats = result["stats"]
        st.subheader(titles[name])
        m = st.columns(4)
        m[0].metric("Flagged area", f"{stats['anomaly_percent']:.1f} %")
        m[1].metric("Obstacle blobs", stats["blobs"])
        m[2].metric("Peak score", f"{stats['max_score']:.2f}", help=f"threshold {stats['threshold']:.3f} (chosen on validation)")
        m[3].metric("Latency", f"{stats['latency_ms']:.0f} ms")
        cols = st.columns(3 if show_xai else 2)
        cols[0].image(service.overlay(result["image"], result["mask"]), caption="Predicted anomaly mask",
                      width="stretch")
        cols[1].image(service.heatmap_rgb(result["scores"]), caption="Score map (probability or reconstruction error)",
                      width="stretch")
        if show_xai:
            cols[2].image(service.blend(result["image"], service.heatmap_rgb(cam, "jet")),
                          caption="Grad-CAM of the predicted region", width="stretch")
    st.caption("A score map shows *where* a model reacts; a Grad-CAM heatmap shows what drives that region. "
               "Neither is a causal proof, and neither replaces the segmentation metrics.")

with results_tab:
    summary = RESULTS / "test_summary.csv"
    if summary.exists():
        st.markdown("Frozen test split (9 images), evaluated once in `notebooks/5_Evaluation.ipynb`.")
        st.dataframe(pd.read_csv(summary, index_col=0), width="stretch")
        paired = RESULTS / "test_paired_differences.csv"
        if paired.exists():
            st.markdown("**Paired bootstrap differences** (a difference is established when its 95 % interval excludes 0):")
            st.dataframe(pd.read_csv(paired), width="stretch", hide_index=True)
    else:
        st.info("Run `notebooks/5_Evaluation.ipynb` to produce the test results.")

with about_tab:
    st.markdown("""
**Problem.** Perception networks trained on a closed list of classes miss unexpected obstacles (animals,
rocks, lost cargo). These models flag them **pixel by pixel** on RoadAnomaly (Lis et al., ICCV 2019).

**Three approaches** (one per binôme):
- **A · DeepLabV3+**: supervised segmentation, frozen ImageNet ResNet50 encoder + ASPP + decoder.
- **B · Autoencoders**: trained on normal road regions only; an obstacle is what they cannot reconstruct
  (pixel autoencoder baseline; feature-space autoencoder on frozen VGG16 features).
- **C · CNN + U-Net**: supervised segmentation (added when delivered).

**Limits.** 60 images in total, 9 test images: results are uncertain (see the intervals). Thresholds were chosen
on the validation split. This demo is a research prototype, not a safety system.
""")
