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
    df = pd.read_csv(LOG_PATH)
    forward = df[df["status"] == "FORWARD"].copy()
    assert len(forward) > 0, "Expected at least 1 FORWARD row"

    # Close cut-off: 18:00 IST on close date
    sc = pd.to_datetime(forward["scored_at"], format="mixed")
    forward["scored_dt"] = sc.apply(lambda t: t if t.tzinfo is None else t.tz_convert("Asia/Kolkata").tz_localize(None))
    forward["close_dt"] = pd.to_datetime(forward["close_date"])
    close_cut = forward["close_dt"] + pd.Timedelta(hours=18)
    early = forward[forward["scored_dt"] < close_cut]
    assert len(early) == 0, f"Found FORWARD rows scored before bidding closed: {early['company'].tolist()}"

    # Must not contain references to Day 1 or Day 2 live tracking in notes
    nonfinal = forward[forward["notes"].astype(str).str.contains(r"day\s*[12]\b|live", case=False, regex=True)]
    assert len(nonfinal) == 0, f"Found FORWARD rows with nonfinal/live subscription: {nonfinal['company'].tolist()}"

    # Feature snapshot must contain http URLs and model_version
    for _, row in forward.iterrows():
        snap = str(row["features_snapshot_json"])
        assert "http" in snap, f"Features snapshot for {row['company']} missing http URLs: {snap}"
        assert "_model_version" in snap, f"Features snapshot for {row['company']} missing _model_version: {snap}"



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


def test_scored_at_is_real_run_time():
    """D-016: FORWARD rows must record real write time with timezone offset and no backdating."""
    assert os.path.exists(LOG_PATH), "prediction_log.csv must exist"
    df = pd.read_csv(LOG_PATH)
    forward = df[df["status"] == "FORWARD"].copy()
    assert len(forward) > 0, "Expected at least 1 active FORWARD row"

    for _, row in forward.iterrows():
        raw_ts = str(row["scored_at"])
        parsed = pd.to_datetime(raw_ts)
        assert parsed.tzinfo is not None or "+" in raw_ts or "-" in raw_ts[10:], (
            f"FORWARD row for {row['company']} must carry timezone offset: {raw_ts}"
        )

    # Verify write-time timestamp generator in opi.log
    from opi.log import get_write_timestamp, set_test_fixture_clock
    ts = get_write_timestamp()
    assert "+05:30" in ts or "Z" in ts or "+" in ts[10:], f"get_write_timestamp() missing offset: {ts}"

    # Verify test fixture clock override works when explicitly enabled
    set_test_fixture_clock(lambda: "2026-10-16T12:00:00+05:30")
    assert get_write_timestamp() == "2026-10-16T12:00:00+05:30"
    set_test_fixture_clock(None)


def test_candidate_ipos_scored_after_close():
    """D-023, D-024: Jio Platforms and Paras Healthcare scored after bidding closed with valid groundings."""
    assert os.path.exists(LOG_PATH), "prediction_log.csv must exist"
    df = pd.read_csv(LOG_PATH)
    companies = df["company"].tolist()
    assert "Jio Platforms Limited" in companies, "Jio Platforms Limited must be scored"
    assert "Paras Healthcare Limited" in companies, "Paras Healthcare Limited must be scored"

    jio = df[df["company"] == "Jio Platforms Limited"].iloc[0]
    paras = df[df["company"] == "Paras Healthcare Limited"].iloc[0]

    assert jio["status"] == "FORWARD"
    assert paras["status"] == "FORWARD"
    assert jio["listing_date"] == "2026-10-28"
    assert paras["listing_date"] == "2026-10-28"
    assert pd.isna(jio["actual_gain_pct"])
    assert pd.isna(paras["actual_gain_pct"])
    assert float(jio["pred_prob_gt10"]) > 0.0
    assert float(paras["pred_prob_gt10"]) > 0.0


def test_jio_sector_flagged_unverified():
    """D-044: Jio Platforms sector label is audited and flagged as UNVERIFIED without row alteration."""
    status_doc = os.path.join(ROOT_DIR, "phases", "Phase 11", "forward_status.md")
    assert os.path.exists(status_doc), "forward_status.md must exist"
    content = open(status_doc, encoding="utf-8").read()
    assert "UNVERIFIED (D-044)" in content, "Jio Platforms sector must be documented as UNVERIFIED"

    # Verify original row in prediction_log.csv was not modified in-place
    df = pd.read_csv(LOG_PATH)
    jio = df[df["company"] == "Jio Platforms Limited"].iloc[0]
    assert jio["status"] == "FORWARD"
    assert "IT & Technology" in str(jio["features_snapshot_json"])



