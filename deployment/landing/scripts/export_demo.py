"""Export the real data the landing page shows (run after the notebooks; `mise run landing:data`).

Writes deployment/landing/public/demo/ (git-ignored):
- for a few openly licensed validation photos: the photo (640x352 JPEG), its ground-truth mask and,
  for every model in models/, its post-processed score map, all at half resolution (176x320) as raw
  little-endian bytes (uint16 scores quantised between the map's min and max, uint8 masks), so the
  page can re-threshold the real maps in the browser;
- gallery photos (openly licensed, any split) with their statistics and credits;
- demo.json: the manifest of all of it, plus the split counts per category (the "receipt").
Only photos with an open licence in credits.txt are exported; each keeps its credit.
"""
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from roadanomaly import data_pipeline as dp
from roadanomaly import splitting
from roadanomaly.inference import Predictor, available_models
from roadanomaly.protocol import IMG_SIZE, MIN_OBJECT_PX_FULL

OUT = Path(__file__).resolve().parents[1] / "public" / "demo"
LIVE_FRAMES = ["animals10_bovine_cattle_beside_road", "cones01_Beeston_MMB_A6_Middle_Street",
               "animals27_wildlife_bear", "vehicle03_Fuhrwerke_in_China"]          # validation, open licences
GALLERY_FRAMES = ["animals03_Zebras_in_the_road", "animals22_red_fox_on_road", "cones03_Bang_Na_Trat_Highway",
                  "animals12_Collared_Peccary_crossing_the_road", "animals06_sheep_roads_lambs",
                  "vehicle01_man_carrying_dry_grass_on_bicycle", "animals18_Goose_on_the_road_Memphis",
                  "cones05_Corner_of_Kingsley_Park"]
HALF = (IMG_SIZE[0] // 2, IMG_SIZE[1] // 2)
TITLES = {"animals10_bovine_cattle_beside_road": "Cow beside an alpine road",
          "cones01_Beeston_MMB_A6_Middle_Street": "Roadworks cones in Beeston",
          "animals27_wildlife_bear": "Bear crossing a forest road",
          "vehicle03_Fuhrwerke_in_China": "Carts on a road in China"}
CATEGORY = {
    "animals": "animal",
    "cones": "cones",
    "lost_tires": "lost tyres",
    "obstacles": "obstacle",
    "vehicle": "vehicle",
}


def credits():
    """frame -> {author, licence, licence_url, source} for openly licensed frames."""
    out = {}
    for names, sources in splitting.parse_credits(dp.DATA_DIR / "credits.txt"):
        if not sources:
            continue
        line, source = sources[0], (sources[1] if len(sources) > 1 else "")
        match = re.match(
            r"(?P<author>.*?),?\s*(?P<lic>CC BY(?:-SA)? [\d.]+(?: DE)?|CC0|public domain)\s*(?P<url>https?://\S+)?",
            line,
        )
        if not match:
            continue
        for name in names:
            author = re.sub(r"\s*\([^)]*@[^)]*\)", "", match["author"]).strip(" ,")   # no e-mail addresses
            out[name] = {"author": author or "unknown", "licence": match["lic"],
                         "licence_url": match["url"] or "", "source": source}
    return out


def half_area(array):
    """2x2 mean pooling: (H, W) -> (H/2, W/2)."""
    h, w = array.shape
    return array.reshape(h // 2, 2, w // 2, 2).mean(axis=(1, 3))


def frame_stats(mask):
    labeled, n = ndimage.label(mask, structure=np.ones((3, 3)))
    areas = ndimage.sum(mask, labeled, range(1, n + 1)) if n else np.array([])
    return {
        "anomaly_percent": round(100 * float(mask.mean()), 1),
        "objects": int((np.asarray(areas) >= MIN_OBJECT_PX_FULL).sum()),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lic = credits()
    manifest = {row["frame"]: row for row in dp.read_manifest()}
    for frame in LIVE_FRAMES + GALLERY_FRAMES:
        assert frame in lic, f"{frame} has no open licence in credits.txt"

    # Live fragment: photos, ground truth and every model's score maps
    images, x = [], []
    for frame in LIVE_FRAMES:
        image, mask = dp.resize_pair(*dp.load_frame(frame), IMG_SIZE)
        Image.fromarray(image).save(OUT / f"{frame}.jpg", quality=86)
        (half_area(mask.astype(np.float32)) >= 0.5).astype(np.uint8).tofile(OUT / f"{frame}-gt.u8")
        x.append(image.astype(np.float32) / 255.0)
        images.append({"frame": frame, "title": TITLES[frame], "split": manifest[frame]["split"],
                       "photo": f"demo/{frame}.jpg", "gt": f"demo/{frame}-gt.u8", **lic[frame],
                       **frame_stats(dp.load_frame(frame)[1])})
    x = np.stack(x)

    models = []
    for name in available_models(dp.MODELS_DIR):
        predictor = Predictor(dp.MODELS_DIR / name)
        scores = predictor.score_maps(x)
        maps, ranges = {}, {}
        for frame, score in zip(LIVE_FRAMES, scores, strict=True):
            small = half_area(score)
            lo, hi = float(small.min()), float(small.max())
            q = np.round((small - lo) / max(hi - lo, 1e-9) * 65535).astype("<u2")
            q.tofile(OUT / f"{name}-{frame}.u16")
            maps[frame], ranges[frame] = f"demo/{name}-{frame}.u16", [lo, hi]
        all_scores = scores.ravel()
        models.append({"name": name, "binome": predictor.config["binome"], "title": predictor.config["title"],
                       "unit": "probability" if predictor.model_type == "segmentation" else "z-score",
                       "threshold": predictor.threshold, "min_blob_half": int(np.ceil(predictor.min_blob / 4)),
                       "slider": [float(np.quantile(all_scores, 0.02)), float(np.quantile(all_scores, 0.999))],
                       "maps": maps, "ranges": ranges})

    # Gallery and the split receipt
    gallery = []
    for frame in GALLERY_FRAMES:
        image, mask = dp.load_frame(frame)
        pil = Image.fromarray(image)
        pil.thumbnail((900, 900))
        pil.save(OUT / f"{frame}.jpg", quality=84)
        gallery.append({"frame": frame, "photo": f"demo/{frame}.jpg", "width": pil.width, "height": pil.height,
                        "split": manifest[frame]["split"], "category": CATEGORY[manifest[frame]["category"]],
                        **frame_stats(mask), **lic[frame]})
    receipt = {}
    for row in manifest.values():
        receipt.setdefault(row["split"], {}).setdefault(CATEGORY[row["category"]], 0)
        receipt[row["split"]][CATEGORY[row["category"]]] += 1

    # Fallback for visitors without JavaScript: the first photo with the first model's mask, at full size
    first = Predictor(dp.MODELS_DIR / models[0]["name"]).predict(x[:1])["masks"][0].astype(bool)
    painted = (x[0] * 255).astype(np.float32)
    painted[first] = 0.45 * painted[first] + 0.55 * np.array([229, 72, 77], np.float32)
    Image.fromarray(painted.astype(np.uint8)).save(OUT / "fallback.jpg", quality=86)

    (OUT / "demo.json").write_text(json.dumps({"size": list(HALF), "images": images, "models": models,
                                               "gallery": gallery, "receipt": receipt}, indent=1))
    print(f"exported {len(images)} live photos x {len(models)} models and {len(gallery)} gallery photos to {OUT}")


if __name__ == "__main__":
    main()
