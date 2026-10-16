"""Append-only forward prediction log and outcome recording module."""

import csv
import json
import os
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
RUN_LOG_PATH = ROOT_DIR / "predictions" / "run_log.csv"

IST = timezone(timedelta(hours=5, minutes=30))
_TEST_FIXTURE_CLOCK: Optional[Callable[[], str]] = None


def set_test_fixture_clock(clock_fn: Optional[Callable[[], str]] = None):
    """Set or reset an explicit fixture clock strictly for test runs."""
    global _TEST_FIXTURE_CLOCK
    _TEST_FIXTURE_CLOCK = clock_fn


def get_write_timestamp() -> str:
    """Generate ISO 8601 timestamp with timezone offset at write time.
    Never accepts caller-supplied or hardcoded timestamps except via test fixture clock.
    """
    if _TEST_FIXTURE_CLOCK is not None:
        return _TEST_FIXTURE_CLOCK()
    return datetime.now(IST).isoformat()


LOG_COLUMNS = [
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

EXCLUDE_FROM_SNAPSHOT = {"listing_price", "listing_gain_pct", "label_good"}


def serialize_features_snapshot(features: Dict[str, Any], model_version: Optional[str] = None) -> str:
    """Serialize feature inputs into auditable JSON, excluding outcome labels."""
    clean = {}
    if model_version:
        clean["_model_version"] = model_version
    for k, v in features.items():
        if k in EXCLUDE_FROM_SNAPSHOT:
            continue
        if pd.isna(v) or v is None:
            clean[k] = None
        elif isinstance(v, (int, np.integer)):
            clean[k] = int(v)
        elif isinstance(v, (float, np.floating)):
            clean[k] = round(float(v), 4)
        else:
            clean[k] = str(v)
    return json.dumps(clean, ensure_ascii=False, sort_keys=True)


def append_run_log(run_id: str, action: str, company: str, status: str, details: str = ""):
    """Record operational execution status to predictions/run_log.csv."""
    RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = RUN_LOG_PATH.exists()
    with open(RUN_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "run_id", "action", "company", "status", "details"])
        writer.writerow([get_write_timestamp(), run_id, action, company, status, details])


def append_prediction_log(
    company: str,
    open_date: str,
    close_date: str,
    listing_date: str,
    features: Dict[str, Any],
    pred_gain_pct: float,
    pred_prob_gt10: float,
    gmp_pct_at_scoring: Optional[float],
    status: str = "FORWARD",
    notes: str = "",
    model_version: Optional[str] = None,
    _fixture_clock: Optional[Callable[[], str]] = None
) -> Dict[str, Any]:
    """Append a verified forward prediction row to predictions/prediction_log.csv (append-only).
    Timestamp is strictly generated at write time with timezone offset.
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = LOG_PATH.exists()
    
    if _fixture_clock is not None:
        timestamp = _fixture_clock()
    else:
        timestamp = get_write_timestamp()
    snapshot_json = serialize_features_snapshot(features, model_version)
    
    row_dict = {
        "scored_at": timestamp,
        "company": company,
        "open_date": open_date,
        "close_date": close_date,
        "listing_date": listing_date,
        "features_snapshot_json": snapshot_json,
        "pred_gain_pct": round(float(pred_gain_pct), 2),
        "pred_prob_gt10": round(float(pred_prob_gt10), 4),
        "gmp_pct_at_scoring": round(float(gmp_pct_at_scoring), 2) if gmp_pct_at_scoring is not None else None,
        "actual_gain_pct": None,
        "status": status,
        "notes": notes
    }
    
    # Check for existing forward duplicate
    if file_exists:
        existing = pd.read_csv(LOG_PATH)
        f_dup = existing[(existing["company"] == company) & (existing["listing_date"] == listing_date) & (existing["status"] == "FORWARD")]
        if len(f_dup) > 0 and status == "FORWARD":
            raise ValueError(f"Duplicate active FORWARD prediction already logged for {company} listing on {listing_date}")
            
    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(LOG_COLUMNS)
        writer.writerow([row_dict[col] for col in LOG_COLUMNS])
        
    return row_dict


from typing import Dict, Any, Optional, Tuple, Union

def update_actual_outcome(
    company: str,
    listing_date: str,
    actual_listing_price: Optional[float] = None,
    issue_price: Optional[float] = None,
    actual_gain_pct: Optional[float] = None,
    source_url: str = "",
    source_snapshot_path: Optional[str] = None,
    log_path: Optional[Union[str, Path]] = None
) -> Tuple[bool, str]:
    """Record actual listing outcome for a listed FORWARD row."""
    target_log = Path(log_path) if log_path else LOG_PATH
    if not target_log.exists():
        return False, f"{target_log} does not exist"
        
    df = pd.read_csv(target_log)
    mask = (df["company"] == company) & (df["listing_date"] == listing_date) & (df["status"] == "FORWARD")
    
    if mask.sum() == 0:
        return False, f"No active FORWARD row found for {company} ({listing_date})"
        
    if actual_gain_pct is not None:
        actual_gain = round(float(actual_gain_pct), 2)
    elif actual_listing_price is not None and issue_price is not None and issue_price > 0:
        actual_gain = round(((actual_listing_price - issue_price) / issue_price) * 100.0, 2)
    else:
        return False, "Must provide either actual_gain_pct or (actual_listing_price and issue_price)"

    df.loc[mask, "actual_gain_pct"] = actual_gain
    
    old_notes = str(df.loc[mask, "notes"].iloc[0]) if pd.notna(df.loc[mask, "notes"].iloc[0]) else ""
    if source_url:
        evidence_note = f"Actual listing verified via {source_url}"
        df.loc[mask, "notes"] = f"{old_notes} | {evidence_note}".strip(" |")
    
    df.to_csv(target_log, index=False)
    return True, f"Updated {company} actual gain to {actual_gain}%"

