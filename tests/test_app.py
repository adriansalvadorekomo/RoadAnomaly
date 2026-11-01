"""The Streamlit demo renders without exceptions (headless, with the trained models of models/)."""
import pytest

from roadanomaly import data_pipeline as dp
from roadanomaly.inference import available_models

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(dp.REPO_ROOT / "deployment" / "app" / "streamlit_app.py")


@pytest.mark.skipif(not available_models(dp.MODELS_DIR), reason="no trained model in models/")
def test_demo_renders_an_example_with_every_model():
    app = AppTest.from_file(APP, default_timeout=300).run()
    assert not app.exception, app.exception
    assert len(app.metric) == 4 * len(available_models(dp.MODELS_DIR))   # 4 metric tiles per model


@pytest.mark.skipif(not available_models(dp.MODELS_DIR), reason="no trained model in models/")
def test_demo_explanations_toggle():
    app = AppTest.from_file(APP, default_timeout=300).run()
    app.sidebar.toggle[0].set_value(True).run()
    assert not app.exception, app.exception
