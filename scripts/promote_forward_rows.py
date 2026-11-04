#!/usr/bin/env python3
"""Governed promotion of listed FORWARD prediction rows into training data (D-083, D-092).

Usage:
    python scripts/promote_forward_rows.py [--apply]

Description:
    Inspects predictions/prediction_log.csv for completed FORWARD rows with
    verified actual listing outcomes. Validates eligibility (mainboard,
    no duplicates, snapshot evidence present). By default, runs in dry-run mode
    reporting candidate rows. Appends to data/ipo_master.csv and logs to
    data/promotions.csv only when --apply is explicitly specified.

    Strict Invariants (D-092):
    - Appends ONLY newly eligible rows; all existing rows in ipo_master.csv remain
      100% byte-identical (0 existing lines modified).
    - Preserves exact 33-column schema defined in ipo_master.csv.
    - Never adds unapproved columns (such as updated_at).
    - Writes integer year (e.g. '2026', not '2026.0').
"""

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from opi.outcomes import effective_outcome

LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
MASTER_PATH = ROOT_DIR / "data" / "ipo_master.csv"
PROMOTIONS_PATH = ROOT_DIR / "data" / "promotions.csv"

MASTER_COLUMNS = [
    "company", "sector", "exchange", "open_date", "close_date", "listing_date",
    "issue_price", "issue_size_cr", "fresh_issue_pct", "ofs_pct", "lot_size",
    "sub_qib", "sub_nii", "sub_retail", "sub_total", "pe_ratio", "peer_median_pe",
    "roe", "roce", "debt_equity", "revenue_growth_pct", "pat_margin_pct", "gmp_pct",
    "nifty_30d_return", "india_vix", "recent_ipo_avg_gain", "listing_price",
    "listing_gain_pct", "label_good", "source_urls", "notes", "year", "gmp_status"
]


def check_forward_row_eligibility(
    row: pd.Series,
    master_df: pd.DataFrame
) -> Tuple[bool, str, Dict[str, Any]]:
    """Verify whether a listed forward row qualifies for promotion to training data."""
    company = str(row["company"]).strip()
    listing_date = str(row["listing_date"]).strip()

    # 1. Status must be FORWARD
    if str(row["status"]).strip() != "FORWARD":
        return False, f"Status is '{row['status']}', not 'FORWARD'", {}

    # 2. Actual outcome must be recorded and non-null (accounting for corrections)
    eff_res = effective_outcome(row)
    eff_gain = eff_res["actual_gain_pct"]
    if eff_gain is None:
        return False, "Actual listing gain is not yet recorded (pending listing)", {}

    # 3. Not already in master dataset
    if not master_df.empty and "company" in master_df.columns and "listing_date" in master_df.columns:
        existing = master_df[
            (master_df["company"].astype(str).str.strip().str.lower() == company.lower()) &
            (master_df["listing_date"].astype(str).str.strip() == listing_date)
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


def promote_forward_rows(
    apply: bool = False,
    log_path: Optional[Path] = None,
    master_path: Optional[Path] = None,
    promotions_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Scan prediction log and evaluate/promote eligible completed forward rows.

    Guarantees that existing lines in master_path remain byte-identical (D-092).
    """
    target_log = log_path or LOG_PATH
    target_master = master_path or MASTER_PATH
    target_promotions = promotions_path or PROMOTIONS_PATH

    if not target_log.exists():
        print(f"Prediction log not found at {target_log}")
        return []

    # Read master with dtype=str to avoid any automatic numeric conversion
    master_df = pd.read_csv(target_master, dtype=str, keep_default_na=False) if target_master.exists() else pd.DataFrame()
    log_df = pd.read_csv(target_log, dtype=str, keep_default_na=False)

    forward_candidates = log_df[log_df["status"].str.strip().str.upper() == "FORWARD"].copy()
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
        now_iso = datetime.now(timezone.utc).isoformat()

        for item in eligible_rows:
            r = item["log_row"]
            f = item["features"]

            eff_res = effective_outcome(r)
            eff_gain = eff_res["actual_gain_pct"]

            # Compute or fetch listing_price
            lp_str = ""
            if f.get("listing_price") is not None:
                lp_str = str(f.get("listing_price"))
            elif f.get("issue_price") is not None and eff_gain is not None:
                try:
                    ip_val = float(f.get("issue_price"))
                    lp_val = round(ip_val * (1.0 + float(eff_gain) / 100.0), 2)
                    lp_str = str(lp_val)
                except Exception:
                    lp_str = ""

            # Check GMP status
            gmp_raw = f.get("gmp_pct")
            has_gmp = (gmp_raw is not None and str(gmp_raw).strip() not in ("", "nan", "None"))
            gmp_status = "OBSERVED" if has_gmp else "NOT_RECORDED"

            # Integer year as string
            l_date_str = str(r.get("listing_date", "")).strip()
            year_str = l_date_str[:4] if len(l_date_str) >= 4 else ""

            # Label good
            label_good = "1" if (eff_gain is not None and float(eff_gain) > 10.0) else "0"

            master_rec = {
                "company": str(r["company"]).strip(),
                "sector": str(f.get("sector") or "").strip(),
                "exchange": str(f.get("exchange") or "").strip(),
                "open_date": str(r.get("open_date") or "").strip(),
                "close_date": str(r.get("close_date") or "").strip(),
                "listing_date": l_date_str,
                "issue_price": str(f.get("issue_price") or "").strip(),
                "issue_size_cr": str(f.get("issue_size_cr") or "").strip(),
                "fresh_issue_pct": str(f.get("fresh_issue_pct") or "").strip(),
                "ofs_pct": str(f.get("ofs_pct") or "").strip(),
                "lot_size": str(f.get("lot_size") or "").strip(),
                "sub_qib": str(f.get("sub_qib") or "").strip(),
                "sub_nii": str(f.get("sub_nii") or "").strip(),
                "sub_retail": str(f.get("sub_retail") or "").strip(),
                "sub_total": str(f.get("sub_total") or "").strip(),
                "pe_ratio": str(f.get("pe_ratio") or "").strip(),
                "peer_median_pe": str(f.get("peer_median_pe") or "").strip(),
                "roe": str(f.get("roe") or "").strip(),
                "roce": str(f.get("roce") or "").strip(),
                "debt_equity": str(f.get("debt_equity") or "").strip(),
                "revenue_growth_pct": str(f.get("revenue_growth_pct") or "").strip(),
                "pat_margin_pct": str(f.get("pat_margin_pct") or "").strip(),
                "gmp_pct": str(f.get("gmp_pct") or "").strip(),
                "nifty_30d_return": str(f.get("nifty_30d_return") or "").strip(),
                "india_vix": str(f.get("india_vix") or "").strip(),
                "recent_ipo_avg_gain": str(f.get("recent_ipo_avg_gain") or "").strip(),
                "listing_price": lp_str,
                "listing_gain_pct": str(eff_gain),
                "label_good": label_good,
                "source_urls": str(f.get("source_urls") or "").strip(),
                "notes": str(f.get("notes") or f"Promoted from forward prediction log").strip(),
                "year": year_str,
                "gmp_status": gmp_status,
            }
            new_master_rows.append(master_rec)

            promotions.append({
                "promoted_at": now_iso,
                "company": str(r["company"]).strip(),
                "listing_date": l_date_str,
                "actual_gain_pct": str(eff_gain),
                "model_version": str(f.get("_model_version", "v4.0.0-champion")),
                "evidence_paths": str(f.get("source_urls", "N/A")),
                "promoted_by": "scripts/promote_forward_rows.py",
            })

        # Append strictly without modifying existing lines (D-092)
        if target_master.exists():
            existing_content = target_master.read_text(encoding="utf-8")
            if not existing_content.endswith("\n"):
                with open(target_master, "a", encoding="utf-8") as f_out:
                    f_out.write("\n")

        with open(target_master, "a", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=MASTER_COLUMNS, lineterminator="\n")
            if not target_master.exists() or os.path.getsize(target_master) == 0:
                writer.writeheader()
            for row_dict in new_master_rows:
                writer.writerow(row_dict)

        print(f"Appended {len(new_master_rows)} row(s) to {target_master}")

        # Append to promotions ledger
        prom_header = ["promoted_at", "company", "listing_date", "actual_gain_pct", "model_version", "evidence_paths", "promoted_by"]
        prom_exists = target_promotions.exists() and os.path.getsize(target_promotions) > 0
        with open(target_promotions, "a", newline="", encoding="utf-8") as pf:
            p_writer = csv.DictWriter(pf, fieldnames=prom_header, lineterminator="\n")
            if not prom_exists:
                p_writer.writeheader()
            for p_dict in promotions:
                p_writer.writerow(p_dict)

        print(f"Logged {len(promotions)} promotion event(s) to {target_promotions}")

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
