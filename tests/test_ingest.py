"""Unit and regression tests for data ingestion, grounding parsers, and market data snapshotting."""

import hashlib
import json
from pathlib import Path
import pytest

from opi.collect import verify_value_in_html

ROOT = Path(__file__).resolve().parents[1]


def test_grounding_accepts_date_format_variants():
    """D-033: Verify that date grounding recognizes various standard date formats in snapshot text."""
    date_val = "2026-10-15"
    
    # 1. Month day, Year
    html1 = "<html><body><p>Bidding closed on Oct 15, 2026 at 5:00 PM</p></body></html>"
    ok1, reason1 = verify_value_in_html(date_val, None, html1)
    assert ok1 is True, f"Failed for 'Oct 15, 2026': {reason1}"

    # 2. Full Month name
    html2 = "<html><body><p>Issue closed October 15, 2026</p></body></html>"
    ok2, reason2 = verify_value_in_html(date_val, None, html2)
    assert ok2 is True, f"Failed for 'October 15, 2026': {reason2}"

    # 3. Day Month Year
    html3 = "<html><body><p>Close Date: 15 Oct 2026</p></body></html>"
    ok3, reason3 = verify_value_in_html(date_val, None, html3)
    assert ok3 is True, f"Failed for '15 Oct 2026': {reason3}"

    # 4. DD-MM-YYYY
    html4 = "<html><body><p>Closing: 15-10-2026</p></body></html>"
    ok4, reason4 = verify_value_in_html(date_val, None, html4)
    assert ok4 is True, f"Failed for '15-10-2026': {reason4}"

    # 5. Non-matching date
    html5 = "<html><body><p>Closed on 20-Oct-2026</p></body></html>"
    ok5, _ = verify_value_in_html(date_val, None, html5)
    assert ok5 is False


def test_mismatch_between_typed_value_and_snapshot_is_refused():
    """D-028: Refuse typed or proposed value that does not match parsed snapshot content."""
    html = "<html><body><p>Issue Price: Rs 271 per share</p><p>Total Subscription: 131.73x</p></body></html>"
    
    # Matching value accepted
    ok_match, _ = verify_value_in_html(271.0, None, html)
    assert ok_match is True

    # Mismatched value refused
    ok_mismatch, reason = verify_value_in_html(350.0, None, html)
    assert ok_mismatch is False
    assert "not found" in reason.lower()


def test_market_data_saved_raw_with_hash(tmp_path):
    """D-030: Verify that market macro data is saved with raw response and SHA-256 hash."""
    from opi.ingest import save_raw_market_data

    sample_raw = b'{"nifty_30d_return": -1.96, "india_vix": 14.77, "source": "yfinance"}'
    saved_path, meta_path, sha = save_raw_market_data(
        raw_bytes=sample_raw,
        date_str="2026-10-19",
        source="yfinance",
        output_dir=tmp_path
    )
    assert saved_path.exists()
    assert meta_path.exists()
    assert hashlib.sha256(sample_raw).hexdigest() == sha

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["source"] == "yfinance"
    assert meta["sha256"] == sha
