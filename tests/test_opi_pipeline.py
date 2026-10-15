"""Unit tests for the opi/ refactored pipeline package (Workstream A)."""

import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import pytest

from opi.collect import parse_chittorgarh_subscription, parse_investorgain_gmp
from opi.validate import validate_timing_and_leakage, validate_ipo_features
from opi.score import score_ipo, load_champion_model, prep_features_for_scoring
from opi.log import serialize_features_snapshot, LOG_PATH
from opi.run_daily import run_daily_forward_test


def test_parser_with_html_fixture():
    """Verify subscription parser against an HTML snippet fixture."""
    html_fixture = """
    <html>
        <table>
            <tr><th>Category</th><th>Subscription Times</th></tr>
            <tr><td>Qualified Institutional Buyers (QIBs)</td><td>256.65x</td></tr>
            <tr><td>Non-Institutional Investors (NII)</td><td>203.21x</td></tr>
            <tr><td>Retail Individual Investors (RII)</td><td>30.55x</td></tr>
            <tr><td>Total</td><td>131.73x</td></tr>
        </table>
    </html>
    """
    subs = parse_chittorgarh_subscription(html_fixture)
    assert subs["sub_qib"] == 256.65
    assert subs["sub_nii"] == 203.21
    assert subs["sub_retail"] == 30.55
    assert subs["sub_total"] == 131.73


def test_gmp_parser_with_html_fixture():
    """Verify GMP parser against an HTML snippet fixture."""
    html_fixture = """
    <div>
        <span>Current GMP: Rs 82</span>
        <p>Estimated Listing Gain: 30.26% GMP</p>
    </div>
    """
    gmp = parse_investorgain_gmp(html_fixture)
    assert gmp["gmp_inr"] == 82.0
    assert gmp["gmp_pct"] == 30.26


def test_timing_and_leakage_validator_catches_violations():
    """Verify validator catches pre-close scoring, post-listing scoring, and live bidding notes."""
    # 1. Scored before 18:00 on close date
    ok, issues = validate_timing_and_leakage(
        close_date_str="2026-10-15",
        listing_date_str="2026-10-21",
        scored_at_str="2026-10-15T14:30:00"
    )
    assert not ok
    assert any("before bidding closed" in s for s in issues)

    # 2. Scored on/after listing date
    ok, issues = validate_timing_and_leakage(
        close_date_str="2026-10-15",
        listing_date_str="2026-10-21",
        scored_at_str="2026-10-22T10:00:00"
    )
    assert not ok
    assert any("strictly before listing date" in s for s in issues)

    # 3. Live / interim subscription note
    ok, issues = validate_timing_and_leakage(
        close_date_str="2026-10-15",
        listing_date_str="2026-10-21",
        scored_at_str="2026-10-15T19:30:00",
        notes="Day 1 live bidding subscription"
    )
    assert not ok
    assert any("Interim/live subscription detected" in s for s in issues)

    # 4. Valid timing
    ok, issues = validate_timing_and_leakage(
        close_date_str="2026-10-15",
        listing_date_str="2026-10-21",
        scored_at_str="2026-10-15T19:30:00",
        notes="Final official subscription post-close"
    )
    assert ok
    assert len(issues) == 0


def test_scoring_probability_matches_evaluation_pipeline():
    """Verify that score_ipo returns Platt-calibrated probability matching cal_clf exactly."""
    art, version, _ = load_champion_model()
    cal_clf = art.get("cal_clf") or art.get("clf")
    levels = art.get("levels")

    sample_input = {
        "company": "Test Company",
        "issue_price": 271.0,
        "issue_size_cr": 712.31,
        "fresh_issue_pct": 0.0,
        "ofs_pct": 100.0,
        "lot_size": 55,
        "sub_qib": 256.65,
        "sub_nii": 203.21,
        "sub_retail": 30.55,
        "sub_total": 131.73,
        "pe_ratio": 40.69,
        "peer_median_pe": 51.39,
        "nifty_30d_return": -3.03,
        "india_vix": 14.12,
        "recent_ipo_avg_gain": 17.22,
        "sector": "Industrial & Manufacturing",
        "exchange": "BOTH",
        "gmp_pct": 30.26
    }

    # Direct model probability
    df_sample = pd.DataFrame([sample_input])
    X, _ = prep_features_for_scoring(df_sample, levels)
    direct_prob = float(cal_clf.predict_proba(X)[0][1])

    # Pipeline score_ipo
    res = score_ipo(sample_input)
    assert abs(res["prob_gt10"] - direct_prob) < 1e-4, (
        f"Score pipeline prob {res['prob_gt10']} does not match direct evaluation prob {direct_prob}"
    )
    assert res["model_version"] == "v4.0.0-champion"


def test_scoring_regime_routing():
    """Verify regime routing: GMP observed uses Raw GMP as primary; no GMP uses model estimate."""
    base_input = {
        "company": "Routing Test",
        "issue_price": 100.0,
        "issue_size_cr": 500.0,
        "lot_size": 50,
        "sub_qib": 10.0,
        "sub_nii": 5.0,
        "sub_retail": 2.0,
        "sub_total": 6.0,
        "sector": "IT & Technology",
        "exchange": "NSE"
    }

    # Case A: With GMP
    input_gmp = dict(base_input, gmp_pct=25.0)
    res_gmp = score_ipo(input_gmp)
    assert res_gmp["primary_expected_return"] == 25.0
    assert "GMP observed" in res_gmp["rule_applied"]
    assert res_gmp["blend_expected_return"] is not None

    # Case B: Without GMP
    input_nogmp = dict(base_input, gmp_pct=None)
    res_nogmp = score_ipo(input_nogmp)
    assert res_nogmp["primary_expected_return"] == res_nogmp["predicted_gain_pct"]
    assert "no GMP" in res_nogmp["rule_applied"]
    assert res_nogmp["blend_expected_return"] is None


def test_leakage_in_features_snapshot():
    """Verify that post-listing outcome columns are never serialized into feature snapshots."""
    row_with_outcomes = {
        "company": "Snapshot Test",
        "issue_price": 100.0,
        "sub_total": 5.0,
        "listing_price": 150.0,
        "listing_gain_pct": 50.0,
        "label_good": 1
    }
    snap_str = serialize_features_snapshot(row_with_outcomes, model_version="v4.0.0-champion")
    assert "listing_price" not in snap_str
    assert "listing_gain_pct" not in snap_str
    assert "label_good" not in snap_str
    assert "_model_version" in snap_str


def test_dry_run_does_not_mutate_log():
    """Verify that run_daily with dry_run=True does not write rows to any log or update dashboard."""
    assert LOG_PATH.exists()
    df_before = pd.read_csv(LOG_PATH)
    rows_before = len(df_before)

    run_log_path = ROOT_DIR / "predictions" / "run_log.csv"
    run_log_before = run_log_path.read_text(encoding="utf-8") if run_log_path.exists() else ""
    dashboard_path = ROOT_DIR / "dashboard" / "index.html"
    dashboard_before = dashboard_path.read_text(encoding="utf-8") if dashboard_path.exists() else ""

    # Run daily forward test in dry-run mode
    run_daily_forward_test(dry_run=True)

    df_after = pd.read_csv(LOG_PATH)
    rows_after = len(df_after)
    assert rows_before == rows_after, f"Dry run mutated prediction_log! Before: {rows_before}, After: {rows_after}"

    run_log_after = run_log_path.read_text(encoding="utf-8") if run_log_path.exists() else ""
    assert run_log_before == run_log_after, "Dry run mutated run_log.csv!"

    dashboard_after = dashboard_path.read_text(encoding="utf-8") if dashboard_path.exists() else ""
    assert dashboard_before == dashboard_after, "Dry run mutated dashboard/index.html!"

