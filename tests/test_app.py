"""The Streamlit demo renders without exceptions (headless, with the trained models of models/)."""
import pytest

from roadanomaly import data_pipeline as dp
from roadanomaly.inference import available_models

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(dp.REPO_ROOT / "deployment" / "app" / "streamlit_app.py")
MODELS = available_models(dp.MODELS_DIR)
needs_models = pytest.mark.skipif(not MODELS, reason="no trained model in models/")


@needs_models
def test_demo_renders_every_tab_with_every_model():
    app = AppTest.from_file(APP, default_timeout=600).run()
    assert not app.exception, app.exception
    assert len(app.tabs) == 5
    assert len(app.metric) >= 4 * len(MODELS)          # 4 detection tiles per model
    assert any("relies most on" in s.value for s in app.success)   # the WHAT sentence of the explained model


@needs_models
def test_demo_explains_with_grad_cam_too():
    app = AppTest.from_file(APP, default_timeout=600).run()
    app.sidebar.button_group[1].set_value("Grad-CAM").run()   # second segmented control: the WHERE method
    assert not app.exception, app.exception
