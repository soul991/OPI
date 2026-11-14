"""
Unit tests for opi.stage_listing (WS-E: Stage 'listing').
"""

import json
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest

from opi.alert_state import already_sent, ensure_alerts_file
from opi.stage_listing import format_listing_message, run_listing_stage


def test_format_listing_message_hd_fire():
    # Issue price: 271.0, Listing open: 334.40, Lot size: 55 shares
    # P&L per lot = (334.40 - 271.00) * 55 = 63.40 * 55 = +₹3,487.00
    msg = format_listing_message(
        company="HD Fire Protect Limited",
        issue_price=271.0,
        listing_open=334.40,
        actual_gain_pct=23.39,
        lot_size=55,
        exchange="NSE",
        raw_gmp=25.0,
        model_final=20.5,
        preview_est=22.0,
        provenance_tier="1",
        provenance_digest="Verified",
    )
    assert "🔔 OPI LISTING DAY OUTCOME: HD Fire Protect Limited" in msg
    assert "• Issue Price: ₹271.00" in msg
    assert "• Official Listing Open: ₹334.40" in msg
    assert "• Actual Listing Gain: +23.39%" in msg
    assert "• Profit / Loss per Lot: +₹3,487.00 (55 shares)" in msg
    assert "• Raw GMP at Close: +25.00% (Error: 1.61 pp)" in msg
    assert "Decision aid only, not financial advice." in msg


@patch("opi.stage_listing.send_telegram", return_value=True)
def test_listing_alert_verified_outcome(mock_send, tmp_path):
    alerts_csv = tmp_path / "alerts.csv"
    ensure_alerts_file(alerts_csv)

    pred_csv = tmp_path / "prediction_log.csv"
    prev_csv = tmp_path / "preview_log.csv"

    features_json = json.dumps({"issue_price": 200.0, "lot_size": 75, "gmp_pct": 15.0})

    df = pd.DataFrame(
        [
            {
                "scored_at": "2026-11-15 19:30:00",
                "company": "Epsilon Energy Limited",
                "open_date": "2026-11-10",
                "close_date": "2026-11-12",
                "listing_date": "2026-11-18",
                "features_snapshot_json": features_json,
                "pred_gain_pct": 12.0,
                "pred_prob_gt10": 0.65,
                "gmp_pct_at_scoring": 15.0,
                "actual_gain_pct": 18.0,
                "status": "FORWARD",
                "notes": "Verified",
                "model_version": "v4.0.0-champion",
            }
        ]
    )
    df.to_csv(pred_csv, index=False)

    # First run on listing date -> sends alert
    sent = run_listing_stage(
        today_ist="2026-11-18",
        alerts_csv=alerts_csv,
        prediction_log_path=pred_csv,
        preview_log_path=prev_csv,
    )
    assert len(sent) == 1
    assert sent[0]["company"] == "Epsilon Energy Limited"
    assert sent[0]["actual_gain_pct"] == 18.0
    assert mock_send.call_count == 1
    assert already_sent("Epsilon Energy Limited", "2026-11-12", "listing", csv_path=alerts_csv)

    # Second run -> suppressed by idempotency
    mock_send.reset_mock()
    sent_second = run_listing_stage(
        today_ist="2026-11-18",
        alerts_csv=alerts_csv,
        prediction_log_path=pred_csv,
        preview_log_path=prev_csv,
    )
    assert len(sent_second) == 0
    assert mock_send.call_count == 0


@patch("opi.stage_listing.send_telegram", return_value=True)
def test_listing_alert_pending_outcome_suppressed(mock_send, tmp_path):
    alerts_csv = tmp_path / "alerts.csv"
    ensure_alerts_file(alerts_csv)

    pred_csv = tmp_path / "prediction_log.csv"
    # Unverified / pending outcome (actual_gain_pct is NaN)
    df = pd.DataFrame(
        [
            {
                "scored_at": "2026-11-15 19:30:00",
                "company": "Pending Listing Limited",
                "open_date": "2026-11-10",
                "close_date": "2026-11-12",
                "listing_date": "2026-11-18",
                "features_snapshot_json": "{}",
                "pred_gain_pct": 10.0,
                "pred_prob_gt10": 0.55,
                "gmp_pct_at_scoring": 12.0,
                "actual_gain_pct": None,  # Pending
                "status": "FORWARD",
                "notes": "Awaiting outcome",
                "model_version": "v4.0.0-champion",
            }
        ]
    )
    df.to_csv(pred_csv, index=False)

    sent = run_listing_stage(
        today_ist="2026-11-18",
        alerts_csv=alerts_csv,
        prediction_log_path=pred_csv,
    )
    assert len(sent) == 0
    assert mock_send.call_count == 0
    assert not already_sent("Pending Listing Limited", "2026-11-12", "listing", csv_path=alerts_csv)
