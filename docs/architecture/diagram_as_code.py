"""RoadAnomaly architecture as code: stack icons on a fixed grid, with explicit orthogonal connectors.

Renders docs/architecture/roadanomaly-stack.png (2160 x 2700, LinkedIn portrait 4:5) and roadanomaly-stack.html.
Graphviz (the `diagrams` library) chose its own routes, so lines wandered and crossed captions; here every container,
icon and connector has a fixed place, which keeps the diagram tidy and every arrow traceable:
- one container per CRISP-DM stage, all the same width and height, stacked top to bottom, titles in a left column;
- icons snap to five shared columns, captions under the icons;
- connectors are right angles with rounded corners; a dot marks every branch; no line crosses a caption or a title.

Run (needs Playwright with Chromium, e.g. `pip install playwright && playwright install chromium`):
    python docs/architecture/diagram_as_code.py
Icons: Python, FastAPI, Vercel, users and storage come from the `diagrams` package (MIT); Keras, Jupyter, Streamlit,
Astro and NVIDIA are Simple Icons (CC0) in their brand colours; the product uses the RoadAnomaly emblem.
"""
import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ICONS = HERE / "icons"
EMBLEM = HERE.parents[1] / "deployment" / "product" / "assets" / "emblem.png"
OUT = HERE / "roadanomaly-stack"
W, H, SCALE = 1080, 1350, 2          # logical canvas; PNG is 2160 x 2700 (12 px text -> 24 px)

PAPER, PANEL, RULE, INK, MUTED, ORANGE = "#FBF7EE", "#F3EAD6", "#DCD2BC", "#2D3A5A", "#55617D", "#EE6011"
FONT = "'Noto Sans', 'Lato', sans-serif"
REPO = "github.com/adriansalvadorekomo/RoadAnomaly-CRISPDM"
SUBTITLE = "Pixel-level detection of unexpected road obstacles · one shared Predictor behind every service"

# ------------------------------------------------------------------ grid
COLS = [290, 455, 620, 785, 950]     # icon centres (x): every icon snaps to one of these columns
ICON = 52                            # icon size
PANEL_X, PANEL_W, PANEL_H = 40, 1000, 150
ROWS = {                             # stage -> (panel top, title lines); all panels share width and height
    "data":       (110, ["Data", "CRISP-DM 1–3"]),
    "modeling":   (310, ["Modeling", "CRISP-DM 4", "TensorFlow · Keras"]),
    "core":       (510, ["Shared core", "one code path"]),
    "evaluation": (710, ["Evaluation & XAI", "CRISP-DM 5"]),
    "deployment": (910, ["Deployment", "CRISP-DM 6", "Docker Compose", "CPU TensorFlow image"]),
    "users":      (1110, ["Users & hosting"]),
}
ICON_OFFSET = 36                     # icon top inside its panel (room above for the fan-out bus)


def icon_top(row):
    return ROWS[row][0] + ICON_OFFSET


def icon_mid(row):
    return icon_top(row) + ICON // 2


def top_port(row):
    return icon_top(row) - 4


def bottom_port(row, lines=2):
    return icon_top(row) + ICON + 18 + 16 * lines - 6


# ------------------------------------------------------------------ nodes: (row, column, icon file, caption lines)
NODES = {
    "dataset":      ("data", 1, "storage", ["RoadAnomaly dataset", "60 photos · pixel masks"]),
    "gpu":          ("modeling", 0, "nvidia", ["NVIDIA RTX 4060", "~20 min, all models"]),
    "notebooks":    ("modeling", 1, "jupyter", ["Jupyter notebooks", "42 / 9 / 9 split"]),
    "model_a":      ("modeling", 2, "keras", ["A · DeepLabV3+", "ResNet50 encoder"]),
    "model_b":      ("modeling", 3, "keras", ["B · Autoencoder", "on VGG16 features"]),
    "model_c":      ("modeling", 4, "keras", ["C · CNN & U-Nets", "3 segmentation nets"]),
    "artifacts":    ("core", 1, "storage", ["models/<name>/", "model.keras + config"]),
    "predictor":    ("core", 3, "python", ["Predictor", "scores → threshold → mask"]),
    "evaluation":   ("evaluation", 0, "jupyter", ["Test split, opened once", "20/22 obstacles · F1 0.74"]),
    "explanations": ("evaluation", 2, "python", ["Explanations", "Grad-CAM++ · exact SHAP"]),
    "landing":      ("deployment", 0, "astro", ["Landing page", "Astro · :4321 local"]),
    "demo":         ("deployment", 1, "streamlit", ["Technical demo", "Streamlit :8501"]),
    "api":          ("deployment", 2, "fastapi", ["FastAPI :8000", "/predict · /explain"]),
    "product":      ("deployment", 4, "emblem", ["Product MVP :8502", "2 modes · 3 plans"]),
    "hosting":      ("users", 0, "vercel", ["Vercel", "hosts the landing page"]),
    "integrators":  ("users", 2, "users", ["Integrators", "call the API"]),
    "clients":      ("users", 4, "users", ["Clients", "ADAS startups · labs"]),
}

# ------------------------------------------------------------------ connectors
A, B, C, D, E = COLS
fan_bus = ROWS["modeling"][0] + 18          # notebooks -> A, B, C: bus inside the modeling panel, above the icons
save_bus = ROWS["core"][0] - 22             # A, B, C -> artifacts: bus between the two panels
pred_bus = ROWS["evaluation"][0] - 30       # predictor -> test split, explanations, demo
client_lane = ROWS["evaluation"][0] - 46    # predictor -> product: turn towards the product column
api_lane = ROWS["deployment"][0] - 22       # predictor -> API: turn above the deployment panel
demo_lane = ROWS["deployment"][0] - 36      # explanations -> demo
core_bottom, eval_bottom, deploy_bottom = bottom_port("core"), bottom_port("evaluation"), bottom_port("deployment")
cy_model, cy_core = icon_mid("modeling"), icon_mid("core")

EDGES = [
    # build time (dashed): data, training, saving, publishing
    {"pts": [(B, bottom_port("data")), (B, top_port("modeling"))], "dash": True},
    {"pts": [(A + 34, cy_model), (B - 34, cy_model)], "dash": True,
     "label": ("trains", (A + B) / 2, cy_model - 10, "middle")},
    {"pts": [(B + 34, cy_model), (536, cy_model), (536, fan_bus), (E, fan_bus), (E, top_port("modeling"))],
     "dash": True},
    {"pts": [(C, fan_bus), (C, top_port("modeling"))], "dot": (C, fan_bus), "dash": True},
    {"pts": [(D, fan_bus), (D, top_port("modeling"))], "dot": (D, fan_bus), "dash": True},
    {"pts": [(C, bottom_port("modeling")), (C, save_bus)], "head": False, "dash": True},
    {"pts": [(D, bottom_port("modeling")), (D, save_bus)], "head": False, "dash": True},
    {"pts": [(E, bottom_port("modeling")), (E, save_bus), (B, save_bus), (B, top_port("core"))], "dash": True,
     "dots": [(C, save_bus), (D, save_bus)], "label": ("save", (B + C) / 2, save_bus - 8, "middle")},
    # runtime (solid): the shared core
    {"pts": [(B + 34, cy_core), (D - 34, cy_core)], "label": ("load", (B + D) / 2, cy_core - 10, "middle")},
    # predictor -> evaluation row, and the demo through the free column
    {"pts": [(D - 18, core_bottom), (D - 18, pred_bus), (A, pred_bus), (A, top_port("evaluation"))],
     "label": ("test set, once", A + 8, pred_bus + 20, "start")},
    {"pts": [(C, pred_bus), (C, top_port("evaluation"))], "dot": (C, pred_bus),
     "label": ("validation, 9 photos", C + 8, pred_bus + 20, "start")},
    {"pts": [(B - 20, pred_bus), (B - 20, top_port("deployment"))], "dot": (B - 20, pred_bus)},
    # predictor -> API (straight down the free column) and -> product (client path)
    {"pts": [(D, core_bottom), (D, api_lane), (C + 14, api_lane), (C + 14, top_port("deployment"))]},
    {"pts": [(D + 18, core_bottom), (D + 18, client_lane), (E, client_lane), (E, top_port("deployment"))],
     "color": ORANGE, "width": 2.6},
    # evaluation -> deployment
    {"pts": [(A, eval_bottom), (A, top_port("deployment"))], "dash": True,
     "label": ("results JSON", A + 8, demo_lane + 12, "start")},
    {"pts": [(C - 12, eval_bottom), (C - 12, top_port("deployment"))],
     "label": ("/explain", C - 20, api_lane + 16, "end")},
    {"pts": [(C - 24, eval_bottom), (C - 24, demo_lane), (B + 20, demo_lane), (B + 20, top_port("deployment"))],
     "dash": True},
    # deployment -> hosting (build time); users -> the services they use
    {"pts": [(A, deploy_bottom), (A, top_port("users"))], "dash": True,
     "label": ("deploy", A + 8, (deploy_bottom + top_port("users")) / 2 + 4, "start")},
    {"pts": [(C, top_port("users")), (C, deploy_bottom + 4)]},
    {"pts": [(E, top_port("users")), (E, deploy_bottom + 4)], "color": ORANGE, "width": 2.6},
]


# ------------------------------------------------------------------ SVG helpers
def sign(v):
    return (v > 0) - (v < 0)


def rounded_path(pts, r=10):
    """Orthogonal polyline with rounded corners (quadratic arcs of radius r)."""
    d = [f"M{pts[0][0]},{pts[0][1]}"]
    for (x0, y0), (x1, y1), (x2, y2) in zip(pts, pts[1:], pts[2:], strict=False):
        r1 = min(r, (abs(x1 - x0) + abs(y1 - y0)) / 2, (abs(x2 - x1) + abs(y2 - y1)) / 2)
        ax, ay = x1 - r1 * sign(x1 - x0), y1 - r1 * sign(y1 - y0)
        bx, by = x1 + r1 * sign(x2 - x1), y1 + r1 * sign(y2 - y1)
        d.append(f"L{ax},{ay} Q{x1},{y1} {bx},{by}")
    d.append(f"L{pts[-1][0]},{pts[-1][1]}")
    return " ".join(d)


def data_uri(name):
    path = EMBLEM if name == "emblem" else ICONS / f"{name}.png"
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def panels():
    out = []
    for top, title in ROWS.values():
        out.append(f'<rect x="{PANEL_X}" y="{top}" width="{PANEL_W}" height="{PANEL_H}" rx="14" fill="{PANEL}" '
                   f'stroke="{RULE}" stroke-width="1.2"/>')
        out.append(f'<line x1="196" y1="{top + 16}" x2="196" y2="{top + PANEL_H - 16}" '
                   f'stroke="{RULE}" stroke-width="1"/>')
        y = top + 36
        for i, line in enumerate(title):
            out.append(f'<text x="60" y="{y}" class="{"stage" if i == 0 else "stage-sub"}">{esc(line)}</text>')
            y += 24 if i == 0 else 18
    return out


def nodes():
    out = []
    for row, col, icon, caption in NODES.values():
        cx, top = COLS[col], icon_top(row)
        out.append(f'<image href="{data_uri(icon)}" x="{cx - ICON // 2}" y="{top}" width="{ICON}" height="{ICON}"/>')
        y = top + ICON + 18
        for i, line in enumerate(caption):
            css = "name" if i == 0 else "cap"
            out.append(f'<text x="{cx}" y="{y}" class="{css}" text-anchor="middle">{esc(line)}</text>')
            y += 16
    return out


def edges():
    lines, dots, labels = [], [], []
    for e in EDGES:
        colour = e.get("color", MUTED)
        marker = "" if e.get("head") is False else f' marker-end="url(#{"arrow-o" if colour == ORANGE else "arrow"})"'
        dash = ' stroke-dasharray="7,5"' if e.get("dash") else ""
        lines.append(f'<path d="{rounded_path(e["pts"])}" fill="none" stroke="{colour}" '
                     f'stroke-width="{e.get("width", 1.8)}"{dash}{marker}/>')
        for x, y in ([e["dot"]] if "dot" in e else []) + e.get("dots", []):
            dots.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{colour}"/>')
        if "label" in e:
            text, x, y, anchor = e["label"]
            labels.append(f'<text x="{x}" y="{y}" class="edge" text-anchor="{anchor}">{esc(text)}</text>')
    return lines + dots + labels


def legend():
    y, x, out = 1300, 60, []
    for text, colour, dash in [("runtime call", MUTED, ""), ("build-time hand-off", MUTED, ' stroke-dasharray="7,5"'),
                               ("client path", ORANGE, ""), ("branch", MUTED, None)]:
        if dash is None:
            out.append(f'<circle cx="{x + 18}" cy="{y - 4}" r="4" fill="{colour}"/>')
        else:
            out.append(f'<path d="M{x},{y - 4} H{x + 36}" stroke="{colour}" stroke-width="1.8" fill="none"{dash} '
                       f'marker-end="url(#{"arrow-o" if colour == ORANGE else "arrow"})"/>')
        out.append(f'<text x="{x + 46}" y="{y}" class="cap">{text}</text>')
        x += 46 + 7 * len(text) + 36
    out.append(f'<text x="{W - 40}" y="{y}" class="cap" text-anchor="end">{REPO}</text>')
    return out


def marker(marker_id, colour):
    """Arrowhead of a fixed size, whatever the line width."""
    return (f'<marker id="{marker_id}" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="9" refX="10" '
            f'refY="4.5" orient="auto"><path d="M0,0 L11,4.5 L0,9 Z" fill="{colour}"/></marker>')


def svg():
    body = "\n".join(panels() + edges() + nodes() + legend())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-labelledby="ra-stack-title ra-stack-desc">
  <title id="ra-stack-title">RoadAnomaly · from 60 road photos to a product</title>
  <desc id="ra-stack-desc">Architecture of RoadAnomaly by CRISP-DM stage: a 60-photo dataset is used in Jupyter
  notebooks to train three Keras model families on an RTX 4060; the saved models are loaded by one shared Predictor,
  which feeds the test evaluation, the explanations, the technical demo, the FastAPI service and the client
  product.</desc>
  <defs>
    {marker("arrow", MUTED)}
    {marker("arrow-o", ORANGE)}
  </defs>
  <style>
    text {{ font-family: {FONT}; fill: {INK}; }}
    .title {{ font-size: 28px; font-weight: 700; }}
    .subtitle {{ font-size: 14px; fill: {MUTED}; }}
    .stage {{ font-size: 15px; font-weight: 700; }}
    .stage-sub {{ font-size: 12px; fill: {MUTED}; }}
    .name {{ font-size: 12.5px; font-weight: 700; }}
    .cap {{ font-size: 12px; fill: {MUTED}; }}
    .edge {{ font-size: 12px; fill: {MUTED}; font-style: italic; }}
  </style>
  <rect width="{W}" height="{H}" fill="{PAPER}"/>
  <text x="{W / 2}" y="58" class="title" text-anchor="middle">RoadAnomaly · from 60 road photos to a product</text>
  <text x="{W / 2}" y="86" class="subtitle" text-anchor="middle">{SUBTITLE}</text>
{body}
</svg>'''


def main():
    html = (f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>RoadAnomaly · architecture</title></head>'
            f'<body style="margin:0;background:{PAPER}">{svg()}</body></html>')
    OUT.with_suffix(".html").write_text(html)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=SCALE)
        page.goto(OUT.with_suffix(".html").as_uri())
        page.evaluate("document.fonts.ready")
        page.locator("svg").screenshot(path=str(OUT.with_suffix(".png")))
        browser.close()
    print(f"{OUT.with_suffix('.png').name}: {W * SCALE}x{H * SCALE}, smallest text {12 * SCALE} px")


if __name__ == "__main__":
    main()
