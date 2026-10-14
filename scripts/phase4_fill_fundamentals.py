#!/usr/bin/env python3
"""Phase 4 Task 3: Fundamentals Coverage Analysis & Spot-Check for 2021-2026 IPOs.

Objectives:
  1. Compute coverage percentages for fundamentals columns across 2021-2026 IPOs:
     - roe, roce, revenue_growth_pct, pat_margin_pct (100% null -> excluded from model)
     - pe_ratio, peer_median_pe, debt_equity (~61-62% filled -> kept in model with native NaN handling)
  2. Generate coverage report CSV at `phases/Phase 4/fundamentals_coverage.csv`.
  3. Spot-check 30 random 2021-2026 IPOs with filled pe_ratio (random_state=42) against plausible bounds:
     - pe_ratio: (0, 500)
     - peer_median_pe: (0, 500)
     - debt_equity: [0, 50)
  4. Log data corrections to `phases/Phase 4/data_corrections.csv`.
  5. Audit all 2021-2026 IPOs for out-of-range fundamentals and export `phases/Phase 4/all_outliers_audit.csv`.

Usage:
  python scripts/phase4_fill_fundamentals.py
  python scripts/phase4_fill_fundamentals.py --apply-corrections
"""

import argparse
import datetime
import os
import sys
import numpy as np
import pandas as pd

# Fundamentals columns defined in Phase 4 plan
FUNDAMENTAL_COLS = [
    "roe",
    "roce",
    "revenue_growth_pct",
    "pat_margin_pct",
    "pe_ratio",
    "peer_median_pe",
    "debt_equity"
]

# Plausible range thresholds
PLAUSIBLE_RANGES = {
    "pe_ratio": (0.0, 500.0, False),         # 0 < x < 500 (strictly positive, non-inclusive)
    "peer_median_pe": (0.0, 500.0, False),   # 0 < x < 500 (strictly positive, non-inclusive)
    "debt_equity": (0.0, 50.0, True),        # 0 <= x < 50 (non-negative, lower-inclusive)
}

COVERAGE_THRESHOLD = 70.0  # Phase 4 70% threshold target


def parse_args():
    parser = argparse.ArgumentParser(description="Phase 4 Fundamentals Coverage and Spot-Check")
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/ipo_master.csv",
        help="Path to master dataset (default: data/ipo_master.csv)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="phases/Phase 4",
        help="Directory to save Phase 4 reports (default: phases/Phase 4)"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=30,
        help="Number of IPOs for spot check (default: 30)"
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for spot-check sampling (default: 42)"
    )
    parser.add_argument(
        "--apply-corrections",
        action="store_true",
        help="Apply spot-check corrections (set outliers to NaN) to ipo_master.csv"
    )
    return parser.parse_args()


def check_bounds(val, col):
    """Check if value falls within plausible domain range. Returns (is_valid, reason)."""
    if pd.isna(val):
        return True, "Missing / NaN"
    low, high, low_inclusive = PLAUSIBLE_RANGES[col]
    if low_inclusive:
        if val < low:
            return False, f"{val} < lower bound {low}"
    else:
        if val <= low:
            return False, f"{val} <= lower bound {low}"
    if val >= high:
        return False, f"{val} >= upper bound {high}"
    return True, "Within range"


def run_fundamentals_analysis(data_path="data/ipo_master.csv", output_dir="phases/Phase 4", sample_size=30, random_state=42, apply_corrections=False):
    today_str = datetime.date.today().isoformat()
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 80)
    print("PHASE 4 TASK 3: FUNDAMENTALS COVERAGE & SPOT-CHECK ANALYSIS")
    print("=" * 80)
    print(f"Date:             {today_str}")
    print(f"Master Dataset:   {data_path}")
    print(f"Output Directory: {output_dir}")
    print(f"Spot Check Size:  {sample_size} IPOs (random_state={random_state})")
    print("-" * 80)

    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        sys.exit(1)

    df = pd.read_csv(data_path)
    print(f"Loaded master dataset: {len(df)} total IPO rows, {len(df.columns)} columns.")

    # 1. Filter 2021-2026 listings
    df["listing_date_dt"] = pd.to_datetime(df["listing_date"], errors="coerce")
    mask_21_26 = (df["listing_date_dt"].dt.year >= 2021) & (df["listing_date_dt"].dt.year <= 2026)
    df_21_26 = df[mask_21_26].copy()
    total_21_26 = len(df_21_26)

    print(f"2021-2026 Listings count: {total_21_26} IPOs (years 2021 through 2026).")
    print("\nListing counts by year (2021-2026):")
    year_counts = df_21_26["listing_date_dt"].dt.year.value_counts().sort_index()
    for yr, cnt in year_counts.items():
        print(f"  Year {yr}: {cnt} IPOs")

    # 2. Compute Coverage for Fundamentals Columns
    print("\n" + "=" * 80)
    print("1. FUNDAMENTALS COVERAGE ANALYSIS (2021-2026 IPOs)")
    print("=" * 80)

    coverage_rows = []
    for col in FUNDAMENTAL_COLS:
        filled_count = int(df_21_26[col].notna().sum())
        pct_filled = round((filled_count / total_21_26) * 100, 2)
        meets_threshold = bool(pct_filled >= COVERAGE_THRESHOLD)

        if col in ["roe", "roce", "revenue_growth_pct", "pat_margin_pct"]:
            decision = "Exclude from model (<70% threshold; 0.0% coverage)"
        elif col in ["pe_ratio", "peer_median_pe", "debt_equity"]:
            decision = "Keep in model with native NaN handling (documented coverage gap)"
        else:
            decision = "Meets threshold; include" if meets_threshold else "Exclude from model"

        coverage_rows.append({
            "column_name": col,
            "total_2021_2026": total_21_26,
            "filled_2021_2026": filled_count,
            "pct_filled": pct_filled,
            "meets_70pct_threshold": meets_threshold,
            "decision": decision
        })

    coverage_df = pd.DataFrame(coverage_rows)
    coverage_csv_path = os.path.join(output_dir, "fundamentals_coverage.csv")
    coverage_df.to_csv(coverage_csv_path, index=False)

    print(f"{'Column Name':<22} | {'Filled':<8} | {'Total':<6} | {'Coverage %':<10} | {'>= 70%?':<8} | {'Decision'}")
    print("-" * 80)
    for _, r in coverage_df.iterrows():
        print(f"{r['column_name']:<22} | {r['filled_2021_2026']:<8} | {r['total_2021_2026']:<6} | {r['pct_filled']:>8.2f}% | {str(r['meets_70pct_threshold']):<8} | {r['decision']}")
    print(f"\nSaved coverage report to: {coverage_csv_path}")

    # 3. Spot-Check of 30 Random 2021-2026 IPOs with pe_ratio filled
    print("\n" + "=" * 80)
    print(f"2. SPOT-CHECK VERIFICATION ({sample_size} Random 2021-2026 IPOs with filled pe_ratio)")
    print("=" * 80)

    df_pe_filled = df_21_26[df_21_26["pe_ratio"].notna()].copy()
    print(f"Total 2021-2026 IPOs with pe_ratio populated: {len(df_pe_filled)} rows.")

    sample_df = df_pe_filled.sample(n=sample_size, random_state=random_state).copy()

    spot_results = []
    corrections_to_log = []

    pass_count = 0
    fail_count = 0

    print(f"\n{'#':<3} | {'Company':<32} | {'Listing Date':<12} | {'P/E':<8} | {'Peer P/E':<8} | {'D/E':<6} | {'Status':<6} | {'Notes / Flags'}")
    print("-" * 105)

    for idx, (orig_idx, row) in enumerate(sample_df.iterrows(), 1):
        company = row["company"]
        list_dt = row["listing_date"]
        pe = row["pe_ratio"]
        peer_pe = row["peer_median_pe"]
        de = row["debt_equity"]

        pe_ok, pe_reason = check_bounds(pe, "pe_ratio")
        peer_ok, peer_reason = check_bounds(peer_pe, "peer_median_pe")
        de_ok, de_reason = check_bounds(de, "debt_equity")

        violations = []
        if not pe_ok:
            violations.append(f"pe_ratio={pe} ({pe_reason})")
            corrections_to_log.append({
                "date": today_str,
                "company": company,
                "column": "pe_ratio",
                "old_value": pe,
                "new_value": np.nan,
                "reason": f"Spot-check failure: pe_ratio {pe} exceeds plausible range (0, 500)"
            })
        if not peer_ok:
            violations.append(f"peer_median_pe={peer_pe} ({peer_reason})")
            corrections_to_log.append({
                "date": today_str,
                "company": company,
                "column": "peer_median_pe",
                "old_value": peer_pe,
                "new_value": np.nan,
                "reason": f"Spot-check failure: peer_median_pe {peer_pe} exceeds plausible range (0, 500)"
            })
        if not de_ok:
            violations.append(f"debt_equity={de} ({de_reason})")
            corrections_to_log.append({
                "date": today_str,
                "company": company,
                "column": "debt_equity",
                "old_value": de,
                "new_value": np.nan,
                "reason": f"Spot-check failure: debt_equity {de} exceeds plausible range [0, 50)"
            })

        is_pass = (len(violations) == 0)
        if is_pass:
            pass_count += 1
            status = "PASS"
            note = "Valid"
        else:
            fail_count += 1
            status = "FAIL"
            note = "; ".join(violations)

        spot_results.append({
            "company": company,
            "listing_date": list_dt,
            "pe_ratio": pe,
            "peer_median_pe": peer_pe,
            "debt_equity": de,
            "status": status,
            "violations": note
        })

        pe_str = f"{pe:.2f}" if pd.notna(pe) else "NaN"
        peer_str = f"{peer_pe:.2f}" if pd.notna(peer_pe) else "NaN"
        de_str = f"{de:.2f}" if pd.notna(de) else "NaN"

        print(f"{idx:<3} | {company[:32]:<32} | {str(list_dt):<12} | {pe_str:<8} | {peer_str:<8} | {de_str:<6} | {status:<6} | {note}")

    pass_pct = round((pass_count / sample_size) * 100, 2)
    fail_pct = round((fail_count / sample_size) * 100, 2)

    print("-" * 105)
    print(f"Spot-Check Summary: {pass_count}/{sample_size} PASSED ({pass_pct}%), {fail_count}/{sample_size} FAILED ({fail_pct}%)")
    print(f"Data Accuracy Target (>= 95%): {'MET' if pass_pct >= 95.0 else 'NOT MET'} ({pass_pct}%)")

    # 4. Log Data Corrections
    print("\n" + "=" * 80)
    print("3. DATA CORRECTIONS LOGGING")
    print("=" * 80)

    corrections_df = pd.DataFrame(corrections_to_log, columns=["date", "company", "column", "old_value", "new_value", "reason"])
    corrections_csv_path = os.path.join(output_dir, "data_corrections.csv")
    corrections_df.to_csv(corrections_csv_path, index=False, na_rep="NaN")

    print(f"Logged {len(corrections_df)} corrections to: {corrections_csv_path}")
    if len(corrections_df) > 0:
        for _, r in corrections_df.iterrows():
            print(f"  - [{r['date']}] {r['company']} | {r['column']}: {r['old_value']} -> {r['new_value']} ({r['reason']})")
    else:
        print("  No corrections needed. All sampled rows passed plausible bounds.")

    # 5. Full 2021-2026 Outlier Audit
    print("\n" + "=" * 80)
    print("4. FULL 2021-2026 DATASET OUTLIER AUDIT (479 IPOs)")
    print("=" * 80)

    all_outliers = []
    for _, row in df_21_26.iterrows():
        comp = row["company"]
        ldate = row["listing_date"]
        for col in ["pe_ratio", "peer_median_pe", "debt_equity"]:
            val = row[col]
            if pd.notna(val):
                ok, reason = check_bounds(val, col)
                if not ok:
                    all_outliers.append({
                        "date": today_str,
                        "company": comp,
                        "listing_date": ldate,
                        "column": col,
                        "value": val,
                        "reason": reason
                    })

    all_outliers_df = pd.DataFrame(all_outliers)
    audit_csv_path = os.path.join(output_dir, "all_outliers_audit.csv")
    all_outliers_df.to_csv(audit_csv_path, index=False)

    print(f"Identified {len(all_outliers_df)} out-of-range values across all {total_21_26} IPOs (2021-2026).")
    print(f"Saved complete audit to: {audit_csv_path}")
    for _, r in all_outliers_df.iterrows():
        print(f"  - {r['company']} ({r['listing_date']}) | {r['column']} = {r['value']} ({r['reason']})")

    # 6. Optional: Apply Corrections to ipo_master.csv
    if apply_corrections and len(corrections_df) > 0:
        print("\n" + "=" * 80)
        print("5. APPLYING CORRECTIONS TO MASTER DATASET")
        print("=" * 80)
        for _, r in corrections_df.iterrows():
            mask = (df["company"] == r["company"])
            df.loc[mask, r["column"]] = np.nan
            print(f"Updated {r['company']} [{r['column']}] -> NaN in {data_path}")
        df = df.drop(columns=["listing_date_dt"], errors="ignore")
        df.to_csv(data_path, index=False)
        print(f"Saved updated master dataset to {data_path}.")
    else:
        print("\nNote: Master dataset left unchanged (corrections logged to CSV). To apply, pass --apply-corrections.")

    print("\n" + "=" * 80)
    print("TASK 3 EXECUTION COMPLETE")
    print("=" * 80)

    return {
        "coverage_df": coverage_df,
        "spot_results": spot_results,
        "corrections_df": corrections_df,
        "all_outliers_df": all_outliers_df,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_pct": pass_pct,
        "fail_pct": fail_pct,
    }


if __name__ == "__main__":
    args = parse_args()
    run_fundamentals_analysis(
        data_path=args.data_path,
        output_dir=args.output_dir,
        sample_size=args.sample_size,
        random_state=args.random_state,
        apply_corrections=args.apply_corrections
    )
