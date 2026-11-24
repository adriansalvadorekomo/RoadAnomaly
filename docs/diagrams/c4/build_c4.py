"""Draw the C4 diagrams of RoadAnomaly (docs/diagrams/c4/*.svg).

Four views, each in a light and a dark theme:
  c4-context     C4 level 1: who uses the system, what it depends on
  c4-container   C4 level 2: the Docker Compose stack and where its models come from
  c4-component   C4 level 3: the one inference path every front end shares
  c4-pipeline    the CRISP-DM path from the photographs to the reported results

Every element comes from the files at the commit it ships with: deployment/ (docker-compose.yml,
Dockerfiles, service.py, api/, app/, product/, landing/), src/roadanomaly/, scripts/ and the
notebooks. Drawing kit: c4kit.py (same engine as the Episteme diagrams).

    uv run --no-project --with fonttools --with brotli python docs/diagrams/c4/build_c4.py [--png]
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from c4kit import Box, Canvas, View, build  # noqa: E402

READOUT = [("MODELS", "6 · 3 approaches"), ("TEST SPLIT", "9 photos · 22 obstacles"), ("TESTS", "75 · pytest")]


# ── C4 level 1 · context ───────────────────────────────────────────────────
def context_view(cv: Canvas):
    analyst = Box(32, 184, 208, 112)
    jury = Box(32, 328, 208, 112)
    team = Box(32, 472, 208, 112)
    system = Box(376, 184, 512, 400)
    ext_x, ext_w = 1032, 216
    dataset = Box(ext_x, 184, ext_w, 88)
    imagenet = Box(ext_x, 288, ext_w, 88)
    vercel = Box(ext_x, 392, ext_w, 88)
    hub = Box(ext_x, 496, ext_w, 88)

    cv.arrow([(analyst.r, analyst.cy), (system.x, analyst.cy)])
    cv.label([("checks photos", False), ("product · :8502", True)], 308, analyst.cy - 34)
    cv.arrow([(jury.r, jury.cy), (system.x, jury.cy)])
    cv.label([("compares models", False), ("demo · landing", True)], 308, jury.cy - 34)
    cv.arrow([(team.r, team.cy), (system.x, team.cy)])
    cv.label([("trains, evaluates", False), ("notebooks · GPU", True)], 308, team.cy - 34)

    for ext, line1, line2 in [(dataset, "reads", "data/raw"), (imagenet, "downloads once", "keras.applications"),
                              (vercel, "landing deployed", "landing:deploy"), (hub, "images pushed", "twelvy1400/*")]:
        cv.arrow([(system.r, ext.cy), (ext.x, ext.cy)])
        cv.label([(line1, False), (line2, True)], 960, ext.cy - 34)

    cv.node(analyst, "person", "Person", "Road-safety analyst", None, ["Uploads road photos,", "reads the warnings"],
            ["user"])
    cv.node(jury, "person", "Person", "Reviewer", None, ["Compares the six models", "and their explanations"],
            ["user"])
    cv.node(team, "person", "Person", "Data scientists", None, ["Six students, three", "pairs (A, B, C)"], ["user"])
    cv.node(system, "container", "Software system", "RoadAnomaly", "TensorFlow · Keras · FastAPI · Streamlit",
            ["Marks, pixel by pixel, what a road camera did not", "expect: animals, rocks, cones, lost loads.", "",
             "Six models from three approaches, trained on 42", "photographs, chosen on 9, judged once on 9 sealed",
             "test photographs (22 obstacles).", "",
             "Every warning is explained twice: Grad-CAM++", "(where) and exact SHAP over five factors (what)."],
            ["tensorflow", "keras", "fastapi", "streamlit"], focal=True)
    cv.node(dataset, "external", "External", "RoadAnomaly dataset", "Lis et al. · ICCV 2019", [], ["folder"])
    cv.node(imagenet, "external", "External", "ImageNet weights", "ResNet50 · VGG16", [], ["keras"])
    cv.node(vercel, "external", "External", "Vercel", "static landing page", [], ["vercel"])
    cv.node(hub, "external", "External", "Docker Hub", "roadanomaly, -landing", [], ["docker"])

    cv.readout(READOUT, 1248, 96)
    cv.legend(632, [("person", "person"), ("focal", "the system"), ("external", "external system"),
                    ("call", "uses")])


# ── C4 level 2 · containers ────────────────────────────────────────────────
def container_view(cv: Canvas):
    w = 248
    xs = [32, 392, 696, 1000]  # API, product, demo, landing (a wider gap before the product for the label)
    integrator = Box(xs[0], 168, w, 96)
    analyst = Box(xs[1], 168, w, 96)
    jury = Box(xs[2], 168, w, 96)
    ra, rb = 352, 568
    api = Box(xs[0], ra, w, 128)
    product = Box(xs[1], ra, w, 128)
    demo = Box(xs[2], ra, w, 128)
    landing = Box(xs[3], ra, w, 128)
    models = Box(32, rb, 912, 128)
    results = Box(xs[3], rb, w, 128)
    notebooks = Box(32, 792, 560, 128)

    cv.zone(Box(16, 312, 1248, 424), "ROADANOMALY", "docker compose · deployment/", at="bottom", lx=560)

    cv.arrow([(integrator.cx, integrator.b), (integrator.cx, api.y)])
    cv.label([("POST /predict, /explain", False)], integrator.cx + 12, 292, "start")
    cv.arrow([(analyst.cx, analyst.b), (analyst.cx, product.y)])
    cv.label([("browser · :8502", True)], analyst.cx + 12, 292, "start")
    cv.arrow([(jury.cx, jury.b), (jury.cx, demo.y)])
    cv.label([("browser · :8501", True)], jury.cx + 12, 292, "start")
    cv.arrow([(jury.r, 216), (landing.cx, 216), (landing.cx, landing.y)])
    cv.label([(":4321", True)], landing.cx + 12, 292, "start")
    cv.arrow([(product.x, 448), (api.r, 448)], dashed=True)
    cv.label([("status", False), ("GET /health", True)], 336, 414)

    for b in (api, product, demo):
        cv.arrow([(b.cx, b.b), (b.cx, models.y)])
    cv.label([("load once, read-only", False)], api.cx + 12, 532, "start")
    cv.arrow([(landing.cx, landing.b), (landing.cx, results.y)], dashed=True)
    cv.label([("at build", False)], landing.cx + 12, 532, "start")

    cv.arrow([(312, notebooks.y), (312, models.b)])
    cv.label([("save_artifact", True)], 324, 768, "start")
    cv.arrow([(notebooks.r, 856), (results.cx, 856), (results.cx, results.b)])
    cv.label([("notebooks 5 and 6 write", False), ("test + XAI JSON", True)], 808, 822)

    cv.node(integrator, "person", "Person", "Integrator", None, ["A customer's own system"], ["user"])
    cv.node(analyst, "person", "Person", "Road-safety analyst", None, ["The product, in French"], ["user"])
    cv.node(jury, "person", "Person", "Reviewer", None, ["Demo and landing page"], ["user"])
    cv.node(api, "container", "Container", "API", "FastAPI · :8000",
            ["/health, /models,", "/predict, /explain"], ["fastapi"])
    cv.node(product, "container", "Container", "Product", "Streamlit · :8502",
            ["Two modes, reports,", "plans; customer MVP"], ["streamlit"])
    cv.node(demo, "container", "Container", "Technical demo", "Streamlit · :8501",
            ["Six models side by side,", "explain, compare"], ["streamlit"])
    cv.node(landing, "container", "Container", "Landing page", "Astro · nginx · :4321",
            ["Static; also served", "by Vercel"], ["astro", "nginx"])
    cv.node(models, "store", "Data store", "Trained models", "models/<name>/ · mounted read-only",
            ["One folder per model: model.keras and config.json (input size, post-processing,",
             "the threshold chosen on validation). API, demo and product load the same folders."],
            ["keras"], focal=True)
    cv.node(results, "store", "Data store", "Results", "reports/results/",
            ["Test and XAI JSON,", "baked into both images"], ["file"])
    cv.node(notebooks, "container", "Container · outside compose", "Notebooks and scripts",
            "Jupyter · TensorFlow 2.20 · RTX 4060",
            ["Train on 42 photos, choose on 9, judge once", "on 9; export the landing's score maps"],
            ["jupyter", "nvidia"])

    cv.readout(READOUT, 1248, 96)
    cv.legend(960, [("person", "person"), ("container", "container"), ("focal", "the one model format"),
                    ("store", "data store"), ("call", "call / read / write"), ("occasional", "occasional")])


# ── C4 level 3 · the shared inference path ─────────────────────────────────
def component_view(cv: Canvas):
    cols = [32, 280, 528, 776, 1024]  # five columns, 224 wide, 24 apart
    w = 224
    entries = [("API", "deployment/api", [], ["fastapi"]),
               ("Technical demo", "deployment/app", [], ["streamlit"]),
               ("Product", "deployment/product", [], ["streamlit"]),
               ("Video script", "scripts/infer_video.py", [], ["python"]),
               ("Notebook 5", "+ landing export", [], ["jupyter"])]
    service = Box(32, 360, 968, 128)
    xai = Box(32, 568, 416, 128)
    predictor = Box(528, 568, 472, 128)
    post = Box(528, 776, 344, 128)
    models = Box(1024, 776, 224, 128)

    cv.zone(Box(16, 336, 1000, 592), "ONE CODE PATH", "deployment/service.py + src/roadanomaly", at="bottom",
            lx=176)

    for x in cols[:4]:
        cv.arrow([(x + w / 2, 264), (x + w / 2, service.y)])
    cv.label([("analyse, explain", False)], cols[0] + w / 2 + 12, 300, "start")
    nb_x = cols[4] + w / 2
    cv.arrow([(nb_x, 264), (nb_x, 632), (predictor.r, 632)])
    cv.label([("calls the", False), ("Predictor", True)], nb_x + 12, 300, "start")

    cv.arrow([(256, service.b), (256, xai.y)])
    cv.label([("explain", False)], 268, 532, "start")
    cv.arrow([(764, service.b), (764, predictor.y)])
    cv.label([("predict", False)], 776, 532, "start")
    cv.arrow([(xai.r, 632), (predictor.x, 632)])
    cv.label([("scores", False)], 488, 616)
    cv.arrow([(700, predictor.b), (700, post.y)])
    cv.label([("score map → mask", False)], 712, 740, "start")
    cv.arrow([(940, predictor.b), (940, 840), (models.x, 840)])
    cv.label([("reads", False)], 952, 740, "start")

    for x, (title, tech, desc, logos) in zip(cols, entries, strict=True):
        cv.node(Box(x, 168, w, 96), "container", "Entry point", title, tech, desc, logos)
    cv.node(service, "container", "Component", "Inference service", "deployment/service.py",
            ["Checks uploads (15 MB, 8,000 px), loads each model once and warms it up, then adds what an",
             "interface needs: overlays, per-image statistics, the paired explanation and the latency."],
            ["python"])
    cv.node(xai, "container", "Component", "Explanations", "roadanomaly/xai.py",
            ["Grad-CAM++ (where) and exact SHAP over five", "factors, all 2⁵ = 32 combinations (what)"],
            ["tensorflow"])
    cv.node(predictor, "container", "Component", "Predictor", "roadanomaly/inference.py",
            ["Any model folder → raw score map. The same code", "for notebook 5, the API and both apps"],
            ["keras"], focal=True)
    cv.node(post, "container", "Component", "Post-processing", "roadanomaly/postprocessing.py",
            ["Upsample, smooth, z-score,", "threshold, minimum blob"], ["numpy"])
    cv.node(models, "store", "Data store", "Model folders", "models/<name>/",
            ["model.keras,", "config.json"], ["keras"])

    cv.readout([("CONSUMERS", "5"), ("API ROUTES", "4"), ("LATENCY", "13–48 ms · RTX 4060")], 1248, 96)
    cv.legend(960, [("container", "component"), ("focal", "the single inference path"),
                    ("store", "data store"), ("call", "call / read")])


# ── the CRISP-DM pipeline, photographs to results ──────────────────────────
def pipeline_view(cv: Canvas):
    w = 248
    xs = [32, 354, 676, 1000]
    r1, r2 = 200, 456
    raw = Box(xs[0], r1, w, 128)
    split = Box(xs[1], r1, w, 128)
    modeling = Box(xs[2], r1, w, 128)
    models = Box(xs[3], r1, w, 128)
    nb5 = Box(xs[0], r2, w, 128)
    results = Box(xs[1], r2, w, 128)
    nb6 = Box(xs[2], r2, w, 128)
    readers = Box(xs[3], r2, w, 128)

    cv.arrow([(raw.r, 264), (split.x, 264)])
    cv.arrow([(split.r, 264), (modeling.x, 264)])
    cv.arrow([(modeling.r, 264), (models.x, 264)])
    cv.arrow([(models.cx, models.b), (models.cx, 392), (nb5.cx, 392), (nb5.cx, nb5.y)])
    cv.label([("every model, once", False)], 640, 380)
    cv.arrow([(1184, models.b), (1184, 424), (nb6.cx, 424), (nb6.cx, nb6.y)])  # right of the branch: no crossing
    cv.arrow([(nb5.r, 520), (results.x, 520)])
    cv.arrow([(nb6.x, 520), (results.r, 520)])
    cv.arrow([(results.cx, results.b), (results.cx, 624), (readers.cx, 624), (readers.cx, readers.b)])
    cv.label([("read at build or start", False)], 800, 648)

    cv.node(raw, "store", "Data store", "Photographs", "data/raw · 60 + masks",
            ["RoadAnomaly, ICCV 2019;", "credits.txt per photo"], ["folder"])
    cv.node(split, "container", "Notebook 3", "Frozen split", "splits/split_manifest.csv",
            ["42 · 9 · 9, group-aware;", "rebuilt and checked"], ["jupyter"])
    cv.node(modeling, "container", "Notebooks 4A · 4B · 4C", "Six models", "train and validation only",
            ["Threshold and early stop", "chosen on validation"], ["tensorflow"])
    cv.node(models, "store", "Data store", "Model folders", "inference.save_artifact",
            ["model.keras and config.json", "per model"], ["keras"])
    cv.node(nb5, "container", "Notebook 5", "Evaluation", "the only use of the test split",
            ["Opens 9 test photos once;", "bootstrap intervals"], ["jupyter"], focal=True)
    cv.node(results, "store", "Data store", "Results", "reports/results/",
            ["test_results.json,", "xai_summary.json"], ["file"])
    cv.node(nb6, "container", "Notebook 6", "Explanations", "Grad-CAM++ · exact SHAP",
            ["Faithfulness checked by", "deletion and insertion"], ["jupyter"])
    cv.node(readers, "external", "Readers", "Landing, product, demo", "the numbers they quote",
            ["Never typed by hand:", "read from the JSON"], ["astro", "streamlit"])

    cv.readout([("TRAIN · VAL · TEST", "42 · 9 · 9"), ("TRAINING", "≈ 20 min · RTX 4060"),
                ("TEST LOOKS", "1 · notebook 5")], 1248, 96)
    cv.legend(704, [("container", "notebook"), ("focal", "the sealed test"), ("store", "file or folder"),
                    ("external", "reader"), ("call", "data flow")])


VIEWS = [
    View("context", context_view, 1280, 740, "c4 model · level 1 · system context", "RoadAnomaly",
         "unexpected road obstacles, pixel by pixel, with an explanation",
         "RoadAnomaly — C4 system context",
         "C4 context diagram: a road-safety analyst checks photos in the product, a reviewer compares the models in "
         "the demo and on the landing page, and the six data scientists train and evaluate them in notebooks. "
         "RoadAnomaly reads the vendored RoadAnomaly dataset, downloads ImageNet weights once, deploys its static "
         "landing page to Vercel and pushes its images to Docker Hub."),
    View("container", container_view, 1280, 1040, "c4 model · level 2 · containers", "The Compose stack",
         "four services, one model format, models trained outside the stack",
         "RoadAnomaly — C4 container view",
         "C4 container diagram: in the Compose stack an integrator calls the FastAPI service, the analyst uses the "
         "Streamlit product and the reviewer the Streamlit demo and the static Astro landing page. The API, the "
         "product and the demo each load the same trained-model folders, mounted read-only; the product only asks "
         "the API for its health. The landing page reads the results JSON at build time. Outside the stack, the "
         "notebooks write the model folders with save_artifact and the results JSON."),
    View("component", component_view, 1280, 1040, "c4 model · level 3 · inference path", "One code path",
         "every front end reaches the models through the same Predictor",
         "RoadAnomaly — C4 component view of the inference path",
         "C4 component diagram: the API, the technical demo, the product and the video script call the inference "
         "service, which checks uploads, caches models and adds overlays and statistics; notebook 5 and the "
         "landing export use the Predictor directly. The service asks the explanation module for Grad-CAM++ and "
         "exact SHAP, both of which score through the Predictor; the Predictor reads a model folder and hands its "
         "score map to post-processing, which returns the mask."),
    View("pipeline", pipeline_view, 1280, 800, "crisp-dm · data to results", "From photographs to results",
         "the test split is opened once, in notebook 5",
         "RoadAnomaly — the CRISP-DM pipeline",
         "Pipeline diagram: 60 photographs and masks go through the frozen group-aware split (42 train, 9 "
         "validation, 9 test) into notebooks 4A, 4B and 4C, which train six models on train and validation only "
         "and save one folder per model. Notebook 5 opens the test split once and writes test_results.json; "
         "notebook 6 explains every model and writes xai_summary.json. The landing page, the product and the demo "
         "read their numbers from those files."),
]

if __name__ == "__main__":
    build(HERE, "RoadAnomaly", VIEWS)
