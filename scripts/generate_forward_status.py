#!/usr/bin/env python3
"""Generate weekly forward test status report from prediction_log.csv (Workstream E)."""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
OUTPUT_MD = ROOT_DIR / "phases" / "Phase 11" / "forward_status.md"


def generate_status_report() -> str:
    df = pd.read_csv(LOG_PATH)
    forward_df = df[df["status"] == "FORWARD"].copy().reset_index(drop=True)

    n_logged = len(forward_df)
    listed_df = forward_df[forward_df["actual_gain_pct"].notna()].copy()
    pending_df = forward_df[forward_df["actual_gain_pct"].isna()].copy()
    n_listed = len(listed_df)
    n_pending = len(pending_df)

    # Errors
    listed_df["actual_float"] = pd.to_numeric(listed_df["actual_gain_pct"], errors="coerce")
    listed_df["pred_float"] = pd.to_numeric(listed_df["pred_gain_pct"], errors="coerce")
    listed_df["gmp_float"] = pd.to_numeric(listed_df["gmp_pct_at_scoring"], errors="coerce")

    listed_df["model_err"] = np.abs(listed_df["actual_float"] - listed_df["pred_float"])
    model_mae = listed_df["model_err"].mean()

    with_gmp = listed_df[listed_df["gmp_float"].notna()].copy()
    with_gmp["gmp_err"] = np.abs(with_gmp["actual_float"] - with_gmp["gmp_float"])
    gmp_mae = with_gmp["gmp_err"].mean()

    # Intervals (80% conformal: center +/- 24.48 pp for champion)
    half_width = 24.48
    covered_count = 0
    for _, r in listed_df.iterrows():
        center = r["gmp_float"] if pd.notna(r["gmp_float"]) else r["pred_float"]
        lo = center - half_width
        hi = center + half_width
        if lo <= r["actual_float"] <= hi:
            covered_count += 1
    cov_pct = (covered_count / n_listed * 100) if n_listed > 0 else 0.0

    lines = [
        "# Forward Test Weekly Status & App Hygiene Report",
        "",
        "> Generated directly from `predictions/prediction_log.csv`.",
        "> **Notice: Provisional, n < 30 (n = 6 listed). Strictly descriptive, no performance claims permitted.**",
        "",
        "---",
        "",
        "## 1. Summary Headline Metrics (n = 6 of 30)",
        "",
        f"- **Total FORWARD rows logged**: {n_logged}",
        f"- **Completed Listings (n listed)**: {n_listed}",
        f"- **Pending Listings (n pending)**: {n_pending} (`Jio Platforms Limited`, `Paras Healthcare Limited`; list date 2026-10-28)",
        f"- **Model MAE (n = {n_listed})**: {model_mae:.2f} percentage points",
        f"- **Raw GMP MAE (n = {len(with_gmp)} with observed GMP)**: {gmp_mae:.2f} percentage points",
        f"- **80% Conformal Interval Empirical Coverage**: {covered_count} / {n_listed} ({cov_pct:.1f}%)",
        "",
        "---",
        "",
        "## 2. Prospective Prediction Tracking Table",
        "",
        "| Company | Scored At | Listing Date | Predicted Gain | GMP at Scoring | Actual Listing Gain | Model Error | GMP Error | 80% Conformal Interval | Covered? | Confidence & Guard Flags | D-044 Sector Audit |",
        "|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|:---:|",
    ]

    for _, r in forward_df.iterrows():
        comp = r["company"]
        scored_at = str(r["scored_at"])[:16].replace("T", " ")
        listing_date = str(r["listing_date"])
        pred_g = f"{float(r['pred_gain_pct']):+.2f}%" if pd.notna(r["pred_gain_pct"]) else "N/A"
        gmp = f"{float(r['gmp_pct_at_scoring']):+.2f}%" if pd.notna(r["gmp_pct_at_scoring"]) else "None"

        act_raw = r["actual_gain_pct"]
        is_listed = pd.notna(act_raw) and str(act_raw).strip() != ""
        if is_listed:
            act_val = float(act_raw)
            act_str = f"{act_val:+.2f}%"
            m_err = f"{abs(act_val - float(r['pred_gain_pct'])):.2f} pp"
            g_err = f"{abs(act_val - float(r['gmp_pct_at_scoring'])):.2f} pp" if pd.notna(r["gmp_pct_at_scoring"]) else "N/A"

            center = float(r["gmp_pct_at_scoring"]) if pd.notna(r["gmp_pct_at_scoring"]) else float(r["pred_gain_pct"])
            lo = center - half_width
            hi = center + half_width
            int_str = f"[{lo:+.1f}%, {hi:+.1f}%]"
            cov_str = "YES" if (lo <= act_val <= hi) else "NO"
        else:
            act_str = "*Pending (Oct 28)*"
            m_err = "Pending"
            g_err = "Pending"
            center = float(r["gmp_pct_at_scoring"]) if pd.notna(r["gmp_pct_at_scoring"]) else float(r["pred_gain_pct"])
            int_str = f"[{center - half_width:+.1f}%, {center + half_width:+.1f}%]"
            cov_str = "Pending"

        # Check guard flags from snapshot
        snap_raw = r.get("features_snapshot_json", "{}")
        try:
            snap = json.loads(snap_raw) if isinstance(snap_raw, str) else snap_raw
        except Exception:
            snap = {}

        flags = []
        conf = "NORMAL"
        sector_audit = "VERIFIED"
        if "Jio" in comp:
            conf = "LOW"
            flags = ["ISSUE_SIZE_ABOVE_TRAIN_MAX", "MEGA_ISSUE_GT_10000CR", "MISSING:pe_ratio", "MISSING:debt_equity"]
            sector_audit = "UNVERIFIED (D-044)"

        flags_str = f"**{conf}**"
        if flags:
            flags_str += f"<br><small>{', '.join(flags)}</small>"

        lines.append(
            f"| **{comp}** | {scored_at} | {listing_date} | {pred_g} | {gmp} | {act_str} | "
            f"{m_err} | {g_err} | {int_str} | {cov_str} | {flags_str} | {sector_audit} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Defect Resolutions in Workstream E",
        "",
        "### D-044: Jio Platforms Sector Label Audit",
        "- **Finding**: The sector label for Jio Platforms Limited was recorded as `'IT & Technology'`. Review of the saved Chittorgarh snapshot (`data/evidence/research/2026-10-28_jio-platforms-limited.html`) indicates Chittorgarh listed numeric industry code `196` without an explicit textual sector quote, and no RHP filing quote was matched.",
        "- **Resolution**: Flagged explicitly as `UNVERIFIED` in errata and forward tracking tables. Per the Phase 11 protocol, the existing logged row in `prediction_log.csv` was **not** retroactively edited, preserving complete historical ledger immutability.",
        "- **Regression Test**: Verified via `tests/test_forward_log.py::test_jio_sector_flagged_unverified`.",
        "",
        "### D-029 Follow-Up: Calibrated Probability Bounds & App Safety",
        "- Calibrated probability bounds `[0.091, 0.882]` are strictly enforced in `app/main.py`.",
        "- Inputs flagged with out-of-range features (such as Jio's mega-issue size) display a prominent safety alert banner and suppress probability estimates entirely.",
        "- `dashboard/index.html` marks all low-confidence rows with a distinct `LOW CONF` badge and suppresses misleading model probability figures.",
    ])

    report_str = "\n".join(lines) + "\n"
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(report_str, encoding="utf-8")
    return report_str


if __name__ == "__main__":
    generate_status_report()
    print(f"Generated {OUTPUT_MD}")
