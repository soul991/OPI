#!/usr/bin/env python3
"""Score the four closed October 15-19, 2026 mainboard IPOs and save code-fetched evidence snapshots.

IPOs:
1. Zetwerk Manufacturing Business Limited
2. Sahajanand Medical Technologies Limited
3. Tonbo Imaging India Limited
4. Bonfiglioli Transmissions Limited

Skipped IPOs:
- Jio Platforms (bidding still open / not yet closed)
- Paras Healthcare (bidding still open / not yet closed)
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import requests
import pandas as pd
import yfinance as yf

from opi.collect import DEFAULT_HEADERS, save_evidence_snapshot, slugify
from opi.log import append_prediction_log, append_run_log, get_write_timestamp
from opi.report import render_dashboard_html
from opi.score import score_ipo
from opi.validate import validate_candidate_for_forward_logging


def save_market_evidence(as_of_date: str = "2026-10-19") -> tuple[float, float, float]:
    """Fetch and snapshot public Nifty 50 and India VIX data as of close date."""
    print("Fetching public market data for Nifty 50 and India VIX...")
    nifty = yf.download("^NSEI", start="2026-08-01", end="2026-10-21", progress=False)
    if isinstance(nifty.columns, pd.MultiIndex):
        nifty.columns = nifty.columns.get_level_values(0)

    vix = yf.download("^INDIAVIX", start="2026-08-01", end="2026-10-21", progress=False)
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = vix.columns.get_level_values(0)

    dt = pd.to_datetime(as_of_date)
    sub1 = nifty.loc[:dt]
    sub0 = nifty.loc[:(dt - pd.Timedelta(days=30))]
    p1 = float(sub1.iloc[-1]["Close"])
    p0 = float(sub0.iloc[-1]["Close"])
    nifty_30d_return = round((p1 - p0) / p0 * 100, 2)

    sub_v = vix.loc[:dt]
    india_vix = round(float(sub_v.iloc[-1]["Close"]), 2)

    # Rolling 5 recent IPO average listing gain from master
    master = pd.read_csv(ROOT_DIR / "data" / "ipo_master.csv", parse_dates=["listing_date"])
    recent_5 = master.sort_values("listing_date").iloc[-5:]
    recent_ipo_avg_gain = round(float(recent_5["listing_gain_pct"].mean()), 2)

    market_evidence_dir = ROOT_DIR / "data" / "evidence" / "market"
    market_evidence_dir.mkdir(parents=True, exist_ok=True)
    snapshot_payload = {
        "as_of_date": as_of_date,
        "accessed_at": get_write_timestamp(),
        "nifty_close": p1,
        "nifty_30d_ago_close": p0,
        "nifty_30d_return": nifty_30d_return,
        "india_vix": india_vix,
        "recent_ipo_avg_gain": recent_ipo_avg_gain,
        "nifty_source": "^NSEI via yfinance (public exchange data)",
        "vix_source": "^INDIAVIX via yfinance (public exchange data)",
    }
    snap_file = market_evidence_dir / f"{as_of_date}_market_macro.json"
    snap_file.write_text(json.dumps(snapshot_payload, indent=2), encoding="utf-8")
    print(f"  Market snapshot saved: {snap_file.relative_to(ROOT_DIR)}")
    print(f"  nifty_30d_return: {nifty_30d_return}%, india_vix: {india_vix}, recent_avg: {recent_ipo_avg_gain}%")
    return nifty_30d_return, india_vix, recent_ipo_avg_gain


def fetch_and_snapshot(url: str, category: str, listing_date: str, company: str) -> str:
    """Fetch URL by code and save snapshot under data/evidence/<category>/."""
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch {url}: HTTP {resp.status_code}")
    saved = save_evidence_snapshot(resp.text, category, listing_date, company, ext="html")
    rel = str(saved.relative_to(ROOT_DIR)).replace("\\", "/")
    print(f"  Saved {category} snapshot: {rel}")
    return rel


def run_candidate_scoring():
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\n=======================================================")
    print(f"  SCORING FOUR OCTOBER 19, 2026 CLOSED MAINBOARD IPOs  ")
    print(f"  Run ID: {run_id}                                     ")
    print(f"=======================================================\n")

    append_run_log(run_id, "START", "ALL", "STARTED", "Forward scoring 4 newly closed IPOs (bidding 15-19 Oct 2026)")

    # 1. Market Data
    nifty_30d, vix_val, recent_avg = save_market_evidence("2026-10-19")

    # 2. Candidate Specifications
    candidates = [
        {
            "company": "Zetwerk Manufacturing Business Limited",
            "sector": "Industrial & Manufacturing",
            "exchange": "BOTH",
            "open_date": "2026-10-15",
            "close_date": "2026-10-19",
            "listing_date": "2026-10-23",
            "issue_price": 151.0,
            "issue_size_cr": 5012.33,
            "fresh_issue_pct": 56.4608,
            "ofs_pct": 43.5392,
            "lot_size": 99,
            "sub_qib": 4.71,
            "sub_nii": 1.45,
            "sub_retail": 0.77,
            "sub_total": 3.10,
            "gmp_pct": 2.32,
            "gmp_as_of_date": "2026-10-19",
            "nifty_30d_return": nifty_30d,
            "india_vix": vix_val,
            "recent_ipo_avg_gain": recent_avg,
            "overview_url": "https://www.chittorgarh.com/ipo/zetwerk-ipo/3091/",
            "sub_url": "https://www.chittorgarh.com/ipo_subscription/zetwerk-ipo/3091/",
            "gmp_url": "https://www.investorgain.com/gmp/zetwerk-ipo/2279/",
            "notes": "Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23",
        },
        {
            "company": "Sahajanand Medical Technologies Limited",
            "sector": "Healthcare & Pharma",
            "exchange": "BOTH",
            "open_date": "2026-10-15",
            "close_date": "2026-10-19",
            "listing_date": "2026-10-23",
            "issue_price": 344.0,
            "issue_size_cr": 475.48,
            "fresh_issue_pct": 0.0,
            "ofs_pct": 100.0,
            "lot_size": 43,
            "sub_qib": 34.70,
            "sub_nii": 14.64,
            "sub_retail": 3.04,
            "sub_total": 14.21,
            "gmp_pct": 6.98,
            "gmp_as_of_date": "2026-10-19",
            "nifty_30d_return": nifty_30d,
            "india_vix": vix_val,
            "recent_ipo_avg_gain": recent_avg,
            "overview_url": "https://www.chittorgarh.com/ipo/sahajanand-medical-technologies-ipo/2550/",
            "sub_url": "https://www.chittorgarh.com/ipo_subscription/sahajanand-medical-technologies-ipo/2550/",
            "gmp_url": "https://www.investorgain.com/gmp/sahajanand-medical-technologies-ipo/1842/",
            "notes": "Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23",
        },
        {
            "company": "Tonbo Imaging India Limited",
            "sector": "Defense & Aerospace",
            "exchange": "BOTH",
            "open_date": "2026-10-15",
            "close_date": "2026-10-19",
            "listing_date": "2026-10-23",
            "issue_price": 700.0,
            "issue_size_cr": 852.18,
            "fresh_issue_pct": 0.0,
            "ofs_pct": 100.0,
            "lot_size": 21,
            "sub_qib": 293.56,
            "sub_nii": 156.36,
            "sub_retail": 31.11,
            "sub_total": 132.81,
            "gmp_pct": 72.86,
            "gmp_as_of_date": "2026-10-19",
            "nifty_30d_return": nifty_30d,
            "india_vix": vix_val,
            "recent_ipo_avg_gain": recent_avg,
            "overview_url": "https://www.chittorgarh.com/ipo/tonbo-imaging-india-ipo/3215/",
            "sub_url": "https://www.chittorgarh.com/ipo_subscription/tonbo-imaging-india-ipo/3215/",
            "gmp_url": "https://www.investorgain.com/gmp/tonbo-imaging-india-ipo/2369/",
            "notes": "Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23",
        },
        {
            "company": "Bonfiglioli Transmissions Limited",
            "sector": "Engineering & Capital Goods",
            "exchange": "BOTH",
            "open_date": "2026-10-15",
            "close_date": "2026-10-19",
            "listing_date": "2026-10-23",
            "issue_price": 586.0,
            "issue_size_cr": 2533.81,
            "fresh_issue_pct": 0.0,
            "ofs_pct": 100.0,
            "lot_size": 25,
            "sub_qib": 120.78,
            "sub_nii": 40.39,
            "sub_retail": 5.90,
            "sub_total": 46.05,
            "gmp_pct": 21.67,
            "gmp_as_of_date": "2026-10-19",
            "nifty_30d_return": nifty_30d,
            "india_vix": vix_val,
            "recent_ipo_avg_gain": recent_avg,
            "overview_url": "https://www.chittorgarh.com/ipo/bonfiglioli-transmissions-ipo/2861/",
            "sub_url": "https://www.chittorgarh.com/ipo_subscription/bonfiglioli-transmissions-ipo/2861/",
            "gmp_url": "https://www.investorgain.com/gmp/bonfiglioli-transmissions-ipo/2124/",
            "notes": "Closed 2026-10-19; final subscription and 19-Oct GMP backed by code-saved snapshots | Scheduled listing 2026-10-23",
        },
    ]

    scored_summary = []

    for c in candidates:
        company = c["company"]
        print(f"\nProcessing {company}...")

        # Save snapshots by code
        sub_snap = fetch_and_snapshot(c["sub_url"], "subscription", c["listing_date"], company)
        gmp_snap = fetch_and_snapshot(c["gmp_url"], "gmp", c["listing_date"], company)
        overview_snap = fetch_and_snapshot(c["overview_url"], "research", c["listing_date"], company)

        # Set source URLs
        c["source_urls"] = f"{c['overview_url']};{c['sub_url']};{c['gmp_url']}"

        # Validate candidate
        is_valid, issues = validate_candidate_for_forward_logging(c)
        if not is_valid:
            print(f"  VALIDATION FAILED: {issues}")
            append_run_log(run_id, "VALIDATE", company, "SKIPPED_VALIDATION_FAILURE", "; ".join(issues))
            continue

        # Score candidate
        result = score_ipo(c)
        print(f"  Scoring Result:")
        print(f"    Predicted Listing Gain : {result['predicted_gain_pct']:+.2f}%")
        print(f"    Calibrated P(gain>10%) : {result['prob_gt10']*100:.1f}%")
        print(f"    Observed GMP           : {result['gmp_pct']:+.2f}%")
        print(f"    Primary Expected Return: {result['primary_expected_return']:+.2f}%")
        print(f"    Blend Expected Return  : {result['blend_expected_return']:+.2f}%")
        print(f"    80% Conformal Range    : {result['conformal_interval_80']}")

        # Append to prediction log
        row = append_prediction_log(
            company=company,
            open_date=c["open_date"],
            close_date=c["close_date"],
            listing_date=c["listing_date"],
            features=c,
            pred_gain_pct=result["predicted_gain_pct"],
            pred_prob_gt10=result["prob_gt10"],
            gmp_pct_at_scoring=result["gmp_pct"],
            status="FORWARD",
            notes=c["notes"],
            model_version=result["model_version"],
        )
        append_run_log(run_id, "SCORE", company, "SCORED_FORWARD", f"pred_gain={result['predicted_gain_pct']}, prob_gt10={result['prob_gt10']}")

        scored_summary.append({
            "company": company,
            "pred_gain_pct": result["predicted_gain_pct"],
            "prob_gt10": result["prob_gt10"],
            "gmp_pct": result["gmp_pct"],
            "interval": result["conformal_interval_80"],
            "listing_date": c["listing_date"],
        })

    # 3. Log skipped IPOs
    skipped = [
        ("Jio Platforms", "Bidding still open or not yet closed as of 2026-10-20"),
        ("Paras Healthcare", "Bidding still open or not yet closed as of 2026-10-20"),
    ]
    for comp, reason in skipped:
        print(f"\nSkipping {comp}: {reason}")
        append_run_log(run_id, "DISCOVERY", comp, "SKIPPED_NOT_CLOSED", reason)

    # 4. Save Fusion CX subscription evidence snapshot
    print("\nSaving evidence snapshot for existing Fusion CX row...")
    try:
        fusion_url = "https://www.chittorgarh.com/news-detail/ipo/closed-ipo/fusion-cx-ipo/11875/"
        fetch_and_snapshot(fusion_url, "subscription", "2026-10-22", "Fusion CX Limited")
    except Exception as e:
        print(f"  Note: Fusion CX snapshot warning: {e}")

    # 5. Refresh Dashboard
    print("\nRefreshing dashboard HTML...")
    dash_path = render_dashboard_html()
    print(f"  Dashboard refreshed: {dash_path}")

    append_run_log(run_id, "COMPLETE", "ALL", "SUCCESS", f"Scored {len(scored_summary)} IPOs; skipped {len(skipped)}")
    print(f"\nFinished scoring. Scored: {len(scored_summary)}, Skipped: {len(skipped)}")
    return scored_summary


if __name__ == "__main__":
    run_candidate_scoring()
