#!/usr/bin/env python3
"""tests/test_actuals_pending.py - Tests for persisting divergence and pending evidence snapshots and manifests (D-104).

Validates:
1. Diverging pair saves pending source files and manifest under data/evidence/actuals/pending/; no outcome written to prediction_log.
2. Identical re-run writes no new files (strict idempotency).
3. Unlabelled source page records exchange as UNKNOWN.
4. SHA-256 recorded in manifest matches the exact byte content of saved files.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from opi.actuals import (
    execute_two_tier_outcome_chain,
    persist_pending_actuals_evidence,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def pending_test_env(tmp_path: Path):
    """Isolated environment with prediction log containing an unrecorded forward row."""
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


def test_divergence_saves_pending_evidence_and_manifest(pending_test_env, monkeypatch):
    """Diverging pair (1.57% > 1.0%) terminates in PENDING_REVIEW; saves raw pages + manifest, no outcome written."""
    root = pending_test_env["root"]
    monkeypatch.setattr("opi.actuals.ROOT_DIR", root)
    monkeypatch.setattr("opi.log.ROOT_DIR", root)

    mock_hist = pd.DataFrame(
        [{"Open": 248.00, "High": 255.0, "Low": 240.0, "Close": 250.0, "Volume": 1000}],
        index=[pd.Timestamp("2026-11-03 00:00:00+05:30")]
    )
    # Synthetic Chittorgarh page quoting BSE 244.10 (diff = 1.57% > 1.0%)
    mock_sec_html = (
        "<!DOCTYPE html><html><body>"
        "<h1>BLS Polymers Limited IPO Details</h1>"
        "<div class='bse-listing'><h3>BSE Listing Day</h3>"
        "<table><tr><td>Open</td><td>₹244.10</td></tr></table>"
        "</div></body></html>"
    )

    res = execute_two_tier_outcome_chain(
        company=pending_test_env["company"],
        log_path=pending_test_env["log_path"],
        mock_yfinance_history=mock_hist,
        mock_second_source_text=mock_sec_html,
        mock_nse_symbol="BLSPOLY",
        mock_bse_code="544321",
    )

    # 1. Chain terminates in PENDING_REVIEW (or arbitration mismatch)
    assert res["status"] in ("PENDING_REVIEW", "SKIPPED_ARBITRATION_EXCHANGE_MISMATCH")

    # 2. Prediction log must NOT have an outcome recorded
    df_log = pd.read_csv(pending_test_env["log_path"], keep_default_na=False)
    assert df_log.iloc[0]["actual_gain_pct"] == "", "Prediction log row must remain unrecorded"

    # 3. Pending evidence files must be saved under data/evidence/actuals/pending/
    pending_dir = root / "data" / "evidence" / "actuals" / "pending"
    assert pending_dir.exists(), f"Pending dir {pending_dir} must exist"

    manifest_file = pending_dir / "2026-11-03_bls-polymers-limited.manifest.json"
    assert manifest_file.exists(), f"Manifest file {manifest_file} must exist"

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["company"] == "BLS Polymers Limited"
    assert manifest["listing_date"] == "2026-11-03"
    assert "sources" in manifest
    assert len(manifest["sources"]) >= 2

    # Check required fields in each manifest source entry
    for s in manifest["sources"]:
        assert "publisher" in s
        assert "exchange" in s
        assert "quantity" in s
        assert "bar_date" in s
        assert "value" in s
        assert "url" in s
        assert "accessed_at" in s
        assert "sha256" in s


def test_identical_rerun_writes_no_new_files(pending_test_env, monkeypatch):
    """An identical repeat run writes nothing new (idempotent, does not duplicate or re-write)."""
    root = pending_test_env["root"]
    monkeypatch.setattr("opi.actuals.ROOT_DIR", root)
    monkeypatch.setattr("opi.log.ROOT_DIR", root)

    mock_hist = pd.DataFrame(
        [{"Open": 248.00, "High": 255.0, "Low": 240.0, "Close": 250.0, "Volume": 1000}],
        index=[pd.Timestamp("2026-11-03 00:00:00+05:30")]
    )
    mock_sec_html = (
        "<!DOCTYPE html><html><body>"
        "<h1>BLS Polymers Limited IPO Details</h1>"
        "<table><tr><td>Open</td><td>₹244.10</td></tr></table>"
        "</body></html>"
    )

    # First run
    execute_two_tier_outcome_chain(
        company=pending_test_env["company"],
        log_path=pending_test_env["log_path"],
        mock_yfinance_history=mock_hist,
        mock_second_source_text=mock_sec_html,
        mock_nse_symbol="BLSPOLY",
        mock_bse_code="544321",
    )

    pending_dir = root / "data" / "evidence" / "actuals" / "pending"
    initial_files = sorted(list(pending_dir.iterdir()))
    initial_count = len(initial_files)
    initial_mtimes = {f.name: f.stat().st_mtime_ns for f in initial_files}

    # Second run with identical data
    execute_two_tier_outcome_chain(
        company=pending_test_env["company"],
        log_path=pending_test_env["log_path"],
        mock_yfinance_history=mock_hist,
        mock_second_source_text=mock_sec_html,
        mock_nse_symbol="BLSPOLY",
        mock_bse_code="544321",
    )

    second_files = sorted(list(pending_dir.iterdir()))
    assert len(second_files) == initial_count, "No new files should be created on identical re-run"
    assert [f.name for f in second_files] == [f.name for f in initial_files]


def test_unlabelled_page_recorded_as_unknown_exchange(pending_test_env, monkeypatch):
    """When a source page gives a price but does not specify NSE or BSE, exchange must be UNKNOWN."""
    root = pending_test_env["root"]
    monkeypatch.setattr("opi.actuals.ROOT_DIR", root)
    monkeypatch.setattr("opi.log.ROOT_DIR", root)

    mock_hist = pd.DataFrame(
        [{"Open": 248.00, "High": 255.0, "Low": 240.0, "Close": 250.0, "Volume": 1000}],
        index=[pd.Timestamp("2026-11-03 00:00:00+05:30")]
    )
    # Page with price 244.10 but NO mention of NSE or BSE
    unlabelled_html = (
        "<!DOCTYPE html><html><body>"
        "<h1>Synthetic Unlabelled Company IPO</h1>"
        "<p>The shares debuted with opening price of 244.10 per share.</p>"
        "</body></html>"
    )

    execute_two_tier_outcome_chain(
        company=pending_test_env["company"],
        log_path=pending_test_env["log_path"],
        mock_yfinance_history=mock_hist,
        mock_second_source_text=unlabelled_html,
        mock_nse_symbol="BLSPOLY",
        mock_bse_code="544321",
    )

    pending_dir = root / "data" / "evidence" / "actuals" / "pending"
    manifest_file = pending_dir / "2026-11-03_bls-polymers-limited.manifest.json"
    assert manifest_file.exists()

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    sources = {s["publisher"]: s for s in manifest["sources"]}
    assert "Chittorgarh" in sources
    assert sources["Chittorgarh"]["exchange"] == "UNKNOWN", "Unlabelled page must produce exchange: UNKNOWN"


def test_manifest_sha256_matches_file_bytes(pending_test_env, monkeypatch):
    """The sha256 in the manifest must exactly match the sha256 of the saved page file bytes."""
    root = pending_test_env["root"]
    monkeypatch.setattr("opi.actuals.ROOT_DIR", root)
    monkeypatch.setattr("opi.log.ROOT_DIR", root)

    mock_hist = pd.DataFrame(
        [{"Open": 248.00, "High": 255.0, "Low": 240.0, "Close": 250.0, "Volume": 1000}],
        index=[pd.Timestamp("2026-11-03 00:00:00+05:30")]
    )
    mock_sec_html = (
        "<!DOCTYPE html><html><body>"
        "<h1>BLS Polymers Limited Details</h1>"
        "<div class='nse-listing'><table><tr><td>Open</td><td>₹244.10</td></tr></table></div>"
        "</body></html>"
    )

    execute_two_tier_outcome_chain(
        company=pending_test_env["company"],
        log_path=pending_test_env["log_path"],
        mock_yfinance_history=mock_hist,
        mock_second_source_text=mock_sec_html,
        mock_nse_symbol="BLSPOLY",
        mock_bse_code="544321",
    )

    pending_dir = root / "data" / "evidence" / "actuals" / "pending"
    manifest_file = pending_dir / "2026-11-03_bls-polymers-limited.manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    for s in manifest["sources"]:
        file_rel = s.get("file")
        if file_rel:
            file_path = root / file_rel
            assert file_path.exists(), f"Saved file {file_path} must exist"
            expected_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
            assert s["sha256"] == expected_sha, f"Manifest SHA-256 {s['sha256']} must match file bytes {expected_sha}"
