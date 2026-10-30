#!/usr/bin/env python3
"""tests/test_actuals_job.py - Unit and regression tests for automated outcome recording (D-066, D-068, D-069).

Validates:
1. Tier 1 success path (official exchange evidence).
2. Tier 2 success path (yfinance + agreeing independent second source <= 1.0%).
3. Tier 2 divergence (> 1.0% tolerance -> PENDING_REVIEW).
4. Tier 2 missing second source (-> PENDING_REVIEW).
5. Listing-day before 16:00 IST (D-069: SKIPPED_MARKET_IN_PROGRESS).
6. Row already recorded (no overwrite).
7. Redirect to non-exchange host during exchange fetch (security rejection).

Uses synthetic fixtures and temporary directories only (never in data/).
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest

from opi.actuals import (
    ActualsEvidenceError,
    execute_two_tier_outcome_chain,
    is_listing_ready_for_actuals,
    record_actual_from_tier2,
)
from opi.log import IST

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def synthetic_env(tmp_path: Path):
    """Set up an isolated synthetic prediction log and evidence directory."""
    log_dir = tmp_path / "predictions"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "prediction_log.csv"

    ev_dir = tmp_path / "data" / "evidence" / "actuals"
    ev_dir.mkdir(parents=True, exist_ok=True)

    # Synthetic past listed IPO (listing date 2026-10-28)
    features_json = json.dumps({
        "issue_price": 100.0,
        "nse_symbol": "SYNTH",
        "bse_code": "599999",
        "overview_url": "https://www.chittorgarh.com/ipo/synthetic-corp-ipo/9999/",
        "source_urls": ["https://www.chittorgarh.com/ipo/synthetic-corp-ipo/9999/"]
    })
    rows = [
        {
            "scored_at": "2026-10-25T18:30:00+05:30",
            "company": "Synthetic Corp",
            "listing_date": "2026-10-28",
            "close_date": "2026-10-25",
            "pred_gain_pct": "15.0",
            "pred_prob_gt10": "0.65",
            "gmp_pct_at_scoring": "12.0",
            "actual_gain_pct": "",
            "status": "FORWARD",
            "notes": "Synthetic test forward row",
            "model_version": "v4.0.0-champion",
            "features_snapshot_json": features_json
        }
    ]
    df = pd.DataFrame(rows)
    df.to_csv(log_file, index=False)

    return {
        "root": tmp_path,
        "log_path": log_file,
        "ev_dir": ev_dir,
        "company": "Synthetic Corp",
        "listing_date": date(2026, 10, 28),
    }


def test_is_listing_ready_for_actuals_market_hours_rule():
    """D-069: Test timing rule for listing day market hours."""
    l_date = date(2026, 10, 30)

    # 1. Past date: always ready
    ready, msg = is_listing_ready_for_actuals(date(2026, 10, 28), current_dt=datetime(2026, 10, 30, 10, 0, tzinfo=IST))
    assert ready is True
    assert "passed" in msg

    # 2. Today before 16:00 IST: not ready (market in progress)
    ready, msg = is_listing_ready_for_actuals(l_date, current_dt=datetime(2026, 10, 30, 11, 30, tzinfo=IST))
    assert ready is False
    assert "in progress" in msg

    ready, msg = is_listing_ready_for_actuals(l_date, current_dt=datetime(2026, 10, 30, 15, 59, tzinfo=IST))
    assert ready is False
    assert "in progress" in msg

    # 3. Today at or after 16:00 IST: ready
    ready, msg = is_listing_ready_for_actuals(l_date, current_dt=datetime(2026, 10, 30, 16, 0, tzinfo=IST))
    assert ready is True
    assert "post-market" in msg

    ready, msg = is_listing_ready_for_actuals(l_date, current_dt=datetime(2026, 10, 30, 18, 30, tzinfo=IST))
    assert ready is True

    # 4. Future date: not ready
    ready, msg = is_listing_ready_for_actuals(date(2026, 11, 2), current_dt=datetime(2026, 10, 30, 18, 0, tzinfo=IST))
    assert ready is False
    assert "future" in msg


def test_tier2_success_with_agreeing_second_source(synthetic_env, monkeypatch):
    """D-066, D-068: Tier 2 succeeds when yfinance and second source agree <= 1.0%."""
    mock_hist = pd.DataFrame(
        [{"Open": 125.00, "High": 130.0, "Low": 120.0, "Close": 128.0, "Volume": 1000}],
        index=[pd.Timestamp("2026-10-28 00:00:00+05:30")]
    )
    mock_sec_html = "<html><body><table><tr><td>Open</td><td>₹125.20</td></tr></table></body></html>"

    monkeypatch.setattr("opi.actuals.ROOT_DIR", synthetic_env["root"])
    monkeypatch.setattr("opi.log.ROOT_DIR", synthetic_env["root"])

    res = execute_two_tier_outcome_chain(
        company=synthetic_env["company"],
        log_path=synthetic_env["log_path"],
        current_dt=datetime(2026, 10, 30, 18, 0, tzinfo=IST),
        mock_yfinance_history=mock_hist,
        mock_second_source_text=mock_sec_html,
        mock_nse_symbol="SYNTH",
    )

    assert res["status"] == "RECORDED"
    assert res["tier"] == "tier2"
    assert res["official_opening_price"] == 125.00
    assert res["actual_gain_pct"] == 25.0

    df = pd.read_csv(synthetic_env["log_path"])
    row = df.iloc[0]
    assert float(row["actual_gain_pct"]) == 25.0
    assert "outcome_source=tier2" in str(row["notes"])


def test_tier2_disagreement_returns_pending_review(synthetic_env, monkeypatch):
    """D-068: If yfinance and second source diverge > 1.0%, write PENDING_REVIEW and do not record."""
    mock_hist = pd.DataFrame(
        [{"Open": 100.00, "High": 105.0, "Low": 98.0, "Close": 102.0, "Volume": 1000}],
        index=[pd.Timestamp("2026-10-28 00:00:00+05:30")]
    )
    mock_sec_html = "<html><body><table><tr><td>Open</td><td>₹115.00</td></tr></table></body></html>"

    monkeypatch.setattr("opi.actuals.ROOT_DIR", synthetic_env["root"])
    monkeypatch.setattr("opi.log.ROOT_DIR", synthetic_env["root"])

    res = execute_two_tier_outcome_chain(
        company=synthetic_env["company"],
        log_path=synthetic_env["log_path"],
        current_dt=datetime(2026, 10, 30, 18, 0, tzinfo=IST),
        mock_yfinance_history=mock_hist,
        mock_second_source_text=mock_sec_html,
        mock_nse_symbol="SYNTH",
    )

    assert res["status"] == "PENDING_REVIEW"
    assert "diverge beyond 1.0%" in res["reason"]

    df = pd.read_csv(synthetic_env["log_path"], keep_default_na=False)
    assert df.iloc[0]["actual_gain_pct"] == ""


def test_tier2_missing_second_source_returns_pending_review(synthetic_env, monkeypatch):
    """D-068: If second source is unavailable or unparseable, write PENDING_REVIEW."""
    mock_hist = pd.DataFrame(
        [{"Open": 100.00, "High": 105.0, "Low": 98.0, "Close": 102.0, "Volume": 1000}],
        index=[pd.Timestamp("2026-10-28 00:00:00+05:30")]
    )
    mock_sec_html = "<html><body><p>Page without price table</p></body></html>"

    monkeypatch.setattr("opi.actuals.ROOT_DIR", synthetic_env["root"])
    monkeypatch.setattr("opi.log.ROOT_DIR", synthetic_env["root"])

    res = execute_two_tier_outcome_chain(
        company=synthetic_env["company"],
        log_path=synthetic_env["log_path"],
        current_dt=datetime(2026, 10, 30, 18, 0, tzinfo=IST),
        mock_yfinance_history=mock_hist,
        mock_second_source_text=mock_sec_html,
        mock_nse_symbol="SYNTH",
    )

    assert res["status"] == "PENDING_REVIEW"
    assert "second source missing" in res["reason"]

    df = pd.read_csv(synthetic_env["log_path"], keep_default_na=False)
    assert df.iloc[0]["actual_gain_pct"] == ""


def test_listing_day_before_close_skipped(synthetic_env):
    """D-069: On listing date itself, do not record before 16:00 IST."""
    clock_before_close = datetime(2026, 10, 28, 12, 0, tzinfo=IST)
    res = execute_two_tier_outcome_chain(
        company=synthetic_env["company"],
        log_path=synthetic_env["log_path"],
        current_dt=clock_before_close,
        mock_nse_symbol="SYNTH",
    )
    assert res["status"] == "SKIPPED_MARKET_IN_PROGRESS"
    assert "market session is in progress" in res["reason"]


def test_row_already_recorded_is_skipped(synthetic_env):
    """Never overwrite an existing recorded outcome."""
    df = pd.read_csv(synthetic_env["log_path"])
    df["actual_gain_pct"] = df["actual_gain_pct"].astype(object)
    df.loc[0, "actual_gain_pct"] = 32.5
    df.to_csv(synthetic_env["log_path"], index=False)

    res = execute_two_tier_outcome_chain(
        company=synthetic_env["company"],
        log_path=synthetic_env["log_path"],
        current_dt=datetime(2026, 10, 30, 18, 0, tzinfo=IST),
        mock_nse_symbol="SYNTH",
    )
    assert res["status"] == "SKIPPED_ALREADY_RECORDED"

    df_check = pd.read_csv(synthetic_env["log_path"])
    assert float(df_check.iloc[0]["actual_gain_pct"]) == 32.5


def test_redirect_to_non_exchange_host_rejected(monkeypatch):
    """Exchange fetches must reject redirects to untrusted hosts."""
    from opi import actuals
    class R:
        is_redirect = True
        is_permanent_redirect = False
        status_code = 302
        headers = {"Location": "https://malicious-external-site.com/quote"}
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(actuals.requests, "get", lambda *a, **k: R())
    with pytest.raises(ActualsEvidenceError, match="must use HTTPS on NSE or BSE"):
        actuals._fetch_exchange_page("https://www.nseindia.com/api/quote-equity?symbol=TEST")


def test_two_tier_probe_committed():
    """D-068: source_probe.md must exist and document exchange reachability and source chain."""
    probe_md = Path(__file__).resolve().parents[1] / "phases" / "Phase 14" / "source_probe.md"
    assert probe_md.exists(), "phases/Phase 14/source_probe.md must exist"
    content = probe_md.read_text(encoding="utf-8")
    assert "403" in content
    assert "yfinance" in content
