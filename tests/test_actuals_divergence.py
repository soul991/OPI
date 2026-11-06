#!/usr/bin/env python3
"""tests/test_actuals_divergence.py - Tests for pre-registered divergence arbitration (D-100, Workstream B).

Validates:
1. Strict 1.0% relative tolerance constant asserted directly (TOLERANCE_PCT == 1.0).
2. Strict majority of 2 of 3 sources recorded as tier2_arbitrated.
3. 1 vs 1 divergence not recorded (SKIPPED_ARBITRATION_NO_MAJORITY).
4. Exchange mismatch not recorded (SKIPPED_ARBITRATION_EXCHANGE_MISMATCH).
5. Unlabelled values (UNKNOWN exchange) excluded from agreement.
6. Yahoo-derived sources deduplicated to single publisher.
7. Already recorded rows untouched (SKIPPED_ALREADY_RECORDED).
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from opi.actuals import (
    TOLERANCE_PCT,
    execute_two_tier_outcome_chain,
    record_actual_from_tier2_arbitrated,
)


def test_tolerance_pct_constant():
    """Phase 19 Inviolable Guardrail: The 1.0% relative tolerance constant must not be loosened."""
    assert TOLERANCE_PCT == 1.0, f"Expected TOLERANCE_PCT == 1.0, found {TOLERANCE_PCT}"


@pytest.fixture
def divergence_env(tmp_path: Path):
    """Set up an isolated prediction log with an unrecorded forward row."""
    log_dir = tmp_path / "predictions"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "prediction_log.csv"

    features_json = json.dumps({
        "issue_price": 150.0,
        "nse_symbol": "BLSPOLY",
        "bse_code": "544321",
        "overview_url": "https://www.chittorgarh.com/ipo/bls-polymers-ipo/3200/",
    })
    rows = [
        {
            "scored_at": "2026-10-31T18:30:00+05:30",
            "company": "BLS Polymers Limited",
            "listing_date": "2026-11-03",
            "close_date": "2026-10-31",
            "pred_gain_pct": "60.0",
            "pred_prob_gt10": "0.95",
            "gmp_pct_at_scoring": "55.0",
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
        "company": "BLS Polymers Limited",
        "listing_date": date(2026, 11, 3),
        "issue_price": Decimal("150.0"),
    }


def test_arbitration_strict_majority_2_of_3_recorded(divergence_env, monkeypatch):
    """2 of 3 independent sources agree on (NSE, open): strict majority -> recorded as tier2_arbitrated."""
    monkeypatch.setattr("opi.actuals.ROOT_DIR", divergence_env["root"])
    monkeypatch.setattr("opi.log.ROOT_DIR", divergence_env["root"])

    sources = [
        {
            "publisher": "Yahoo Finance",
            "exchange": "NSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 248.0,
            "source_url": "https://finance.yahoo.com/quote/BLSPOLY.NS",
        },
        {
            "publisher": "Chittorgarh",
            "exchange": "NSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 244.1,
            "source_url": "https://www.chittorgarh.com/ipo/bls-polymers-ipo/3200/",
        },
        {
            "publisher": "Groww",
            "exchange": "NSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 248.0,
            "source_url": "https://groww.in/blog/bls-polymers-ipo-listing",
        },
    ]

    res = record_actual_from_tier2_arbitrated(
        company=divergence_env["company"],
        listing_date=divergence_env["listing_date"],
        issue_price=divergence_env["issue_price"],
        nse_symbol="BLSPOLY",
        bse_code="544321",
        overview_url="https://www.chittorgarh.com/ipo/bls-polymers-ipo/3200/",
        log_path=divergence_env["log_path"],
        initial_sources=[sources[0], sources[1]],
        mock_additional_sources=[sources[2]],
    )

    assert res["status"] == "RECORDED"
    assert res["tier"] == "tier2_arbitrated"
    assert res["official_opening_price"] == 248.0
    # Gain on 150 issue price: (248 - 150) / 150 * 100 = 65.33%
    assert res["actual_gain_pct"] == 65.33

    manifest = res["manifest"]
    assert manifest["outcome_source"] == "tier2_arbitrated"
    assert manifest["exchange"] == "NSE"
    assert manifest["quantity"] == "open"
    assert "Groww" in manifest["source_publisher"]
    assert "Yahoo Finance" in manifest["source_publisher"]
    assert len(manifest["source_values"]) == 3

    # Confirm all sources carry hypothetical gains
    for s in manifest["source_values"]:
        assert "hypothetical_gain_pct" in s
        assert s["hypothetical_gain_pct"] is not None

    # Check prediction log was updated
    df = pd.read_csv(divergence_env["log_path"], keep_default_na=False)
    assert float(df.iloc[0]["actual_gain_pct"]) == 65.33
    assert "tier2_arbitrated" in str(df.iloc[0]["notes"])


def test_arbitration_one_vs_one_rejected_no_majority(divergence_env, monkeypatch):
    """1 vs 1 divergence without third agreeing source: rejected with SKIPPED_ARBITRATION_NO_MAJORITY."""
    monkeypatch.setattr("opi.actuals.ROOT_DIR", divergence_env["root"])
    monkeypatch.setattr("opi.log.ROOT_DIR", divergence_env["root"])

    sources = [
        {
            "publisher": "Yahoo Finance",
            "exchange": "NSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 248.0,
        },
        {
            "publisher": "Chittorgarh",
            "exchange": "NSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 244.1,
        },
    ]

    res = record_actual_from_tier2_arbitrated(
        company=divergence_env["company"],
        listing_date=divergence_env["listing_date"],
        issue_price=divergence_env["issue_price"],
        nse_symbol="BLSPOLY",
        bse_code="544321",
        overview_url="https://www.chittorgarh.com/ipo/bls-polymers-ipo/3200/",
        log_path=divergence_env["log_path"],
        initial_sources=sources,
        mock_additional_sources=[],
    )

    assert res["status"] == "PENDING_REVIEW"
    assert "SKIPPED_ARBITRATION_NO_MAJORITY" in res["reason"]

    # Verify prediction log was untouched
    df = pd.read_csv(divergence_env["log_path"], keep_default_na=False)
    assert df.iloc[0]["actual_gain_pct"] == ""


def test_arbitration_exchange_mismatch_rejected(divergence_env, monkeypatch):
    """Sources on different exchanges without intra-exchange agreement -> SKIPPED_ARBITRATION_EXCHANGE_MISMATCH."""
    monkeypatch.setattr("opi.actuals.ROOT_DIR", divergence_env["root"])
    monkeypatch.setattr("opi.log.ROOT_DIR", divergence_env["root"])

    sources = [
        {
            "publisher": "Yahoo Finance",
            "exchange": "NSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 248.0,
        },
        {
            "publisher": "Chittorgarh",
            "exchange": "BSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 244.1,
        },
    ]

    res = record_actual_from_tier2_arbitrated(
        company=divergence_env["company"],
        listing_date=divergence_env["listing_date"],
        issue_price=divergence_env["issue_price"],
        nse_symbol="BLSPOLY",
        bse_code="544321",
        overview_url="https://www.chittorgarh.com/ipo/bls-polymers-ipo/3200/",
        log_path=divergence_env["log_path"],
        initial_sources=sources,
        mock_additional_sources=[],
    )

    assert res["status"] == "PENDING_REVIEW"
    assert "SKIPPED_ARBITRATION_EXCHANGE_MISMATCH" in res["reason"]


def test_arbitration_unlabelled_values_excluded(divergence_env, monkeypatch):
    """Sources with UNKNOWN exchange are excluded from arbitration agreement."""
    monkeypatch.setattr("opi.actuals.ROOT_DIR", divergence_env["root"])
    monkeypatch.setattr("opi.log.ROOT_DIR", divergence_env["root"])

    sources = [
        {
            "publisher": "Yahoo Finance",
            "exchange": "NSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 248.0,
        },
        {
            "publisher": "Source B",
            "exchange": "UNKNOWN",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 248.0,
        },
        {
            "publisher": "Source C",
            "exchange": "UNKNOWN",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 248.0,
        },
    ]

    res = record_actual_from_tier2_arbitrated(
        company=divergence_env["company"],
        listing_date=divergence_env["listing_date"],
        issue_price=divergence_env["issue_price"],
        nse_symbol="BLSPOLY",
        bse_code="544321",
        overview_url="https://www.chittorgarh.com/ipo/bls-polymers-ipo/3200/",
        log_path=divergence_env["log_path"],
        initial_sources=sources,
        mock_additional_sources=[],
    )

    assert res["status"] == "PENDING_REVIEW"
    assert "SKIPPED_ARBITRATION" in res["reason"]


def test_arbitration_yahoo_derived_counted_once(divergence_env, monkeypatch):
    """Yahoo Finance and a Yahoo-derived source count as 1 publisher; cannot form 2-publisher majority alone."""
    monkeypatch.setattr("opi.actuals.ROOT_DIR", divergence_env["root"])
    monkeypatch.setattr("opi.log.ROOT_DIR", divergence_env["root"])

    sources = [
        {
            "publisher": "Yahoo Finance",
            "exchange": "NSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 248.0,
        },
        {
            "publisher": "Yahoo Scraper Mirror",
            "exchange": "NSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 248.0,
        },
        {
            "publisher": "Chittorgarh",
            "exchange": "NSE",
            "quantity": "open",
            "bar_date": "2026-11-03",
            "value": 244.1,
        },
    ]

    res = record_actual_from_tier2_arbitrated(
        company=divergence_env["company"],
        listing_date=divergence_env["listing_date"],
        issue_price=divergence_env["issue_price"],
        nse_symbol="BLSPOLY",
        bse_code="544321",
        overview_url="https://www.chittorgarh.com/ipo/bls-polymers-ipo/3200/",
        log_path=divergence_env["log_path"],
        initial_sources=sources,
        mock_additional_sources=[],
    )

    # Deduped publishers: Yahoo Finance (248.0) and Chittorgarh (244.1) -> 1 vs 1 -> no majority
    assert res["status"] == "PENDING_REVIEW"
    assert "SKIPPED_ARBITRATION_NO_MAJORITY" in res["reason"]


def test_arbitration_already_recorded_row_untouched(divergence_env, monkeypatch):
    """Never overwrite a row that already has an actual outcome recorded."""
    monkeypatch.setattr("opi.actuals.ROOT_DIR", divergence_env["root"])
    monkeypatch.setattr("opi.log.ROOT_DIR", divergence_env["root"])

    df = pd.read_csv(divergence_env["log_path"])
    df["actual_gain_pct"] = df["actual_gain_pct"].astype(object)
    df.loc[0, "actual_gain_pct"] = 62.0
    df.to_csv(divergence_env["log_path"], index=False)

    res = record_actual_from_tier2_arbitrated(
        company=divergence_env["company"],
        listing_date=divergence_env["listing_date"],
        issue_price=divergence_env["issue_price"],
        nse_symbol="BLSPOLY",
        bse_code="544321",
        overview_url="https://www.chittorgarh.com/ipo/bls-polymers-ipo/3200/",
        log_path=divergence_env["log_path"],
        initial_sources=[],
    )

    assert res["status"] == "SKIPPED_ALREADY_RECORDED"
    df_check = pd.read_csv(divergence_env["log_path"])
    assert float(df_check.iloc[0]["actual_gain_pct"]) == 62.0
