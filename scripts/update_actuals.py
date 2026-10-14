#!/usr/bin/env python3
"""Update Actuals Script for OPI Prediction Log.

Usage:
    python scripts/update_actuals.py [--log predictions/prediction_log.csv] [--master data/ipo_master.csv]

Description:
    1. Reads predictions/prediction_log.csv.
    2. Identifies rows where actual_gain_pct is empty and listing_date has passed.
    3. Looks up the company in data/ipo_master.csv to find actual listing_gain_pct.
    4. Fills in actual_gain_pct and saves the updated log.
    5. Prints a detailed summary of updated records and remaining pending IPOs.
"""

import os
import sys
import re
import argparse
from datetime import datetime, date
import pandas as pd
import numpy as np

# Ensure repository root is on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

DEFAULT_LOG = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")
DEFAULT_MASTER = os.path.join(ROOT_DIR, "data", "ipo_master.csv")


def clean_name(s):
    """Normalize company name by removing noise words and non-alphanumeric chars."""
    if not isinstance(s, str):
        return ""
    # Strip common company suffixes and noise tokens
    s_clean = re.sub(r"\b(ipo|ltd|limited|pvt|private|india|technologies|services|corp|corporation)\b", "", s, flags=re.I)
    return re.sub(r"[^a-z0-9]", "", s_clean.lower())


def find_in_master(company_name, listing_date_str, df_master):
    """Lookup company in master dataframe using robust multi-stage matching."""
    if not company_name or df_master.empty:
        return None

    c_raw = str(company_name).strip().lower()

    # 1. Exact case-insensitive match
    exact = df_master[df_master["company"].astype(str).str.strip().str.lower() == c_raw]
    if not exact.empty:
        return exact.iloc[0]

    # 2. Normalized token matching
    c_norm = clean_name(company_name)
    if c_norm and len(c_norm) >= 3:
        # Match normalized names
        master_norms = df_master["company"].apply(clean_name)
        matched_idx = master_norms[master_norms == c_norm].index
        if len(matched_idx) > 0:
            return df_master.loc[matched_idx[0]]

        # Substring / containment matching
        candidates = []
        for idx, m_norm in master_norms.items():
            if m_norm and (c_norm in m_norm or m_norm in c_norm):
                candidates.append(idx)
        
        if len(candidates) == 1:
            return df_master.loc[candidates[0]]
        elif len(candidates) > 1:
            # If multiple matches, tie-break by listing date if available
            if listing_date_str:
                for c_idx in candidates:
                    m_date = str(df_master.loc[c_idx, "listing_date"]).strip()
                    if m_date == str(listing_date_str).strip():
                        return df_master.loc[c_idx]
            return df_master.loc[candidates[0]]

    return None


def parse_date(date_str):
    """Safely parse a date string into a date object."""
    if not date_str or pd.isna(date_str):
        return None
    date_str = str(date_str).strip()
    if not date_str:
        return None
    try:
        # Expect YYYY-MM-DD or standard ISO
        return datetime.fromisoformat(date_str[:10]).date()
    except (ValueError, TypeError):
        try:
            return pd.to_datetime(date_str).date()
        except Exception:
            return None


def update_actuals(log_path=DEFAULT_LOG, master_path=DEFAULT_MASTER, as_of=None):
    """Read prediction log, lookup actuals for listed IPOs, and update."""
    if not os.path.exists(log_path):
        print(f"Error: Prediction log '{log_path}' does not exist.")
        return 0

    if not os.path.exists(master_path):
        print(f"Error: Master data file '{master_path}' does not exist.")
        return 0

    # Read log keeping raw string representations
    log_df = pd.read_csv(log_path, dtype=str, keep_default_na=False)
    if log_df.empty:
        print("Prediction log is empty. No rows to update.")
        return 0

    # Read master dataset
    master_df = pd.read_csv(master_path)

    as_of_date = parse_date(as_of) if as_of else datetime.now().date()
    print(f"Evaluating listing dates as of: {as_of_date}")
    print(f"Total records in prediction log: {len(log_df)}")

    updated_count = 0
    already_filled = 0
    pending_future = 0
    not_found = 0
    updated_records = []

    for idx, row in log_df.iterrows():
        company = row["company"]
        status_val = str(row.get("status", "")).strip().upper()
        if status_val.startswith("TEST") or status_val.startswith("INVALID"):
            continue

        actual_val = row["actual_gain_pct"].strip()

        # Check if actual is already populated
        if actual_val != "" and actual_val.lower() not in ["nan", "none", "null"]:
            already_filled += 1
            continue

        # Check listing date
        list_date_str = row["listing_date"].strip()
        list_date = parse_date(list_date_str)

        if list_date is not None and list_date > as_of_date:
            # Listing date has not passed yet
            pending_future += 1
            continue

        # Listing date has passed (or is unlisted date, check master)
        matched_row = find_in_master(company, list_date_str, master_df)
        if matched_row is None:
            not_found += 1
            print(f"  [Pending/Not Found] '{company}' (Listing date: {list_date_str}) not matched in master dataset.")
            continue

        # Verify listing gain in master
        master_gain = matched_row.get("listing_gain_pct")
        if pd.isna(master_gain) or str(master_gain).strip() == "":
            print(f"  [Pending] Matched '{company}' -> '{matched_row['company']}', but master has no listing_gain_pct yet.")
            continue

        # Format and update actual listing gain
        gain_float = float(master_gain)
        actual_str = f"{gain_float:.2f}"
        log_df.at[idx, "actual_gain_pct"] = actual_str

        # If listing_date in log was missing, populate from master
        if not list_date_str and pd.notna(matched_row.get("listing_date")):
            log_df.at[idx, "listing_date"] = str(matched_row["listing_date"])[:10]

        pred_gain_val = float(row["pred_gain_pct"]) if row["pred_gain_pct"] else np.nan
        pred_prob_val = float(row["pred_prob_gt10"]) if row["pred_prob_gt10"] else np.nan
        abs_err = abs(gain_float - pred_gain_val) if not np.isnan(pred_gain_val) else np.nan

        updated_records.append({
            "company": company,
            "master_company": matched_row["company"],
            "listing_date": log_df.at[idx, "listing_date"],
            "pred_gain": pred_gain_val,
            "pred_prob": pred_prob_val,
            "actual_gain": gain_float,
            "abs_error": abs_err,
        })
        updated_count += 1

    # Save changes if any updates were made
    if updated_count > 0:
        log_df.to_csv(log_path, index=False)
        print(f"\nSuccessfully updated {updated_count} row(s) in '{log_path}'.")
    else:
        print("\nNo rows required updating.")

    # Print summary report
    print("\n" + "=" * 78)
    print("  ACTUAL LISTING GAINS UPDATE REPORT")
    print("=" * 78)
    print(f"Total Logged Predictions : {len(log_df)}")
    print(f"Already Completed Rows   : {already_filled}")
    print(f"Newly Updated Rows       : {updated_count}")
    print(f"Pending Future Listings  : {pending_future}")
    print(f"Passed but Unmatched     : {not_found}")
    print("-" * 78)

    if updated_records:
        print(f"{'Company':<25} {'Listing Date':<12} {'Pred %':<9} {'Actual %':<10} {'Error %':<9} {'Direction'}")
        print("-" * 78)
        for r in updated_records:
            pred_s = f"{r['pred_gain']:+.2f}%" if not np.isnan(r['pred_gain']) else "N/A"
            act_s = f"{r['actual_gain']:+.2f}%"
            err_s = f"{r['abs_error']:.2f}%" if not np.isnan(r['abs_error']) else "N/A"
            
            # Directional check (>10% gain threshold)
            pred_high = (r['pred_gain'] > 10.0) or (r['pred_prob'] >= 0.5)
            actual_high = r['actual_gain'] > 10.0
            direction = "CORRECT" if pred_high == actual_high else "MISS"
            
            print(f"{r['company']:<25} {r['listing_date']:<12} {pred_s:<9} {act_s:<10} {err_s:<9} {direction}")
        print("-" * 78)

    print("=" * 78)
    return updated_count


def main():
    parser = argparse.ArgumentParser(description="Update actual listing gains in prediction_log.csv from ipo_master.csv.")
    parser.add_argument("--log", type=str, default=DEFAULT_LOG, help="Path to predictions/prediction_log.csv")
    parser.add_argument("--master", type=str, default=DEFAULT_MASTER, help="Path to data/ipo_master.csv")
    parser.add_argument("--as-of", type=str, default=None, help="Evaluate as of date (YYYY-MM-DD)")

    args = parser.parse_args()
    update_actuals(log_path=args.log, master_path=args.master, as_of=args.as_of)


if __name__ == "__main__":
    main()
