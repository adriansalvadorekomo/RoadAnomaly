"""The RoadAnomaly product (deployment/product): offer rules, obstacle findings, report, and the app itself."""
import json

import numpy as np
import pytest

from deployment.product import findings, offer
from roadanomaly import data_pipeline as dp
from roadanomaly.inference import available_models

MODELS = available_models(dp.MODELS_DIR)
needs_models = pytest.mark.skipif(not {m.model for m in offer.MODES.values()} <= set(MODELS),
                                  reason="the two product models are not in models/")


# ------------------------------------------------------------------ offer
def test_plans_follow_the_marketing_deck():
    prices = {k: offer.PLANS[k].price_dt for k in offer.PAID_PLANS}
    assert prices == {"bronze": 50, "silver": 200, "gold": 600}
    assert offer.PLANS["bronze"].monthly_images == 500 and offer.PLANS["silver"].monthly_images == 5000
    assert offer.PLANS["gold"].monthly_images is None
    assert offer.cheapest_plan_with("explanation") == "Silver"
    assert offer.cheapest_plan_with("api") == "Gold"


def test_modes_use_trained_models_and_quote_the_test_numbers(tmp_path):
    results = {"frames": ["a", "b"], "models": {
        "A_deeplabv3plus": {"summary": {"objects detected": "20/22", "false alarms / predicted blobs": "38/67"}}}}
    path = tmp_path / "test_results.json"
    path.write_text(json.dumps(results))
    t = offer.tested(offer.MODES["max"], path)
    assert t == {"found": 20, "obstacles": 22, "false_alarms": 38, "flagged": 67, "photos": 2}
    assert "20 obstacles repérés sur 22" in offer.tested_sentence(offer.MODES["max"], path)
    assert offer.tested(offer.MODES["sobre"], path) is None          # model missing from the results
    assert offer.tested_sentence(offer.MODES["max"], tmp_path / "missing.json") == ""


def test_low_false_alarm_mode_really_has_fewer_false_alarms():
    """The promise of the 'peu de fausses alarmes' mode holds on the real test results (notebook 5)."""
    sober, maximum = offer.tested(offer.MODES["sobre"]), offer.tested(offer.MODES["max"])
    if sober is None or maximum is None:
        pytest.skip("notebook 5 has not produced reports/results/test_results.json")
    assert sober["false_alarms"] < maximum["false_alarms"]
    assert maximum["found"] >= sober["found"]


# ------------------------------------------------------------------ findings
def test_obstacles_are_numbered_largest_first_with_their_position():
    mask = np.zeros((100, 300), bool)
    mask[80:95, 10:20] = True          # small, bottom left
    mask[10:40, 130:190] = True        # large, top centre
    obstacles = findings.find_obstacles(mask)
    assert [o.number for o in obstacles] == [1, 2]
    assert obstacles[0].box == (130, 10, 190, 40)
    assert obstacles[0].position == "au centre, arrière-plan"
    assert obstacles[1].position == "à gauche, premier plan"
    assert obstacles[0].area_percent == pytest.approx(100 * 30 * 60 / mask.size)
    assert findings.find_obstacles(np.zeros((10, 10), bool)) == []


def test_annotated_image_is_upscaled_and_orange_on_the_obstacle():
    image = np.full((40, 60, 3), 0.5, np.float32)
    mask = np.zeros((40, 60), bool)
    mask[20:30, 20:40] = True
    out = findings.annotate(image, mask, findings.find_obstacles(mask))
    assert out.shape == (80, 120, 3) and out.dtype == np.uint8
    inside, outside = out[50, 60], out[5, 5]
    assert inside[0] > inside[2] and tuple(outside) == (128, 128, 128)


def test_explanation_sentence_names_the_two_largest_factors():
    rows, sentence = findings.explanation(
        {"colour": 1.0, "texture": 0.0, "contrast": 3.0, "object": -2.0, "context": 0.0})
    assert [r["factor"] for r in rows[:2]] == ["contrast", "object"]
    assert sum(r["share"] for r in rows) == pytest.approx(1.0)
    assert sentence.startswith("Le signalement repose surtout sur la luminosité et le contraste (50 %)")
    assert "l'obstacle lui-même (33 %, qui atténue l'alerte)" in sentence


def test_reports_contain_every_analysed_image():
    obstacle = findings.Obstacle(1, (0, 0, 2, 2), 1.5, "au centre, mi-distance")
    rows = [{"image": "route <1>.jpg", "mode": "Détection maximale", "obstacles": 1, "obstacle_list": [obstacle],
             "flagged_percent": 1.5, "latency_ms": 21.4, "analysed_at": "08/11/2026 10:00",
             "annotated": np.zeros((8, 8, 3), np.uint8)},
            {"image": "vide.png", "mode": "Peu de fausses alarmes", "obstacles": 0, "obstacle_list": [],
             "flagged_percent": 0.0, "latency_ms": 40.0, "analysed_at": "08/11/2026 10:01",
             "annotated": np.zeros((8, 8, 3), np.uint8)}]
    csv_text = findings.report_csv(rows).decode("utf-8-sig").splitlines()
    assert csv_text[0] == ";".join(findings.REPORT_COLUMNS)
    assert csv_text[1] == "route <1>.jpg;Détection maximale;1;1,50;21;08/11/2026 10:00"
    page = findings.report_html(rows, "Silver", b"png", "08/11/2026")
    assert "route &lt;1&gt;.jpg" in page and "<b>2</b>images analysées" in page
    assert "Aucun obstacle inattendu" in page and "1 obstacle signalé" in page
    assert "1,5 % de l'image" in page
    assert findings.percent(0.01) == "< 0,1 %" and findings.percent(0) == "0,0 %"


# ------------------------------------------------------------------ the app (headless)
APP = str(dp.REPO_ROOT / "deployment" / "product" / "app.py")


def _app():
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(APP, default_timeout=600)


@needs_models
def test_product_analyses_the_examples_and_explains_them():
    app = _app().run()
    assert not app.exception, app.exception
    app.button(key="analyse").click().run()
    assert not app.exception, app.exception
    assert app.session_state["used"] == 2                          # two default examples, counted once each
    assert len(app.session_state["history"]) == 2
    why = [b for b in app.button if b.key and b.key.startswith("why:")]
    assert why, "the trial plan offers the explanation on images with obstacles"
    why[0].click().run()
    assert not app.exception, app.exception
    assert any(i.value.startswith("Le signalement repose surtout sur") for i in app.info)


@needs_models
def test_bronze_plan_hides_the_explanation_and_stops_at_its_quota():
    app = _app()
    app.session_state["plan"] = "bronze"
    app.session_state["used"] = offer.PLANS["bronze"].monthly_images
    app.run()
    assert not app.exception, app.exception
    assert app.button(key="analyse").disabled
    assert any("toutes les images" in w.value for w in app.warning)
