#!/usr/bin/env python3
"""Governed promotion of listed FORWARD prediction rows into training data.

Usage:
    python scripts/promote_forward_rows.py [--apply]

Description:
    Inspects predictions/prediction_log.csv for completed FORWARD rows with
    verified actual listing outcomes. Validates eligibility (mainboard,
    no duplicates, snapshot evidence present). By default, runs in dry-run mode
    reporting candidate rows. Appends to data/ipo_master.csv and logs to
    data/promotions.csv only when --apply is explicitly specified.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
MASTER_PATH = ROOT_DIR / "data" / "ipo_master.csv"
PROMOTIONS_PATH = ROOT_DIR / "data" / "promotions.csv"


def check_forward_row_eligibility(
    row: pd.Series,
    master_df: pd.DataFrame
) -> Tuple[bool, str, Dict[str, Any]]:
    """Verify whether a listed forward row qualifies for promotion to training data."""
    company = str(row["company"])
    listing_date = str(row["listing_date"])
    
    # 1. Status must be FORWARD
    if str(row["status"]).strip() != "FORWARD":
        return False, f"Status is '{row['status']}', not 'FORWARD'", {}

    # 2. Actual outcome must be recorded and non-null
    act = row.get("actual_gain_pct")
    if pd.isna(act) or str(act).strip() == "":
        return False, "Actual listing gain is not yet recorded (pending listing)", {}

    # 3. Not already in master dataset
    if not master_df.empty:
        existing = master_df[
            (master_df["company"].astype(str).str.lower() == company.lower()) &
            (master_df["listing_date"].astype(str) == listing_date)
        ]
        if len(existing) > 0:
            return False, f"Already present in data/ipo_master.csv (index {existing.index[0]})", {}

    # 4. Feature snapshot parseable
    snap_str = row.get("features_snapshot_json")
    if pd.isna(snap_str) or not str(snap_str).strip():
        return False, "Missing features_snapshot_json", {}

    try:
        features = json.loads(str(snap_str))
    except Exception as e:
        return False, f"Failed to parse features_snapshot_json: {e}", {}

    # 5. Mainboard verification
    issue_size = features.get("issue_size_cr")
    if issue_size is not None:
        try:
            if float(issue_size) < 25.0:
                return False, f"Issue size ({issue_size} Cr) below Mainboard threshold", features
        except ValueError:
            pass

    return True, "Eligible for promotion", features


def promote_forward_rows(apply: bool = False) -> List[Dict[str, Any]]:
    """Scan prediction log and evaluate/promote eligible completed forward rows."""
    if not LOG_PATH.exists():
        print(f"Prediction log not found at {LOG_PATH}")
        return []

    log_df = pd.read_csv(LOG_PATH)
    master_df = pd.read_csv(MASTER_PATH) if MASTER_PATH.exists() else pd.DataFrame()

    forward_candidates = log_df[log_df["status"] == "FORWARD"].copy()
    print(f"\n=================================================================")
    print(f"  OPI GOVERNED ROW PROMOTION RUN [{'APPLY' if apply else 'DRY RUN'}]")
    print(f"=================================================================")
    print(f"Total FORWARD rows in log: {len(forward_candidates)}")

    eligible_rows = []
    for idx, row in forward_candidates.iterrows():
        is_eligible, reason, feats = check_forward_row_eligibility(row, master_df)
        company = row["company"]
        print(f"\nCandidate: {company} (Listing Date: {row['listing_date']})")
        print(f"  Status        : {row['status']}")
        print(f"  Actual Gain   : {row['actual_gain_pct'] or 'None'}")
        print(f"  Audit Verdict : {'ELIGIBLE' if is_eligible else 'INELIGIBLE'} ({reason})")

        if is_eligible:
            eligible_rows.append({
                "log_row": row,
                "features": feats
            })

    print(f"\nSummary: {len(eligible_rows)} eligible candidate(s) found.")

    if apply and eligible_rows:
        new_master_rows = []
        promotions = []
        now_iso = datetime.now().isoformat()

        for item in eligible_rows:
            r = item["log_row"]
            f = item["features"]
            
            # Construct master record matching schema
            master_rec = {
                "company": r["company"],
                "listing_date": r["listing_date"],
                "open_date": r.get("open_date"),
                "close_date": r.get("close_date"),
                "issue_price": f.get("issue_price"),
                "listing_price": None,
                "listing_gain_pct": float(r["actual_gain_pct"]),
                "issue_size_cr": f.get("issue_size_cr"),
                "fresh_issue_pct": f.get("fresh_issue_pct"),
                "ofs_pct": f.get("ofs_pct"),
                "lot_size": f.get("lot_size"),
                "sub_qib": f.get("sub_qib"),
                "sub_nii": f.get("sub_nii"),
                "sub_retail": f.get("sub_retail"),
                "sub_total": f.get("sub_total"),
                "pe_ratio": f.get("pe_ratio"),
                "peer_median_pe": f.get("peer_median_pe"),
                "debt_equity": f.get("debt_equity"),
                "sector": f.get("sector"),
                "exchange": f.get("exchange"),
                "gmp_pct": f.get("gmp_pct"),
                "gmp_status": "OBSERVED" if f.get("gmp_pct") is not None else "NOT_RECORDED",
                "label_good": 1 if float(r["actual_gain_pct"]) > 10.0 else 0,
                "updated_at": now_iso
            }
            new_master_rows.append(master_rec)

            promotions.append({
                "promoted_at": now_iso,
                "company": r["company"],
                "listing_date": r["listing_date"],
                "actual_gain_pct": r["actual_gain_pct"],
                "model_version": f.get("_model_version", "v4.0.0-champion"),
                "evidence_paths": f.get("source_urls", "N/A"),
                "promoted_by": "scripts/promote_forward_rows.py"
            })

        # Append to master dataset
        new_df = pd.DataFrame(new_master_rows)
        updated_master = pd.concat([master_df, new_df], ignore_index=True)
        updated_master.to_csv(MASTER_PATH, index=False)
        print(f"Appended {len(new_master_rows)} row(s) to {MASTER_PATH}")

        # Append to promotions ledger
        prom_df = pd.DataFrame(promotions)
        prom_exists = PROMOTIONS_PATH.exists() and os.path.getsize(PROMOTIONS_PATH) > 0
        prom_df.to_csv(PROMOTIONS_PATH, mode="a", header=not prom_exists, index=False)
        print(f"Logged {len(promotions)} promotion event(s) to {PROMOTIONS_PATH}")

    elif not apply and eligible_rows:
        print("Dry run completed. Run with --apply to execute row promotion.")

    return eligible_rows


def main():
    parser = argparse.ArgumentParser(description="Audit and promote eligible forward prediction rows to master data.")
    parser.add_argument("--apply", action="store_true", help="Execute row promotion (modifies ipo_master.csv and promotions.csv)")
    args = parser.parse_args()

    promote_forward_rows(apply=args.apply)


if __name__ == "__main__":
    main()
