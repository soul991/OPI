#!/usr/bin/env python3
"""tests/test_actuals_manifest.py - Tests for exchange and quantity source labelling (D-101, Workstream A).

Validates:
1. Yahoo Finance source labelling (.NS -> NSE, .BO -> BSE, other -> UNKNOWN).
2. Page-level exchange and quantity extraction on synthetic fixtures (Chittorgarh, Groww).
3. UNKNOWN recorded when exchange cannot be read from the page (never guessed).
4. Manifests produced by Tier 2 and Tier 2b include exchange, quantity, source_publisher,
   and source_values list.
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
    make_yfinance_source_value,
    parse_source_value_metadata,
    record_actual_from_tier2,
    record_actual_from_tier2b,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_yfinance_symbol_exchange_labelling():
    """Verify Yahoo Finance symbol parsing maps .NS to NSE, .BO to BSE, others to UNKNOWN."""
    d = date(2026, 11, 3)

    v_nse = make_yfinance_source_value("BLSPOLY.NS", d, 248.0)
    assert v_nse["publisher"] == "Yahoo Finance"
    assert v_nse["exchange"] == "NSE"
    assert v_nse["quantity"] == "open"
    assert v_nse["bar_date"] == "2026-11-03"
    assert v_nse["value"] == 248.0

    v_bse = make_yfinance_source_value("544321.BO", d, 244.1)
    assert v_bse["publisher"] == "Yahoo Finance"
    assert v_bse["exchange"] == "BSE"
    assert v_bse["quantity"] == "open"
    assert v_bse["bar_date"] == "2026-11-03"
    assert v_bse["value"] == 244.1

    v_unk = make_yfinance_source_value("GLOBAL.L", d, 150.0)
    assert v_unk["publisher"] == "Yahoo Finance"
    assert v_unk["exchange"] == "UNKNOWN"
    assert v_unk["quantity"] == "open"
    assert v_unk["value"] == 150.0


def test_chittorgarh_fixture_bse_labelling():
    """Chittorgarh page with explicit BSE table labels BSE, open."""
    html_path = FIXTURES_DIR / "synthetic_chittorgarh_bse.html"
    assert html_path.exists(), "Synthetic fixture must exist"
    content = html_path.read_text(encoding="utf-8")

    meta = parse_source_value_metadata(
        content=content,
        target_date=date(2026, 11, 3),
        publisher="Chittorgarh",
        url="https://www.chittorgarh.com/ipo/synthetic-ipo/1000/",
    )
    assert meta["publisher"] == "Chittorgarh"
    assert meta["exchange"] == "BSE"
    assert meta["quantity"] == "open"
    assert meta["value"] == 244.10


def test_chittorgarh_fixture_nse_labelling():
    """Chittorgarh page with explicit NSE table labels NSE, open."""
    html_path = FIXTURES_DIR / "synthetic_chittorgarh_nse.html"
    assert html_path.exists(), "Synthetic fixture must exist"
    content = html_path.read_text(encoding="utf-8")

    meta = parse_source_value_metadata(
        content=content,
        target_date=date(2026, 11, 3),
        publisher="Chittorgarh",
        url="https://www.chittorgarh.com/ipo/synthetic-ipo/1000/",
    )
    assert meta["publisher"] == "Chittorgarh"
    assert meta["exchange"] == "NSE"
    assert meta["quantity"] == "open"
    assert meta["value"] == 248.00


def test_chittorgarh_fixture_unknown_labelling():
    """Chittorgarh page without explicit exchange labels UNKNOWN (never guesses BSE)."""
    html_path = FIXTURES_DIR / "synthetic_chittorgarh_unknown.html"
    assert html_path.exists(), "Synthetic fixture must exist"
    content = html_path.read_text(encoding="utf-8")

    meta = parse_source_value_metadata(
        content=content,
        target_date=date(2026, 11, 3),
        publisher="Chittorgarh",
        url="https://www.chittorgarh.com/ipo/synthetic-ipo/1000/",
    )
    assert meta["publisher"] == "Chittorgarh"
    assert meta["exchange"] == "UNKNOWN"
    assert meta["quantity"] == "open"
    assert meta["value"] == 244.10


def test_groww_fixture_nse_labelling():
    """Groww article with explicit NSE text labels NSE, listing_price."""
    html_path = FIXTURES_DIR / "synthetic_groww_nse.html"
    assert html_path.exists(), "Synthetic fixture must exist"
    content = html_path.read_text(encoding="utf-8")

    meta = parse_source_value_metadata(
        content=content,
        target_date=date(2026, 11, 3),
        publisher="Groww",
        url="https://groww.in/blog/synthetic-ipo-listing",
    )
    assert meta["publisher"] == "Groww"
    assert meta["exchange"] == "NSE"
    assert meta["quantity"] == "listing_price"
    assert meta["value"] == 248.00


def test_groww_fixture_bse_labelling():
    """Groww article with explicit BSE text labels BSE, listing_price."""
    html_path = FIXTURES_DIR / "synthetic_groww_bse.html"
    assert html_path.exists(), "Synthetic fixture must exist"
    content = html_path.read_text(encoding="utf-8")

    meta = parse_source_value_metadata(
        content=content,
        target_date=date(2026, 11, 3),
        publisher="Groww",
        url="https://groww.in/blog/synthetic-ipo-listing",
    )
    assert meta["publisher"] == "Groww"
    assert meta["exchange"] == "BSE"
    assert meta["quantity"] == "listing_price"
    assert meta["value"] == 244.10


def test_groww_fixture_unknown_labelling():
    """Groww article without exchange text labels UNKNOWN (never guesses NSE)."""
    html_path = FIXTURES_DIR / "synthetic_groww_unknown.html"
    assert html_path.exists(), "Synthetic fixture must exist"
    content = html_path.read_text(encoding="utf-8")

    meta = parse_source_value_metadata(
        content=content,
        target_date=date(2026, 11, 3),
        publisher="Groww",
        url="https://groww.in/blog/synthetic-ipo-listing",
    )
    assert meta["publisher"] == "Groww"
    assert meta["exchange"] == "UNKNOWN"
    assert meta["quantity"] == "open"
    assert meta["value"] == 248.00


def test_source_value_labelling_and_manifest_fields(tmp_path: Path, monkeypatch):
    """Tier 2 manifest must contain top-level exchange, quantity, source_publisher, and source_values."""
    monkeypatch.setattr("opi.actuals.ROOT_DIR", tmp_path)
    monkeypatch.setattr("opi.log.ROOT_DIR", tmp_path)

    log_dir = tmp_path / "predictions"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "prediction_log.csv"

    # Forward row for Synthetic IPO
    features_json = json.dumps({
        "issue_price": 100.0,
        "nse_symbol": "SYNTH",
        "bse_code": "599999",
        "overview_url": "https://www.chittorgarh.com/ipo/synthetic-corp-ipo/9999/",
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
            "notes": "",
            "model_version": "v4.0.0-champion",
            "features_snapshot_json": features_json
        }
    ]
    pd.DataFrame(rows).to_csv(log_file, index=False)

    mock_hist = pd.DataFrame(
        [{"Open": 110.00, "High": 115.0, "Low": 108.0, "Close": 112.0, "Volume": 1000}],
        index=[pd.Timestamp("2026-10-28 00:00:00+05:30")]
    )
    mock_sec_html = (
        "<html><body>"
        "<div class='nse-listing'><h3>NSE Listing Day</h3>"
        "<table><tr><td>Open</td><td>₹110.50</td></tr></table>"
        "</div></body></html>"
    )

    res = record_actual_from_tier2(
        company="Synthetic Corp",
        listing_date=date(2026, 10, 28),
        issue_price=Decimal("100.0"),
        nse_symbol="SYNTH",
        bse_code="599999",
        overview_url="https://www.chittorgarh.com/ipo/synthetic-corp-ipo/9999/",
        quote_url=None,
        log_path=log_file,
        mock_yfinance_history=mock_hist,
        mock_second_source_text=mock_sec_html,
    )

    assert res["status"] == "RECORDED"
    manifest = res["manifest"]

    # Top-level Workstream A fields
    assert manifest["exchange"] == "NSE"
    assert manifest["quantity"] == "open"
    assert manifest["source_publisher"] == "Yahoo Finance"

    # source_values array
    assert "source_values" in manifest
    assert len(manifest["source_values"]) == 2

    # yfinance source value
    yf_val = manifest["source_values"][0]
    assert yf_val["publisher"] == "Yahoo Finance"
    assert yf_val["exchange"] == "NSE"
    assert yf_val["quantity"] == "open"
    assert yf_val["bar_date"] == "2026-10-28"
    assert yf_val["value"] == 110.00

    # Chittorgarh source value
    cg_val = manifest["source_values"][1]
    assert cg_val["publisher"] == "Chittorgarh"
    assert cg_val["exchange"] == "NSE"
    assert cg_val["quantity"] == "open"
    assert cg_val["bar_date"] == "2026-10-28"
    assert cg_val["value"] == 110.50
