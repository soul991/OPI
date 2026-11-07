#!/usr/bin/env python3
"""tests/test_actuals_exchange_policy.py - Tests for primary exchange outcome policy (D-105, Workstream C).

Validates:
1. Dual-listed (NSE+BSE) IPO with two independent NSE values agreeing <= 1.0% -> RECORDED on NSE.
2. Dual-listed IPO with 1 NSE value and 1 BSE value only -> NOT recorded (SKIPPED_POLICY_NO_PRIMARY_EXCHANGE_MAJORITY).
3. Sole BSE listing (no NSE listing) -> BSE values compared and recorded.
4. Yahoo Finance and Yahoo-derived sources count strictly as one publisher (cannot form 2-source majority alone).
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from opi.actuals import record_actual_from_tier2_arbitrated


@pytest.fixture
def policy_test_env(tmp_path: Path):
    """Isolated environment with prediction log containing an unrecorded forward row."""
    log_dir = tmp_path / "predictions"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "prediction_log.csv"

    features_json = json.dumps({
        "issue_price": 100.0,
        "nse_symbol": "TESTSYM",
        "bse_code": "500001",
        "overview_url": "https://www.chittorgarh.com/ipo/test-ipo/1000/",
    })
    rows = [
        {
            "scored_at": "2026-10-31T18:30:00+05:30",
            "company": "Test Exchange Policy Corp",
            "listing_date": "2026-11-03",
            "close_date": "2026-10-31",
            "pred_gain_pct": "20.0",
            "pred_prob_gt10": "0.75",
            "gmp_pct_at_scoring": "18.0",
            "actual_gain_pct": "",
            "status": "FORWARD",
            "notes": "",
            "model_version": "v4.0.0-champion",
            "features_snapshot_json": features_json
        }
    ]
    pd.DataFrame(rows).to_csv(log_file, index=False)

    return {
        "root": tmp_path,
        "log_path": log_file,
        "company": "Test Exchange Policy Corp",
        "listing_date": date(2026, 11, 3),
        "issue_price": Decimal("100.0"),
    }


def test_nse_listed_dual_source_agreement_recorded(policy_test_env, monkeypatch):
    """NSE-listed IPO with 2 independent NSE sources agreeing within 1.0% -> recorded on NSE."""
    root = policy_test_env["root"]
    monkeypatch.setattr("opi.actuals.ROOT_DIR", root)
    monkeypatch.setattr("opi.log.ROOT_DIR", root)

    sources = [
        {"publisher": "Yahoo Finance", "exchange": "NSE", "quantity": "open", "bar_date": "2026-11-03", "value": 250.0},
        {"publisher": "Groww", "exchange": "NSE", "quantity": "open", "bar_date": "2026-11-03", "value": 251.0},
        {"publisher": "Chittorgarh", "exchange": "BSE", "quantity": "open", "bar_date": "2026-11-03", "value": 244.0},
    ]

    res = record_actual_from_tier2_arbitrated(
        company=policy_test_env["company"],
        listing_date=policy_test_env["listing_date"],
        issue_price=policy_test_env["issue_price"],
        nse_symbol="TESTSYM",
        bse_code="500001",
        overview_url="https://www.chittorgarh.com/ipo/test-ipo/1000/",
        log_path=policy_test_env["log_path"],
        initial_sources=[sources[0], sources[2]],
        mock_additional_sources=[sources[1]],
    )

    assert res["status"] == "RECORDED"
    assert res["tier"] == "tier2_arbitrated"
    assert res["manifest"]["exchange"] == "NSE"
    assert res["official_opening_price"] == 250.5


def test_dual_listed_cross_exchange_only_rejected(policy_test_env, monkeypatch):
    """Dual-listed IPO with 1 NSE source and 1 BSE source only -> rejected under primary exchange policy."""
    root = policy_test_env["root"]
    monkeypatch.setattr("opi.actuals.ROOT_DIR", root)
    monkeypatch.setattr("opi.log.ROOT_DIR", root)

    sources = [
        {"publisher": "Yahoo Finance", "exchange": "NSE", "quantity": "open", "bar_date": "2026-11-03", "value": 248.0},
        {"publisher": "Chittorgarh", "exchange": "BSE", "quantity": "open", "bar_date": "2026-11-03", "value": 244.1},
    ]

    res = record_actual_from_tier2_arbitrated(
        company=policy_test_env["company"],
        listing_date=policy_test_env["listing_date"],
        issue_price=policy_test_env["issue_price"],
        nse_symbol="TESTSYM",
        bse_code="500001",
        overview_url="https://www.chittorgarh.com/ipo/test-ipo/1000/",
        log_path=policy_test_env["log_path"],
        initial_sources=sources,
        mock_additional_sources=[],
    )

    assert res["status"] == "PENDING_REVIEW"
    assert "SKIPPED_POLICY_NO_PRIMARY_EXCHANGE_MAJORITY" in res["reason"]


def test_sole_bse_listing_bse_sources_recorded(policy_test_env, monkeypatch):
    """Sole BSE listing (no NSE symbol) -> BSE values compared and recorded on BSE."""
    root = policy_test_env["root"]
    monkeypatch.setattr("opi.actuals.ROOT_DIR", root)
    monkeypatch.setattr("opi.log.ROOT_DIR", root)

    sources = [
        {"publisher": "Yahoo Finance", "exchange": "BSE", "quantity": "open", "bar_date": "2026-11-03", "value": 120.0},
        {"publisher": "Chittorgarh", "exchange": "BSE", "quantity": "open", "bar_date": "2026-11-03", "value": 120.5},
    ]

    res = record_actual_from_tier2_arbitrated(
        company=policy_test_env["company"],
        listing_date=policy_test_env["listing_date"],
        issue_price=policy_test_env["issue_price"],
        nse_symbol=None,  # Sole BSE listing
        bse_code="544994",
        overview_url="https://www.chittorgarh.com/ipo/test-ipo/1000/",
        log_path=policy_test_env["log_path"],
        initial_sources=sources,
        mock_additional_sources=[],
    )

    assert res["status"] == "RECORDED"
    assert res["tier"] == "tier2_arbitrated"
    assert res["manifest"]["exchange"] == "BSE"
    assert res["official_opening_price"] == 120.25


def test_yahoo_counted_once_cannot_form_majority_alone(policy_test_env, monkeypatch):
    """Yahoo Finance and Yahoo mirror count as 1 publisher; cannot form majority alone on primary exchange."""
    root = policy_test_env["root"]
    monkeypatch.setattr("opi.actuals.ROOT_DIR", root)
    monkeypatch.setattr("opi.log.ROOT_DIR", root)

    sources = [
        {"publisher": "Yahoo Finance", "exchange": "NSE", "quantity": "open", "bar_date": "2026-11-03", "value": 250.0},
        {"publisher": "Yahoo Finance Aggregator", "exchange": "NSE", "quantity": "open", "bar_date": "2026-11-03", "value": 250.0},
        {"publisher": "Chittorgarh", "exchange": "BSE", "quantity": "open", "bar_date": "2026-11-03", "value": 240.0},
    ]

    res = record_actual_from_tier2_arbitrated(
        company=policy_test_env["company"],
        listing_date=policy_test_env["listing_date"],
        issue_price=policy_test_env["issue_price"],
        nse_symbol="TESTSYM",
        bse_code="500001",
        overview_url="https://www.chittorgarh.com/ipo/test-ipo/1000/",
        log_path=policy_test_env["log_path"],
        initial_sources=sources,
        mock_additional_sources=[],
    )

    assert res["status"] == "PENDING_REVIEW"
    assert "SKIPPED_POLICY_NO_PRIMARY_EXCHANGE_MAJORITY" in res["reason"]
