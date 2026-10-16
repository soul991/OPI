"""Unit tests for Phase 9 validation, mainboard discipline, and PREVIEW vs FORWARD gating."""

from datetime import datetime, date, timedelta
import pytest
from opi.validate import (
    validate_mainboard_eligibility,
    determine_prediction_mode,
    validate_candidate_for_forward_logging,
    validate_timing_and_leakage
)


def test_mainboard_eligibility_enforcement():
    """Ensure non-mainboard (SME, FPO, rights issue) or tiny issues are strictly rejected."""
    # 1. SME in company name
    cand_sme_name = {"company": "Acme Widgets SME Limited", "issue_size_cr": 45.0, "exchange": "BSE"}
    ok, issues = validate_mainboard_eligibility(cand_sme_name)
    assert ok is False
    assert any("sme" in iss.lower() for iss in issues)

    # 2. SME in exchange
    cand_sme_exch = {"company": "Zenith Dynamics Limited", "issue_size_cr": 50.0, "exchange": "NSE SME"}
    ok, issues = validate_mainboard_eligibility(cand_sme_exch)
    assert ok is False
    assert any("sme" in iss.lower() for iss in issues)

    # 3. Micro issue below 25 Cr
    cand_tiny = {"company": "Micro Tech Limited", "issue_size_cr": 14.5, "exchange": "BSE"}
    ok, issues = validate_mainboard_eligibility(cand_tiny)
    assert ok is False
    assert any("below standard mainboard threshold" in iss.lower() for iss in issues)

    # 4. Valid mainboard IPO
    cand_valid = {"company": "Bharat Heavy Infra Limited", "issue_size_cr": 850.0, "exchange": "BOTH"}
    ok, issues = validate_mainboard_eligibility(cand_valid)
    assert ok is True
    assert len(issues) == 0


def test_determine_prediction_mode_gating():
    """Ensure predictions scored before bidding close are PREVIEW only and cannot be FORWARD."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=6)

    # 1. Scored while bidding is ongoing (close date is tomorrow)
    mode, reasons = determine_prediction_mode(
        close_date_str=tomorrow.isoformat(),
        listing_date_str=next_week.isoformat(),
        scored_at_str=datetime.now().isoformat()
    )
    assert mode == "PREVIEW"
    assert "PREVIEW mode only" in reasons[0]

    # 2. Interim day 1/2 notes force PREVIEW mode even if dates are past
    mode, reasons = determine_prediction_mode(
        close_date_str=(today - timedelta(days=2)).isoformat(),
        listing_date_str=next_week.isoformat(),
        scored_at_str=datetime.now().isoformat(),
        notes="Day 1 live bidding tracking"
    )
    assert mode == "PREVIEW"

    # 3. Post-bidding close before listing date is FORWARD_ELIGIBLE
    close_yesterday = today - timedelta(days=1)
    mode, reasons = determine_prediction_mode(
        close_date_str=close_yesterday.isoformat(),
        listing_date_str=next_week.isoformat(),
        scored_at_str=datetime.now().isoformat()
    )
    assert mode == "FORWARD_ELIGIBLE"

    # 4. Post-listing is INVALID
    past_listing = today - timedelta(days=1)
    mode, reasons = determine_prediction_mode(
        close_date_str=(today - timedelta(days=4)).isoformat(),
        listing_date_str=past_listing.isoformat(),
        scored_at_str=datetime.now().isoformat()
    )
    assert mode == "INVALID"


def test_validate_candidate_for_forward_logging_rejection():
    """Verify that validate_candidate_for_forward_logging blocks PREVIEW and SME candidates."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=6)

    # PREVIEW candidate cannot be logged as FORWARD
    preview_cand = {
        "company": "Live Bidding Candidate",
        "close_date": tomorrow.isoformat(),
        "listing_date": next_week.isoformat(),
        "issue_size_cr": 400.0,
        "lot_size": 30,
        "sub_qib": 2.5,
        "sub_nii": 1.2,
        "sub_retail": 1.8,
        "sub_total": 2.0,
        "exchange": "NSE"
    }
    ok, issues = validate_candidate_for_forward_logging(preview_cand)
    assert ok is False
    assert any("preview" in iss.lower() for iss in issues)
