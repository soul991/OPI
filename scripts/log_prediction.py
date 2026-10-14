#!/usr/bin/env python3
"""Forward Prediction Scoring & Logging Script for OPI.

Usage:
    python scripts/log_prediction.py [input_csv] [--notes "analyst note"]

Description:
    1. Loads the latest model (prefers Phase 4 model/ipo_model_phase4.joblib,
       falling back to model/ipo_model.joblib).
    2. Reads upcoming or unlisted IPO candidate(s) from input CSV (default: new_ipo.csv).
    3. Runs domain feature engineering via prep() in model/train.py.
    4. Computes estimated listing gain (%) and probability of gain > 10%.
    5. Captures a JSON snapshot of input features for auditable provenance.
    6. Appends prediction rows to predictions/prediction_log.csv (APPEND-ONLY).
    7. Displays prediction summary to the user.
"""

import os
import sys
import csv
import json
import argparse
from datetime import datetime
import numpy as np
import pandas as pd
import joblib

# Ensure repository root and model directory are on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "model"))

from train import prep, FEATURES, ALL_NUM, CAT

LOG_PATH = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")
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
    "notes",
]

# Columns representing post-listing outcomes that must NEVER be in feature snapshots
EXCLUDE_SNAPSHOT_COLS = {"listing_price", "listing_gain_pct", "label_good"}


def load_model(custom_path=None):
    """Load model artifact, preferring Phase 4 then falling back to baseline."""
    if custom_path:
        if not os.path.exists(custom_path):
            raise FileNotFoundError(f"Specified model path not found: {custom_path}")
        path = custom_path
        version = "Custom"
    else:
        p4_path = os.path.join(ROOT_DIR, "model", "ipo_model_phase4.joblib")
        p2_path = os.path.join(ROOT_DIR, "model", "ipo_model.joblib")
        if os.path.exists(p4_path):
            path = p4_path
            version = "Phase 4 (model/ipo_model_phase4.joblib)"
        elif os.path.exists(p2_path):
            path = p2_path
            version = "Phase 2 / Baseline (model/ipo_model.joblib)"
        else:
            raise FileNotFoundError(
                f"No model found at {p4_path} or {p2_path}. Please train a model first."
            )

    print(f"Loading model artifact: {path} [{version}]")
    art = joblib.load(path)
    return art, path, version


def create_feature_snapshot(row):
    """Serialize all available input features into a clean JSON dictionary."""
    snapshot = {}
    for col in row.index:
        if col in EXCLUDE_SNAPSHOT_COLS:
            continue
        val = row[col]
        if pd.isna(val) or val is None:
            snapshot[col] = None
        elif isinstance(val, (np.integer, int)):
            snapshot[col] = int(val)
        elif isinstance(val, (np.floating, float)):
            snapshot[col] = round(float(val), 4)
        else:
            snapshot[col] = str(val)
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True)


def ensure_log_initialized(log_file=LOG_PATH):
    """Ensure prediction log file and directory exist with header."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
        with open(log_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(LOG_COLUMNS)


def append_prediction_row(record, log_file=LOG_PATH):
    """Append a single prediction record to the prediction log CSV (APPEND-ONLY)."""
    ensure_log_initialized(log_file)
    with open(log_file, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(record)


def score_dataframe(df, art, notes_override=None, log_file=LOG_PATH, status="FORWARD"):
    """Score all rows in df and append to log."""
    reg = art.get("reg")
    # Use calibrated classifier (cal_clf) when available, matching the
    # evaluation pipeline.  Fall back to raw clf only if cal_clf is absent
    # (e.g. Phase-2 baseline model).
    clf = art.get("cal_clf") or art.get("clf")
    levels = art.get("levels")

    if reg is None or clf is None:
        raise ValueError("Loaded model artifact missing 'reg' or 'clf'/'cal_clf' estimator.")

    scored_records = []

    for idx, row in df.iterrows():
        company_name = str(row.get("company", f"IPO_{idx+1}"))
        one = pd.DataFrame([row])
        
        # Feature transformation via standard prep()
        X, _ = prep(one, cat_levels=levels)

        # Regressor prediction (listing gain %)
        pred_gain = float(reg.predict(X)[0])

        # Classifier prediction (probability gain > 10%)
        probs = clf.predict_proba(X)[0]
        if hasattr(clf, "classes_") and 1 in clf.classes_:
            class_idx = list(clf.classes_).index(1)
            pred_prob = float(probs[class_idx])
        elif len(probs) > 1:
            pred_prob = float(probs[1])
        else:
            pred_prob = float(probs[0])

        # GMP at scoring
        raw_gmp = row.get("gmp_pct")
        if pd.notna(raw_gmp) and str(raw_gmp).strip() != "":
            try:
                gmp_at_scoring = round(float(raw_gmp), 2)
            except (ValueError, TypeError):
                gmp_at_scoring = ""
        else:
            gmp_at_scoring = ""

        # Notes resolution
        row_notes = str(row.get("notes", "")).strip() if pd.notna(row.get("notes")) else ""
        if notes_override and row_notes:
            combined_notes = f"{row_notes} | {notes_override}"
        elif notes_override:
            combined_notes = notes_override
        else:
            combined_notes = row_notes

        snapshot_json = create_feature_snapshot(row)
        now_iso = datetime.now().isoformat()

        record = {
            "scored_at": now_iso,
            "company": company_name,
            "open_date": str(row.get("open_date", "")).strip() if pd.notna(row.get("open_date")) else "",
            "close_date": str(row.get("close_date", "")).strip() if pd.notna(row.get("close_date")) else "",
            "listing_date": str(row.get("listing_date", "")).strip() if pd.notna(row.get("listing_date")) else "",
            "features_snapshot_json": snapshot_json,
            "pred_gain_pct": round(pred_gain, 2),
            "pred_prob_gt10": round(pred_prob, 4),
            "gmp_pct_at_scoring": gmp_at_scoring,
            "actual_gain_pct": "",  # Strictly empty at initial scoring
            "status": str(status or row.get("status") or "FORWARD").strip(),
            "notes": combined_notes,
        }

        # Append to prediction log
        append_prediction_row(record, log_file=log_file)
        scored_records.append(record)

        # Missing input check
        missing = [c for c in FEATURES if pd.isna(row.get(c)) or row.get(c) == ""]

        # Formatted output
        print("\n" + "=" * 78)
        print(f"  PREDICTION LOGGED: {company_name}")
        print("=" * 78)
        print(f"Scored At               : {now_iso}")
        print(f"Dates (Open/Close/List) : {record['open_date'] or 'N/A'} / {record['close_date'] or 'N/A'} / {record['listing_date'] or 'N/A'}")
        
        issue_price = f"₹{row.get('issue_price')}" if pd.notna(row.get('issue_price')) else "N/A"
        issue_size = f"₹{row.get('issue_size_cr')} Cr" if pd.notna(row.get('issue_size_cr')) else "N/A"
        print(f"Issue Price / Size (Cr) : {issue_price} / {issue_size}")
        
        sub_tot = f"{row.get('sub_total')}x" if pd.notna(row.get('sub_total')) else "N/A"
        sub_q = f"QIB: {row.get('sub_qib')}x" if pd.notna(row.get('sub_qib')) else "QIB: N/A"
        sub_n = f"NII: {row.get('sub_nii')}x" if pd.notna(row.get('sub_nii')) else "NII: N/A"
        sub_r = f"Retail: {row.get('sub_retail')}x" if pd.notna(row.get('sub_retail')) else "Retail: N/A"
        print(f"Subscription Demand     : {sub_tot} ({sub_q}, {sub_n}, {sub_r})")
        
        gmp_str = f"{gmp_at_scoring:+.2f}%" if gmp_at_scoring != "" else "N/A"
        print(f"GMP % at Scoring        : {gmp_str}")
        print("-" * 78)
        print(f"Estimated Listing Gain  : {pred_gain:+.2f}%")
        print(f"P(Gain > 10%)           : {pred_prob*100:.1f}% (raw prob: {pred_prob:.4f})")
        print("-" * 78)
        print(f"Missing Features ({len(missing)}): {', '.join(missing) if missing else 'None'}")
        if len(missing) > 6:
            print("WARNING: Multiple inputs missing. Confidence in model output is reduced.")
        print(f"Logged Status           : Appended to {os.path.relpath(log_file, ROOT_DIR)} (actual_gain_pct=EMPTY)")
        print("Disclaimer              : Decision aid only. Not financial advice.")
        print("=" * 78)

    return scored_records


def main():
    parser = argparse.ArgumentParser(description="Score new IPOs and log forward predictions.")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="new_ipo.csv",
        help="Path to input CSV containing IPO features (default: new_ipo.csv)",
    )
    parser.add_argument("--model", type=str, default=None, help="Custom path to model artifact .joblib")
    parser.add_argument("--notes", type=str, default=None, help="Additional qualitative analyst notes")
    parser.add_argument("--status", type=str, default="FORWARD", help="Prediction status: FORWARD (default), TEST_NOT_FORWARD, etc.")
    parser.add_argument("--log", type=str, default=LOG_PATH, help="Path to prediction log CSV")

    args = parser.parse_args()

    input_path = os.path.abspath(args.csv_path)
    if not os.path.exists(input_path):
        print(f"Error: Input file '{args.csv_path}' not found.")
        sys.exit(1)

    df = pd.read_csv(input_path)
    if df.empty:
        print(f"Error: Input file '{args.csv_path}' is empty.")
        sys.exit(1)

    art, model_path, version = load_model(args.model)
    score_dataframe(df, art, notes_override=args.notes, log_file=args.log, status=args.status)


if __name__ == "__main__":
    main()
