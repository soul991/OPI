#!/usr/bin/env python3
"""Forward Prediction Performance Reporter for OPI.

Usage:
    python scripts/forward_report.py [--log predictions/prediction_log.csv]

Description:
    Reads predictions/prediction_log.csv and evaluates performance strictly on
    genuine out-of-sample forward predictions (status == 'FORWARD').
    Explicitly filters out and reports counts of excluded rows (TEST_* and INVALID).
    Enforces Phase 5 Rule: no statistical claims allowed when n < 30 ("n too small").
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_PATH = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")


def generate_forward_report(log_path=LOG_PATH):
    """Analyze and report on genuine forward predictions in log_path."""
    if not os.path.exists(log_path):
        print(f"Prediction log not found at: {log_path}")
        return None

    df = pd.read_csv(log_path)
    if df.empty:
        print("Prediction log is empty.")
        return None

    # Ensure status column exists
    if "status" not in df.columns:
        print("Warning: 'status' column missing; treating all rows as unverified.")
        df["status"] = "UNVERIFIED"

    # Identify and categorize rows
    status_series = df["status"].fillna("").astype(str).str.strip().str.upper()
    test_mask = status_series.str.startswith("TEST")
    invalid_mask = status_series.str.startswith("INVALID")
    forward_mask = status_series == "FORWARD"
    other_mask = ~test_mask & ~invalid_mask & ~forward_mask

    total_rows = len(df)
    test_count = int(test_mask.sum())
    invalid_count = int(invalid_mask.sum())
    other_count = int(other_mask.sum())
    forward_df = df[forward_mask].copy()
    n_forward = len(forward_df)

    print("=" * 78)
    print("  OPI FORWARD PREDICTION AUDIT & PERFORMANCE REPORT")
    print("=" * 78)
    print(f"Log File Location          : {os.path.relpath(log_path, ROOT_DIR)}")
    print(f"Total Logged Rows          : {total_rows}")
    print(f"Excluded TEST Rows         : {test_count} (status starting with TEST_*)")
    print(f"Excluded INVALID Rows      : {invalid_count} (status starting with INVALID*)")
    if other_count > 0:
        print(f"Excluded Other Rows        : {other_count} (status unverified/unknown)")
    print(f"Genuine FORWARD Rows       : {n_forward} (status == 'FORWARD')")
    print("-" * 78)

    if n_forward == 0:
        print("No genuine forward predictions recorded yet.")
        print("All existing rows are test placeholders or invalid entries.")
        print("Genuine upcoming IPO predictions will be logged in Phase 5 Workstream D.")
        print("=" * 78)
        return {
            "total_rows": total_rows,
            "test_rows": test_count,
            "invalid_rows": invalid_count,
            "forward_rows": 0,
            "evaluated_rows": 0,
            "mae": None,
            "status": "NO_FORWARD_ROWS"
        }

    # Analyze evaluated vs pending forward rows
    forward_df["actual_clean"] = pd.to_numeric(forward_df["actual_gain_pct"], errors="coerce")
    forward_df["pred_clean"] = pd.to_numeric(forward_df["pred_gain_pct"], errors="coerce")
    forward_df["prob_clean"] = pd.to_numeric(forward_df["pred_prob_gt10"], errors="coerce")

    evaluated = forward_df[forward_df["actual_clean"].notna()].copy()
    pending = forward_df[forward_df["actual_clean"].isna()].copy()
    n_eval = len(evaluated)
    n_pending = len(pending)

    print(f"Evaluated (Listed) Rows    : {n_eval}")
    print(f"Pending (Unlisted) Rows    : {n_pending}")
    print("-" * 78)

    if n_eval < 30:
        print(f"[!] Sample Size Warning: n = {n_eval} evaluated IPOs.")
        print("    Per Phase 5 Section 4.D / Section 6: claims about final forward performance")
        print("    are strictly forbidden below n = 30 ('n too small'). All metrics are PROVISIONAL.")
        print("-" * 78)

    if n_eval > 0:
        evaluated["abs_error"] = (evaluated["pred_clean"] - evaluated["actual_clean"]).abs()
        mae = float(evaluated["abs_error"].mean())
        median_err = float(evaluated["abs_error"].median())
        
        # Binary pop prediction accuracy
        pred_pop = evaluated["pred_clean"] > 10.0
        act_pop = evaluated["actual_clean"] > 10.0
        acc_pop = float((pred_pop == act_pop).mean() * 100)

        print(f"Provisional MAE            : {mae:.2f}% (n={n_eval})")
        print(f"Provisional Median Error   : {median_err:.2f}%")
        print(f"Provisional Pop (>10%) Acc : {acc_pop:.1f}%")
        print("-" * 78)
        print(f"{'Company':<25} {'Listing Date':<12} {'Pred %':<9} {'Actual %':<10} {'Error %':<9}")
        print("-" * 78)
        for _, r in evaluated.iterrows():
            print(f"{str(r['company'])[:24]:<25} {str(r.get('listing_date',''))[:10]:<12} {r['pred_clean']:+6.2f}%   {r['actual_clean']:+6.2f}%    {r['abs_error']:5.2f}%")
    else:
        mae = None
        print("No forward rows have listed yet. Awaiting actual listing day returns.")

    if n_pending > 0:
        print("\nPending Upcoming IPOs:")
        for _, r in pending.iterrows():
            print(f"  - {r['company']}: Pred {r['pred_clean']:+.2f}%, P(>10%) {r['prob_clean']:.1%}, Listing: {r.get('listing_date', 'N/A')}")

    print("=" * 78)
    return {
        "total_rows": total_rows,
        "test_rows": test_count,
        "invalid_rows": invalid_count,
        "forward_rows": n_forward,
        "evaluated_rows": n_eval,
        "pending_rows": n_pending,
        "mae": mae,
        "provisional": n_eval < 30
    }


def main():
    parser = argparse.ArgumentParser(description="Report forward prediction performance for OPI.")
    parser.add_argument("--log", type=str, default=LOG_PATH, help="Path to prediction log CSV")
    args = parser.parse_args()
    generate_forward_report(args.log)


if __name__ == "__main__":
    main()
