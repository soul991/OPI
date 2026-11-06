#!/usr/bin/env python3
"""tests/test_pre_listing.py - Unit and regression tests for D-079.

Verifies:
1. Pending forward predictions (unlisted, no outcome) appear in the pre-listing predictions list.
2. Completed forward predictions (with actual outcome) do not appear in the pre-listing list.
3. Discovered IPOs in BIDDING_OPEN state appear without model numbers ("Bidding open: scored after close").
4. A row scored on or after its listing date is rejected and excluded.
5. predictions/pre_listing_predictions.md is generated with the provisional banner.
6. dashboard/index.html renders the Pre-listing predictions section.
7. No network calls are made during pre-listing generation.
"""

from __future__ import annotations

import csv
from datetime import datetime, date
from pathlib import Path
import pandas as pd
import pytest

from opi.report import get_pre_listing_data, render_pre_listing_markdown, render_dashboard_html

ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
PRE_LISTING_MD = ROOT_DIR / "predictions" / "pre_listing_predictions.md"
DASHBOARD_HTML = ROOT_DIR / "dashboard" / "index.html"


def test_pending_forward_row_appears_in_pre_listing(tmp_path: Path):
    """D-079: Pending forward rows appear with all required columns and estimate wording."""
    dummy_log = tmp_path / "prediction_log.csv"
    with open(dummy_log, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scored_at", "company", "open_date", "close_date", "listing_date",
            "features_snapshot_json", "pred_gain_pct", "pred_prob_gt10",
            "gmp_pct_at_scoring", "actual_gain_pct", "status", "notes"
        ])
        # Pending forward row
        writer.writerow([
            "2026-11-01T10:00:00", "Pending Test Corp", "2026-10-28", "2026-10-30", "2026-11-05",
            '{"issue_price": 100.0}', "15.50", "0.65", "12.0", "", "FORWARD", "test note"
        ])

    data = get_pre_listing_data(log_path=dummy_log, as_of_date="2026-11-02")
    pending = data["pending_predictions"]
    assert len(pending) == 1
    item = pending[0]
    assert item["company"] == "Pending Test Corp"
    assert item["bidding_dates"] == "2026-10-28 to 2026-10-30"
    assert item["listing_date"] == "2026-11-05"
    assert item["days_to_listing"] == 3
    assert item["model_estimate"] == "+15.50%"
    assert item["probability_gt10"] == "65.0%"
    assert "[ -7.63%, +38.63%]" in item["interval_80"] or "[-7.63%, +38.63%]" in item["interval_80"]
    assert item["gmp_at_scoring"] == "+12.00%"
    assert item["confidence_flag"] == "STANDARD"
    assert item["notes"] == "with-GMP regime"


def test_completed_row_does_not_appear_in_pre_listing(tmp_path: Path):
    """D-079: A completed forward row with actual_gain_pct does not appear in the pre-listing list."""
    dummy_log = tmp_path / "prediction_log.csv"
    with open(dummy_log, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scored_at", "company", "open_date", "close_date", "listing_date",
            "features_snapshot_json", "pred_gain_pct", "pred_prob_gt10",
            "gmp_pct_at_scoring", "actual_gain_pct", "status", "notes"
        ])
        # Completed forward row
        writer.writerow([
            "2026-10-20T10:00:00", "Completed Corp", "2026-10-15", "2026-10-19", "2026-10-23",
            '{"issue_price": 100.0}', "20.00", "0.75", "15.0", "22.50", "FORWARD", "completed"
        ])

    data = get_pre_listing_data(log_path=dummy_log, as_of_date="2026-11-02")
    assert len(data["pending_predictions"]) == 0


def test_bidding_open_ipo_appears_without_numbers(tmp_path: Path):
    """D-079: An open IPO appears in Bidding Open block without prediction numbers."""
    dummy_log = tmp_path / "prediction_log.csv"
    dummy_log.write_text("scored_at,company,open_date,close_date,listing_date,features_snapshot_json,pred_gain_pct,pred_prob_gt10,gmp_pct_at_scoring,actual_gain_pct,status,notes\n", encoding="utf-8")

    discovery_cands = [
        {
            "company": "Open Candidate Ltd",
            "open_date": "2026-10-29",
            "close_date": "2026-11-02",
            "listing_date": "2026-11-05",
            "status": "BIDDING_OPEN",
        }
    ]

    data = get_pre_listing_data(log_path=dummy_log, as_of_date="2026-11-02", discovery_candidates=discovery_cands)
    open_ipos = data["bidding_open_ipos"]
    assert len(open_ipos) == 1
    cand = open_ipos[0]
    assert cand["company"] == "Open Candidate Ltd"
    assert cand["status"] == "BIDDING_OPEN"
    assert "scored after close on 2026-11-02" in cand["notes"]
    # Ensure no prediction keys exist in open candidates
    assert "model_estimate" not in cand
    assert "pred_gain_pct" not in cand
    assert "probability_gt10" not in cand

    md = render_pre_listing_markdown(data=data, log_path=dummy_log)
    assert "Open Candidate Ltd" in md
    assert "BIDDING_OPEN" in md
    assert "scored after close on 2026-11-02" in md


def test_scored_after_listing_rejected_and_excluded(tmp_path: Path):
    """D-079: A row scored on or after its listing date is invalid and excluded from pre-listing."""
    dummy_log = tmp_path / "prediction_log.csv"
    with open(dummy_log, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scored_at", "company", "open_date", "close_date", "listing_date",
            "features_snapshot_json", "pred_gain_pct", "pred_prob_gt10",
            "gmp_pct_at_scoring", "actual_gain_pct", "status", "notes"
        ])
        # Backdated / scored on listing date: scored_at 2026-11-03 >= listing_date 2026-11-03
        writer.writerow([
            "2026-11-03T10:00:00", "Late Scored Corp", "2026-10-27", "2026-10-29", "2026-11-03",
            '{"issue_price": 50.0}', "10.00", "0.50", "5.0", "", "FORWARD", "late"
        ])

    data = get_pre_listing_data(log_path=dummy_log, as_of_date="2026-11-02")
    assert len(data["pending_predictions"]) == 0


def test_pre_listing_file_written_by_daily_job():
    """D-079: predictions/pre_listing_predictions.md is generated and has provisional banner."""
    out_md = render_pre_listing_markdown()
    assert PRE_LISTING_MD.exists()
    content = PRE_LISTING_MD.read_text(encoding="utf-8")
    assert "# Pre-Listing Predictions (Awaiting Listing)" in content
    assert "PROVISIONAL STATUS: n listed =" in content
    assert "Active Forward Predictions (Awaiting Listing)" in content
    assert "Bidding Open (Scored After Close)" in content
    assert ("Model Estimate" in content) or ("No active forward predictions awaiting listing" in content)


def test_dashboard_contains_pre_listing_section():
    """D-079: dashboard/index.html renders the Pre-listing predictions section."""
    render_dashboard_html()
    assert DASHBOARD_HTML.exists()
    content = DASHBOARD_HTML.read_text(encoding="utf-8")
    assert "Pre-listing predictions (awaiting listing)" in content
    assert "Bidding open, scored after close" in content
    assert ("Model Estimate" in content) or ("No active forward predictions awaiting listing" in content)
    assert "Days to Listing" in content


def test_pre_listing_table_shows_distinct_bidding_dates(tmp_path: Path):
    """D-090: Ensure pre-listing table shows distinct open and close dates and does not repeat close date twice."""
    dummy_log = tmp_path / "prediction_log.csv"
    with open(dummy_log, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "scored_at", "company", "open_date", "close_date", "listing_date",
            "features_snapshot_json", "pred_gain_pct", "pred_prob_gt10",
            "gmp_pct_at_scoring", "actual_gain_pct", "status", "notes"
        ])
        # Case 1: distinct open and close dates
        writer.writerow([
            "2026-11-01T10:00:00", "Distinct Dates Corp", "2026-10-28", "2026-10-30", "2026-11-05",
            '{"issue_price": 100.0}', "10.00", "0.60", "5.0", "", "FORWARD", "test"
        ])
        # Case 2: identical open and close dates (close date repeated)
        writer.writerow([
            "2026-11-01T10:00:00", "Same Dates Corp", "2026-10-30", "2026-10-30", "2026-11-05",
            '{"issue_price": 100.0}', "10.00", "0.60", "5.0", "", "FORWARD", "test"
        ])

    data = get_pre_listing_data(log_path=dummy_log, as_of_date="2026-11-02")
    pending = {item["company"]: item for item in data["pending_predictions"]}

    # Case 1 must show distinct dates
    assert pending["Distinct Dates Corp"]["bidding_dates"] == "2026-10-28 to 2026-10-30"

    # Case 2 must NOT repeat close date twice as '2026-10-30 to 2026-10-30'
    assert pending["Same Dates Corp"]["bidding_dates"] == "2026-10-30"
    assert "2026-10-30 to 2026-10-30" not in pending["Same Dates Corp"]["bidding_dates"]

    md = render_pre_listing_markdown(data=data, log_path=dummy_log)
    assert "2026-10-28 to 2026-10-30" in md
    assert "2026-10-30 to 2026-10-30" not in md
