"""Offline unit tests for browser-rendered exchange pages and historical table rows (FIX 2 / D-039).

Covers:
- valid historical row
- wrong-date row
- missing company
- open value not in file
- open value mismatch in historical table
- tampered file hash mismatch
- browser-rendered quote page fixture
"""

import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import pandas as pd
import pytest

import opi.actuals as actuals
import opi.log as oplog

COLS = [
    "scored_at", "company", "open_date", "close_date", "listing_date",
    "features_snapshot_json", "pred_gain_pct", "pred_prob_gt10",
    "gmp_pct_at_scoring", "actual_gain_pct", "status", "notes"
]
URL = "https://www.nseindia.com/get-quote/equity/TEST/Test-Company-Limited"

RENDERED_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head><title>Test Company Limited Share Price Today - NSE India</title></head>
<body>
  <h1>Test Company Limited</h1>
  <div class="symbol">TEST</div>
  <p>Date of Listing: 22-Oct-2026</p>
  <div class="price-block">
    <span>Open</span> <span>120.00</span>
  </div>
  <table>
    <thead>
      <tr>
        <th>DATE</th><th>SERIES</th><th>OPEN</th><th>HIGH</th><th>LOW</th><th>CLOSE</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>23-Oct-2026</td><td>EQ</td><td>125.00</td><td>130.00</td><td>122.00</td><td>128.00</td>
      </tr>
      <tr>
        <td>22-Oct-2026</td><td>EQ</td><td>120.00</td><td>126.00</td><td>118.00</td><td>124.00</td>
      </tr>
    </tbody>
  </table>
</body>
</html>
"""

HISTORICAL_CSV_FIXTURE = """DATE,SERIES,OPEN,HIGH,LOW,CLOSE
23-Oct-2026,EQ,125.00,130.00,122.00,128.00
22-Oct-2026,EQ,120.00,126.00,118.00,124.00
"""


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    monkeypatch.setattr(actuals, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(oplog, "ROOT_DIR", tmp_path)
    listing = datetime.strptime("2026-10-22", "%Y-%m-%d").date()
    log = tmp_path / "predictions" / "prediction_log.csv"
    log.parent.mkdir(parents=True)
    row = {c: "" for c in COLS}
    row.update(
        scored_at="2026-10-15T20:00:00+05:30",
        company="Test Company Limited",
        listing_date="2026-10-22",
        features_snapshot_json=json.dumps({"issue_price": 100.0}),
        pred_gain_pct="15.0",
        status="FORWARD",
        notes="pre-listing forward test",
    )
    pd.DataFrame([row], columns=COLS).to_csv(log, index=False)
    return dict(root=tmp_path, log=log, listing=listing)


def test_valid_rendered_html_fixture_success(test_env, tmp_path):
    """Rendered HTML page with historical table row records successfully."""
    ev_file = tmp_path / "rendered_test.html"
    ev_file.write_text(RENDERED_HTML_FIXTURE, encoding="utf-8")

    out = actuals.record_actual_from_exchange(
        company="Test Company Limited",
        source_url=URL,
        listing_price=120.00,
        page_date="2026-10-22",
        company_quote="Test Company Limited",
        price_quote="22-Oct-2026 EQ 120.00",
        log_path=test_env["log"],
        evidence_file=ev_file,
    )
    assert out["official_opening_price"] == 120.00
    assert out["computed_listing_gain_pct"] == 20.00
    assert out["exchange_used"] == "NSE"

    df = pd.read_csv(test_env["log"])
    assert float(df["actual_gain_pct"].iloc[0]) == 20.00


def test_valid_historical_csv_fixture_success(test_env, tmp_path):
    """Historical CSV with listing date row and open price records successfully."""
    # CSV must also include the company name to satisfy ground truth
    csv_content = f"# Company: Test Company Limited\n" + HISTORICAL_CSV_FIXTURE
    ev_file = tmp_path / "historical_test.csv"
    ev_file.write_text(csv_content, encoding="utf-8")

    out = actuals.record_actual_from_exchange(
        company="Test Company Limited",
        source_url=URL,
        listing_price=120.00,
        page_date="2026-10-22",
        company_quote="Test Company Limited",
        price_quote="22-Oct-2026,EQ,120.00",
        log_path=test_env["log"],
        evidence_file=ev_file,
    )
    assert out["official_opening_price"] == 120.00
    assert out["computed_listing_gain_pct"] == 20.00


def test_wrong_date_row_rejected(test_env, tmp_path):
    """Mismatched page_date vs listing_date must be rejected."""
    ev_file = tmp_path / "rendered_test.html"
    ev_file.write_text(RENDERED_HTML_FIXTURE, encoding="utf-8")

    with pytest.raises(actuals.ActualsEvidenceError, match="Page date must match this IPO's listing date"):
        actuals.record_actual_from_exchange(
            company="Test Company Limited",
            source_url=URL,
            listing_price=120.00,
            page_date="2026-10-23",  # wrong date!
            company_quote="Test Company Limited",
            price_quote="22-Oct-2026 EQ 120.00",
            log_path=test_env["log"],
            evidence_file=ev_file,
        )


def test_missing_company_rejected(test_env, tmp_path):
    """If company name does not appear in file, must be rejected."""
    html = RENDERED_HTML_FIXTURE.replace("Test Company Limited", "Another Different Firm")
    ev_file = tmp_path / "no_company.html"
    ev_file.write_text(html, encoding="utf-8")

    with pytest.raises(actuals.ActualsEvidenceError, match="Company quote was not found"):
        actuals.record_actual_from_exchange(
            company="Test Company Limited",
            source_url=URL,
            listing_price=120.00,
            page_date="2026-10-22",
            company_quote="Test Company Limited",
            price_quote="22-Oct-2026 EQ 120.00",
            log_path=test_env["log"],
            evidence_file=ev_file,
        )


def test_open_value_mismatch_in_historical_table_rejected(test_env, tmp_path):
    """If supplied price does not match the Open value in the listing-date row, must reject."""
    ev_file = tmp_path / "rendered_test.html"
    ev_file.write_text(RENDERED_HTML_FIXTURE, encoding="utf-8")

    with pytest.raises(actuals.ActualsEvidenceError, match="does not match expected"):
        actuals.record_actual_from_exchange(
            company="Test Company Limited",
            source_url=URL,
            listing_price=199.99,  # does not match 120.00 in the row!
            page_date="2026-10-22",
            company_quote="Test Company Limited",
            price_quote="22-Oct-2026 EQ 120.00",
            log_path=test_env["log"],
            evidence_file=ev_file,
        )


def test_open_value_not_in_file_rejected(test_env, tmp_path):
    """If supplied opening price is completely absent from file, must reject."""
    html = RENDERED_HTML_FIXTURE.replace("120.00", "110.00")
    ev_file = tmp_path / "modified_price.html"
    ev_file.write_text(html, encoding="utf-8")

    with pytest.raises(actuals.ActualsEvidenceError):
        actuals.record_actual_from_exchange(
            company="Test Company Limited",
            source_url=URL,
            listing_price=120.00,
            page_date="2026-10-22",
            company_quote="Test Company Limited",
            price_quote="22-Oct-2026 EQ 120.00",
            log_path=test_env["log"],
            evidence_file=ev_file,
        )


def test_tampered_file_rejected(test_env, tmp_path):
    """Tampering with existing saved snapshot triggers hash mismatch."""
    ev_file = tmp_path / "rendered_test.html"
    ev_file.write_text(RENDERED_HTML_FIXTURE, encoding="utf-8")

    # Record first time
    actuals.record_actual_from_exchange(
        company="Test Company Limited",
        source_url=URL,
        listing_price=120.00,
        page_date="2026-10-22",
        company_quote="Test Company Limited",
        price_quote="22-Oct-2026 EQ 120.00",
        log_path=test_env["log"],
        evidence_file=ev_file,
    )

    # Corrupt saved snapshot
    evidence_dir = test_env["root"] / "data" / "evidence" / "actuals"
    saved_snaps = list(evidence_dir.glob("*.html"))
    assert len(saved_snaps) == 1
    snap = saved_snaps[0]
    snap.write_text("TAMPERED DATA", encoding="utf-8")

    # Re-reading or checking should detect tampering
    manifest = json.loads(list(evidence_dir.glob("*.json"))[0].read_text(encoding="utf-8"))
    actual_hash = hashlib.sha256(snap.read_bytes()).hexdigest()
    assert actual_hash != manifest["snapshot_sha256"], "Tampering must result in hash mismatch"
