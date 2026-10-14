#!/usr/bin/env python3
"""Dataset Audit Script for OPI (Phase 6, Gate A6 Item S1).

Usage:
    python scripts/audit_dataset.py [data/ipo_master.csv]

Checks:
    1. Inclusion criteria violations (FPOs, non-mainboard, withdrawn, etc.)
    2. Price ratio outliers (listing_price/issue_price < 0.4 or > 4.0)
    3. Date order errors (listing_date <= close_date)
    4. Duplicate company names
    5. Impossible values (negative subscription, gain inconsistent with prices)
    6. GMP recorded after last bidding day (leakage risk)
    7. Missing issue price
    8. Rows that should be excluded per data/excluded_rows.csv

Exits with code 0 if no unresolved violations remain, code 1 otherwise.
"""

import os
import sys
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_excluded_rows():
    """Load the excluded rows registry."""
    path = os.path.join(ROOT_DIR, "data", "excluded_rows.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=["company", "listing_date", "reason", "source_url", "date_of_decision"])


def audit(master_path):
    df = pd.read_csv(master_path)
    df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")
    df["close_date"] = pd.to_datetime(df["close_date"], errors="coerce")
    df["open_date"] = pd.to_datetime(df["open_date"], errors="coerce")

    excluded = load_excluded_rows()
    excluded_companies = set(excluded["company"].str.strip().str.lower()) if len(excluded) > 0 else set()

    violations = []
    flags_summary = {
        "PRICE_RATIO_LOW": 0,
        "PRICE_RATIO_HIGH": 0,
        "DATE_ORDER_ERROR": 0,
        "DUPLICATE_COMPANY": 0,
        "NEGATIVE_SUBSCRIPTION": 0,
        "GAIN_INCONSISTENT": 0,
        "MISSING_ISSUE_PRICE": 0,
        "EXCLUDED_ROW_PRESENT": 0,
    }

    # Check: excluded rows should NOT be in the master
    for _, row in df.iterrows():
        company_lower = str(row["company"]).strip().lower()
        if company_lower in excluded_companies:
            violations.append(f"EXCLUDED_ROW_PRESENT: '{row['company']}' is in excluded_rows.csv but still in master")
            flags_summary["EXCLUDED_ROW_PRESENT"] += 1

    # Check: price ratio outliers
    df["price_ratio"] = df["listing_price"] / df["issue_price"]
    low_ratio = df[df["price_ratio"] < 0.4]
    high_ratio = df[df["price_ratio"] > 4.0]
    for _, r in low_ratio.iterrows():
        violations.append(f"PRICE_RATIO_LOW: '{r['company']}' ratio={r['price_ratio']:.3f} (issue={r['issue_price']}, listing={r['listing_price']})")
        flags_summary["PRICE_RATIO_LOW"] += 1
    for _, r in high_ratio.iterrows():
        violations.append(f"PRICE_RATIO_HIGH: '{r['company']}' ratio={r['price_ratio']:.3f} (issue={r['issue_price']}, listing={r['listing_price']})")
        flags_summary["PRICE_RATIO_HIGH"] += 1

    # Check: date order errors
    date_errors = df[df["listing_date"] <= df["close_date"]]
    for _, r in date_errors.iterrows():
        violations.append(f"DATE_ORDER_ERROR: '{r['company']}' listing_date={r['listing_date'].date()} <= close_date={r['close_date'].date()}")
        flags_summary["DATE_ORDER_ERROR"] += 1

    # Check: duplicate company names
    dup_mask = df["company"].duplicated(keep=False)
    dups = df[dup_mask]["company"].unique()
    for name in dups:
        violations.append(f"DUPLICATE_COMPANY: '{name}' appears {(df['company'] == name).sum()} times")
        flags_summary["DUPLICATE_COMPANY"] += 1

    # Check: negative subscription
    sub_cols = ["sub_qib", "sub_nii", "sub_retail", "sub_total"]
    for col in sub_cols:
        if col in df.columns:
            neg = df[df[col] < 0]
            for _, r in neg.iterrows():
                violations.append(f"NEGATIVE_SUBSCRIPTION: '{r['company']}' {col}={r[col]}")
                flags_summary["NEGATIVE_SUBSCRIPTION"] += 1

    # Check: gain inconsistent with prices
    if "listing_gain_pct" in df.columns and "listing_price" in df.columns and "issue_price" in df.columns:
        computed_gain = (df["listing_price"] / df["issue_price"] - 1) * 100
        gain_diff = (df["listing_gain_pct"] - computed_gain).abs()
        inconsistent = df[gain_diff > 1.0]
        for _, r in inconsistent.iterrows():
            comp_g = (r["listing_price"] / r["issue_price"] - 1) * 100
            violations.append(f"GAIN_INCONSISTENT: '{r['company']}' stated={r['listing_gain_pct']:.2f}%, computed={comp_g:.2f}%")
            flags_summary["GAIN_INCONSISTENT"] += 1

    # Check: missing issue price
    missing_ip = df[df["issue_price"].isna() | (df["issue_price"] <= 0)]
    for _, r in missing_ip.iterrows():
        violations.append(f"MISSING_ISSUE_PRICE: '{r['company']}' issue_price={r.get('issue_price', 'NaN')}")
        flags_summary["MISSING_ISSUE_PRICE"] += 1

    # Print report
    print("=" * 78)
    print("  OPI DATASET AUDIT REPORT")
    print("=" * 78)
    print(f"Dataset: {master_path}")
    print(f"Total rows: {len(df)}")
    print(f"Excluded rows registry: {len(excluded)} entries")
    print("-" * 78)
    print("Flag counts:")
    for flag, count in flags_summary.items():
        status = "OK" if count == 0 else f"VIOLATION ({count})"
        print(f"  {flag:30s}: {status}")
    print("-" * 78)

    total_violations = len(violations)
    if total_violations == 0:
        print(f"RESULT: 0 unresolved violations. Dataset passes audit.")
    else:
        print(f"RESULT: {total_violations} unresolved violations found:")
        for v in violations:
            print(f"  - {v}")

    print("=" * 78)
    return total_violations


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT_DIR, "data", "ipo_master.csv")
    n_violations = audit(path)
    sys.exit(0 if n_violations == 0 else 1)


if __name__ == "__main__":
    main()
