#!/usr/bin/env python3
"""Grounded forward scoring CLI for upcoming/closed Mainboard IPOs using opi.ingest.

Replaces deprecated scripts/score_oct19_ipos.py with deterministic parsing,
snapshot-first ingestion, and grounding enforcement.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import yfinance as yf

from opi.discover import is_company_in_master, get_today_ist
from opi.ingest import ingest_ipo_data, save_raw_market_data, IngestionError, slugify
from opi.score import score_ipo
from opi.log import append_prediction_log, append_run_log, get_write_timestamp
from opi.report import render_dashboard_html
from opi.validate import validate_candidate_for_forward_logging


def get_market_data(as_of_date: str) -> tuple[float, float, float]:
    """Fetch market macro data, save raw response with SHA-256 hash, and return (nifty_30d, vix, recent_avg)."""
    print(f"Fetching public market data for Nifty 50 and India VIX as of {as_of_date}...")
    dt = pd.to_datetime(as_of_date)
    end_date = (dt + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    nifty = yf.download("^NSEI", start="2026-08-01", end=end_date, progress=False)
    if isinstance(nifty.columns, pd.MultiIndex):
        nifty.columns = nifty.columns.get_level_values(0)

    vix = yf.download("^INDIAVIX", start="2026-08-01", end=end_date, progress=False)
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = vix.columns.get_level_values(0)

    sub1 = nifty.loc[:dt]
    sub0 = nifty.loc[:(dt - pd.Timedelta(days=30))]
    p1 = float(sub1.iloc[-1]["Close"])
    p0 = float(sub0.iloc[-1]["Close"])
    nifty_30d_return = round((p1 - p0) / p0 * 100, 2)

    sub_v = vix.loc[:dt]
    india_vix = round(float(sub_v.iloc[-1]["Close"]), 2)

    master = pd.read_csv(ROOT_DIR / "data" / "ipo_master.csv", parse_dates=["listing_date"])
    recent_5 = master.sort_values("listing_date").iloc[-5:]
    recent_ipo_avg_gain = round(float(recent_5["listing_gain_pct"].mean()), 2)

    # Save raw market data with hash
    raw_payload = json.dumps({
        "as_of_date": as_of_date,
        "nifty_close": p1,
        "nifty_30d_ago_close": p0,
        "nifty_30d_return": nifty_30d_return,
        "india_vix": india_vix,
        "recent_ipo_avg_gain": recent_ipo_avg_gain,
        "source": "yfinance"
    }, indent=2).encode("utf-8")

    save_raw_market_data(raw_payload, as_of_date, source="yfinance")
    return nifty_30d_return, india_vix, recent_ipo_avg_gain


def score_and_log_ipo(
    company: str,
    listing_date: str,
    close_date: str,
    overview_url: str,
    sub_url: str,
    gmp_url: Optional[str] = None,
    open_date: Optional[str] = None,
    sector: str = "Other",
    exchange: str = "BOTH",
    proposed_values: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Ingest, deterministically parse, score, and optionally log an IPO prediction."""
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\n--- Grounded Scoring: {company} (Listing: {listing_date}) ---")

    # 0. Refuse to score already-listed companies or unknown listing dates
    in_master, _ = is_company_in_master(company)
    if in_master:
        msg = f"Refusing to score {company}: already in data/ipo_master.csv"
        print(f"  [SKIPPED_ALREADY_LISTED] {msg}")
        if not dry_run:
            append_run_log(run_id, "SCORE", company, "SKIPPED_ALREADY_LISTED", msg)
        raise ValueError(f"SKIPPED_ALREADY_LISTED: {msg}")

    if not listing_date or str(listing_date).strip().lower() in ("", "unknown", "none"):
        msg = f"Refusing to score {company}: listing date is missing or unknown"
        print(f"  [SKIPPED_UNKNOWN_LISTING_DATE] {msg}")
        if not dry_run:
            append_run_log(run_id, "SCORE", company, "SKIPPED_UNKNOWN_LISTING_DATE", msg)
        raise ValueError(f"SKIPPED_UNKNOWN_LISTING_DATE: {msg}")

    try:
        l_dt = datetime.strptime(str(listing_date)[:10], "%Y-%m-%d").date()
        today_dt = datetime.strptime(get_today_ist(), "%Y-%m-%d").date()
        if l_dt <= today_dt:
            msg = f"Refusing to score {company}: listing date {listing_date} is on or before today ({today_dt})"
            print(f"  [SKIPPED_ALREADY_LISTED] {msg}")
            if not dry_run:
                append_run_log(run_id, "SCORE", company, "SKIPPED_ALREADY_LISTED", msg)
            raise ValueError(f"SKIPPED_ALREADY_LISTED: {msg}")
    except ValueError as ve:
        if "SKIPPED_" in str(ve):
            raise
        msg = f"Refusing to score {company}: invalid listing date '{listing_date}' ({ve})"
        print(f"  [SKIPPED_UNKNOWN_LISTING_DATE] {msg}")
        if not dry_run:
            append_run_log(run_id, "SCORE", company, "SKIPPED_UNKNOWN_LISTING_DATE", msg)
        raise ValueError(f"SKIPPED_UNKNOWN_LISTING_DATE: {msg}")

    # 1. Deterministic Ingestion & Grounding
    if not gmp_url:
        try:
            from opi.gmp import discover_gmp_url
            gmp_url = discover_gmp_url(company, allow_network=True)
        except Exception:
            pass

    parsed = ingest_ipo_data(
        company=company,
        listing_date=listing_date,
        close_date=close_date,
        overview_url=overview_url,
        subscription_url=sub_url,
        gmp_url=gmp_url,
        proposed_values=proposed_values,
    )

    # 2. Market Macro
    nifty_30d, vix_val, recent_avg = get_market_data(close_date)

    # 3. Assemble Feature Vector
    features = {
        "company": company,
        "sector": sector,
        "exchange": exchange,
        "open_date": open_date or close_date,
        "close_date": close_date,
        "listing_date": listing_date,
        "issue_price": parsed.get("issue_price"),
        "issue_size_cr": parsed.get("issue_size_cr"),
        "fresh_issue_pct": parsed.get("fresh_issue_pct", 50.0),
        "ofs_pct": parsed.get("ofs_pct", 50.0),
        "lot_size": parsed.get("lot_size"),
        "sub_qib": parsed.get("sub_qib"),
        "sub_nii": parsed.get("sub_nii"),
        "sub_retail": parsed.get("sub_retail"),
        "sub_total": parsed.get("sub_total"),
        "pe_ratio": None,
        "peer_median_pe": None,
        "debt_equity": None,
        "gmp_pct": parsed.get("gmp_pct"),
        "gmp_as_of_date": parsed.get("gmp_as_of_date", close_date),
        "nifty_30d_return": nifty_30d,
        "india_vix": vix_val,
        "recent_ipo_avg_gain": recent_avg,
    }

    # 3.5 Grounded Research Agent for Missing Fields (D-082)
    missing_fields = [k for k in ["gmp_pct", "pe_ratio", "peer_median_pe", "debt_equity", "fresh_issue_pct", "ofs_pct"] if features.get(k) is None]
    if missing_fields:
        try:
            from opi.research_agent import execute_research_run
            is_test = os.getenv("OPI_ENV") == "test"
            has_key = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY"))

            if has_key or is_test:
                print(f"  Invoking research agent for missing fields: {missing_fields}...")
                agent_sources = {}
                if overview_url:
                    overview_target = ROOT_DIR / "data" / "evidence" / "research" / f"{listing_date}_{slugify(company)}.html"
                    if overview_target.exists():
                        agent_sources[overview_url] = overview_target.read_text(encoding="utf-8", errors="replace")
                if sub_url:
                    sub_target = ROOT_DIR / "data" / "evidence" / "subscription" / f"{listing_date}_{slugify(company)}.html"
                    if sub_target.exists():
                        agent_sources[sub_url] = sub_target.read_text(encoding="utf-8", errors="replace")

                prov_name = "mock" if (is_test and not has_key) else os.getenv("OPI_LLM_PROVIDER", "openrouter")
                schema = execute_research_run(
                    company_name=company,
                    provider_name=prov_name,
                    html_fixtures=agent_sources if agent_sources else None,
                )

                metrics = schema.grounding_metrics()
                notes_str = schema.notes or ""
                model_used = "unknown"
                if "model: " in notes_str:
                    model_used = notes_str.split("model: ")[-1].rstrip(")")
                elif prov_name == "mock":
                    model_used = "mock"

                stats_detail = (
                    f"provider={prov_name};model={model_used};requests=1;"
                    f"proposed={metrics['populated_fields']};grounded={metrics['verified_fields']};"
                    f"grounding_rate={metrics['grounding_rate_pct']}"
                )
                if not dry_run:
                    append_run_log(run_id, "RESEARCH_AGENT", company, "STATS", stats_detail)
                print(f"  [Research Agent] {stats_detail}")

                grounded_feats = schema.to_model_features()
                dumped = schema.model_dump()
                for k in missing_fields:
                    if grounded_feats.get(k) is not None and dumped.get(k, {}).get("grounding_status") == "VERIFIED_IN_SNAPSHOT":
                        features[k] = grounded_feats[k]
                        print(f"  [Research Agent Grounded] {k} = {features[k]}")
            else:
                if not dry_run:
                    append_run_log(run_id, "RESEARCH_AGENT", company, "SKIPPED_NO_KEY", "No API key configured")
        except Exception as ag_err:
            err_msg = str(ag_err)[:100]
            print(f"  [ALERT] [Research Agent Failure] {company}: {ag_err}")
            if not dry_run:
                append_run_log(run_id, "RESEARCH_AGENT", company, "FAILED", f"error={err_msg}")
                append_run_log(run_id, "ALERT", company, "RESEARCH_AGENT_ALERT", f"error={err_msg}")

    # 4. Score with Champion Model
    res = score_ipo(features)
    print(f"  Model Predicted Gain: {res['predicted_gain_pct']}%")
    print(f"  Platt-Calibrated P(gain > 10%): {res['prob_gt10']}")
    print(f"  Observed GMP: {res.get('gmp_pct')}%")
    print(f"  Rule Applied: {res.get('rule_applied')}")

    if dry_run:
        print("  [DRY-RUN] No prediction logged to disk.")
        return res

    # 5. Build Grounded Evidence Snapshots
    features["overview_url"] = overview_url
    features["sub_url"] = sub_url
    if gmp_url:
        features["gmp_url"] = gmp_url
        features["source_urls"] = f"{overview_url};{sub_url};{gmp_url}"
    else:
        features["source_urls"] = f"{overview_url};{sub_url}"
    notes = f"Closed {close_date}; final subscription and GMP grounded via opi.ingest | Scheduled listing {listing_date}"
    features["notes"] = notes

    # 6. Append to Log and Regenerate Dashboard
    append_prediction_log(
        company=company,
        open_date=features["open_date"],
        close_date=close_date,
        listing_date=listing_date,
        features=features,
        pred_gain_pct=res["predicted_gain_pct"],
        pred_prob_gt10=res["prob_gt10"],
        gmp_pct_at_scoring=res.get("gmp_pct"),
        status="FORWARD",
        notes=notes,
        model_version="v4.0.0-champion",
    )
    render_dashboard_html()
    print("  Successfully logged prediction and refreshed dashboard.")
    return res


def main():
    parser = argparse.ArgumentParser(description="Score upcoming Mainboard IPO with grounded ingest.")
    parser.add_argument("--company", required=True, help="Exact company name")
    parser.add_argument("--listing-date", required=True, help="Scheduled listing date (YYYY-MM-DD)")
    parser.add_argument("--close-date", required=True, help="Final bidding close date (YYYY-MM-DD)")
    parser.add_argument("--open-date", help="Bidding open date (YYYY-MM-DD)")
    parser.add_argument("--overview-url", required=True, help="URL to IPO overview page")
    parser.add_argument("--sub-url", required=True, help="URL to final subscription page")
    parser.add_argument("--gmp-url", help="URL to GMP history page")
    parser.add_argument("--sector", default="Other", help="Company sector classification")
    parser.add_argument("--exchange", default="BOTH", help="Listing exchange (NSE, BSE, BOTH)")
    parser.add_argument("--dry-run", action="store_true", help="Perform ingest and scoring without writing log")

    args = parser.parse_args()
    score_and_log_ipo(
        company=args.company,
        listing_date=args.listing_date,
        close_date=args.close_date,
        overview_url=args.overview_url,
        sub_url=args.sub_url,
        gmp_url=args.gmp_url,
        open_date=args.open_date,
        sector=args.sector,
        exchange=args.exchange,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
