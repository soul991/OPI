"""Tests for Workstream A out-of-range and mega-issue scoring guard (D-040)."""

import json
from pathlib import Path
import pytest
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]

from opi.score import score_ipo, check_feature_ranges, load_feature_ranges


def test_feature_ranges_artifact_exists_and_valid():
    """Verify model/feature_ranges.json exists and contains training boundaries."""
    ranges = load_feature_ranges()
    assert "features" in ranges, "feature_ranges.json must contain 'features'"
    assert "issue_size_cr" in ranges["features"]
    max_size = ranges["features"]["issue_size_cr"]["max"]
    assert max_size > 27000.0, f"Expected Hyundai-like max ~27870 cr, got {max_size}"
    assert "model_sha256" in ranges
    assert "master_sha256" in ranges


def test_jio_like_input_triggers_range_flags():
    """D-040: Jio Platforms-like input (size 30,213 cr, missing P/E and debt/equity) triggers safety flags."""
    jio_input = {
        "company": "Jio Platforms Limited",
        "sector": "IT & Technology",
        "exchange": "BOTH",
        "issue_price": 1119.0,
        "issue_size_cr": 30213.0,
        "fresh_issue_pct": 50.0,
        "ofs_pct": 50.0,
        "lot_size": 13,
        "sub_qib": 15.0,
        "sub_nii": 10.0,
        "sub_retail": 5.0,
        "sub_total": 8.5,
        "pe_ratio": None,
        "peer_median_pe": None,
        "debt_equity": None,
        "gmp_pct": 22.34,
        "nifty_30d_return": 1.2,
        "india_vix": 14.5,
        "recent_ipo_avg_gain": 15.0,
    }

    flags, conf, disp_prob = check_feature_ranges(jio_input)

    assert "ISSUE_SIZE_ABOVE_TRAIN_MAX" in flags, "Must flag issue size above training max"
    assert "MEGA_ISSUE_GT_10000CR" in flags, "Must flag mega issue > 10,000 cr"
    assert "MISSING:pe_ratio" in flags, "Must flag missing pe_ratio"
    assert "MISSING:debt_equity" in flags, "Must flag missing debt_equity"
    assert conf == "LOW", "Confidence must be LOW for out-of-range input"
    assert disp_prob is False, "Probability display must be suppressed for out-of-range input"

    # Verify score_ipo return payload
    res = score_ipo(jio_input)
    assert res["confidence"] == "LOW"
    assert res["display_probability"] is False
    assert "ISSUE_SIZE_ABOVE_TRAIN_MAX" in res["input_flags"]
    assert "MEGA_ISSUE_GT_10000CR" in res["input_flags"]


def test_normal_input_has_no_range_flags():
    """Normal within-bounds input has no out-of-range flags and confidence NORMAL."""
    normal_input = {
        "company": "Standard Engineering Limited",
        "sector": "Capital Goods",
        "exchange": "NSE",
        "issue_price": 250.0,
        "issue_size_cr": 750.0,
        "fresh_issue_pct": 80.0,
        "ofs_pct": 20.0,
        "lot_size": 60,
        "sub_qib": 10.0,
        "sub_nii": 8.0,
        "sub_retail": 3.0,
        "sub_total": 6.5,
        "pe_ratio": 24.5,
        "peer_median_pe": 28.0,
        "debt_equity": 0.45,
        "gmp_pct": 18.0,
        "nifty_30d_return": 2.1,
        "india_vix": 13.8,
        "recent_ipo_avg_gain": 12.5,
    }

    flags, conf, disp_prob = check_feature_ranges(normal_input)
    range_flags = [f for f in flags if "ABOVE_TRAIN_MAX" in f or "BELOW_TRAIN_MIN" in f or "MEGA_ISSUE" in f]
    assert len(range_flags) == 0, f"Normal input should have no range flags, got {range_flags}"
    assert conf == "NORMAL"
    assert disp_prob is True

    res = score_ipo(normal_input)
    assert res["confidence"] == "NORMAL"
    assert res["display_probability"] is True


def test_jio_row_in_prediction_log_evaluated_as_low_confidence():
    """The logged Jio Platforms row is dynamically detected as LOW confidence without modifying the row."""
    log_path = ROOT_DIR / "predictions" / "prediction_log.csv"
    assert log_path.exists()
    df = pd.read_csv(log_path, dtype=str)
    jio_rows = df[df["company"].str.contains("Jio Platforms", case=False)]
    assert len(jio_rows) > 0, "Jio Platforms row must be in prediction_log.csv"

    jio_row = jio_rows.iloc[0]
    feats = json.loads(jio_row["features_snapshot_json"])
    flags, conf, disp_prob = check_feature_ranges(feats)

    assert "ISSUE_SIZE_ABOVE_TRAIN_MAX" in flags
    assert conf == "LOW"
    assert disp_prob is False
