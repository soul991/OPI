#!/usr/bin/env python3
"""scripts/recompute_phase15.py - Recomputes all Phase 15 metrics from effective outcomes.

Every number in Phase 15 outcome reports comes directly from running this script.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from opi.outcomes import get_effective_predictions_df


def compute_metrics() -> dict[str, float]:
    df = get_effective_predictions_df(log_path=ROOT_DIR / "predictions" / "prediction_log.csv")
    fwd = df[df["status"] == "FORWARD"].copy()
    fwd["actual_clean"] = pd.to_numeric(fwd["actual_gain_pct"], errors="coerce")
    fwd["pred_clean"] = pd.to_numeric(fwd["pred_gain_pct"], errors="coerce")
    fwd["gmp_clean"] = pd.to_numeric(fwd["gmp_pct_at_scoring"], errors="coerce")

    listed = fwd[fwd["actual_clean"].notna()].copy()
    n_listed = len(listed)

    model_mae_8 = float((listed["pred_clean"] - listed["actual_clean"]).abs().mean())

    with_gmp = listed[listed["gmp_clean"].notna()].copy()
    n_gmp = len(with_gmp)
    gmp_mae_7 = float((with_gmp["gmp_clean"] - with_gmp["actual_clean"]).abs().mean())
    model_mae_with_gmp_7 = float((with_gmp["pred_clean"] - with_gmp["actual_clean"]).abs().mean())

    no_bonfiglioli = listed[~listed["company"].str.contains("Bonfiglioli")]
    model_mae_no_outlier_7 = float((no_bonfiglioli["pred_clean"] - no_bonfiglioli["actual_clean"]).abs().mean())

    # Paras Healthcare specific metrics
    paras = listed[listed["company"].str.contains("Paras")].iloc[0]
    paras_pred = float(paras["pred_clean"])
    paras_gmp = float(paras["gmp_clean"])
    paras_act = float(paras["actual_clean"])
    paras_raw_act = float(paras["raw_actual_gain_pct"])

    paras_model_err_before = abs(paras_pred - paras_raw_act)
    paras_model_err_after = abs(paras_pred - paras_act)
    paras_gmp_err_before = abs(paras_gmp - paras_raw_act)
    paras_gmp_err_after = abs(paras_gmp - paras_act)

    print("=" * 70)
    print("  PHASE 15 RECOMPUTED HEADLINE METRICS (EFFECTIVE OUTCOMES)")
    print("=" * 70)
    print(f"Listed Forward IPOs (n)           : {n_listed}")
    print(f"Model MAE (n={n_listed})                     : {model_mae_8:.4f} pp ({model_mae_8:.2f} pp)")
    print(f"GMP MAE (n={n_gmp})                       : {gmp_mae_7:.4f} pp ({gmp_mae_7:.2f} pp)")
    print(f"Model MAE on GMP subset (n={n_gmp})        : {model_mae_with_gmp_7:.4f} pp ({model_mae_with_gmp_7:.2f} pp)")
    print(f"Model MAE excluding Bonfiglioli (n=7): {model_mae_no_outlier_7:.4f} pp ({model_mae_no_outlier_7:.2f} pp)")
    print("-" * 70)
    print(f"Paras Healthcare Actual (raw)     : {paras_raw_act:+.2f}%")
    print(f"Paras Healthcare Actual (eff)     : {paras_act:+.2f}%")
    print(f"Paras Healthcare Model Error Before: {paras_model_err_before:.2f} pp")
    print(f"Paras Healthcare Model Error After : {paras_model_err_after:.2f} pp")
    print(f"Paras Healthcare GMP Error Before  : {paras_gmp_err_before:.2f} pp")
    print(f"Paras Healthcare GMP Error After   : {paras_gmp_err_after:.2f} pp")
    print("=" * 70)

    return {
        "n_listed": n_listed,
        "model_mae_8": model_mae_8,
        "gmp_mae_7": gmp_mae_7,
        "model_mae_with_gmp_7": model_mae_with_gmp_7,
        "model_mae_no_outlier_7": model_mae_no_outlier_7,
        "paras_raw_act": paras_raw_act,
        "paras_act": paras_act,
        "paras_model_err_before": paras_model_err_before,
        "paras_model_err_after": paras_model_err_after,
        "paras_gmp_err_before": paras_gmp_err_before,
        "paras_gmp_err_after": paras_gmp_err_after,
    }


if __name__ == "__main__":
    compute_metrics()
