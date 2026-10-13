#!/usr/bin/env python3
"""Validate the IPO master CSV. Usage: python validate_dataset.py data/ipo_master.csv"""
import sys
import pandas as pd

EXPECTED = ["company","sector","exchange","open_date","close_date","listing_date","issue_price",
 "issue_size_cr","fresh_issue_pct","ofs_pct","lot_size","sub_qib","sub_nii","sub_retail","sub_total",
 "pe_ratio","peer_median_pe","roe","roce","debt_equity","revenue_growth_pct","pat_margin_pct",
 "gmp_pct","nifty_30d_return","india_vix","recent_ipo_avg_gain","listing_price","listing_gain_pct",
 "label_good","source_urls","notes"]

def main(path):
    df = pd.read_csv(path)
    errors, warns = [], []
    if list(df.columns) != EXPECTED:
        print("Columns do not match schema.")
        print("Missing:", set(EXPECTED) - set(df.columns), "Extra:", set(df.columns) - set(EXPECTED))
        sys.exit(1)
    for c in ["open_date", "close_date", "listing_date"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
        if df[c].isna().any():
            errors.append(f"{c}: {int(df[c].isna().sum())} unparseable/missing dates")
    if (df.open_date > df.close_date).any(): errors.append("open_date after close_date in some rows")
    if (df.close_date > df.listing_date).any(): errors.append("close_date after listing_date in some rows")
    if df.duplicated(["company", "listing_date"]).any(): errors.append("duplicate (company, listing_date) rows")
    calc = (df.listing_price - df.issue_price) / df.issue_price * 100
    bad = ((calc - df.listing_gain_pct).abs() > 0.5) & calc.notna()
    if bad.any(): errors.append(f"listing_gain_pct mismatch with prices in {int(bad.sum())} rows")
    lab = (df.listing_gain_pct > 10).astype(int)
    if ((lab != df.label_good) & df.listing_gain_pct.notna()).any(): errors.append("label_good inconsistent with listing_gain_pct")
    for c in ["fresh_issue_pct", "ofs_pct"]:
        if ((df[c] < 0) | (df[c] > 100)).any(): errors.append(f"{c} outside 0-100")
    for c in ["sub_qib", "sub_nii", "sub_retail", "sub_total", "issue_price", "issue_size_cr"]:
        if (df[c] < 0).any(): errors.append(f"{c} has negative values")
    if (df.listing_gain_pct.abs() > 300).any(): warns.append("listing_gain_pct beyond +/-300% in some rows: verify")
    miss = (df.isna().mean() * 100).round(1)
    print(f"Rows: {len(df)}")
    print("Rows per year:\n" + df.listing_date.dt.year.value_counts().sort_index().to_string())
    print("Columns >40% missing:", miss[miss > 40].to_dict() or "none")
    for w in warns: print("WARN:", w)
    if errors:
        print("ERRORS:")
        for e in errors: print(" -", e)
        sys.exit(1)
    print("OK: dataset passes validation")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/ipo_master.csv")
