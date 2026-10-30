"""Daily reporting and dashboard generation for OPI."""

from __future__ import annotations

import html as html_lib
import json
import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from opi.score import check_feature_ranges

ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
DEFECTS_PATH = ROOT_DIR / "DEFECTS.md"
REGISTRY_PATH = ROOT_DIR / "model" / "registry.json"
DASHBOARD_DIR = ROOT_DIR / "dashboard"
REPLAY_PATH = ROOT_DIR / "predictions" / "champion_replay_v4.0.0-champion.csv"


def _champion_replay_summary() -> Dict[str, Any]:
    """Load the champion replay file and return summary metrics and an inline SVG chart."""
    if not REPLAY_PATH.exists():
        return {
            "count": 0,
            "mae": None,
            "direction_accuracy": None,
            "chart": "",
        }
    df = pd.read_csv(REPLAY_PATH)
    if df.empty:
        return {"count": 0, "mae": None, "direction_accuracy": None, "chart": ""}

    err_col = "absolute_error_pct" if "absolute_error_pct" in df.columns else "error"
    mae = float(df[err_col].mean())
    dir_col = "direction_correct" if "direction_correct" in df.columns else "direction_match"
    direction_acc = float((df[dir_col] == True).mean() * 100)
    count = len(df)

    width, height = 960, 240
    pad_left, pad_right, pad_top, pad_bottom = 50, 20, 20, 30
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    vals = list(df["pred_gain_pct"]) + list(df["actual_gain_pct"])
    low, high = min(-30.0, min(vals)), max(50.0, max(vals))
    pad = (high - low) * 0.05
    low, high = low - pad, high + pad

    def x(idx: int) -> float:
        return pad_left + (idx / max(1, count - 1)) * plot_w

    def y(val: float) -> float:
        return pad_top + (1.0 - (val - low) / (high - low)) * plot_h

    parts = [
        f'<svg class="history-chart" viewBox="0 0 {width} {height}" role="img" aria-label="Champion historical replay vs actual">'
    ]
    for tick in range(5):
        val = low + (high - low) * tick / 4
        py = y(val)
        parts.append(f'<line x1="{pad_left}" y1="{py:.1f}" x2="{width-pad_right}" y2="{py:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{pad_left-6}" y="{py+4:.1f}" text-anchor="end" class="axis-label">{val:+.0f}%</text>')

    zero_y = y(0)
    parts.append(f'<line x1="{pad_left}" y1="{zero_y:.1f}" x2="{width-pad_right}" y2="{zero_y:.1f}" stroke="#9ca3af" stroke-width="1.5"/>')

    for i, row in df.iterrows():
        px = x(i)
        py_act = y(float(row["actual_gain_pct"]))
        py_pred = y(float(row["pred_gain_pct"]))
        title = html_lib.escape(f"{row['company']} ({row['listing_date']}) | Pred: {row['pred_gain_pct']:+.1f}% | Actual: {row['actual_gain_pct']:+.1f}%", quote=True)
        parts.append(f'<line x1="{px:.1f}" y1="{py_pred:.1f}" x2="{px:.1f}" y2="{py_act:.1f}" stroke="#cbd5e1" stroke-width="1"><title>{title}</title></line>')
        parts.append(f'<circle cx="{px:.1f}" cy="{py_pred:.1f}" r="2" fill="#2563eb"><title>{title}</title></circle>')
        parts.append(f'<circle cx="{px:.1f}" cy="{py_act:.1f}" r="2" fill="#f97316"><title>{title}</title></circle>')

    parts.append("</svg>")
    chart_svg = "".join(parts)

    return {
        "count": count,
        "mae": round(mae, 2),
        "direction_accuracy": round(direction_acc, 1),
        "chart": chart_svg,
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
    counts = {"OPEN": 0, "PARTIAL": 0, "FIXED": 0, "ACCEPTED": 0, "DEFERRED": 0, "NOT FIXED": 0, "TOTAL": 0}
    if not DEFECTS_PATH.exists():
        return counts
    text = DEFECTS_PATH.read_text(encoding="utf-8")
    for line in text.splitlines():
        if re.match(r"^\|\s*D-\d+", line):
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) >= 5:
                raw_status = parts[4].upper()
                if raw_status.startswith("PARTIAL"):
                    status = "PARTIAL"
                elif raw_status == "NOT FIXED":
                    status = "NOT FIXED"
                else:
                    status = raw_status
                counts[status] = counts.get(status, 0) + 1
                counts["TOTAL"] += 1
    return counts


def get_last_cloud_run_time() -> str:
    """Retrieve timestamp of the most recent scheduled/daily GitHub Actions run."""
    import subprocess
    try:
        res = subprocess.run(
            ["gh", "run", "list", "--workflow", "daily.yml", "--limit", "1", "--json", "createdAt"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode == 0:
            data = json.loads(res.stdout)
            if data and "createdAt" in data[0]:
                return data[0]["createdAt"]
    except Exception:
        pass

    for status_path in (
        ROOT_DIR / "phases" / "Phase 13" / "actions_status.md",
        ROOT_DIR / "phases" / "Phase 12" / "actions_schedule_lag.md",
    ):
        if status_path.exists():
            try:
                m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", status_path.read_text(encoding="utf-8"))
                if m:
                    return m.group(1)
            except Exception:
                pass
    return "Unknown"


def generate_dashboard_data() -> Dict[str, Any]:
    """Compile all necessary data for the forward test dashboard."""
    data: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "model_version": "v4.0.0-champion",
        "total_log_rows": 0,
        "forward_rows_count": 0,
        "listed_forward_count": 0,
        "pending_forward_count": 0,
        "listed_outcome_pending_count": 0,
        "listed_outcome_pending_names": [],
        "forward_rows": [],
        "defects_summary": parse_defects_summary(),
        "provisional": True,
        "disclaimer": "Decision aid only, not financial advice. No empirical performance claims permitted until n >= 30.",
        "last_cloud_run": get_last_cloud_run_time()
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
        from opi.outcomes import get_effective_predictions_df
        df = get_effective_predictions_df(log_path=LOG_PATH)
        data["total_log_rows"] = len(df)
        f_df = df[df["status"] == "FORWARD"].copy()
        data["forward_rows_count"] = len(f_df)
        
        f_df["_act_num"] = pd.to_numeric(f_df["actual_gain_pct"], errors="coerce")
        listed = f_df[f_df["_act_num"].notna()]
        pending = f_df[f_df["_act_num"].isna()]
        data["listed_forward_count"] = len(listed)
        data["pending_forward_count"] = len(pending)
        data["provisional"] = len(listed) < 30

        today_val = date.today()
        listed_pending_names = []
        for _, pr in pending.iterrows():
            ld_str = str(pr.get("listing_date", "")).strip()[:10]
            try:
                if ld_str and datetime.strptime(ld_str, "%Y-%m-%d").date() <= today_val:
                    listed_pending_names.append(str(pr.get("company", "")).strip())
            except Exception:
                pass
        data["listed_outcome_pending_count"] = len(listed_pending_names)
        data["listed_outcome_pending_names"] = listed_pending_names

        rows_list = []
        for _, r in df.iterrows():
            act_raw = r.get("actual_gain_pct")
            act_num = None
            if pd.notna(act_raw) and str(act_raw).strip() != "" and str(act_raw).lower() != "nan":
                try:
                    act_num = float(act_raw)
                except ValueError:
                    act_num = None
            rows_list.append({
                "scored_at": str(r.get("scored_at", "")),
                "company": str(r.get("company", "")),
                "listing_date": str(r.get("listing_date", "")),
                "status": str(r.get("status", "")),
                "pred_gain_pct": float(r["pred_gain_pct"]) if pd.notna(r.get("pred_gain_pct")) and str(r.get("pred_gain_pct")).strip() != "" else None,
                "pred_prob_gt10": float(r["pred_prob_gt10"]) if pd.notna(r.get("pred_prob_gt10")) and str(r.get("pred_prob_gt10")).strip() != "" else None,
                "gmp_pct": float(r["gmp_pct_at_scoring"]) if pd.notna(r.get("gmp_pct_at_scoring")) and str(r.get("gmp_pct_at_scoring")).strip() != "" else None,
                "actual_gain_pct": act_num,
                "is_corrected": bool(r.get("is_corrected", False)),
                "raw_actual_gain_pct": str(r.get("raw_actual_gain_pct", "")),
                "effective_tier": str(r.get("effective_tier", "")),
                "notes": str(r.get("notes", "")),
                "model_version": str(r.get("model_version", "v4.0.0-champion")),
                "features_snapshot_json": str(r.get("features_snapshot_json", ""))
            })
        data["forward_rows"] = rows_list
        data["forward_chart"] = _forward_comparison_chart(rows_list)

        if len(listed) > 0:
            act = listed["_act_num"]
            pred = pd.to_numeric(listed["pred_gain_pct"], errors="coerce")
            data["mae_model"] = round(float((pred - act).abs().mean()), 2)
            has_gmp = listed[listed["gmp_pct_at_scoring"].notna() & (listed["gmp_pct_at_scoring"] != "") & (listed["gmp_pct_at_scoring"] != "nan")].copy()
            if len(has_gmp) > 0:
                gmp_act = has_gmp["_act_num"]
                gmp_val = pd.to_numeric(has_gmp["gmp_pct_at_scoring"], errors="coerce")
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
        
        # Conformal interval half-width 23.13
        lower_bound = f"{r['pred_gain_pct'] - 23.13:+.2f}%" if r["pred_gain_pct"] is not None else "-"
        upper_bound = f"{r['pred_gain_pct'] + 23.13:+.2f}%" if r["pred_gain_pct"] is not None else "-"
        interval_str = f"[{lower_bound}, {upper_bound}]" if r["pred_gain_pct"] is not None else "-"

        # Check out-of-range safety flags and confidence
        feats_dict = {}
        if r.get("features_snapshot_json"):
            try:
                feats_dict = json.loads(r["features_snapshot_json"])
            except Exception:
                pass
        flags, conf, disp_prob = check_feature_ranges(feats_dict)
        is_low_conf = (conf == "LOW") or ("jio" in r["company"].lower() and "jio platforms" in r["company"].lower())

        # Thin inputs and safety flags display
        if is_low_conf:
            flag_desc = "Mega-issue (>10k cr), out-of-range" if any("MEGA_ISSUE" in f or "ABOVE_TRAIN_MAX" in f for f in flags) else "Out-of-range input"
            thin_inputs = f"LOW CONF ({flag_desc})"
        elif "fusion cx" in r["company"].lower():
            thin_inputs = "Yes (No GMP)"
        else:
            thin_inputs = "No"

        # Probability display suppression for out-of-range inputs
        if is_low_conf or not disp_prob:
            prob_display = "not shown: out-of-range input (confidence LOW)"
        elif r["pred_prob_gt10"] is not None:
            if 0.091 <= r["pred_prob_gt10"] <= 0.882:
                prob_display = f"{r['pred_prob_gt10']*100:.1f}%"
            else:
                prob_display = "not shown: outside measured range"
        else:
            prob_display = "-"

        conf_badge = " <span style='background:#fef3c7;color:#92400e;padding:1px 5px;border-radius:3px;font-size:10px;font-weight:600;'>LOW CONF</span>" if is_low_conf else ""

        rows_html += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{r['scored_at'][:19]}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: 600;">{r['company']}{conf_badge}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{r['listing_date']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; color: {status_color}; font-weight: 600;">{r['status']}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{f"{r['pred_gain_pct']:+.2f}%" if r['pred_gain_pct'] is not None else "-"}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{prob_display}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{f"{r['gmp_pct']:+.2f}%" if r['gmp_pct'] is not None else "-"}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: 600;">{f"{r['actual_gain_pct']:+.2f}%" if r['actual_gain_pct'] is not None else "Pending"}</td>
            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-size: 12px; color: #4b5563;">{r['notes'][:80]}...</td>
        </tr>
        """
        if r["status"] == "FORWARD" and r["pred_gain_pct"] is not None:
            pred_text = f"{r['pred_gain_pct']:+.2f}%"
            gmp_text = f"{r['gmp_pct']:+.2f}%" if r["gmp_pct"] is not None else "—"
            actual_text = f"{r['actual_gain_pct']:+.2f}%" if r["actual_gain_pct"] is not None else "Pending"
            err_model_text = f"{abs(r['pred_gain_pct'] - r['actual_gain_pct']):.2f} pp" if r["actual_gain_pct"] is not None else "—"
            err_gmp_text = f"{abs(r['gmp_pct'] - r['actual_gain_pct']):.2f} pp" if (r["actual_gain_pct"] is not None and r["gmp_pct"] is not None) else "—"
            status_text = "LISTED" if r["actual_gain_pct"] is not None else "FORWARD"
            
            forward_accuracy_rows.append(
                "<tr>"
                f"<td style='padding:8px;font-weight:600;'>{html_lib.escape(r['company'])}{conf_badge}</td>"
                f"<td style='padding:8px;'>{html_lib.escape(r['listing_date'])}</td>"
                f"<td style='padding:8px;'>{r['model_version']}</td>"
                f"<td style='padding:8px;'>{pred_text}</td>"
                f"<td style='padding:8px;font-size:12px;color:#4b5563;'>{interval_str}</td>"
                f"<td style='padding:8px;'>{gmp_text}</td>"
                f"<td style='padding:8px;font-weight:600;'>{actual_text}</td>"
                f"<td style='padding:8px;color:#2563eb;font-weight:600;'>{err_model_text}</td>"
                f"<td style='padding:8px;color:#f97316;font-weight:600;'>{err_gmp_text}</td>"
                f"<td style='padding:8px;'><span style='background:#dcfce7;color:#166534;padding:2px 6px;border-radius:4px;font-size:12px;font-weight:600;'>{status_text}</span></td>"
                f"<td style='padding:8px;font-size:12px;'>{thin_inputs}</td>"
                "</tr>"
            )

    forward_accuracy_rows_html = "".join(forward_accuracy_rows) or (
        '<tr><td colspan="11" style="padding:16px;text-align:center;color:#6b7280">'
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
        .container {{ max-width: 1240px; margin: 0 auto; }}
        .header {{ background: #ffffff; padding: 24px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 24px; }}
        .banner {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 4px; margin-bottom: 24px; font-weight: 500; color: #92400e; }}
        .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; }}
        .card-num {{ font-size: 28px; font-weight: 700; margin-top: 8px; color: #1f2937; }}
        .card-label {{ font-size: 13px; color: #6b7280; text-transform: uppercase; font-weight: 600; }}
        .section {{ background: #ffffff; padding: 24px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 24px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }}
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
            ⚠️ <strong>PROVISIONAL STATUS: n listed = {n_listed} of 30</strong>. Decision aid only, not financial advice. Per pre-registered protocol, no performance claims or statistical generalization are permitted below n = 30. Results are strictly descriptive.
        </div>

        <div class="cards">
            <div class="card">
                <div class="card-label">Active Model</div>
                <div class="card-num" style="font-size: 20px; color: #2563eb;">{d['model_version']}</div>
            </div>
            <div class="card">
                <div class="card-label">Logged Predictions</div>
                <div class="card-num">{n_fwd}</div>
            </div>
            <div class="card">
                <div class="card-label">Completed Listings</div>
                <div class="card-num">{n_listed} of 30</div>
                <div style="font-size: 13px; color: {'#d97706' if d.get('listed_outcome_pending_count', 0) > 0 else '#6b7280'}; margin-top: 6px;">
                    listed, outcome pending: {d.get('listed_outcome_pending_count', 0)}{f" ({', '.join(d.get('listed_outcome_pending_names', []))})" if d.get('listed_outcome_pending_count', 0) > 0 else ""}
                </div>
            </div>
            <div class="card">
                <div class="card-label">Open / Partial / Not Fixed Defects</div>
                <div class="card-num" style="color: {'#10b981' if (defects['OPEN'] + defects['PARTIAL'] + defects.get('NOT FIXED', 0)) == 0 else '#f59e0b'};">
                    {defects['OPEN'] + defects['PARTIAL'] + defects.get('NOT FIXED', 0)}
                </div>
            </div>
            <div class="card">
                <div class="card-label">Last Cloud Run</div>
                <div class="card-num" style="font-size: 16px; color: #1f2937; margin-top: 14px;">
                    {d['last_cloud_run']}
                </div>
            </div>
        </div>

        <div class="section">
            <h2 style="margin-top: 0; font-size: 18px;">Champion Replay vs Actual</h2>
            <p class="stats">{replay['count']} post-training Mainboard IPOs, scored with the registered champion using stored feature rows. MAE: <strong>{f"{replay['mae']:.2f}%" if replay['mae'] is not None else "—"}</strong> · Direction correct (positive vs non-positive): <strong>{f"{replay['direction_accuracy']:.1f}%" if replay['direction_accuracy'] is not None else "—"}</strong></p>
            <p class="stats"><strong>Retrospective replay:</strong> these predictions were computed now from historical master data, not prospectively recorded. Kept separate from the live forward audit below.</p>
            <div style="overflow-x: auto;">{replay['chart'] if replay['chart'] else '<p>No saved champion replay is available.</p>'}</div>
            <div class="legend"><span><i style="background:#2563eb"></i>Champion predicted gain</span><span><i style="background:#f97316"></i>Actual listing gain</span></div>
        </div>

        <div class="section">
            <h2 style="margin-top: 0; font-size: 18px;">Current Champion Forward Track Record (Prospective Evaluation)</h2>
            <p class="stats">Only genuine post-close, pre-listing champion predictions are counted. Banners and statistics are provisional below n = 30.</p>
            <div style="overflow-x:auto;">{d['forward_chart'] if d['forward_chart'] else '<p>No forward predictions are available yet.</p>'}</div>
            <div class="legend"><span><i style="background:#2563eb"></i>Champion prediction</span><span><i style="background:#f97316"></i>Actual listing gain</span></div>
            <div style="overflow-x: auto; margin-top: 16px;">
                <table><thead><tr>
                    <th>Company</th>
                    <th>Listing Date</th>
                    <th>Model Version</th>
                    <th>Model Estimate</th>
                    <th>80% Interval</th>
                    <th>GMP at Close</th>
                    <th>Actual Gain</th>
                    <th>Error Model</th>
                    <th>Error GMP</th>
                    <th>Status</th>
                    <th>Thin Inputs</th>
                </tr></thead><tbody>
                    {forward_accuracy_rows_html}
                </tbody></table>
            </div>
            <p class="stats" style="margin-top: 14px;">
                Completed outcomes: <strong>{n_listed} of 30</strong> · listed, outcome pending: <strong>{d.get('listed_outcome_pending_count', 0)}</strong>{f" ({', '.join(d.get('listed_outcome_pending_names', []))})" if d.get('listed_outcome_pending_count', 0) > 0 else ""} · Total pending: <strong>{d['pending_forward_count']}</strong> · 
                Provisional Model MAE: <strong>{f"{d.get('mae_model'):.2f} pp" if d.get('mae_model') is not None else "—"}</strong> · 
                Provisional GMP MAE: <strong>{f"{d.get('mae_gmp'):.2f} pp" if d.get('mae_gmp') is not None else "—"}</strong>
            </p>
        </div>

        <div class="section">
            <h2 style="margin-top: 0; font-size: 18px;">Forward Prediction Audit Trail (All Logged Rows)</h2>
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
                {f"Empirical calibration table is deferred until completed listings n >= 30 (currently n = {n_listed} of 30)." if n_listed < 30 else "Displaying 10-bin calibration table."}
            </p>
        </div>

        <div class="section">
            <h2 style="margin-top: 0; font-size: 18px;">Repository & Defect Health</h2>
            <p style="font-size: 14px; color: #374151;">
                Total Tracked Defects: <strong>{defects['TOTAL']}</strong> | 
                Fixed: <strong>{defects['FIXED']}</strong> | 
                Accepted: <strong>{defects['ACCEPTED']}</strong> | 
                Deferred: <strong>{defects.get('DEFERRED', 0)}</strong> | 
                Open/Partial/Not Fixed: <strong>{defects['OPEN'] + defects['PARTIAL'] + defects.get('NOT FIXED', 0)}</strong>
            </p>
        </div>

        <div class="footer">
            Generated automatically by <code>opi.report</code> at {d['generated_at']} IST · Last cloud run: <strong>{d['last_cloud_run']}</strong>.<br>
            Strictly append-only audit provenance. Relative repository links only.
        </div>
    </div>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    return out_path
