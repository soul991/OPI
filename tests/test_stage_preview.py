"""
Unit tests for opi.stage_preview (WS-D: Stage 'preview').
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest

from opi.alert_state import already_sent, ensure_alerts_file
from opi.stage_preview import (
    compute_suggestion,
    format_preview_message,
    run_preview_stage,
)


def test_compute_suggestion_regime_a_gmp():
    # T1 = 10.0%, Marginal = [5.0%, 10.0%)
    sug, basis = compute_suggestion(gmp_pct=15.0, pred_gain=8.0, prob_gt10=0.40)
    assert sug == "APPLY"
    assert ">= T1 (+10.0%)" in basis

    sug, basis = compute_suggestion(gmp_pct=7.5, pred_gain=20.0, prob_gt10=0.80)
    assert sug == "MARGINAL: small expected gain, your call"
    assert "marginal band" in basis

    sug, basis = compute_suggestion(gmp_pct=2.0, pred_gain=18.0, prob_gt10=0.75)
    assert sug == "SKIP"
    assert "below 5.0% minimum threshold" in basis

    sug, basis = compute_suggestion(gmp_pct=-3.5, pred_gain=18.0, prob_gt10=0.75)
    assert sug == "SKIP"
    assert "Negative GMP discount" in basis


def test_compute_suggestion_regime_b_model_fallback():
    # No marginal band on model fallback; T2 = 15.0% and P >= 0.60
    sug, basis = compute_suggestion(gmp_pct=None, pred_gain=16.5, prob_gt10=0.65)
    assert sug == "APPLY"
    assert ">= T2 (+15.0%) with calibrated P(>10%) >= 60%" in basis

    # Below P threshold -> SKIP
    sug, basis = compute_suggestion(gmp_pct=None, pred_gain=18.0, prob_gt10=0.55)
    assert sug == "SKIP"
    assert "below threshold" in basis

    # In 5-10% range without GMP -> SKIP (model has no marginal band)
    sug, basis = compute_suggestion(gmp_pct=None, pred_gain=8.5, prob_gt10=0.55)
    assert sug == "SKIP"


def test_compute_suggestion_regime_c_missing_data():
    sug, basis = compute_suggestion(gmp_pct=None, pred_gain=None, prob_gt10=None)
    assert sug == "NO SUGGESTION"
    assert "Insufficient data" in basis


def test_format_preview_message():
    msg = format_preview_message(
        company="Zetwerk Manufacturing Business Limited",
        close_date="2026-11-20",
        listing_date="2026-11-25",
        issue_price="120",
        lot_size="100",
        sub_qib=2.5,
        sub_nii=1.8,
        sub_retail=4.2,
        sub_total=3.1,
        sub_as_of="11:45 IST",
        gmp_pct=14.5,
        gmp_source="Investorgain",
        gmp_as_of="2026-11-20 11:30 IST",
        pred_gain=12.5,
        prob_gt10=0.72,
        pi_lower=-2.5,
        pi_upper=27.5,
        suggestion="APPLY",
        suggestion_basis="Observed GMP (+14.5%) >= T1 (+10.0%)",
        n_listed=13,
    )
    assert "🎯 OPI PREVIEW ALERT: Zetwerk Manufacturing Business Limited" in msg
    assert "• Grey Market Premium (GMP): +14.5% (Investorgain, as of 2026-11-20 11:30 IST)" in msg
    assert "• Model PREVIEW Estimate: +12.5% (live subscription; model trained on final figures)" in msg
    assert "💡 Decision Suggestion: APPLY" in msg
    assert "⚠️ Sample Size Notice: n listed = 13 of 30 (Provisional)" in msg
    assert "Decision aid only, not financial advice." in msg


@patch("opi.stage_preview.send_telegram", return_value=True)
def test_preview_stage_logs_to_preview_log_only(mock_send, tmp_path):
    alerts_csv = tmp_path / "alerts.csv"
    preview_csv = tmp_path / "preview_log.csv"
    ensure_alerts_file(alerts_csv)

    candidates = [
        {
            "company": "Gamma Technologies Limited",
            "open_date": "2026-11-18",
            "close_date": "2026-11-20",
            "listing_date": "2026-11-27",
            "status": "BIDDING_OPEN",
            "type": "Mainboard",
            "issue_price": "250",
            "lot_size": "60",
            "sub_qib": 5.5,
            "sub_nii": 3.2,
            "sub_retail": 8.1,
            "sub_total": 6.0,
            "gmp_pct": 18.0,
            "gmp_source": "Chittorgarh",
            "gmp_as_of": "2026-11-20 11:15 IST",
        }
    ]

    # Run preview for today == 2026-11-20
    sent = run_preview_stage(
        candidates=candidates,
        alerts_csv=alerts_csv,
        preview_csv=preview_csv,
        as_of_date="2026-11-20",
    )
    assert len(sent) == 1
    assert sent[0]["company"] == "Gamma Technologies Limited"
    assert sent[0]["suggestion"] == "APPLY"
    assert mock_send.call_count == 1

    # Verify preview_log.csv received the row
    assert preview_csv.exists()
    p_df = pd.read_csv(preview_csv)
    assert len(p_df) == 1
    assert p_df.iloc[0]["company"] == "Gamma Technologies Limited"
    assert p_df.iloc[0]["suggestion"] == "APPLY"

    # Verify real prediction_log.csv was NOT touched
    pred_path = Path("predictions/prediction_log.csv")
    if pred_path.exists():
        real_df = pd.read_csv(pred_path)
        assert not (real_df["company"] == "Gamma Technologies Limited").any()
        assert not (real_df["status"] == "PREVIEW").any()

    # Second trigger on same candidate is idempotent
    mock_send.reset_mock()
    sent_second = run_preview_stage(
        candidates=candidates,
        alerts_csv=alerts_csv,
        preview_csv=preview_csv,
        as_of_date="2026-11-20",
    )
    assert len(sent_second) == 0
    assert mock_send.call_count == 0


def test_preview_vs_forward_smoke():
    res = subprocess.run(
        [sys.executable, "scripts/preview_vs_forward.py"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "OPI PREVIEW vs FORWARD ESTIMATE ACCURACY" in res.stdout
