#!/usr/bin/env python3
"""Forward Prediction Performance Reporter for OPI.

Usage:
    python scripts/forward_report.py [--log predictions/prediction_log.csv]

Description:
    Reads predictions/prediction_log.csv and evaluates performance strictly on
    genuine out-of-sample forward predictions (status == 'FORWARD').
    Explicitly filters out and reports counts of excluded rows (TEST_* and INVALID).
    Enforces Phase 10 Rule: no statistical claims or interval comparisons allowed
    when n < 30 ("n listed = ... of 30", descriptive only).
"""

from __future__ import annotations

import argparse
import os
import sys
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from opi.report import parse_defects_summary

LOG_PATH = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")


def generate_forward_report(log_path: str = LOG_PATH) -> dict | None:
    """Analyze and report on genuine forward predictions in log_path."""
    if not os.path.exists(log_path):
        print(f"Prediction log not found at: {log_path}")
        return None

    df = pd.read_csv(log_path)
    if df.empty:
        print("Prediction log is empty.")
        return None

    if "status" not in df.columns:
        print("Warning: 'status' column missing; treating all rows as unverified.")
        df["status"] = "UNVERIFIED"

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

    print("=" * 86)
    print("  OPI FORWARD PREDICTION AUDIT & PROSPECTIVE PERFORMANCE REPORT")
    print("=" * 86)
    print(f"Log File Location          : {os.path.relpath(log_path, ROOT_DIR)}")
    print(f"Total Logged Rows          : {total_rows}")
    print(f"Excluded TEST Rows         : {test_count} (status starting with TEST_*)")
    print(f"Excluded INVALID Rows      : {invalid_count} (status starting with INVALID*)")
    if other_count > 0:
        print(f"Excluded Other Rows        : {other_count} (status unverified/unknown)")
    print(f"Genuine FORWARD Rows       : {n_forward} (status == 'FORWARD')")
    defects = parse_defects_summary()
    print(f"Tracked Defects Health     : {defects['TOTAL']} total ({defects['FIXED']} fixed, {defects['ACCEPTED']} accepted, {defects['DEFERRED']} deferred, {defects['OPEN'] + defects['PARTIAL']} open/partial)")
    print("-" * 86)

    if n_forward == 0:
        print("No genuine forward predictions recorded yet.")
        print("=" * 86)
        return {
            "total_rows": total_rows,
            "test_rows": test_count,
            "invalid_rows": invalid_count,
            "forward_rows": 0,
            "evaluated_rows": 0,
            "status": "NO_FORWARD_ROWS"
        }

    forward_df["actual_clean"] = pd.to_numeric(forward_df["actual_gain_pct"], errors="coerce")
    forward_df["pred_clean"] = pd.to_numeric(forward_df["pred_gain_pct"], errors="coerce")
    forward_df["prob_clean"] = pd.to_numeric(forward_df["pred_prob_gt10"], errors="coerce")
    forward_df["gmp_clean"] = pd.to_numeric(forward_df["gmp_pct_at_scoring"], errors="coerce")

    evaluated = forward_df[forward_df["actual_clean"].notna()].copy()
    pending = forward_df[forward_df["actual_clean"].isna()].copy()
    n_eval = len(evaluated)
    n_pending = len(pending)

    print(f"Evaluated (Listed) Rows    : {n_eval} of 30 target")
    print(f"Pending (Unlisted) Rows    : {n_pending}")
    print("-" * 86)

    print(f"[!] PROVISIONAL STATUS BANNER: n listed = {n_eval} of 30")
    print("    Per pre-registered rules: no empirical superiority claims or interval comparisons")
    print("    are permitted below n = 30 ('n too small'). All metrics are strictly descriptive.")
    print("-" * 86)

    mae_model = None
    mae_gmp = None

    if n_eval > 0:
        evaluated["err_model"] = (evaluated["pred_clean"] - evaluated["actual_clean"]).abs()
        mae_model = float(evaluated["err_model"].mean())
        has_gmp = evaluated[evaluated["gmp_clean"].notna()].copy()
        if len(has_gmp) > 0:
            has_gmp["err_gmp"] = (has_gmp["gmp_clean"] - has_gmp["actual_clean"]).abs()
            mae_gmp = float(has_gmp["err_gmp"].mean())

        print(f"Provisional Model MAE      : {mae_model:.2f} percentage points (n={n_eval})")
        if mae_gmp is not None:
            print(f"Provisional Raw GMP MAE    : {mae_gmp:.2f} percentage points (n={len(has_gmp)})")
        print("-" * 86)
        print(f"{'Company':<26} {'Listing':<11} {'Model %':<9} {'GMP %':<8} {'Actual %':<10} {'Err Model':<10} {'Err GMP'}")
        print("-" * 86)
        for _, r in evaluated.iterrows():
            gmp_str = f"{r['gmp_clean']:+5.1f}%" if pd.notna(r['gmp_clean']) else "  N/A"
            err_gmp_str = f"{abs(r['gmp_clean'] - r['actual_clean']):5.2f} pp" if pd.notna(r['gmp_clean']) else "  N/A"
            print(f"{str(r['company'])[:25]:<26} {str(r.get('listing_date',''))[:10]:<11} {r['pred_clean']:+6.2f}%   {gmp_str:<8} {r['actual_clean']:+6.2f}%    {r['err_model']:5.2f} pp    {err_gmp_str}")
    else:
        print("No forward rows have listed yet. Awaiting actual listing day returns.")

    if n_pending > 0:
        print("\nPending Upcoming IPOs:")
        for _, r in pending.iterrows():
            gmp_str = f", GMP {r['gmp_clean']:+.1f}%" if pd.notna(r['gmp_clean']) else ""
            thin = " [Thin inputs: No GMP]" if pd.isna(r['gmp_clean']) else ""
            print(f"  - {r['company']}: Model {r['pred_clean']:+.2f}%{gmp_str}, P(>10%) {r['prob_clean']:.1%}, Listing: {r.get('listing_date', 'N/A')}{thin}")

    print("=" * 86)
    return {
        "total_rows": total_rows,
        "test_rows": test_count,
        "invalid_rows": invalid_count,
        "forward_rows": n_forward,
        "evaluated_rows": n_eval,
        "pending_rows": n_pending,
        "mae_model": mae_model,
        "mae_gmp": mae_gmp,
        "provisional": n_eval < 30
    }


def main():
    parser = argparse.ArgumentParser(description="Report forward prediction performance for OPI.")
    parser.add_argument("--log", type=str, default=LOG_PATH, help="Path to prediction log CSV")
    args = parser.parse_args()
    generate_forward_report(args.log)


if __name__ == "__main__":
    main()
