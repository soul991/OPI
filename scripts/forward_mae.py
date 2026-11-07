"""Compute forward cohort listing outcomes, MAE, and evidence metadata.

This script audits predictions/prediction_log.csv against
predictions/outcome_corrections.csv and data/evidence/actuals/ manifests,
calculating cumulative forward MAE and formatting the verified outcomes table.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
PREDICTION_LOG_PATH = ROOT_DIR / "predictions" / "prediction_log.csv"
OUTCOME_CORRECTIONS_PATH = ROOT_DIR / "predictions" / "outcome_corrections.csv"
EVIDENCE_DIR = ROOT_DIR / "data" / "evidence" / "actuals"


def get_forward_cohort_data(
    log_path: Path = PREDICTION_LOG_PATH,
    corrections_path: Path = OUTCOME_CORRECTIONS_PATH,
    evidence_dir: Path = EVIDENCE_DIR,
) -> List[Dict[str, Any]]:
    """Extract all evaluated prospective FORWARD rows with their outcome metadata."""
    import pandas as pd

    log_path = Path(log_path)
    if not log_path.exists():
        return []

    df = pd.read_csv(log_path)
    fwd = df[df["status"] == "FORWARD"].copy()

    corr_p = Path(corrections_path)
    corr = pd.read_csv(corr_p) if corr_p.exists() else pd.DataFrame()

    # Apply corrections to actual_gain_pct
    if not corr.empty and "field" in corr.columns:
        for _, row in corr.iterrows():
            if row.get("field") == "actual_gain_pct":
                mask = (fwd["company"] == row["company"]) & (fwd["listing_date"] == row["listing_date"])
                fwd.loc[mask, "actual_gain_pct"] = float(row["new_value"])

    manifests = {}
    p_ev = Path(evidence_dir)
    if p_ev.exists():
        for jf in sorted(p_ev.glob("*.json")):
            if "tier2b" in jf.name or "pending" in str(jf):
                continue
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    d = json.load(f)
                c = d.get("company")
                ld = d.get("listing_date")
                if c and ld:
                    manifests[(str(c).strip(), str(ld).strip())] = (jf, d)
            except Exception:
                pass

    rows = []
    for _, r in fwd.iterrows():
        c = str(r["company"]).strip()
        ld = str(r["listing_date"]).strip()
        act_val = r.get("actual_gain_pct")
        if pd.isna(act_val) or str(act_val).strip() == "" or str(act_val).lower() == "nan":
            continue
        act_pct = float(act_val)
        pred_pct = float(r["pred_gain_pct"])
        abs_err = round(abs(pred_pct - act_pct), 4)

        val = r.get("features_snapshot_json", "")
        if str(val).startswith("{"):
            snap = json.loads(str(val))
        elif Path(str(val)).exists():
            with open(str(val), "r", encoding="utf-8") as f:
                snap = json.load(f)
        else:
            snap = {}
        issue_price = float(snap.get("issue_price", 0.0))

        ev_file = ""
        out_source = "tier1"
        rec_open = round(issue_price * (1.0 + act_pct / 100.0), 2)

        if (c, ld) in manifests:
            jf, md = manifests[(c, ld)]
            ev_file = jf.name
            out_source = md.get("outcome_source") or "tier1"
            if md.get("official_opening_price"):
                rec_open = round(float(md["official_opening_price"]), 2)

        if not corr.empty and "company" in corr.columns:
            for _, crow in corr.iterrows():
                if str(crow.get("company", "")).strip() == c and str(crow.get("listing_date", "")).strip() == ld:
                    if "evidence_path" in crow and pd.notna(crow["evidence_path"]):
                        ev_file = Path(str(crow["evidence_path"])).name
                    if "tier" in crow and pd.notna(crow["tier"]):
                        out_source = str(crow["tier"])
                    reason_str = str(crow.get("reason", ""))
                    m = re.search(r"(\d+\.\d+),\s*\+?\-?\d+", reason_str)
                    if m:
                        rec_open = round(float(m.group(1)), 2)

        rows.append({
            "company": c,
            "listing_date": ld,
            "issue_price": issue_price,
            "recorded_listing_open": rec_open,
            "actual_gain_pct": act_pct,
            "pred_gain_pct": pred_pct,
            "abs_err": abs_err,
            "outcome_source": out_source,
            "evidence_file": ev_file,
        })

    return rows


def compute_forward_cohort_mae(
    log_path: Path = PREDICTION_LOG_PATH,
    corrections_path: Path = OUTCOME_CORRECTIONS_PATH,
    evidence_dir: Path = EVIDENCE_DIR,
) -> Dict[str, Any]:
    """Calculate sample size and cumulative MAE across all evaluated forward rows."""
    rows = get_forward_cohort_data(log_path, corrections_path, evidence_dir)
    errors = [r["abs_err"] for r in rows]
    mae = sum(errors) / len(errors) if errors else 0.0
    return {
        "n": len(rows),
        "mae": round(mae, 4),
        "rows": rows,
    }


def generate_forward_cohort_markdown_table(rows: List[Dict[str, Any]]) -> str:
    """Generate Markdown table for forward cohort outcomes and evidence."""
    lines = [
        "| Company | Issue Price | Recorded Listing Open | Actual % | Outcome Source | Evidence File |",
        "|---|:---:|:---:|:---:|:---:|---|",
    ]
    for r in rows:
        sign = "+" if r["actual_gain_pct"] >= 0 else ""
        lines.append(
            f"| **{r['company']}** | ₹{r['issue_price']:.2f} | ₹{r['recorded_listing_open']:.2f} | **{sign}{r['actual_gain_pct']:.2f}%** | `{r['outcome_source']}` | `{r['evidence_file']}` |"
        )
    return "\n".join(lines)


def main() -> int:
    res = compute_forward_cohort_mae()
    print("=" * 78)
    print("  OPI PROSPECTIVE FORWARD COHORT PERFORMANCE & EVIDENCE AUDIT")
    print("=" * 78)
    print(f"Sample Size (n) : {res['n']}")
    print(f"Cumulative MAE  : {res['mae']:.4f} pp")
    print("-" * 78)
    print("Per-IPO Predictions, Outcomes, and Errors:")
    for r in res["rows"]:
        sign_p = "+" if r["pred_gain_pct"] >= 0 else ""
        sign_a = "+" if r["actual_gain_pct"] >= 0 else ""
        print(f"  - {r['company']} ({r['listing_date']}): Pred={sign_p}{r['pred_gain_pct']:.2f}%, Actual={sign_a}{r['actual_gain_pct']:.2f}%, Abs Err={r['abs_err']:.4f} pp")
    print("-" * 78)
    print("Verified Forward Outcomes Evidence Table:")
    print(generate_forward_cohort_markdown_table(res["rows"]))
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
