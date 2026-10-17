"""Reporting and static dashboard generation module for OPI."""

import json
import os
import re
import html as html_lib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
DEFECTS_PATH = ROOT_DIR / "DEFECTS.md"
REGISTRY_PATH = ROOT_DIR / "model" / "registry.json"
DASHBOARD_DIR = ROOT_DIR / "dashboard"
CHAMPION_REPLAY_PATH = ROOT_DIR / "predictions" / "champion_replay_v4.0.0-champion.csv"


def _champion_replay_summary() -> Dict[str, Any]:
    """Read a frozen post-training replay. It never fits or rescales the registered model."""
    if not CHAMPION_REPLAY_PATH.is_file():
        return {"count": 0, "mae": None, "direction_accuracy": None, "chart": ""}
    frame = pd.read_csv(CHAMPION_REPLAY_PATH)
    required = {"company", "listing_date", "actual_gain_pct", "pred_gain_pct"}
    if not required.issubset(frame.columns):
        return {"count": 0, "mae": None, "direction_accuracy": None, "chart": ""}
    frame = frame.dropna(subset=["company", "listing_date", "actual_gain_pct", "pred_gain_pct"]).copy()
    frame["listing_date"] = pd.to_datetime(frame["listing_date"], errors="coerce")
    frame = frame.dropna(subset=["listing_date"]).sort_values("listing_date")
    if frame.empty:
        return {"count": 0, "mae": None, "direction_accuracy": None, "chart": ""}

    predicted = frame["pred_gain_pct"].astype(float)
    actual = frame["actual_gain_pct"].astype(float)
    count = len(frame)
    mae = float((predicted - actual).abs().mean())
    direction_accuracy = float(((predicted > 0) == (actual > 0)).mean())

    # Render a dependency-free SVG so the chart is available offline and on static hosting.
    width, height = 1120, 390
    left, right, top, bottom = 64, 18, 20, 54
    plot_w, plot_h = width - left - right, height - top - bottom
    low = min(-50.0, float(actual.min()), float(predicted.min()))
    high = max(50.0, float(actual.max()), float(predicted.max()))
    pad = max(5.0, (high - low) * 0.06)
    low -= pad
    high += pad

    def y(value: float) -> float:
        return top + (high - value) / (high - low) * plot_h

    def x(index: int) -> float:
        return left + (index / max(1, count - 1)) * plot_w

    parts = [f'<svg class="history-chart" viewBox="0 0 {width} {height}" role="img" aria-label="Chronological retrospective champion predictions and actual IPO listing gains">']
    tick_count = 5
    for tick in range(tick_count + 1):
        value = low + (high - low) * tick / tick_count
        py = y(value)
        parts.append(f'<line x1="{left}" y1="{py:.1f}" x2="{width-right}" y2="{py:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{left-9}" y="{py+4:.1f}" text-anchor="end" class="axis-label">{value:+.0f}%</text>')
    year_marks = frame.groupby(frame["listing_date"].dt.year).indices
    for year, indexes in year_marks.items():
        mid = (min(indexes) + max(indexes)) // 2
        px = x(mid)
        parts.append(f'<text x="{px:.1f}" y="{height-16}" text-anchor="middle" class="axis-label">{int(year)}</text>')
    pred_points, actual_points = [], []
    for index, row in enumerate(frame.itertuples(index=False)):
        px = x(index)
        pred = float(row.pred_gain_pct)
        act = float(row.actual_gain_pct)
        py, ay = y(pred), y(act)
        title = html_lib.escape(f"{row.company} | {row.listing_date:%Y-%m-%d} | prediction {pred:+.2f}% | actual {act:+.2f}%", quote=True)
        parts.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{ay:.1f}" stroke="#cbd5e1" stroke-width="1"><title>{title}</title></line>')
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.1" fill="#2563eb"><title>{title}</title></circle>')
        parts.append(f'<circle cx="{px:.1f}" cy="{ay:.1f}" r="2.1" fill="#f97316"><title>{title}</title></circle>')
        pred_points.append(f"{px:.1f},{py:.1f}")
        actual_points.append(f"{px:.1f},{ay:.1f}")
    parts.append(f'<polyline points="{" ".join(pred_points)}" fill="none" stroke="#2563eb" stroke-width="1.5" opacity=".72"/>')
    parts.append(f'<polyline points="{" ".join(actual_points)}" fill="none" stroke="#f97316" stroke-width="1.5" opacity=".72"/>')
    parts.append(f'<text x="{left + plot_w/2:.1f}" y="{height-1}" text-anchor="middle" class="axis-label">Listing date (chronological IPOs)</text>')
    parts.append('</svg>')
    return {
        "count": count,
        "mae": round(mae, 2),
        "direction_accuracy": round(direction_accuracy * 100, 1),
        "chart": "".join(parts),
    }


def _forward_comparison_chart(rows: List[Dict[str, Any]]) -> str:
    """Render paired live-prediction/actual bars; pending actuals remain visibly blank."""
    items = [r for r in rows if r.get("status") == "FORWARD" and r.get("pred_gain_pct") is not None]
    if not items:
        return ""
    width, row_height = 960, 56
    height = 60 + len(items) * row_height
    left, right = 230, 30
    plot_w = width - left - right
    values = [float(r["pred_gain_pct"]) for r in items]
    values += [float(r["actual_gain_pct"]) for r in items if r.get("actual_gain_pct") is not None]
    low, high = min(-20.0, min(values)), max(20.0, max(values))
    pad = max(4.0, (high - low) * 0.08)
    low, high = low - pad, high + pad

    def x(value: float) -> float:
        return left + (value - low) / (high - low) * plot_w

    parts = [f'<svg class="live-chart" viewBox="0 0 {width} {height}" role="img" aria-label="Paired model predictions and actual listing gains from genuine forward predictions">']
    for tick in range(5):
        value = low + (high - low) * tick / 4
        px = x(value)
        parts.append(f'<line x1="{px:.1f}" y1="20" x2="{px:.1f}" y2="{height-16}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{px:.1f}" y="14" text-anchor="middle" class="axis-label">{value:+.0f}%</text>')
    zero_x = x(0)
    parts.append(f'<line x1="{zero_x:.1f}" y1="20" x2="{zero_x:.1f}" y2="{height-16}" stroke="#9ca3af" stroke-width="1.5"/>')
    for index, row in enumerate(items):
        y = 42 + index * row_height
        company = html_lib.escape(row["company"])
        listing_date = html_lib.escape(row["listing_date"])
        pred = float(row["pred_gain_pct"])
        parts.append(f'<text x="8" y="{y+4}" class="row-label">{company}</text>')
        parts.append(f'<text x="8" y="{y+20}" class="axis-label">Listing {listing_date}</text>')
        pred_x = x(pred)
        title = html_lib.escape(f"{row['company']} | prediction {pred:+.2f}%", quote=True)
        parts.append(f'<line x1="{zero_x:.1f}" y1="{y}" x2="{pred_x:.1f}" y2="{y}" stroke="#2563eb" stroke-width="7" stroke-linecap="round"><title>{title}</title></line>')
        parts.append(f'<circle cx="{pred_x:.1f}" cy="{y}" r="4.5" fill="#2563eb"><title>{title}</title></circle>')
        actual = row.get("actual_gain_pct")
        if actual is not None:
            actual = float(actual)
            actual_x = x(actual)
            actual_title = html_lib.escape(f"{row['company']} | actual {actual:+.2f}%", quote=True)
            parts.append(f'<line x1="{zero_x:.1f}" y1="{y+12}" x2="{actual_x:.1f}" y2="{y+12}" stroke="#f97316" stroke-width="7" stroke-linecap="round"><title>{actual_title}</title></line>')
            parts.append(f'<circle cx="{actual_x:.1f}" cy="{y+12}" r="4.5" fill="#f97316"><title>{actual_title}</title></circle>')
        else:
            parts.append(f'<text x="{width-right}" y="{y+16}" text-anchor="end" class="axis-label">Actual pending</text>')
    parts.append('</svg>')
    return "".join(parts)


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
    data["champion_replay"] = _champion_replay_summary()
    data["forward_chart"] = ""

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
        data["forward_chart"] = _forward_comparison_chart(rows_list)

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
    replay = d["champion_replay"]

    rows_html = ""
    forward_accuracy_rows = []
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
        if r["status"] == "FORWARD" and r["pred_gain_pct"] is not None:
            pred_text = f"{r['pred_gain_pct']:+.2f}%"
            actual_text = f"{r['actual_gain_pct']:+.2f}%" if r["actual_gain_pct"] is not None else "Pending"
            error_text = (
                f"{abs(r['pred_gain_pct'] - r['actual_gain_pct']):.2f}%"
                if r["actual_gain_pct"] is not None else "—"
            )
            forward_accuracy_rows.append(
                "<tr>"
                f"<td>{html_lib.escape(r['company'])}</td><td>{html_lib.escape(r['listing_date'])}</td>"
                f"<td>{pred_text}</td><td>{actual_text}</td><td>{error_text}</td></tr>"
            )
    forward_accuracy_rows_html = "".join(forward_accuracy_rows) or (
        '<tr><td colspan="5" style="padding:16px;text-align:center;color:#6b7280">'
        "No active champion predictions recorded.</td></tr>"
    )

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
        .history-chart {{ display: block; width: 100%; height: auto; }}
        .live-chart {{ display: block; width: 100%; height: auto; min-height: 100px; }}
        .axis-label {{ font: 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #6b7280; }}
        .row-label {{ font: 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-weight: 600; fill: #1f2937; }}
        .legend {{ display: flex; flex-wrap: wrap; gap: 18px; color: #4b5563; font-size: 13px; margin: 12px 0 0; }}
        .legend span {{ display: inline-flex; align-items: center; gap: 7px; }}
        .legend i {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; }}
        .stats {{ color: #4b5563; font-size: 14px; }}
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
            <h2 style="margin-top: 0; font-size: 18px;">Champion Replay vs Actual</h2>
            <p class="stats">{replay['count']} post-training Mainboard IPOs, scored with the registered champion using stored feature rows. MAE: <strong>{f"{replay['mae']:.2f}%" if replay['mae'] is not None else "—"}</strong> · Direction correct (positive vs non-positive): <strong>{f"{replay['direction_accuracy']:.1f}%" if replay['direction_accuracy'] is not None else "—"}</strong></p>
            <p class="stats"><strong>Retrospective replay:</strong> these predictions were computed now from the historical master data, so this is not a prospectively recorded track record. The historical feature rows do not all have verified pre-listing snapshots; treat the comparison as exploratory, and keep it separate from the live forward audit below.</p>
            <div style="overflow-x: auto;">{replay['chart'] if replay['chart'] else '<p>No saved champion replay is available.</p>'}</div>
            <div class="legend"><span><i style="background:#2563eb"></i>Champion predicted gain</span><span><i style="background:#f97316"></i>Actual listing gain</span><span>Hover a point for IPO, date, prediction, and actual.</span></div>
        </div>

        <div class="section">
            <h2 style="margin-top: 0; font-size: 18px;">Current Champion Forward Track Record</h2>
            <p class="stats">Only genuine post-close, pre-listing champion predictions are counted here. The chart updates when the daily report runs and after an official exchange actual is recorded. Pending listings remain forecasts and are not counted as accuracy results.</p>
            <div style="overflow-x:auto;">{d['forward_chart'] if d['forward_chart'] else '<p>No forward predictions are available yet.</p>'}</div>
            <div class="legend"><span><i style="background:#2563eb"></i>Champion prediction</span><span><i style="background:#f97316"></i>Actual listing gain</span></div>
            <div style="overflow-x: auto;">
                <table><thead><tr><th>Company</th><th>Listing date</th><th>Champion prediction</th><th>Actual gain</th><th>Absolute error</th></tr></thead><tbody>
                    {forward_accuracy_rows_html}
                </tbody></table>
            </div>
            <p class="stats">Completed champion outcomes: <strong>{n_listed}</strong> · Pending: <strong>{d['pending_forward_count']}</strong> · Mean absolute error: <strong>{f"{d.get('mae_model'):.2f}%" if d.get('mae_model') is not None else "—"}</strong></p>
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
