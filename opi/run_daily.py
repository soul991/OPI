"""Daily automated forward test runner for OPI.

Usage:
    python -m opi.run_daily [--dry-run]
"""

import argparse
import os
import sys
from datetime import datetime, date, time
from pathlib import Path
import pandas as pd

from opi.collect import collect_ipo_data
from opi.validate import validate_timing_and_leakage, validate_ipo_features
from opi.score import score_ipo
from opi.log import append_prediction_log, append_run_log, update_actual_outcome
from opi.report import render_dashboard_html

ROOT_DIR = Path(__file__).resolve().parents[1]


def run_daily_forward_test(dry_run: bool = False):
    """Execute the daily forward test pipeline."""
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\n{'='*78}")
    print(f"  OPI DAILY AUTOMATED FORWARD TEST [{run_id}] {'(DRY RUN)' if dry_run else ''}")
    print(f"{'='*78}")

    if not dry_run:
        append_run_log(run_id, "START", "ALL", "STARTED", f"dry_run={dry_run}")
    else:
        print(f"[DRY RUN] Operation started with run_id={run_id}")

    # 1. Candidate discovery
    # Check if new_ipo.csv exists and has a candidate
    candidate_path = ROOT_DIR / "new_ipo.csv"
    candidate = None
    if candidate_path.exists():
        try:
            cand_df = pd.read_csv(candidate_path)
            if len(cand_df) > 0:
                candidate = cand_df.iloc[0].to_dict()
        except Exception as e:
            print(f"Error reading new_ipo.csv: {e}")

    if not candidate:
        print("No new IPO candidates found in new_ipo.csv.")
        if not dry_run:
            append_run_log(run_id, "DISCOVERY", "NONE", "SKIPPED_NO_CANDIDATES", "No rows in new_ipo.csv")
    else:
        company = str(candidate.get("company", "UNKNOWN"))
        close_date = str(candidate.get("close_date", ""))
        listing_date = str(candidate.get("listing_date", ""))
        now_iso = datetime.now().isoformat()

        print(f"\nProcessing Candidate: {company}")
        print(f"Close Date: {close_date} | Listing Date: {listing_date}")

        # Timing and leakage validation
        timing_valid, timing_issues = validate_timing_and_leakage(
            close_date_str=close_date,
            listing_date_str=listing_date,
            scored_at_str=now_iso,
            notes=str(candidate.get("notes", ""))
        )

        if not timing_valid:
            print(f"Validation FAILED for {company}:")
            for iss in timing_issues:
                print(f"  - {iss}")
            if not dry_run:
                append_run_log(run_id, "VALIDATE", company, "SKIPPED_TIMING_RULE", "; ".join(timing_issues))
        else:
            feat_valid, feat_issues = validate_ipo_features(candidate)
            if not feat_valid:
                print(f"Feature Validation FAILED for {company}:")
                for iss in feat_issues:
                    print(f"  - {iss}")
                if not dry_run:
                    append_run_log(run_id, "VALIDATE", company, "SKIPPED_FEATURE_RULE", "; ".join(feat_issues))
            else:
                # Score candidate
                scored = score_ipo(candidate)
                print(f"\nScoring Results for {company}:")
                print(f"  Model Point Estimate : {scored['predicted_gain_pct']:+.2f}%")
                print(f"  Calibrated P(>10%)   : {scored['prob_gt10']*100:.1f}%")
                print(f"  Rule Applied         : {scored['rule_applied']}")
                print(f"  Expected Return      : {scored['primary_expected_return']:+.2f}%")
                print(f"  80% Conformal Range  : {scored['conformal_interval_80']}")
                print(f"  Model Version        : {scored['model_version']}")

                if not dry_run:
                    try:
                        append_prediction_log(
                            company=company,
                            open_date=str(candidate.get("open_date", "")),
                            close_date=close_date,
                            listing_date=listing_date,
                            features=candidate,
                            pred_gain_pct=scored["predicted_gain_pct"],
                            pred_prob_gt10=scored["prob_gt10"],
                            gmp_pct_at_scoring=scored["gmp_pct"],
                            status="FORWARD",
                            notes=str(candidate.get("notes", "Scored via automated daily forward runner")),
                            model_version=scored["model_version"]
                        )
                        print(f"Successfully logged FORWARD prediction to predictions/prediction_log.csv")
                        append_run_log(run_id, "SCORE_AND_LOG", company, "LOGGED_FORWARD")
                    except ValueError as dup_err:
                        print(f"Notice: {dup_err}")
                        append_run_log(run_id, "SCORE_AND_LOG", company, "ALREADY_LOGGED", str(dup_err))
                else:
                    print("[DRY RUN] Prediction was computed but NOT logged to prediction_log.csv.")

    # 2. Check for pending forward IPOs needing actuals
    log_path = ROOT_DIR / "predictions" / "prediction_log.csv"
    if log_path.exists():
        log_df = pd.read_csv(log_path)
        pending = log_df[(log_df["status"] == "FORWARD") & (log_df["actual_gain_pct"].isna())]
        today_date = date.today()
        for _, r in pending.iterrows():
            comp_name = r["company"]
            l_date = pd.to_datetime(r["listing_date"]).date()
            if l_date <= today_date:
                print(f"\n{comp_name} listed on {l_date} <= today ({today_date}) - outcome update pending.")
                print(
                    "Record it with scripts/update_actuals.py using an official NSE/BSE page, "
                    "the opening-price quote, and the listing-date quote. The runner will not "
                    "copy an actual from the historical master dataset."
                )
            else:
                print(f"{comp_name} scheduled to list on {l_date} > today ({today_date}) - unlisted, carried over.")

    # 3. Regenerate dashboard only if not in dry-run
    if not dry_run:
        dashboard_path = render_dashboard_html()
        print(f"\nDashboard updated at: {dashboard_path}")
        append_run_log(run_id, "FINISH", "ALL", "SUCCESS")
    else:
        print("[DRY RUN] Dashboard update skipped in dry-run mode.")
    print(f"{'='*78}\n")


def main():
    parser = argparse.ArgumentParser(description="OPI Automated Daily Forward Test Runner")
    parser.add_argument("--dry-run", action="store_true", help="Run discovery and scoring without writing to log")
    args = parser.parse_args()
    run_daily_forward_test(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
