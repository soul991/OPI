"""Smoke tests for OPI Streamlit application using AppTest."""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parents[1] / "app" / "main.py")


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
