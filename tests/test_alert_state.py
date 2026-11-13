"""
Unit tests for opi.alert_state (WS-B: Alert State & Idempotency).
"""

from pathlib import Path
import tempfile
import pandas as pd
import pytest

from opi.alert_state import (
    ALERTS_COLUMNS,
    already_sent,
    compute_message_digest,
    ensure_alerts_file,
    load_sent_keys,
    record_alert_sent,
)


def test_ensure_alerts_file(tmp_path):
    f = tmp_path / "alerts.csv"
    assert not f.exists()
    p = ensure_alerts_file(f)
    assert p.exists()
    df = pd.read_csv(p)
    assert list(df.columns) == ALERTS_COLUMNS


def test_compute_message_digest():
    d1 = compute_message_digest("Hello Alert")
    d2 = compute_message_digest("Hello Alert")
    d3 = compute_message_digest("Different Alert")
    assert d1 == d2
    assert d1 != d3
    assert len(d1) == 16


def test_already_sent_and_record_alert(tmp_path):
    f = tmp_path / "alerts.csv"
    ensure_alerts_file(f)

    # Before record
    assert not already_sent("Acme Ltd", "2026-11-20", "preview", csv_path=f)

    # Record alert
    record_alert_sent(
        company="Acme Ltd",
        close_date="2026-11-20",
        listing_date="2026-11-25",
        alert_type="preview",
        stage="preview",
        text="Preview message text",
        run_id="run_101",
        csv_path=f,
    )

    # After record
    assert already_sent("Acme Ltd", "2026-11-20", "preview", csv_path=f)
    assert already_sent("acme ltd", "2026-11-20", "preview", csv_path=f)
    assert not already_sent("Acme Ltd", "2026-11-20", "announce", csv_path=f)
    assert not already_sent("Other Ltd", "2026-11-20", "preview", csv_path=f)


def test_record_alert_invalid_type(tmp_path):
    f = tmp_path / "alerts.csv"
    with pytest.raises(ValueError, match="Invalid alert_type"):
        record_alert_sent(
            company="Acme",
            close_date="2026-11-20",
            listing_date="",
            alert_type="allotment",  # Not a valid alert type
            stage="preview",
            text="text",
            csv_path=f,
        )


def test_no_preview_or_alert_in_real_prediction_log():
    # Enforces the core Phase 21 rule on the actual repo file
    pred_path = Path("predictions/prediction_log.csv")
    if pred_path.exists():
        df = pd.read_csv(pred_path)
        statuses = df["status"].astype(str).str.upper()
        assert not (statuses == "PREVIEW").any(), "prediction_log.csv must NEVER contain PREVIEW status rows!"
        assert not statuses.str.contains("ALERT").any(), "prediction_log.csv must NEVER contain ALERT rows!"
