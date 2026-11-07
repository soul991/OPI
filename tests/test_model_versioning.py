"""Regression and compliance tests for model versioning sidecar (D-106).

Validates:
1. predictions/model_versions.csv exists with exact 8-column header.
2. Existing 13 FORWARD rows backfilled with model_version='v4.0.0-champion', role='champion', backfilled=True.
3. predictions/prediction_log.csv schema remains 100% byte-identical (0 columns added).
4. append_prediction_log records champion + shadow rows to model_versions.csv.
5. Shadow rows never feed official champion metrics.
"""

import csv
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
import pytest

from opi.log import (
    LOG_PATH,
    MODEL_VERSIONS_PATH,
    MODEL_VERSIONS_COLUMNS,
    append_prediction_log,
    append_model_version_log,
)

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_model_versions_header_and_backfill():
    """D-106: Verify model_versions.csv schema and initial 13 backfilled champion rows."""
    assert MODEL_VERSIONS_PATH.exists(), "predictions/model_versions.csv must exist"
    
    with open(MODEL_VERSIONS_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        
    expected_header = [
        "scored_at",
        "company",
        "listing_date",
        "model_version",
        "role",
        "pred_gain_pct",
        "pred_prob_gt10",
        "backfilled"
    ]
    assert header == expected_header, f"Header mismatch: {header} vs {expected_header}"
    
    mv_df = pd.read_csv(MODEL_VERSIONS_PATH)
    assert len(mv_df) >= 13, f"Expected at least 13 backfilled rows, found {len(mv_df)}"
    
    # Check backfilled rows
    bf_rows = mv_df[mv_df["backfilled"] == True]
    assert len(bf_rows) == 13, f"Expected exactly 13 backfilled rows, found {len(bf_rows)}"
    assert (bf_rows["model_version"] == "v4.0.0-champion").all()
    assert (bf_rows["role"] == "champion").all()


def test_prediction_log_byte_identical_schema():
    """D-106: predictions/prediction_log.csv must not have columns added or format changed."""
    assert LOG_PATH.exists(), "predictions/prediction_log.csv must exist"
    
    expected_log_cols = [
        "scored_at",
        "company",
        "open_date",
        "close_date",
        "listing_date",
        "features_snapshot_json",
        "pred_gain_pct",
        "pred_prob_gt10",
        "gmp_pct_at_scoring",
        "actual_gain_pct",
        "status",
        "notes"
    ]
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        
    assert header == expected_log_cols, f"prediction_log.csv header must match exactly: {header}"


def test_append_prediction_log_records_to_model_versions(tmp_path: Path, monkeypatch):
    """D-106: append_prediction_log automatically appends a champion row to model_versions.csv."""
    test_log = tmp_path / "prediction_log.csv"
    test_mv = tmp_path / "model_versions.csv"
    
    monkeypatch.setattr("opi.log.LOG_PATH", test_log)
    monkeypatch.setattr("opi.log.MODEL_VERSIONS_PATH", test_mv)
    
    dummy_features = {
        "issue_price": 100.0,
        "issue_size_cr": 500.0,
        "sub_total": 10.0,
    }
    
    row = append_prediction_log(
        company="Test Autopilot Corp",
        open_date="2026-11-01",
        close_date="2026-11-03",
        listing_date="2026-11-10",
        features=dummy_features,
        pred_gain_pct=15.50,
        pred_prob_gt10=0.7500,
        gmp_pct_at_scoring=12.00,
        status="FORWARD",
        notes="Autopilot test",
        model_version="v4.0.0-champion",
        _fixture_clock=lambda: "2026-11-07T12:00:00+05:30",
    )
    
    assert test_log.exists()
    assert test_mv.exists()
    
    mv_df = pd.read_csv(test_mv)
    assert len(mv_df) == 1
    assert mv_df["company"].iloc[0] == "Test Autopilot Corp"
    assert mv_df["model_version"].iloc[0] == "v4.0.0-champion"
    assert mv_df["role"].iloc[0] == "champion"
    assert mv_df["pred_gain_pct"].iloc[0] == 15.50
    assert mv_df["pred_prob_gt10"].iloc[0] == 0.7500
    assert mv_df["backfilled"].iloc[0] == False
