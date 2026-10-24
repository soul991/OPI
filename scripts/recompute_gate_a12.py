#!/usr/bin/env python3
"""Phase 12 Gate A12 Headline Metrics Recomputation.

Reads directly from predictions/prediction_log.csv, data/ipo_master.csv, and DEFECTS.md.
No hard-coded values or manual transcription.
"""

from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def recompute_all():
    log_path = ROOT / "predictions" / "prediction_log.csv"
    log_df = pd.read_csv(log_path, dtype=str)
    fwd = log_df[log_df["status"].str.strip().str.upper() == "FORWARD"].copy()
    listed = fwd[
        fwd["actual_gain_pct"].notna()
        & (fwd["actual_gain_pct"] != "")
        & (fwd["actual_gain_pct"] != "nan")
    ].copy()

    err_m = (
        listed["pred_gain_pct"].astype(float) - listed["actual_gain_pct"].astype(float)
    ).abs()
    mae_m = err_m.mean()

    with_gmp = listed[
        listed["gmp_pct_at_scoring"].notna()
        & (listed["gmp_pct_at_scoring"] != "")
        & (listed["gmp_pct_at_scoring"] != "nan")
    ].copy()
    err_g = (
        with_gmp["gmp_pct_at_scoring"].astype(float)
        - with_gmp["actual_gain_pct"].astype(float)
    ).abs()
    mae_g = err_g.mean()

    master_df = pd.read_csv(ROOT / "data" / "ipo_master.csv")
    master_rows = len(master_df)

    defects_path = ROOT / "DEFECTS.md"
    defect_rows = []
    for line in defects_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\|\s*D-\d+", line):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            defect_rows.append(parts)
    total_defects = len(defect_rows)

    status_counts = {}
    for r in defect_rows:
        st = r[4].upper()
        status_counts[st] = status_counts.get(st, 0) + 1

    return {
        "model_mae": mae_m,
        "model_mae_n": len(listed),
        "gmp_mae": mae_g,
        "gmp_mae_n": len(with_gmp),
        "master_rows": master_rows,
        "log_total_rows": len(log_df),
        "fwd_rows": len(fwd),
        "listed_rows": len(listed),
        "pending_rows": len(fwd) - len(listed),
        "total_defects": total_defects,
        "defect_status_counts": status_counts,
    }


if __name__ == "__main__":
    res = recompute_all()
    print("--- Phase 12 Headline Numbers ---")
    print(f"1. Forward Model MAE (n={res['listed_rows']}): {res['model_mae']:.4f} pp")
    print(f"2. Forward Raw GMP MAE (n={res['gmp_mae_n']}): {res['gmp_mae']:.4f} pp")
    print(f"3. Master Dataset Row Count: {res['master_rows']} rows")
    print(
        f"4. Prediction Log Breakdown: {res['log_total_rows']} total ({res['fwd_rows']} FORWARD: {res['listed_rows']} listed, {res['pending_rows']} pending)"
    )
    print(
        f"5. Defect Counts: {res['total_defects']} total ({res['defect_status_counts']})"
    )
