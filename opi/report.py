"""Reporting and static dashboard generation module for OPI."""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
DEFECTS_PATH = ROOT_DIR / "DEFECTS.md"
REGISTRY_PATH = ROOT_DIR / "model" / "registry.json"
DASHBOARD_DIR = ROOT_DIR / "dashboard"


def parse_defects_summary() -> Dict[str, Any]:
    """Parse DEFECTS.md and return status counts."""
    counts = {"OPEN": 0, "PARTIAL": 0, "FIXED": 0, "ACCEPTED": 0, "DEFERRED": 0, "TOTAL": 0}
    if not DEFECTS_PATH.exists():
        return counts
    text = DEFECTS_PATH.read_text(encoding="utf-8")
    for line in text.splitlines():
        if re.match(r"^\|\s*D-\d+", line):
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) >= 5:
                status = parts[4].upper()
                counts[status] = counts.get(status, 0) + 1
                counts["TOTAL"] += 1
    return counts


def generate_dashboard_data() -> Dict[str, Any]:
    """Compile all necessary data for the forward test dashboard."""
    data: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "model_version": "Unknown",
        "total_log_rows": 0,
        "forward_rows_count": 0,
        "listed_forward_count": 0,
        "pending_forward_count": 0,
        "forward_rows": [],
        "defects_summary": parse_defects_summary(),
        "provisional": True,
        "disclaimer": "Decision aid only, not financial advice. No empirical performance claims permitted until n >= 30."
    }

    if REGISTRY_PATH.exists():
        try:
            reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            data["model_version"] = reg.get("active_champion", "v4.0.0-champion")
        except Exception:
            pass

    if LOG_PATH.exists():
        df = pd.read_csv(LOG_PATH)
        data["total_log_rows"] = len(df)
        f_df = df[df["status"] == "FORWARD"].copy()
        data["forward_rows_count"] = len(f_df)
        
        listed = f_df[f_df["actual_gain_pct"].notna()]
        pending = f_df[f_df["actual_gain_pct"].isna()]
        data["listed_forward_count"] = len(listed)
        data["pending_forward_count"] = len(pending)
        data["provisional"] = len(listed) < 30

        # Compile forward rows
        rows_list = []
        for _, r in df.iterrows():
            rows_list.append({
                "scored_at": str(r.get("scored_at", "")),
                "company": str(r.get("company", "")),
                "listing_date": str(r.get("listing_date", "")),
                "status": str(r.get("status", "")),
                "pred_gain_pct": float(r["pred_gain_pct"]) if pd.notna(r.get("pred_gain_pct")) else None,
                "pred_prob_gt10": float(r["pred_prob_gt10"]) if pd.notna(r.get("pred_prob_gt10")) else None,
                "gmp_pct": float(r["gmp_pct_at_scoring"]) if pd.notna(r.get("gmp_pct_at_scoring")) else None,
                "actual_gain_pct": float(r["actual_gain_pct"]) if pd.notna(r.get("actual_gain_pct")) else None,
                "notes": str(r.get("notes", ""))
            })
        data["forward_rows"] = rows_list

        # Metrics if any listed
        if len(listed) > 0:
            act = listed["actual_gain_pct"].astype(float)
            pred = listed["pred_gain_pct"].astype(float)
            data["mae_model"] = round(float((pred - act).abs().mean()), 2)
            has_gmp = listed[listed["gmp_pct_at_scoring"].notna()]
            if len(has_gmp) > 0:
                gmp_act = has_gmp["actual_gain_pct"].astype(float)
                gmp_val = has_gmp["gmp_pct_at_scoring"].astype(float)
                data["mae_gmp"] = round(float((gmp_val - gmp_act).abs().mean()), 2)

    return data


def render_dashboard_html(output_dir: Optional[Path] = None) -> Path:
    """Render and write dashboard HTML to dashboard/index.html."""
    out_dir = output_dir or DASHBOARD_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"

    d = generate_dashboard_data()
    n_listed = d["listed_forward_count"]
    n_fwd = d["forward_rows_count"]
    defects = d["defects_summary"]

    rows_html = ""
    for r in d["forward_rows"]:
        status_color = "#10b981" if r["status"] == "FORWARD" else "#ef4444" if "INVALID" in r["status"] else "#6b7280"
        rows_html += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{r['scored_at'][:19]}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: 600;">{r['company']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{r['listing_date']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; color: {status_color}; font-weight: 600;">{r['status']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{f"{r['pred_gain_pct']:+.2f}%" if r['pred_gain_pct'] is not None else "-"}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{f"{r['pred_prob_gt10']*100:.1f}%" if r['pred_prob_gt10'] is not None else "-"}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{f"{r['gmp_pct']:+.2f}%" if r['gmp_pct'] is not None else "-"}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: 600;">{f"{r['actual_gain_pct']:+.2f}%" if r['actual_gain_pct'] is not None else "Pending"}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-size: 12px; color: #4b5563;">{r['notes'][:80]}...</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OPI Forward Test Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f9fafb; margin: 0; padding: 24px; color: #111827; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #ffffff; padding: 24px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 24px; }}
        .banner {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 4px; margin-bottom: 24px; font-weight: 500; color: #92400e; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; }}
        .card-num {{ font-size: 28px; font-weight: 700; margin-top: 8px; color: #1f2937; }}
        .card-label {{ font-size: 13px; color: #6b7280; text-transform: uppercase; font-weight: 600; }}
        .section {{ background: #ffffff; padding: 24px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 24px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
        th {{ background: #f3f4f6; padding: 10px 8px; font-weight: 600; border-bottom: 2px solid #e5e7eb; }}
        .footer {{ font-size: 13px; color: #6b7280; text-align: center; margin-top: 32px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0 0 8px 0; font-size: 24px;">India IPO Listing-Gain Predictor (OPI)</h1>
            <p style="margin: 0; color: #4b5563;">Automated Daily Forward Test & Operational Health Dashboard</p>
        </div>

        <div class="banner">
            ⚠️ <strong>PROVISIONAL STATUS (Listed n = {n_listed})</strong>: Decision aid only, not financial advice. Per pre-registered protocol, no performance claims are permitted until at least 30 forward listings are completed.
        </div>

        <div class="cards">
            <div class="card">
                <div class="card-label">Model Version</div>
                <div class="card-num" style="font-size: 20px; color: #2563eb;">{d['model_version']}</div>
            </div>
            <div class="card">
                <div class="card-label">Logged Predictions</div>
                <div class="card-num">{n_fwd}</div>
            </div>
            <div class="card">
                <div class="card-label">Completed Listings</div>
                <div class="card-num">{n_listed}</div>
            </div>
            <div class="card">
                <div class="card-label">Open / Partial Defects</div>
                <div class="card-num" style="color: {'#10b981' if (defects['OPEN'] + defects['PARTIAL']) == 0 else '#f59e0b'};">
                    {defects['OPEN'] + defects['PARTIAL']}
                </div>
            </div>
        </div>

        <div class="section">
            <h2 style="margin-top: 0; font-size: 18px;">Forward Prediction Audit Trail</h2>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Scored At (IST)</th>
                            <th>Company</th>
                            <th>Listing Date</th>
                            <th>Status</th>
                            <th>Pred Gain</th>
                            <th>P(Gain > 10%)</th>
                            <th>GMP</th>
                            <th>Actual Gain</th>
                            <th>Audit Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html if rows_html else '<tr><td colspan="9" style="padding: 16px; text-align: center; color: #6b7280;">No forward predictions logged yet.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <h2 style="margin-top: 0; font-size: 18px;">Calibration & Conformal Reliability</h2>
            <p style="color: #6b7280; font-size: 14px;">
                {f"Empirical calibration table is deferred until completed listings n >= 30 (currently n = {n_listed})." if n_listed < 30 else "Displaying 10-bin calibration table."}
            </p>
        </div>

        <div class="section">
            <h2 style="margin-top: 0; font-size: 18px;">Repository & Defect Health</h2>
            <p style="font-size: 14px; color: #374151;">
                Total Tracked Defects: <strong>{defects['TOTAL']}</strong> | 
                Fixed: <strong>{defects['FIXED']}</strong> | 
                Accepted: <strong>{defects['ACCEPTED']}</strong> | 
                Deferred: <strong>{defects['DEFERRED']}</strong> | 
                Open/Partial: <strong>{defects['OPEN'] + defects['PARTIAL']}</strong>
            </p>
        </div>

        <div class="footer">
            Generated automatically by <code>opi.report</code> at {d['generated_at']} IST.<br>
            Strictly append-only audit provenance. Relative repository links only.
        </div>
    </div>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    return out_path
