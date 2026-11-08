"""RoadAnomaly demo (Streamlit).

Upload a road photograph or pick a validation example, see what each model flags, and ask any model to
explain itself with the paired method of notebook 6: WHERE (Grad-CAM++ / Grad-CAM) and WHAT (exact
Shapley values over five image factors). Run: `mise run app` (or `streamlit run deployment/app/streamlit_app.py`).
The demo calls the same inference service as the API (deployment/service.py).
"""
import json
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # make `deployment` importable
from deployment import service  # noqa: E402
from roadanomaly import data_pipeline as dp  # noqa: E402
from roadanomaly import xai

RESULTS = dp.REPO_ROOT / "reports" / "results"
TEAL, RED, INK, MUTED = "#0d7480", "#e5484d", "#1f3038", "#5d6b72"
METHODS = {"Grad-CAM++": "gradcam++", "Grad-CAM": "gradcam"}

st.set_page_config(page_title="RoadAnomaly · find the unexpected on the road", page_icon="▲", layout="wide",
                   initial_sidebar_state="expanded")

# A few rules the theme cannot express: tighter page, quieter image captions, numbered factor chips
st.markdown("""
<style>
  .block-container { padding-top: 2.2rem; max-width: 1320px; }
  [data-testid="stImageCaption"] { font-size: 0.85rem; color: #5d6b72; }
  .ra-kicker { color: #5d6b72; font-size: 0.95rem; margin: -0.6rem 0 1.2rem; }
  .ra-note { color: #5d6b72; font-size: 0.85rem; }
  .ra-check { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px; background: #e6f2f3; color: #0a5d67;
              font-size: 0.85rem; font-variant-numeric: tabular-nums; }
  /* the dark sidebar: the selected segment is filled, teal on slate would be unreadable */
  [data-testid="stSidebar"] button[data-variant="segmented_control"][aria-checked="true"] {
    background: #0d7480; color: #ffffff; border-color: #0d7480; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data, cached
@st.cache_data(show_spinner=False)
def examples():
    """Openly licensed validation photographs (the test split stays out of the demo)."""
    demo_json = dp.REPO_ROOT / "deployment" / "landing" / "public" / "demo" / "demo.json"
    titles = {i["frame"]: i["title"] for i in json.loads(demo_json.read_text())["images"]} if demo_json.exists() else {}
    frames = [row["frame"] for row in dp.read_manifest() if row["split"] == "val"]
    return {f: titles.get(f, f.split("_", 1)[-1].replace("_", " ")) for f in frames}


@st.cache_data(show_spinner=False)
def load_example(frame):
    image, mask = dp.load_frame(frame)
    return image, mask.astype(bool)


@st.cache_data(show_spinner=False, max_entries=64)
def analysed(name, image):
    result = service.analyse(name, image)
    return {k: result[k] for k in ("image", "mask", "scores", "stats")}


@st.cache_data(show_spinner=False, max_entries=64)
def explained(name, image, method):
    result, e = service.explain(name, image, method=method)
    return result["image"], {k: e[k] for k in ("region", "where", "where_method", "what", "sentence")}


def display_name(name):
    """'DeepLabV3+', 'Feature autoencoder', 'CNN baseline': the short name, first letter up, acronyms kept."""
    short = service.SHORT_NAMES.get(name, name).removeprefix("The ")
    return short[:1].upper() + short[1:]


def model_title(name):
    return f"{service.model_info(name)['binome']} · {display_name(name)}"


def signed(x, digits=3):
    """A number with a true minus sign (U+2212), as in print."""
    return f"{x:.{digits}f}".replace("-", "−")


def gap_text(gap):
    return "0" if gap == 0 else f"{gap:.0e}".replace("e-", "e−")


def latency(ms):
    return f"{ms:.0f} ms" if ms < 1000 else f"{ms / 1000:.1f} s"


def shap_chart(what, step=40):
    """Horizontal bars of the exact Shapley values; teal raises the anomaly score, red lowers it."""
    df = pd.DataFrame(
        [
            {"factor": xai.FACTOR_LABELS[f], "value": v, "effect": "raises the score" if v >= 0 else "lowers the score"}
            for f, v in what["phi"].items()
        ]
    )
    order = df.reindex(df["value"].abs().sort_values(ascending=False).index)["factor"].tolist()
    bars = alt.Chart(df).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X("value:Q", title="contribution to the score (Shapley value)"),
        y=alt.Y("factor:N", sort=order, title=None, axis=alt.Axis(labelFontSize=13, labelLimit=220)),
        color=alt.Color("effect:N", scale=alt.Scale(domain=["raises the score", "lowers the score"], range=[TEAL, RED]),
                        legend=alt.Legend(orient="bottom", title=None)),
        tooltip=[alt.Tooltip("factor:N"), alt.Tooltip("value:Q", format="+.3f")],
    )
    rule = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=INK).encode(x="x:Q")
    return (bars + rule).properties(height=alt.Step(step))


# the key test metrics and their column labels
# (the full names are in the help tooltips and in the "All test metrics" table)
KEY_METRICS = {
    "AuPRC (main)": "AuPRC",
    "AUROC": "AUROC",
    "F1 = Dice (per-image mean)": "F1",
    "IoU (per-image mean)": "IoU",
    "FPR95 (lower is better)": "FPR95 ↓",
    "Boundary IoU (15 px band)": "Boundary IoU",
    "objects detected": "Obstacles found",
    "false alarms / predicted blobs": "False alarms",
}
METRIC_HELP = {
    "AuPRC (main)": "area under the pixel precision-recall curve; the main score (obstacles are 9 % of pixels)",
    "FPR95 (lower is better)": "false-positive rate at 95 % pixel recall",
    "objects detected": "annotated obstacles with at least half of their pixels flagged",
    "false alarms / predicted blobs": "predicted blobs with less than half of their pixels on an obstacle",
}
# the landing page's light teal ramp (at most 55 % teal), so the slate text stays readable on every cell
SHARE_CMAP = LinearSegmentedColormap.from_list("teal", ["#f7f9fa", "#76b0b7"])


def test_table(path):
    """test_summary.csv (metrics x model titles) -> models as rows, labelled like the rest of the demo."""
    raw = pd.read_csv(path, index_col=0)
    results = RESULTS / "test_results.json"
    titles = {m["title"]: n for n, m in json.loads(results.read_text())["models"].items()} if results.exists() else {}
    raw.columns = [model_title(titles[c]) if titles.get(c) in names else c for c in raw.columns]
    table = raw.T
    for column in table.columns:  # "20/22"-style counts stay text, every other metric becomes a float
        numbers = pd.to_numeric(table[column], errors="coerce")
        table[column] = numbers if numbers.notna().all() else table[column]
    return table


# ------------------------------------------------------------------ sidebar
names = service.model_names()
with st.sidebar:
    st.markdown("### ▲ RoadAnomaly")
    st.caption("Pixel-level detection of unexpected obstacles on the road. ESPRIT Deep Learning, CRISP-DM.")
    if not names:
        st.error("No trained model in `models/`. Run the modeling notebooks (`mise run pipeline`) first.")
        st.stop()
    st.markdown("**Photograph**")
    source = st.segmented_control("Source", ["Example", "Upload"], default="Example", label_visibility="collapsed")
    ground_truth, label = None, None
    if source == "Upload":
        upload = st.file_uploader("Road photograph", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
        if upload is not None:
            try:
                image = service.decode_image(upload.getvalue())
                label = upload.name
            except service.InputError as error:
                st.error(f"This file cannot be used: {error}")
                st.stop()
    else:
        ex = examples()
        frame = st.selectbox("Validation example", list(ex), format_func=ex.get)
        image, ground_truth = load_example(frame)
        label = ex[frame]
    st.markdown("**Models**")
    chosen = st.multiselect("Models", names, default=names, format_func=display_name, label_visibility="collapsed")
    st.markdown("**Explanation**")
    method_label = st.segmented_control(
        "Where method",
        list(METHODS),
        default="Grad-CAM++",
        help="Grad-CAM++ localises several objects and whole objects better; Grad-CAM is the classic.",
    )
    method = METHODS[method_label or "Grad-CAM++"]
    st.divider()
    st.caption("Explanations describe a model; they are not causal proof and never replace the test metrics.")

if source == "Upload" and label is None:
    st.title("Find the unexpected on the road")
    st.markdown(
        '<p class="ra-kicker">Upload a road photograph in the sidebar, or switch back to the examples.</p>',
        unsafe_allow_html=True,
    )
    st.stop()
if not chosen:
    st.warning("Choose at least one model in the sidebar.")
    st.stop()

# ------------------------------------------------------------------ header
st.title("Find the unexpected on the road")
st.markdown(
    f'<p class="ra-kicker">{len(chosen)} of {len(names)} models on <b>{label}</b>. '
    f"Each model marks the pixels it did not expect; ask any of them why in the Explain tab.</p>",
    unsafe_allow_html=True,
)

detect_tab, explain_tab, compare_tab, results_tab, method_tab = st.tabs(
    ["Detect", "Explain", "Compare", "Test results", "Method"])

# ------------------------------------------------------------------ DETECT
with detect_tab:
    left, right = st.columns(2, gap="medium")
    left.image(image, caption="Input photograph", width="stretch")
    if ground_truth is not None:
        right.image(
            service.overlay(image, ground_truth, color=(47, 211, 196)), caption="Human annotation", width="stretch"
        )
    else:
        right.info("Uploaded photographs have no annotation: compare the models with each other instead.")
    for row in range(0, len(chosen), 2):
        cols = st.columns(2, gap="medium")
        for col, name in zip(cols, chosen[row:row + 2], strict=False):
            with col.container(border=True):
                with st.spinner(f"Running {model_title(name)}…"):
                    r = analysed(name, image)
                s = r["stats"]
                st.markdown(f"**{model_title(name)}**")
                st.image(service.overlay(r["image"], r["mask"]), width="stretch")
                m = st.columns(4)
                m[0].metric("Flagged", f"{s['anomaly_percent']:.1f} %")
                m[1].metric("Blobs", s["blobs"])
                m[2].metric(
                    "Peak score", f"{s['max_score']:.2f}", help=f"Threshold {s['threshold']:.3f}, chosen on validation"
                )
                m[3].metric(
                    "Latency", latency(s["latency_ms"]), help="One forward pass on this machine, after a warm-up call"
                )

# ------------------------------------------------------------------ EXPLAIN
with explain_tab:
    st.markdown("Every explanation pairs two methods on the same target, the model's score on the region it flagged: "
                "**where** (a Grad-CAM family heatmap) and **what** (exact Shapley values over five image factors).")
    name = (
        st.pills("Model to explain", chosen, default=chosen[0], format_func=model_title, selection_mode="single")
        or chosen[0]
    )
    with st.spinner(f"Explaining {model_title(name)}: one gradient pass and 32 factor combinations…"):
        shown, e = explained(name, image, method)
    where_col, what_col = st.columns([1.05, 1], gap="large")
    with where_col:
        st.subheader("Where")
        st.image(service.blend(shown, service.heatmap_rgb(e["where"], "jet")), width="stretch",
                 caption=f"{method_label} of the score on the flagged region (outlined below)")
        st.image(service.overlay(shown, e["region"], color=(229, 72, 77), alpha=0.35), width="stretch",
                 caption="The flagged region every explanation targets")
    with what_col:
        st.subheader("What")
        st.altair_chart(shap_chart(e["what"]), width="stretch")
        st.success(e["sentence"])
        w = e["what"]
        st.markdown(
            f'<span class="ra-check">Exact: Σφ = {sum(w["phi"].values()):+.3f} = f(x) − f(all removed) '
            f"= {signed(w['full'])} − ({signed(w['base'])}) · gap {gap_text(w['efficiency_gap'])} · "
            f"{w['evaluations']} evaluations</span>",
            unsafe_allow_html=True,
        )
        with st.expander("How each factor is removed"):
            st.dataframe(pd.DataFrame([{"factor": xai.FACTOR_LABELS[f], "removed by": xai.FACTOR_REMOVAL[f],
                                        "Shapley value": round(w["phi"][f], 4)} for f in xai.FACTORS]),
                         hide_index=True, width="stretch")

# ------------------------------------------------------------------ COMPARE
with compare_tab:
    rows = []
    for name in chosen:
        s = analysed(name, image)["stats"]
        rows.append({"Model": model_title(name), "Flagged": s["anomaly_percent"], "Blobs": s["blobs"],
                     "Peak score": s["max_score"], "Threshold": s["threshold"], "Latency": s["latency_ms"]})
    st.subheader("Detection on this photograph")
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        column_config={
            "Flagged": st.column_config.ProgressColumn(
                "Flagged",
                format="%.1f %%",
                min_value=0,
                max_value=max(r["Flagged"] for r in rows) or 1,
                help="share of the image's pixels flagged as obstacle",
            ),
            "Peak score": st.column_config.NumberColumn(
                format="%.2f", help="anomaly probability (A, C) or reconstruction error (B)"
            ),
            "Threshold": st.column_config.NumberColumn(format="%.3f", help="chosen on the validation split"),
            "Latency": st.column_config.NumberColumn(format="%.0f ms", help="one forward pass, after a warm-up call"),
        },
    )
    st.subheader("What each model relies on, on this photograph")
    st.caption(
        "Share of each factor in the model's total Shapley attribution (units differ between models, shares do not)."
    )
    if st.button("Explain all selected models", type="primary"):
        st.session_state["compare_key"] = (label, tuple(chosen), method)
    if st.session_state.get("compare_key") == (label, tuple(chosen), method):
        share_rows = []
        progress = st.progress(0.0, text="Explaining…")
        for i, name in enumerate(chosen, start=1):
            _, e = explained(name, image, method)
            total = sum(abs(v) for v in e["what"]["phi"].values()) or 1.0
            share_rows += [{"model": model_title(name), "factor": xai.FACTOR_LABELS[f], "share": abs(v) / total}
                           for f, v in e["what"]["phi"].items()]
            progress.progress(i / len(chosen), text=f"Explained {i} of {len(chosen)} models")
        progress.empty()
        chart = alt.Chart(pd.DataFrame(share_rows)).mark_bar().encode(
            x=alt.X("share:Q", stack="normalize", title="share of the attribution", axis=alt.Axis(format="%")),
            y=alt.Y("model:N", title=None, axis=alt.Axis(labelFontSize=13, labelLimit=240)),
            color=alt.Color("factor:N", title=None, legend=alt.Legend(orient="bottom")),
            tooltip=["model", "factor", alt.Tooltip("share:Q", format=".0%")],
        ).properties(height=48 * len(chosen) + 40)
        st.altair_chart(chart, width="stretch")

# ------------------------------------------------------------------ TEST RESULTS
with results_tab:
    summary = RESULTS / "test_summary.csv"
    if summary.exists():
        st.markdown(
            "Frozen test split (9 photographs, 22 obstacles), evaluated once in `notebooks/5_Evaluation.ipynb`."
        )
        table = test_table(summary)
        key = [c for c in KEY_METRICS if c in table.columns]
        st.dataframe(
            table[key],
            width="stretch",
            column_config={
                c: st.column_config.NumberColumn(KEY_METRICS[c], format="%.3f", help=METRIC_HELP.get(c, c))
                if pd.api.types.is_float_dtype(table[c])
                else st.column_config.TextColumn(KEY_METRICS[c], help=METRIC_HELP.get(c, c))
                for c in key
            },
        )
        with st.expander("All test metrics"):
            # one column per model mixes scores and "20/22" counts, so the cells are shown as text
            st.dataframe(table.T.map(lambda v: f"{v:.3f}" if isinstance(v, float) else str(v)), width="stretch")
        paired = RESULTS / "test_paired_differences.csv"
        if paired.exists():
            with st.expander(
                "Paired bootstrap differences (a difference is established when its 95 % interval excludes 0)"
            ):
                diffs = pd.read_csv(paired)
                diffs["A - B"] = diffs["A - B"].map(lambda pair: " − ".join(display_name(n) for n in pair.split(" - ")))
                st.dataframe(diffs.rename(columns={"A - B": "Comparison"}), hide_index=True, width="stretch",
                             column_config={c: st.column_config.NumberColumn(format="%.3f")
                                            for c in ("mean difference", "95% low", "95% high")})
    xai_summary = RESULTS / "xai_summary.json"
    if xai_summary.exists():
        st.subheader("What each model relies on, over the validation split")
        data = json.loads(xai_summary.read_text())
        df = pd.DataFrame(data["shares"]).T.rename(columns={f: v["label"] for f, v in data["factors"].items()})
        df.index = [model_title(n) if n in names else n for n in df.index]
        st.caption("Mean share of each factor in the model's exact Shapley attribution, nine validation photographs "
                   "(notebooks/6_XAI.ipynb). The largest factor of each model is in bold.")
        st.dataframe(
            df.style.format("{:.0%}")
            .background_gradient(cmap=SHARE_CMAP, axis=None, vmin=0, vmax=0.6, text_color_threshold=0)
            .apply(lambda row: ["font-weight: 700" if v == row.max() else "" for v in row], axis=1),
            width="stretch",
        )
    if not summary.exists():
        st.info("Run `notebooks/5_Evaluation.ipynb` to produce the test results.")

# ------------------------------------------------------------------ METHOD
with method_tab:
    a, b = st.columns(2, gap="large")
    with a:
        st.subheader("Six models, three approaches")
        st.markdown("""
- **A · DeepLabV3+**: supervised segmentation, frozen ImageNet ResNet50 encoder, ASPP and decoder.
- **B · Autoencoders**: trained on normal road only; an obstacle is what they cannot rebuild
  (pixel autoencoder, and a feature-space autoencoder on frozen VGG16 features).
- **C · CNN and U-Nets**: supervised segmentation, from a simple encoder–decoder to a U-Net with an
  ImageNet ResNet50 encoder.

Thresholds were chosen on the validation split; the test split was opened once, for all models together.
""")
    with b:
        st.subheader("Two explanations, always together")
        st.markdown("""
- **Where — Grad-CAM++ / Grad-CAM**: the gradient of the model's score on the flagged region with respect to a decoder
  (segmentation) or bottleneck (autoencoder) layer, turned into a heatmap.
- **What — exact SHAP**: the same score is recomputed with every combination of five image factors removed
  (32 combinations), giving exact Shapley values that add up to the score change.
""")
        st.dataframe(
            pd.DataFrame([{"factor": xai.FACTOR_LABELS[f], "removed by": xai.FACTOR_REMOVAL[f]} for f in xai.FACTORS]),
            hide_index=True,
            width="stretch",
        )
    st.caption("Research prototype. 60 photographs in total, 9 for the test: results are uncertain, see the intervals.")
