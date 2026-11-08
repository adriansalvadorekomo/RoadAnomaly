"""From a model's mask to what a customer reads: numbered obstacles, an annotated image, a plain explanation, a report.

Pure functions (NumPy, Pillow, SciPy): no Streamlit and no TensorFlow, so they are tested on synthetic masks.
"""
import base64
import csv
import html
import io
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

from roadanomaly.metrics import EIGHT_CONNECTED

# Brand colours (sampled from the logo): orange marks the unexpected, navy the normal
ORANGE = (238, 96, 17)
NAVY = (45, 58, 90)

DISPLAY_SCALE = 2          # annotated images are drawn at twice the model resolution, so boxes and numbers stay sharp
BOX_WIDTH = 4
TAG_FONT_PX = 26
MASK_ALPHA = 0.45

# Where an obstacle sits in the photograph (fractions of the width / height of its centre)
LEFT_EDGE, RIGHT_EDGE = 1 / 3, 2 / 3
FOREGROUND_FROM, MIDDLE_FROM = 0.70, 0.45   # lower in a road photograph = closer to the camera

FACTOR_LABELS_FR = {
    "colour": "la couleur",
    "texture": "la texture fine",
    "contrast": "la luminosité et le contraste",
    "object": "l'obstacle lui-même",
    "context": "la scène autour",
}


@dataclass(frozen=True)
class Obstacle:
    number: int
    box: tuple[int, int, int, int]    # x0, y0, x1, y1 in model pixels (x1, y1 exclusive)
    area_percent: float               # share of the image
    position: str                     # e.g. "au centre, premier plan"


def position_words(cx, cy):
    """Centre of an obstacle (fractions of width and height) -> where it is, in words."""
    side = "à gauche" if cx < LEFT_EDGE else "à droite" if cx > RIGHT_EDGE else "au centre"
    depth = "premier plan" if cy >= FOREGROUND_FROM else "mi-distance" if cy >= MIDDLE_FROM else "arrière-plan"
    return f"{side}, {depth}"


def find_obstacles(mask):
    """Binary mask (H, W) -> obstacles (8-connected regions), largest first and numbered from 1."""
    mask = np.asarray(mask, dtype=bool)
    labels, count = ndimage.label(mask, structure=EIGHT_CONNECTED)
    if count == 0:
        return []
    height, width = mask.shape
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    regions = []
    for size, (rows, cols) in zip(sizes, ndimage.find_objects(labels), strict=True):
        cy = (rows.start + rows.stop) / 2 / height
        cx = (cols.start + cols.stop) / 2 / width
        regions.append((size, (cols.start, rows.start, cols.stop, rows.stop), position_words(cx, cy)))
    regions.sort(key=lambda r: -r[0])
    return [Obstacle(i, box, float(100 * size / mask.size), where)
            for i, (size, box, where) in enumerate(regions, start=1)]


def to_uint8(image):
    """Float image in [0, 1] or uint8 image -> uint8 (H, W, 3)."""
    image = np.asarray(image)
    return image if image.dtype == np.uint8 else (np.clip(image, 0, 1) * 255).round().astype(np.uint8)


def annotate(image, mask, obstacles):
    """The customer's view: the obstacles painted orange, framed and numbered (like the frame in the logo)."""
    base = to_uint8(image).astype(np.float32)
    mask = np.asarray(mask, dtype=bool)
    base[mask] = (1 - MASK_ALPHA) * base[mask] + MASK_ALPHA * np.array(ORANGE, np.float32)
    picture = Image.fromarray(base.astype(np.uint8))
    picture = picture.resize((picture.width * DISPLAY_SCALE, picture.height * DISPLAY_SCALE), Image.Resampling.BILINEAR)
    draw = ImageDraw.Draw(picture)
    font = ImageFont.load_default(size=TAG_FONT_PX)
    for o in obstacles:
        x0, y0, x1, y1 = (DISPLAY_SCALE * v for v in o.box)
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=ORANGE, width=BOX_WIDTH)
        tag = str(o.number)
        left, top, right, bottom = draw.textbbox((0, 0), tag, font=font)
        pad = 6
        tag_w, tag_h = right - left + 2 * pad, bottom - top + 2 * pad
        ty = y0 - tag_h if y0 >= tag_h else y0          # above the frame, or inside it at the top edge
        draw.rectangle((x0, ty, x0 + tag_w, ty + tag_h), fill=ORANGE)
        draw.text((x0 + pad - left, ty + pad - top), tag, fill="white", font=font)
    return np.asarray(picture)


def explanation(phi):
    """Exact Shapley values of the five factors -> rows sorted by weight and one plain French sentence.

    Each row: factor key, French label, share of the total attribution (0-1), and whether it raises the alert.
    """
    total = sum(abs(v) for v in phi.values()) or 1.0
    rows = sorted(({"factor": f, "label": FACTOR_LABELS_FR[f], "share": abs(v) / total, "raises": v >= 0}
                   for f, v in phi.items()), key=lambda r: -r["share"])
    first, second = rows[0], rows[1]

    def part(row):
        effect = "" if row["raises"] else ", qui atténue l'alerte"
        return f"{row['label']} ({100 * row['share']:.0f} %{effect})"

    sentence = f"Le signalement repose surtout sur {part(first)}, puis sur {part(second)}."
    return rows, sentence


# ------------------------------------------------------------------ synthesis report
REPORT_COLUMNS = ("image", "mode", "obstacles", "surface_signalee_pct", "latence_ms", "analyse_le")


def report_csv(rows):
    """History rows -> CSV bytes for a French spreadsheet (';' separator, UTF-8 with BOM, decimal comma)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(REPORT_COLUMNS)
    for r in rows:
        writer.writerow([r["image"], r["mode"], r["obstacles"], f"{r['flagged_percent']:.2f}".replace(".", ","),
                         f"{r['latency_ms']:.0f}", r["analysed_at"]])
    return buffer.getvalue().encode("utf-8-sig")


def _png_data_uri(array, width=None):
    picture = Image.fromarray(to_uint8(array))
    if width and picture.width > width:
        picture = picture.resize((width, round(picture.height * width / picture.width)), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    picture.convert("RGB").save(buffer, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def report_html(rows, plan_name, logo_png, generated_at):
    """History rows -> one self-contained, printable HTML report (images embedded)."""
    logo = "data:image/png;base64," + base64.b64encode(logo_png).decode("ascii")
    with_obstacles = sum(1 for r in rows if r["obstacles"])
    cards = "\n".join(f"""
      <article>
        <img src="{_png_data_uri(r['annotated'], width=640)}" alt="{html.escape(r['image'])}, obstacles surlignés">
        <div>
          <h3>{html.escape(r['image'])}</h3>
          <p class="verdict {'alert' if r['obstacles'] else 'clear'}">{verdict(r['obstacles'])}</p>
          <p>Mode : {html.escape(r['mode'])} · {percent(r['flagged_percent'])} de l'image · {r['latency_ms']:.0f} ms</p>
          {''.join(f"<p>N° {o.number} : {html.escape(o.position)}, {percent(o.area_percent)} de l'image</p>"
                   for o in r['obstacle_list'])}
        </div>
      </article>""" for r in rows)
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>RoadAnomaly · rapport de synthèse</title>
<style>
  body {{ font-family: Lato, "Noto Sans", "Segoe UI", system-ui, sans-serif; color: #1f2a44; background: #fbf7ee;
         max-width: 960px; margin: 2rem auto; padding: 0 1.5rem; }}
  header {{ display: flex; align-items: center; gap: 1.5rem; border-bottom: 3px solid #ee6011; padding-bottom: 1rem; }}
  header img {{ height: 72px; }}
  .kpis {{ display: flex; gap: 1rem; margin: 1.5rem 0; }}
  .kpis div {{ background: #fff; border: 1px solid #e6dcc3; border-radius: 10px; padding: .8rem 1rem; flex: 1; }}
  .kpis b {{ display: block; font-size: 1.6rem; }}
  article {{ display: grid; grid-template-columns: 1.4fr 1fr; gap: 1rem; background: #fff; border: 1px solid #e6dcc3;
            border-radius: 10px; padding: 1rem; margin-bottom: 1rem; break-inside: avoid; }}
  article img {{ width: 100%; border-radius: 6px; }}
  h3 {{ margin: 0 0 .4rem; }} p {{ margin: .25rem 0; }}
  .verdict.alert {{ color: #b8460b; font-weight: 700; }} .verdict.clear {{ color: #2d3a5a; font-weight: 700; }}
  footer {{ color: #5b6478; font-size: .85rem; margin-top: 2rem; }}
</style></head><body>
<header><img src="{logo}" alt="RoadAnomaly"><div><h1>Rapport de synthèse</h1>
<p>Offre {html.escape(plan_name)} · généré le {html.escape(generated_at)}</p></div></header>
<section class="kpis">
  <div><b>{len(rows)}</b>images analysées</div>
  <div><b>{sum(r['obstacles'] for r in rows)}</b>obstacles signalés</div>
  <div><b>{with_obstacles}</b>images avec au moins un obstacle</div>
</section>
{cards}
<footer>RoadAnomaly est un outil d'aide à la décision : chaque signalement doit être vérifié par une personne.
Les positions sont données dans l'image (gauche / centre / droite, premier plan / arrière-plan), pas en mètres.</footer>
</body></html>"""


def percent(value):
    """Share of the image in French notation: '2,8 %', or '< 0,1 %' for a zone too small to round."""
    return "< 0,1 %" if 0 < value < 0.05 else f"{value:.1f} %".replace(".", ",")


def verdict(count):
    if count == 0:
        return "Aucun obstacle inattendu"
    return f"{count} obstacle{'s' if count > 1 else ''} signalé{'s' if count > 1 else ''}"
