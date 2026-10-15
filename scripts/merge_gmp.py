#!/usr/bin/env python3
"""Merge sourced GMP records from data/gmp_sourced.csv into data/ipo_master.csv.

Usage:
    python scripts/merge_gmp.py [--dry-run]

Matches rows by company name and listing date.
Updates `gmp_pct` with the sourced value (rounded to 2 decimal places).
Updates `gmp_status` to 'OBSERVED' for confidence in ['high', 'medium'].
Rows with confidence 'low' are excluded from updates.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MASTER_PATH = os.path.join(ROOT_DIR, "data", "ipo_master.csv")
SOURCED_PATH = os.path.join(ROOT_DIR, "data", "gmp_sourced.csv")


def main():
    parser = argparse.ArgumentParser(description="Merge sourced GMP into master dataset.")
    parser.add_argument("--dry-run", action="store_true", help="Print updates without modifying master.")
    args = parser.parse_args()

    if not os.path.exists(SOURCED_PATH):
        print(f"Error: {SOURCED_PATH} not found.")
        sys.exit(1)

    master_df = pd.read_csv(MASTER_PATH)
    sourced_df = pd.read_csv(SOURCED_PATH)

    print(f"Loaded master: {len(master_df)} rows")
    print(f"Loaded sourced: {len(sourced_df)} rows")

    updates_count = 0
    skipped_low_conf = 0
    not_found = []

    # Standardize string matching
    master_df["_match_key"] = master_df["company"].str.strip().str.lower() + "_" + master_df["listing_date"].astype(str)
    sourced_df["_match_key"] = sourced_df["company"].str.strip().str.lower() + "_" + sourced_df["listing_date"].astype(str)

    for idx, row in sourced_df.iterrows():
        key = row["_match_key"]
        conf = str(row.get("confidence", "high")).strip().lower()
        if conf == "low":
            skipped_low_conf += 1
            continue

        match_idx = master_df[master_df["_match_key"] == key].index
        if len(match_idx) == 0:
            # Try matching by company only if single match
            comp_matches = master_df[master_df["company"].str.strip().str.lower() == row["company"].str.strip().str.lower()].index
            if len(comp_matches) == 1:
                match_idx = comp_matches
            else:
                not_found.append((row["company"], row["listing_date"]))
                continue

        m_idx = match_idx[0]
        old_gmp = master_df.loc[m_idx, "gmp_pct"]
        new_gmp = round(float(row["gmp_pct"]), 2)
        old_status = master_df.loc[m_idx, "gmp_status"]
        new_status = "OBSERVED"

        if not args.dry_run:
            master_df.loc[m_idx, "gmp_pct"] = new_gmp
            master_df.loc[m_idx, "gmp_status"] = new_status

        updates_count += 1
        print(f"Updated {master_df.loc[m_idx, 'company']} ({master_df.loc[m_idx, 'listing_date']}): gmp_pct {old_gmp} -> {new_gmp}, status {old_status} -> {new_status}")

    # Drop temporary key
    master_df.drop(columns=["_match_key"], inplace=True)

    if not args.dry_run:
        master_df.to_csv(MASTER_PATH, index=False)
        print(f"Saved updated master to {MASTER_PATH}")

    print(f"\nSummary:")
    print(f"  Successfully merged: {updates_count}")
    print(f"  Skipped (low confidence): {skipped_low_conf}")
    print(f"  Not found in master: {len(not_found)}")
    if not_found:
        for nf in not_found:
            print(f"    - {nf[0]} ({nf[1]})")


if __name__ == "__main__":
    main()
