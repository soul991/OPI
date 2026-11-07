"""Tests for forward cohort MAE calculation and dashboard integration."""

from pathlib import Path
import pytest
from scripts.forward_mae import compute_forward_cohort_mae, get_forward_cohort_data
from opi.report import render_dashboard_html

ROOT_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_PATH = ROOT_DIR / "dashboard" / "index.html"


def test_forward_cohort_mae_pinned_at_n_12():
    """Verify forward MAE calculation matches exact pre-registered cohort value at n=12."""
    res = compute_forward_cohort_mae()
    assert res["n"] == 12, f"Expected exactly 12 evaluated forward IPOs, got {res['n']}"
    assert res["mae"] == 5.6675, f"Expected cumulative forward MAE 5.6675, got {res['mae']}"
    assert len(res["rows"]) == 12


def test_dashboard_html_contains_forward_mae_value():
    """Verify dashboard/index.html includes the exact cumulative MAE value from forward_mae.py."""
    res = compute_forward_cohort_mae()
    mae_str = f"{res['mae']:.4f} pp"

    render_dashboard_html()
    assert DASHBOARD_PATH.exists()
    content = DASHBOARD_PATH.read_text(encoding="utf-8")

    assert mae_str in content, f"Expected dashboard HTML to contain '{mae_str}'"
    assert "Cumulative MAE" in content
