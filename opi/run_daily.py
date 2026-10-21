"""Daily automated forward test runner for OPI.

Usage:
    python -m opi.run_daily [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, date
from pathlib import Path
import pandas as pd

from opi.discover import discover_ipos
from opi.ingest import ingest_ipo_data, IngestionError
from opi.validate import validate_timing_and_leakage, validate_ipo_features
from opi.score import score_ipo
from opi.log import append_prediction_log, append_run_log, get_write_timestamp
from opi.report import render_dashboard_html

ROOT_DIR = Path(__file__).resolve().parents[1]


def run_daily_forward_test(dry_run: bool = False):
    """Execute the daily forward test pipeline with automated Mainboard discovery."""
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\n{'='*78}")
    print(f"  OPI DAILY AUTOMATED FORWARD TEST [{run_id}] {'(DRY RUN)' if dry_run else ''}")
    print(f"{'='*78}")

    if not dry_run:
        append_run_log(run_id, "START", "ALL", "STARTED", f"dry_run={dry_run}")
    else:
        print(f"[DRY RUN] Operation started with run_id={run_id}")

    # 1. Automated Candidate Discovery (Mainboard only)
    print("\n[Step 1] Running Mainboard IPO discovery...")
    discovered = []
    try:
        discovered = discover_ipos()
        print(f"Discovered {len(discovered)} Mainboard candidate(s).")
    except Exception as e:
        print(f"Discovery warning (fetch blocked or network issue): {e}")
        if not dry_run:
            append_run_log(run_id, "DISCOVERY", "ALL", "SKIPPED_FETCH_BLOCKED", str(e))

    # Also check if manual new_ipo.csv has any rows
    candidate_path = ROOT_DIR / "new_ipo.csv"
    if candidate_path.exists():
        try:
            cand_df = pd.read_csv(candidate_path)
            for _, r in cand_df.iterrows():
                row_dict = r.to_dict()
                if row_dict.get("company") and not any(d["company"] == row_dict["company"] for d in discovered):
                    row_dict["status"] = "MANUAL_INPUT"
                    discovered.append(row_dict)
        except Exception as e:
            print(f"Error reading new_ipo.csv: {e}")

    log_path = ROOT_DIR / "predictions" / "prediction_log.csv"
    logged_companies = set()
    if log_path.exists():
        try:
            log_df = pd.read_csv(log_path)
            logged_companies = set(log_df["company"].dropna().tolist())
        except Exception:
            pass

    for cand in discovered:
        company = str(cand.get("company", "UNKNOWN"))
        cand_status = cand.get("status", "UNKNOWN")
        close_date = str(cand.get("close_date", ""))
        listing_date = str(cand.get("listing_date", ""))

        if cand_status == "BIDDING_OPEN":
            print(f"\nCandidate: {company} | Status: BIDDING_OPEN")
            print(f"  Bidding closes on {close_date}. Forward prediction deferred until bidding concludes.")
            if not dry_run:
                append_run_log(
                    run_id, "DISCOVERY", company, "SKIPPED_BIDDING_OPEN",
                    f"Bidding window open until {close_date}; score only post-close"
                )
            continue

        if company in logged_companies:
            print(f"\nCandidate: {company} | Status: ALREADY_LOGGED in prediction_log.csv.")
            continue

        if cand_status == "CLOSED_UNLISTED":
            print(f"\nCandidate: {company} | Status: CLOSED_UNLISTED (Close: {close_date}, Listing: {listing_date})")
            # Ready for forward scoring if detailed URLs are available
            overview_url = cand.get("overview_url")
            sub_url = cand.get("sub_url")
            gmp_url = cand.get("gmp_url")

            if not overview_url or not sub_url:
                print(f"  Insufficient evidence URLs for automated scoring of {company}. Marking SKIPPED_INSUFFICIENT_SOURCES.")
                if not dry_run:
                    append_run_log(run_id, "INGEST", company, "SKIPPED_INSUFFICIENT_SOURCES", "Overview or subscription URL missing")
                continue

            try:
                # Score candidate
                from scripts.score_ipo import score_and_log_ipo
                score_and_log_ipo(
                    company=company,
                    listing_date=listing_date,
                    close_date=close_date,
                    overview_url=overview_url,
                    sub_url=sub_url,
                    gmp_url=gmp_url,
                    dry_run=dry_run,
                )
            except Exception as score_err:
                print(f"  Scoring failed for {company}: {score_err}")
                if not dry_run:
                    append_run_log(run_id, "SCORE", company, "SKIPPED_SCORING_ERROR", str(score_err))

    # 2. Check for pending forward IPOs needing actuals
    print("\n[Step 2] Checking pending forward listings for outcome updates...")
    if log_path.exists():
        log_df = pd.read_csv(log_path)
        pending = log_df[(log_df["status"] == "FORWARD") & (log_df["actual_gain_pct"].isna())]
        today_date = date.today()
        for _, r in pending.iterrows():
            comp_name = r["company"]
            try:
                l_date = pd.to_datetime(r["listing_date"]).date()
            except Exception:
                continue

            if l_date <= today_date:
                print(f"  - {comp_name} listed on {l_date} <= today ({today_date}): outcome update pending.")
                print(
                    "    Use scripts/update_actuals.py with official NSE/BSE URL or browser snapshot."
                )
            else:
                print(f"  - {comp_name} scheduled to list on {l_date} > today ({today_date}): unlisted, carried over.")

    # 3. Regenerate dashboard
    if not dry_run:
        dashboard_path = render_dashboard_html()
        print(f"\n[Step 3] Dashboard updated at: {dashboard_path}")
        append_run_log(run_id, "FINISH", "ALL", "SUCCESS")
    else:
        print("\n[Step 3] [DRY RUN] Dashboard update skipped in dry-run mode.")
    print(f"\n{'='*78}\n")


def main():
    parser = argparse.ArgumentParser(description="OPI Automated Daily Forward Test Runner")
    parser.add_argument("--dry-run", action="store_true", help="Run discovery and scoring without writing to log")
    args = parser.parse_args()
    run_daily_forward_test(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
