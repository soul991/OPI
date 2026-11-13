"""
Unit tests for opi.stage_announce (WS-C: Stage 'announce').
"""

from pathlib import Path
from unittest.mock import patch
import pytest

from opi.alert_state import already_sent, ensure_alerts_file
from opi.discover import parse_discovery_html
from opi.stage_announce import format_announce_message, run_announce_stage


def test_format_announce_message():
    cand = {
        "company": "Tata Technologies Limited",
        "open_date": "2026-11-20",
        "close_date": "2026-11-22",
        "listing_date": "2026-11-30",
        "price_band": "475 - 500",
        "lot_size": "30",
        "issue_size_cr": "3042.51",
        "fresh_pct": "0.0",
        "ofs_pct": "100.0",
        "exchange": "NSE / BSE",
    }
    msg = format_announce_message(cand)
    assert "📢 OPI IPO ANNOUNCEMENT: Tata Technologies Limited" in msg
    assert "• Bidding Opens: 2026-11-20" in msg
    assert "• Bidding Closes: 2026-11-22" in msg
    assert "• Listing Date: 2026-11-30" in msg
    assert "• Price Band / Price: ₹475 - 500" in msg
    assert "• Lot Size: 30 shares" in msg
    assert "• Issue Size: ₹3042.51 Cr" in msg
    assert "Decision aid only, not financial advice." in msg


@patch("opi.stage_announce.send_telegram", return_value=True)
def test_announce_sends_new_ipo(mock_send, tmp_path):
    alerts_csv = tmp_path / "alerts.csv"
    ensure_alerts_file(alerts_csv)

    candidates = [
        {
            "company": "Alpha Tech Limited",
            "open_date": "2026-12-01",
            "close_date": "2026-12-03",
            "listing_date": "2026-12-10",
            "status": "UPCOMING",
            "type": "Mainboard",
        }
    ]

    # First run: should send and record
    sent = run_announce_stage(candidates=candidates, alerts_csv=alerts_csv)
    assert len(sent) == 1
    assert sent[0]["company"] == "Alpha Tech Limited"
    assert mock_send.call_count == 1
    assert already_sent("Alpha Tech Limited", "2026-12-03", "announce", csv_path=alerts_csv)

    # Second run: should be suppressed by idempotency
    mock_send.reset_mock()
    sent_second = run_announce_stage(candidates=candidates, alerts_csv=alerts_csv)
    assert len(sent_second) == 0
    assert mock_send.call_count == 0


@patch("opi.stage_announce.send_telegram", return_value=True)
def test_announce_skips_sme_and_listed(mock_send, tmp_path):
    alerts_csv = tmp_path / "alerts.csv"
    ensure_alerts_file(alerts_csv)

    candidates = [
        {
            "company": "Small SME Tech",
            "open_date": "2026-12-01",
            "close_date": "2026-12-03",
            "status": "UPCOMING",
            "type": "BSE SME",
        },
        {
            "company": "Old Listed Corp",
            "open_date": "2026-11-01",
            "close_date": "2026-11-03",
            "status": "LISTED",
            "type": "Mainboard",
        },
        {
            "company": "Missing Dates Corp",
            "open_date": "",
            "close_date": "",
            "status": "UPCOMING",
            "type": "Mainboard",
        },
    ]

    sent = run_announce_stage(candidates=candidates, alerts_csv=alerts_csv)
    assert len(sent) == 0
    assert mock_send.call_count == 0


@patch("opi.stage_announce.send_telegram", return_value=True)
def test_announce_with_fixture(mock_send, tmp_path):
    alerts_csv = tmp_path / "alerts.csv"
    ensure_alerts_file(alerts_csv)

    fixture_path = Path("tests/fixtures/discovery_page.html")
    if fixture_path.exists():
        html = fixture_path.read_text(encoding="utf-8")
        candidates = parse_discovery_html(html, as_of_date="2026-10-15")
        # Ensure discovery returns parsed items
        assert isinstance(candidates, list)
        sent = run_announce_stage(candidates=candidates, alerts_csv=alerts_csv)
        # Any sent candidate must have an announce record
        for item in sent:
            assert already_sent(item["company"], item["close_date"], "announce", csv_path=alerts_csv)
