"""test_market_evidence_job.py - Unit tests for automated market evidence recording (D-085, D-086)."""

import datetime as dt
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from opi.market import (
    ensure_market_evidence_for_listed_dates,
    fetch_market_history,
)

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_job_records_missing_listing_date_nifty_evidence(tmp_path):
    """Verify that ensure_market_evidence_for_listed_dates writes .raw and .json for missing dates (D-085)."""
    # Create synthetic prediction log with one listed row having actual outcome
    log_file = tmp_path / "prediction_log.csv"
    df = pd.DataFrame([{
        "company": "Synthetic Listed IPO",
        "listing_date": "2026-11-02",
        "status": "FORWARD",
        "actual_gain_pct": "5.50",
    }])
    df.to_csv(log_file, index=False)

    market_dir = tmp_path / "evidence" / "market"
    run_log_file = tmp_path / "run_log.csv"

    # Mock yfinance Ticker history
    mock_nifty_df = pd.DataFrame(
        {
            "Open": [24000.0, 24100.0, 24200.0],
            "High": [24150.0, 24250.0, 24300.0],
            "Low": [23950.0, 24050.0, 24150.0],
            "Close": [24050.0, 24150.0, 24250.0],
            "Volume": [1000, 2000, 3000],
        },
        index=[
            pd.Timestamp("2026-10-31"),
            pd.Timestamp("2026-11-01"),
            pd.Timestamp("2026-11-02"),
        ],
    )
    mock_vix_df = pd.DataFrame(
        {"Close": [14.5, 15.0, 15.2]},
        index=[
            pd.Timestamp("2026-10-31"),
            pd.Timestamp("2026-11-01"),
            pd.Timestamp("2026-11-02"),
        ],
    )

    mock_nifty_ticker = MagicMock()
    mock_nifty_ticker.history.return_value = mock_nifty_df
    mock_vix_ticker = MagicMock()
    mock_vix_ticker.history.return_value = mock_vix_df

    def mock_ticker(sym):
        if sym == "^NSEI":
            return mock_nifty_ticker
        return mock_vix_ticker

    with patch("yfinance.Ticker", side_effect=mock_ticker):
        with patch("opi.log.RUN_LOG_PATH", run_log_file):
            res = ensure_market_evidence_for_listed_dates(
                log_path=log_file,
                save=True,
                overwrite=False,
                market_dir=market_dir,
                run_id="run_test_001",
            )

    assert res["status"] == "OK"
    assert "2026-11-02" in res["recorded"]

    raw_file = market_dir / "2026-11-02_nifty.raw"
    json_file = market_dir / "2026-11-02_nifty.json"

    assert raw_file.exists(), "Raw evidence file must be created"
    assert json_file.exists(), "Parsed JSON evidence file must be created"

    parsed = json.loads(json_file.read_text(encoding="utf-8"))
    assert parsed["as_of_date"] == "2026-11-02"
    assert parsed["nifty_close"] == 24250.0
    assert parsed["nifty_prev_close"] == 24150.0
    assert parsed["india_vix"] == 15.2


def test_job_skips_when_market_data_unavailable(tmp_path):
    """Verify that when yfinance returns empty history, it skips without error and logs skip."""
    log_file = tmp_path / "prediction_log.csv"
    df = pd.DataFrame([{
        "company": "Synthetic Listed IPO",
        "listing_date": "2026-11-02",
        "status": "FORWARD",
        "actual_gain_pct": "5.50",
    }])
    df.to_csv(log_file, index=False)

    market_dir = tmp_path / "evidence" / "market"
    run_log_file = tmp_path / "run_log.csv"

    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()  # empty

    with patch("yfinance.Ticker", return_value=mock_ticker):
        with patch("opi.log.RUN_LOG_PATH", run_log_file):
            res = ensure_market_evidence_for_listed_dates(
                log_path=log_file,
                save=True,
                overwrite=False,
                market_dir=market_dir,
                run_id="run_test_002",
            )

    assert res["status"] == "OK"
    assert "2026-11-02" in res["skipped"]
    assert not (market_dir / "2026-11-02_nifty.json").exists()


def test_job_never_overwrites_existing_file(tmp_path):
    """Verify that existing market evidence files are never mutated or overwritten."""
    log_file = tmp_path / "prediction_log.csv"
    df = pd.DataFrame([{
        "company": "Synthetic Listed IPO",
        "listing_date": "2026-11-02",
        "status": "FORWARD",
        "actual_gain_pct": "5.50",
    }])
    df.to_csv(log_file, index=False)

    market_dir = tmp_path / "evidence" / "market"
    market_dir.mkdir(parents=True, exist_ok=True)
    raw_file = market_dir / "2026-11-02_nifty.raw"
    json_file = market_dir / "2026-11-02_nifty.json"

    original_raw = b"ORIGINAL_RAW_CONTENT_DO_NOT_TOUCH"
    original_json = '{"as_of_date": "2026-11-02", "nifty_close": 99999.0}'
    raw_file.write_bytes(original_raw)
    json_file.write_text(original_json, encoding="utf-8")

    # Mock yfinance to return new values
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame(
        {"Open": [20000.0, 21000.0], "High": [21000.0, 22000.0], "Low": [19000.0, 20000.0], "Close": [20500.0, 21500.0]},
        index=[pd.Timestamp("2026-11-01"), pd.Timestamp("2026-11-02")],
    )

    with patch("yfinance.Ticker", return_value=mock_ticker):
        res = ensure_market_evidence_for_listed_dates(
            log_path=log_file,
            save=True,
            overwrite=False,
            market_dir=market_dir,
            run_id="run_test_003",
        )

    # File should not be rewritten
    assert raw_file.read_bytes() == original_raw
    assert json_file.read_text(encoding="utf-8") == original_json


def test_job_records_nifty_evidence_for_unrecorded_past_listing(tmp_path):
    """D-097: Past listing dates without recorded outcomes still receive market evidence, while future dates are excluded."""
    log_file = tmp_path / "prediction_log.csv"
    df = pd.DataFrame([
        {
            "company": "Past Pending IPO",
            "listing_date": "2026-11-03",
            "status": "FORWARD",
            "actual_gain_pct": "",  # Unrecorded outcome!
        },
        {
            "company": "Future Pending IPO",
            "listing_date": "2026-11-25",
            "status": "FORWARD",
            "actual_gain_pct": "",
        }
    ])
    df.to_csv(log_file, index=False)

    market_dir = tmp_path / "evidence" / "market"
    run_log_file = tmp_path / "run_log.csv"

    mock_nifty_df = pd.DataFrame(
        {
            "Open": [24000.0, 24100.0],
            "High": [24150.0, 24250.0],
            "Low": [23950.0, 24050.0],
            "Close": [24050.0, 24150.0],
            "Volume": [1000, 2000],
        },
        index=[
            pd.Timestamp("2026-11-02"),
            pd.Timestamp("2026-11-03"),
        ],
    )
    mock_vix_df = pd.DataFrame(
        {"Close": [14.5, 15.0]},
        index=[
            pd.Timestamp("2026-11-02"),
            pd.Timestamp("2026-11-03"),
        ],
    )

    mock_nifty_ticker = MagicMock()
    mock_nifty_ticker.history.return_value = mock_nifty_df
    mock_vix_ticker = MagicMock()
    mock_vix_ticker.history.return_value = mock_vix_df

    def mock_ticker(sym):
        if sym == "^NSEI":
            return mock_nifty_ticker
        return mock_vix_ticker

    with patch("yfinance.Ticker", side_effect=mock_ticker):
        with patch("opi.log.RUN_LOG_PATH", run_log_file):
            res = ensure_market_evidence_for_listed_dates(
                log_path=log_file,
                save=True,
                overwrite=False,
                market_dir=market_dir,
                run_id="run_test_d097",
            )

    assert res["status"] == "OK"
    assert "2026-11-03" in res["recorded"]
    assert "2026-11-25" not in res["needed_dates"]

    raw_file = market_dir / "2026-11-03_nifty.raw"
    json_file = market_dir / "2026-11-03_nifty.json"

    assert raw_file.exists()
    assert json_file.exists()
    assert not (market_dir / "2026-11-25_nifty.json").exists()
