"""Smoke tests for OPI Streamlit application using AppTest."""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parents[1] / "app" / "main.py")

@pytest.fixture(autouse=True)
def test_env_setup(monkeypatch):
    monkeypatch.setenv("OPI_ENV", "test")


def test_streamlit_app_renders_cleanly():
    """Verify that app/main.py initializes, executes, and renders without exceptions."""
    at = AppTest.from_file(APP_PATH).run(timeout=30)
    assert not at.exception, f"App raised unhandled exception: {at.exception}"

    # Verify title
    assert len(at.title) >= 1
    assert "Indian Mainboard IPO" in at.title[0].value

    # Verify mandatory non-advisory disclaimer
    captions = [c.value for c in at.caption]
    assert any("Decision aid, not financial advice" in c for c in captions)

    # Verify metrics rendered
    metric_labels = [m.label for m in at.metric]
    assert "Estimated Listing Gain" in metric_labels
    assert "80% Conformal Interval" in metric_labels


def test_streamlit_app_advisory_wording_prohibited():
    """Verify that strictly non-advisory language is maintained throughout all rendered text."""
    at = AppTest.from_file(APP_PATH).run(timeout=30)
    assert not at.exception

    # Check that advisory recommendations ('apply', 'avoid', 'buy', 'sell') are absent from all text
    all_text = " ".join(
        [t.value for t in at.markdown] +
        [t.value for t in at.caption] +
        [t.value for t in at.title] +
        [t.value for t in at.subheader]
    ).lower()

    for forbidden in ["apply now", "avoid this", "strong buy", "sell recommendation", "investment advice"]:
        assert forbidden not in all_text, f"Forbidden advisory phrase '{forbidden}' found in app UI"


def test_probability_hidden_outside_calibrated_range(monkeypatch):
    """D-029: Verify that probabilities outside the measured calibrated range are hidden."""
    import opi.score as score_module
    from app.main import get_calibrated_probability_range

    cal_min, cal_max = get_calibrated_probability_range()
    assert 0.05 < cal_min < 0.15
    assert 0.80 < cal_max < 0.95

    # Mock score_ipo to return an extreme uncalibrated probability
    orig_score = score_module.score_ipo
    def fake_score(data):
        res = orig_score(data)
        res["prob_gt10"] = 0.965
        return res

    monkeypatch.setattr(score_module, "score_ipo", fake_score)
    at = AppTest.from_file(APP_PATH).run(timeout=30)
    assert not at.exception
    metric_values = [m.value for m in at.metric]
    assert "not shown: outside measured range" in metric_values


def test_table_values_are_strings():
    """D-033: Verify that all values in the grounding evidence table are rendered as strings."""
    at = AppTest.from_file(APP_PATH).run(timeout=30)
    assert not at.exception
    dfs = at.dataframe
    assert len(dfs) >= 1
    df = dfs[0].value
    assert "Grounded Value" in df.columns
    assert "Raw Value" in df.columns
    for val in df["Grounded Value"]:
        assert isinstance(val, str), f"Grounded Value {val!r} is not string: {type(val)}"
    for val in df["Raw Value"]:
        assert isinstance(val, str), f"Raw Value {val!r} is not string: {type(val)}"
