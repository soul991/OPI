"""Regression tests for forward log integrity and scheduling rules (D-004, D-005)."""

import os
from datetime import date
import pandas as pd
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_PATH = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")


def test_forward_rows_scored_after_bidding_closed():
    """D-004: Every FORWARD row must be scored strictly after bidding closed (final subscription)."""
    assert os.path.exists(LOG_PATH), "prediction_log.csv must exist"
    df = pd.read_csv(LOG_PATH, parse_dates=["scored_at", "close_date", "listing_date"])
    forward = df[df["status"] == "FORWARD"].copy()
    assert len(forward) > 0, "Expected at least 1 FORWARD row"

    # Close cut-off: 18:00 IST on close date
    close_cut = forward["close_date"] + pd.Timedelta(hours=18)
    early = forward[forward["scored_at"] < close_cut]
    assert len(early) == 0, f"Found FORWARD rows scored before bidding closed: {early['company'].tolist()}"

    # Must not contain references to Day 1 or Day 2 live tracking in notes
    nonfinal = forward[forward["notes"].astype(str).str.contains(r"day\s*[12]\b|live", case=False, regex=True)]
    assert len(nonfinal) == 0, f"Found FORWARD rows with nonfinal/live subscription: {nonfinal['company'].tolist()}"

    # Feature snapshot must contain http URLs
    for _, row in forward.iterrows():
        snap = str(row["features_snapshot_json"])
        assert "http" in snap, f"Features snapshot for {row['company']} missing http URLs: {snap}"


def test_actuals_only_for_listed():
    """D-005: Actual listing gain must only be recorded for IPOs whose listing date has passed."""
    assert os.path.exists(LOG_PATH), "prediction_log.csv must exist"
    df = pd.read_csv(LOG_PATH, parse_dates=["listing_date"])
    forward = df[df["status"] == "FORWARD"].copy()

    # If listing date is in the future, actual_gain_pct must be null/empty
    today = date.today()
    unlisted = forward[forward["listing_date"].dt.date > today]
    for _, row in unlisted.iterrows():
        act = row["actual_gain_pct"]
        assert pd.isna(act) or str(act).strip() == "", (
            f"Unlisted IPO {row['company']} (listing {row['listing_date'].date()}) "
            f"has premature actual_gain_pct={act}"
        )
