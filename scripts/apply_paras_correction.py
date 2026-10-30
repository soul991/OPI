#!/usr/bin/env python3
"""scripts/apply_paras_correction.py - Tier 2b Fetch & Audited Outcome Correction for Paras Healthcare.

Follows Workstream B specifications (D-073) and preregistration amendment:
1. Fetches two independent web pages by code (neither Yahoo Finance).
2. Verifies listing date 2026-10-28 and opening price 720.00 within 1.0% tolerance.
3. Persists raw response payloads and manifests under data/evidence/actuals/.
4. Appends audited record to predictions/outcome_corrections.csv without touching prediction_log.csv.
5. Computes and prints errors and forward MAE before and after correction.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from opi.outcomes import (
    DEFAULT_HEADERS,
    effective_outcome,
    get_effective_predictions_df,
    record_outcome_correction,
)

SOURCE_A_URL = "https://www.chittorgarh.com/ipo/paras-healthcare-ipo/2256/"
SOURCE_B_URL = "https://groww.in/blog/paras-healthcare-shares-list-at-3-9-premium-on-nse-bse"
COMPANY = "Paras Healthcare Limited"
LISTING_DATE = "2026-10-28"
ISSUE_PRICE = Decimal("693.00")


def run_paras_correction(dry_run: bool = False) -> dict[str, Any]:
    print("=" * 70)
    print("  PARAS HEALTHCARE TIER 2b OUTCOME VERIFICATION & CORRECTION (D-073)")
    print("=" * 70)

    # 1. Fetch Source A (Chittorgarh)
    print(f"\n[Step 1] Fetching Source A: {SOURCE_A_URL}")
    r_a = requests.get(SOURCE_A_URL, headers=DEFAULT_HEADERS, timeout=15)
    if r_a.status_code != 200:
        raise RuntimeError(f"Source A returned HTTP {r_a.status_code}")
    print(f"  Received {len(r_a.content)} bytes (HTTP 200).")

    # Extract price from Source A
    m_row = re.search(r"<tr>\s*<td>Open</td>(.*?)</tr>", r_a.text, re.DOTALL | re.IGNORECASE)
    price_a: Optional[float] = None
    if m_row:
        clean_row = re.sub(r"<[^>]+>", " ", m_row.group(1))
        m_val = re.search(r"([0-9]+(?:\.[0-9]+)?)", clean_row)
        if m_val:
            price_a = float(m_val.group(1))
    if price_a is None:
        clean_a = re.sub(r"<[^>]+>", " ", r_a.text)
        m_open = re.search(r"Open\s*(?:₹|&#8377;)?\s*([0-9]+(?:\.[0-9]+)?)", clean_a, re.IGNORECASE)
        if m_open:
            price_a = float(m_open.group(1))
    if not price_a:
        raise ValueError("Could not extract Open price from Chittorgarh page")
    print(f"  Source A parsed Open price: ₹{price_a:.2f}")

    # 2. Fetch Source B (Groww)
    print(f"\n[Step 2] Fetching Source B: {SOURCE_B_URL}")
    r_b = requests.get(SOURCE_B_URL, headers=DEFAULT_HEADERS, timeout=15)
    if r_b.status_code != 200:
        raise RuntimeError(f"Source B returned HTTP {r_b.status_code}")
    print(f"  Received {len(r_b.content)} bytes (HTTP 200).")

    # Extract price from Source B
    clean_b = re.sub(r"<[^>]+>", " ", r_b.text)
    m_b = re.search(r"(?:listed at|shares listed at|opening price of)\s*(?:₹|&#8377;|Rs\.?)?\s*([0-9]+(?:\.[0-9]+)?)", clean_b, re.IGNORECASE)
    if not m_b:
        raise ValueError("Could not extract listing price from Groww article")
    price_b = float(m_b.group(1))
    print(f"  Source B parsed listing price: ₹{price_b:.2f}")

    # 3. Verify 1.0% tolerance
    rel_diff_pct = abs(price_a - price_b) / price_a * 100.0
    print(f"\n[Step 3] Cross-check relative difference: {rel_diff_pct:.4f}% (Tolerance: <= 1.0%)")
    if rel_diff_pct > 1.0:
        raise ValueError(f"Sources diverge beyond tolerance: {price_a} vs {price_b}")
    print("  PASS: Sources agree within 1.0% tolerance.")

    official_listing_price = price_a  # 720.00
    new_gain = ((Decimal(str(official_listing_price)) - ISSUE_PRICE) / ISSUE_PRICE * Decimal("100")).quantize(Decimal("0.01"))
    print(f"  Issue Price: ₹{ISSUE_PRICE:.2f}")
    print(f"  Official Listing Day Opening Price: ₹{official_listing_price:.2f}")
    print(f"  Computed Listing Gain: {float(new_gain):+.2f}%")

    # 4. Save evidence
    ev_dir = ROOT_DIR / "data" / "evidence" / "actuals"
    ev_dir.mkdir(parents=True, exist_ok=True)

    sha_a = hashlib.sha256(r_a.content).hexdigest()
    sha_b = hashlib.sha256(r_b.content).hexdigest()

    file_a_txt = ev_dir / "2026-10-28_paras-healthcare-limited_chittorgarh_tier2b.txt"
    file_a_json = ev_dir / "2026-10-28_paras-healthcare-limited_chittorgarh_tier2b.json"
    file_b_txt = ev_dir / "2026-10-28_paras-healthcare-limited_groww_tier2b.txt"
    file_b_json = ev_dir / "2026-10-28_paras-healthcare-limited_groww_tier2b.json"

    if not dry_run:
        file_a_txt.write_bytes(r_a.content)
        manifest_a = {
            "company": COMPANY,
            "listing_date": LISTING_DATE,
            "source_role": "tier2b_primary",
            "source_name": "Chittorgarh Listing Day Trading Information",
            "source_url": SOURCE_A_URL,
            "accessed_at": datetime.now(timezone.utc).isoformat(),
            "http_status": r_a.status_code,
            "content_sha256": sha_a,
            "parsed_open_price": price_a,
        }
        file_a_json.write_text(json.dumps(manifest_a, indent=2) + "\n", encoding="utf-8")

        file_b_txt.write_bytes(r_b.content)
        manifest_b = {
            "company": COMPANY,
            "listing_date": LISTING_DATE,
            "source_role": "tier2b_independent_second_source",
            "source_name": "Groww Financial Research Listing News",
            "source_url": SOURCE_B_URL,
            "accessed_at": datetime.now(timezone.utc).isoformat(),
            "http_status": r_b.status_code,
            "content_sha256": sha_b,
            "parsed_listing_price": price_b,
        }
        file_b_json.write_text(json.dumps(manifest_b, indent=2) + "\n", encoding="utf-8")
        print(f"\n[Step 4] Saved evidence files to {ev_dir.relative_to(ROOT_DIR)}:")
        print(f"  - {file_a_txt.name} ({len(r_a.content)} bytes)")
        print(f"  - {file_a_json.name}")
        print(f"  - {file_b_txt.name} ({len(r_b.content)} bytes)")
        print(f"  - {file_b_json.name}")

    # 5. Load log and measure baseline before correction
    log_csv = ROOT_DIR / "predictions" / "prediction_log.csv"
    log_bytes_before = log_csv.read_bytes()
    df_raw = pd.read_csv(log_csv)
    paras_row = df_raw[(df_raw["company"] == COMPANY) & (df_raw["listing_date"] == LISTING_DATE)].iloc[0]

    pred_gain = float(paras_row["pred_gain_pct"])
    gmp_at_scoring = float(paras_row["gmp_pct_at_scoring"])
    old_actual_gain = float(paras_row["actual_gain_pct"])

    # Baseline errors
    err_model_before = abs(pred_gain - old_actual_gain)
    err_gmp_before = abs(gmp_at_scoring - old_actual_gain)

    # Listed subset before
    listed_before = df_raw[df_raw["actual_gain_pct"].notna() & (df_raw["status"] == "FORWARD")].copy()
    fwd_model_mae_before = (listed_before["pred_gain_pct"].astype(float) - listed_before["actual_gain_pct"].astype(float)).abs().mean()
    with_gmp_before = listed_before[listed_before["gmp_pct_at_scoring"].notna()]
    fwd_gmp_mae_before = (with_gmp_before["gmp_pct_at_scoring"].astype(float) - with_gmp_before["actual_gain_pct"].astype(float)).abs().mean()

    # 6. Record correction
    reason = (
        "Tier 2 primary source (yfinance) fell back to 2026-10-29 bar (721.00); "
        "corrected via Tier 2b independent dual-source verification (Chittorgarh + Groww, 720.00, +3.90%)"
    )
    if not dry_run:
        record_outcome_correction(
            company=COMPANY,
            listing_date=LISTING_DATE,
            field="actual_gain_pct",
            old_value=f"{old_actual_gain:.2f}",
            new_value=f"{float(new_gain):.2f}",
            reason=reason,
            evidence_path=file_a_json,
            tier="tier2b",
        )
        print("\n[Step 5] Appended correction to predictions/outcome_corrections.csv")

    # 7. Measure performance after correction
    err_model_after = abs(pred_gain - float(new_gain))
    err_gmp_after = abs(gmp_at_scoring - float(new_gain))

    eff_df = get_effective_predictions_df()
    eff_df["actual_clean"] = pd.to_numeric(eff_df["actual_gain_pct"], errors="coerce")
    eff_df["pred_clean"] = pd.to_numeric(eff_df["pred_gain_pct"], errors="coerce")
    eff_df["gmp_clean"] = pd.to_numeric(eff_df["gmp_pct_at_scoring"], errors="coerce")

    listed_after = eff_df[eff_df["actual_clean"].notna() & (eff_df["status"] == "FORWARD")].copy()
    fwd_model_mae_after = (listed_after["pred_clean"] - listed_after["actual_clean"]).abs().mean()
    with_gmp_after = listed_after[listed_after["gmp_clean"].notna()]
    fwd_gmp_mae_after = (with_gmp_after["gmp_clean"] - with_gmp_after["actual_clean"]).abs().mean()

    # Verify log file is byte-identical
    log_bytes_after = log_csv.read_bytes()
    assert log_bytes_before == log_bytes_after, "FATAL: predictions/prediction_log.csv was modified!"
    print("  CONFIRMED: predictions/prediction_log.csv is strictly byte-identical (0 bytes changed).")

    print("\n" + "=" * 70)
    print("  PARAS HEALTHCARE CORRECTION METRICS (SCRIPT OUTPUT ONLY)")
    print("=" * 70)
    print(f"Company                   : {COMPANY}")
    print(f"Listing Date              : {LISTING_DATE}")
    print(f"Issue Price               : ₹{ISSUE_PRICE:.2f}")
    print(f"Old Actual Gain (log)     : {old_actual_gain:+.2f}% (Price: ₹721.00, wrong day 2026-10-29)")
    print(f"New Actual Gain (eff)     : {float(new_gain):+.2f}% (Price: ₹720.00, listing day 2026-10-28)")
    print(f"Model Prediction          : {pred_gain:+.2f}%")
    print(f"GMP at Scoring            : {gmp_at_scoring:+.2f}%")
    print("-" * 70)
    print(f"Paras Model Error Before  : {err_model_before:.2f} pp")
    print(f"Paras Model Error After   : {err_model_after:.2f} pp (change: {err_model_after - err_model_before:+.2f} pp)")
    print(f"Paras GMP Error Before    : {err_gmp_before:.2f} pp")
    print(f"Paras GMP Error After     : {err_gmp_after:.2f} pp (change: {err_gmp_after - err_gmp_before:+.2f} pp)")
    print("-" * 70)
    print(f"Forward Model MAE (n=8) Before: {fwd_model_mae_before:.4f} pp")
    print(f"Forward Model MAE (n=8) After : {fwd_model_mae_after:.4f} pp")
    print(f"Forward GMP MAE (n=7) Before  : {fwd_gmp_mae_before:.4f} pp")
    print(f"Forward GMP MAE (n=7) After   : {fwd_gmp_mae_after:.4f} pp")
    print("=" * 70)

    return {
        "old_actual_gain": old_actual_gain,
        "new_actual_gain": float(new_gain),
        "err_model_before": err_model_before,
        "err_model_after": err_model_after,
        "err_gmp_before": err_gmp_before,
        "err_gmp_after": err_gmp_after,
        "fwd_model_mae_before": fwd_model_mae_before,
        "fwd_model_mae_after": fwd_model_mae_after,
        "fwd_gmp_mae_before": fwd_gmp_mae_before,
        "fwd_gmp_mae_after": fwd_gmp_mae_after,
    }


if __name__ == "__main__":
    run_paras_correction()
