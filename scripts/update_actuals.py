#!/usr/bin/env python3
"""Record a listed IPO outcome from a code-fetched official NSE/BSE page.

Without evidence arguments this command only lists pending outcomes. It never
copies an outcome from the historical master dataset into the forward log.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from opi.actuals import ActualsEvidenceError, record_actual_from_exchange, execute_two_tier_outcome_chain
from opi.log import IST
from opi.report import render_dashboard_html

DEFAULT_LOG = ROOT_DIR / "predictions" / "prediction_log.csv"


def show_pending(log_path: Path = DEFAULT_LOG) -> int:
    """List forward outcomes awaiting evidence without changing any files."""
    if not log_path.is_file():
        print(f"Prediction log not found: {log_path}")
        return 1
    frame = pd.read_csv(log_path, dtype=str, keep_default_na=False)
    if frame.empty:
        print("Prediction log is empty; no outcomes are pending.")
        return 0
    pending = frame[(frame["status"] == "FORWARD") & (frame["actual_gain_pct"].str.strip() == "")]
    if pending.empty:
        print("No forward outcomes are pending.")
        return 0
    today = datetime.now(IST).date()
    print("Pending FORWARD outcomes (read-only):")
    for row in pending.itertuples(index=False):
        listing_date = pd.to_datetime(row.listing_date, errors="coerce")
        if pd.isna(listing_date):
            state = "invalid listing date; review prediction row"
        elif listing_date.date() > today:
            state = f"scheduled for {listing_date.date()}"
        else:
            state = "listed date passed; official exchange evidence is still required"
        print(f"- {row.company} | {row.listing_date} | {state}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record a listing-day opening price after verifying a code-fetched official exchange snapshot."
    )
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="Prediction log CSV")
    parser.add_argument("--company", help="Exact company name from the active FORWARD log row")
    parser.add_argument("--source-url", help="HTTPS URL on an NSE or BSE domain")
    parser.add_argument("--actual-listing-price", type=float, help="Official opening/listing price in INR")
    parser.add_argument("--page-date", help="Date represented by the exchange record, YYYY-MM-DD")
    parser.add_argument("--company-quote", help="Exact company identifier copied from the fetched exchange page")
    parser.add_argument(
        "--evidence-file",
        type=Path,
        default=None,
        help="Path to locally saved official exchange page from browser",
    )
    parser.add_argument(
        "--price-quote",
        help="Exact page excerpt that labels the opening/listing price and includes its value",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Attempt automated recording via two-tier source chain (Tier 1 Exchange -> Tier 2 yfinance + cross-check)",
    )
    args = parser.parse_args()

    evidence_args = (
        args.source_url,
        args.actual_listing_price,
        args.page_date,
        args.company_quote,
        args.price_quote,
    )
    if not args.company and not any(evidence_args) and not args.evidence_file:
        return show_pending(args.log)

    if args.auto and args.company:
        print(f"Executing automated two-tier outcome recording for '{args.company}'...")
        res = execute_two_tier_outcome_chain(company=args.company, log_path=args.log)
        status = res.get("status")
        if status == "RECORDED":
            print("Actual outcome recorded successfully via automated chain.")
            print(f"Company: {args.company}")
            print(f"Tier used: {res.get('tier')}")
            print(f"Official opening price: INR {res.get('official_opening_price'):.2f}")
            print(f"Computed listing gain: {res.get('actual_gain_pct'):+.2f}%")
            dash = render_dashboard_html()
            print(f"Dashboard refreshed: {dash}")
            return 0
        else:
            print(f"Automated recording ended with status {status}: {res.get('reason')}", file=sys.stderr)
            return 1

    if not args.company or not all(evidence_args):
        parser.error(
            "manual recording requires --company, --source-url, --actual-listing-price, --page-date, "
            "--company-quote, and --price-quote together (or use --auto with --company)"
        )

    try:
        result = record_actual_from_exchange(
            company=args.company,
            source_url=args.source_url,
            listing_price=args.actual_listing_price,
            page_date=args.page_date,
            company_quote=args.company_quote,
            price_quote=args.price_quote,
            log_path=args.log,
            evidence_file=args.evidence_file,
        )
    except ActualsEvidenceError as exc:
        print(f"NOT RECORDED: {exc}", file=sys.stderr)
        return 1

    print("Actual outcome recorded from verified exchange evidence.")
    print(f"Company: {result['company']}")
    print(f"Listing date: {result['listing_date']}")
    print(f"Official opening price: INR {result['official_opening_price']:.2f}")
    print(f"Computed listing gain: {result['computed_listing_gain_pct']:+.2f}%")
    print(f"Source: {result['final_url']}")
    print(f"Snapshot: {result['snapshot_path']}")
    print(f"SHA-256: {result['snapshot_sha256']}")
    print(result["update_message"])
    dashboard_path = render_dashboard_html()
    print(f"Dashboard refreshed: {dashboard_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
