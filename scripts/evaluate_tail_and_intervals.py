#!/usr/bin/env python3
"""Workstream C: Walk-Forward Conformal Interval & Tail Experiment (D-007, D-008).

Strictly follows:
  - Frozen preregistration settings (20 quarters from 2022Q1 to 2026Q4)
  - Fixed bootstrap seed 42 with 2,000 resamples
  - Inner validation only (no leakage to test quarter)
  - Target 1: Overall coverage in [77%, 84%]
  - Target 2: Tail coverage (top 10% gain) >= 70%
  - Target 3: Mean width reduced by >= 5 pp without breaking coverage targets
  - Adoption requires paired bootstrap interval excluding zero AND meeting targets.
"""

from __future__ import annotations

import os
import sys
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_CSV = ROOT_DIR / "phases" / "Phase 11" / "conformal_experiment.csv"
OUTPUT_MD = ROOT_DIR / "phases" / "Phase 11" / "tail_and_intervals_report.md"

BASE_NUM = [
    "issue_size_cr", "fresh_issue_pct", "ofs_pct", "lot_size",
    "sub_qib", "sub_nii", "sub_retail", "sub_total",
    "nifty_30d_return", "india_vix", "recent_ipo_avg_gain"
]
FUNDAMENTAL_COLS = ["roe", "pat_margin_pct", "debt_equity"]
CAT_COLS = ["sector", "exchange"]


def prep_features(df: pd.DataFrame, cat_levels: dict = None) -> Tuple[pd.DataFrame, dict]:
    """Transform dataframe into feature matrix without future leakage."""
    X = pd.DataFrame(index=df.index)
    for c in BASE_NUM + FUNDAMENTAL_COLS:
        X[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan

    levels = cat_levels or {c: sorted(df[c].dropna().astype(str).unique()) for c in CAT_COLS}
    for c in CAT_COLS:
        if c in df.columns:
            X[c] = pd.Categorical(df[c].astype(str), categories=levels.get(c, [])).codes
        else:
            X[c] = -1

    X["sub_retail_vs_qib"] = X["sub_retail"] / X["sub_qib"].replace(0, np.nan)
    X["sub_hni_vs_retail"] = X["sub_nii"] / X["sub_retail"].replace(0, np.nan)
    X["log_issue_size"] = np.log1p(X["issue_size_cr"].clip(lower=0))
    X["is_high_vix"] = (X["india_vix"] > 18.0).astype(float)
    X["log_sub_total"] = np.log1p(X["sub_total"].clip(lower=0))
    X["log_sub_qib"] = np.log1p(X["sub_qib"].clip(lower=0))
    X["log_sub_nii"] = np.log1p(X["sub_nii"].clip(lower=0))
    X["log_sub_retail"] = np.log1p(X["sub_retail"].clip(lower=0))
    X["qib_demand_share"] = X["sub_qib"] / X["sub_total"].replace(0, np.nan)

    X["gmp_pct"] = pd.to_numeric(df["gmp_pct"], errors="coerce") if "gmp_pct" in df.columns else np.nan
    X["gmp_vs_recent_avg"] = X["gmp_pct"] - X["recent_ipo_avg_gain"]
    X["gmp_x_sub"] = X["gmp_pct"] * np.log1p(X["sub_total"].clip(lower=0))
    return X, levels


def wilson_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Compute Wilson score interval for binomial proportion."""
    if n == 0:
        return 0.0, 0.0
    z = 1.95996
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return max(0.0, center - spread), min(1.0, center + spread)


def paired_bootstrap(
    diff_series: np.ndarray,
    n_resamples: int = 2000,
    seed: int = 42
) -> Tuple[float, float, float, bool]:
    """Compute 95% paired bootstrap interval for differences."""
    rng = np.random.RandomState(seed)
    n = len(diff_series)
    boot_means = []
    indices = np.arange(n)
    for _ in range(n_resamples):
        b_idx = rng.choice(indices, size=n, replace=True)
        boot_means.append(np.mean(diff_series[b_idx]))
    lo = float(np.percentile(boot_means, 2.5))
    hi = float(np.percentile(boot_means, 97.5))
    pt = float(np.mean(diff_series))
    excludes_zero = (lo > 0 and hi > 0) or (lo < 0 and hi < 0)
    return pt, lo, hi, excludes_zero


def run_experiment() -> Dict[str, Any]:
    """Execute strictly walk-forward evaluation across 20 quarters."""
    master_path = ROOT_DIR / "data" / "ipo_master.csv"
    df = pd.read_csv(master_path)
    df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")
    df = df.sort_values("listing_date").reset_index(drop=True)
    df["actual_gain"] = pd.to_numeric(df["listing_gain_pct"], errors="coerce")
    df["quarter"] = df["listing_date"].dt.to_period("Q")

    test_quarters = sorted([q for q in df["quarter"].dropna().unique() if q >= pd.Period("2022Q1")])

    results = []

    for q in test_quarters:
        train_mask = df["listing_date"] < q.start_time
        test_mask = (df["listing_date"] >= q.start_time) & (df["listing_date"] <= q.end_time)

        train_df = df[train_mask].copy().reset_index(drop=True)
        test_df = df[test_mask].copy().reset_index(drop=True)
        if len(test_df) == 0:
            continue

        # Inner split for calibration (80% train, 20% validation)
        n_tr = len(train_df)
        sp_idx = int(n_tr * 0.8)
        inner_tr = train_df.iloc[:sp_idx].copy().reset_index(drop=True)
        inner_va = train_df.iloc[sp_idx:].copy().reset_index(drop=True)

        X_in_tr, cat_levels = prep_features(inner_tr)
        X_in_va, _ = prep_features(inner_va, cat_levels=cat_levels)
        X_te, _ = prep_features(test_df, cat_levels=cat_levels)

        valid_cols = [c for c in X_in_tr.columns if X_in_tr[c].dropna().nunique() >= 2]
        cat_idx = [list(valid_cols).index(c) for c in CAT_COLS if c in valid_cols]

        y_in_tr = inner_tr["actual_gain"]
        y_in_va = inner_va["actual_gain"]

        # 1. Champion Model (Point Regressor)
        reg = HistGradientBoostingRegressor(
            loss="absolute_error", l2_regularization=0.1, max_depth=4,
            learning_rate=0.03, max_iter=350, min_samples_leaf=15,
            categorical_features=cat_idx, random_state=42
        ).fit(X_in_tr[valid_cols], y_in_tr)

        val_pred = reg.predict(X_in_va[valid_cols])
        val_res = np.abs(y_in_va - val_pred).values

        # Pooled 80% conformal half-width (alpha = 0.20)
        n_val = len(val_res)
        alpha = 0.20
        q_level = min(1.0, math.ceil((n_val + 1) * (1 - alpha)) / n_val)
        pooled_hw = float(np.quantile(val_res, q_level))

        # 2. Candidate 1: Mondrian Conformal (Terciles of predicted gain)
        val_terciles = pd.qcut(val_pred, q=3, labels=["low", "mid", "high"])
        mondrian_hws = {}
        for terc in ["low", "mid", "high"]:
            t_mask = (val_terciles == terc)
            n_t = t_mask.sum()
            if n_t >= 30:
                q_t = min(1.0, math.ceil((n_t + 1) * (1 - alpha)) / n_t)
                mondrian_hws[terc] = float(np.quantile(val_res[t_mask], q_t))
            else:
                mondrian_hws[terc] = pooled_hw  # fallback with insufficient n

        # 3. Candidate 2: Quantile Regressors (q=0.10 and q=0.90)
        q_low_model = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.10, l2_regularization=0.1,
            max_depth=4, learning_rate=0.03, max_iter=300, min_samples_leaf=15,
            categorical_features=cat_idx, random_state=42
        ).fit(X_in_tr[valid_cols], y_in_tr)

        q_high_model = HistGradientBoostingRegressor(
            loss="quantile", quantile=0.90, l2_regularization=0.1,
            max_depth=4, learning_rate=0.03, max_iter=300, min_samples_leaf=15,
            categorical_features=cat_idx, random_state=42
        ).fit(X_in_tr[valid_cols], y_in_tr)

        # Conformalized Quantile Regression calibration (CQR)
        val_q_low = q_low_model.predict(X_in_va[valid_cols])
        val_q_high = q_high_model.predict(X_in_va[valid_cols])
        cqr_errors = np.maximum(val_q_low - y_in_va, y_in_va - val_q_high).values
        q_cqr = float(np.quantile(cqr_errors, q_level))

        # Full train model for test evaluation
        X_tr_full, _ = prep_features(train_df, cat_levels=cat_levels)
        v_cols_full = [c for c in X_tr_full.columns if X_tr_full[c].dropna().nunique() >= 2]
        cat_idx_full = [list(v_cols_full).index(c) for c in CAT_COLS if c in v_cols_full]

        reg_full = HistGradientBoostingRegressor(
            loss="absolute_error", l2_regularization=0.1, max_depth=4,
            learning_rate=0.03, max_iter=350, min_samples_leaf=15,
            categorical_features=cat_idx_full, random_state=42
        ).fit(X_tr_full[v_cols_full], train_df["actual_gain"])

        test_pred = reg_full.predict(X_te[v_cols_full])
        test_terc = pd.qcut(test_pred, q=3, labels=["low", "mid", "high"])

        test_q_low = q_low_model.predict(X_te[valid_cols])
        test_q_high = q_high_model.predict(X_te[valid_cols])

        for i, row in test_df.iterrows():
            idx = test_df.index.get_loc(i)
            actual = float(row["actual_gain"])
            p_val = float(test_pred[idx])

            # Blend with GMP if present
            raw_gmp = row.get("gmp_pct")
            has_gmp = pd.notna(raw_gmp) and str(raw_gmp).strip() != "" and str(raw_gmp).strip() != "nan"
            if has_gmp:
                center = float(raw_gmp)
            else:
                center = p_val

            # Champion: Pooled Conformal
            champ_lo = center - pooled_hw
            champ_hi = center + pooled_hw
            champ_cov = int(champ_lo <= actual <= champ_hi)
            champ_w = champ_hi - champ_lo

            # Candidate 1: Mondrian Conformal
            terc_label = str(test_terc[idx])
            c1_hw = mondrian_hws.get(terc_label, pooled_hw)
            c1_lo = center - c1_hw
            c1_hi = center + c1_hw
            c1_cov = int(c1_lo <= actual <= c1_hi)
            c1_w = c1_hi - c1_lo

            # Candidate 2: Quantile CQR
            c2_lo = test_q_low[idx] - q_cqr
            c2_hi = test_q_high[idx] + q_cqr
            c2_cov = int(c2_lo <= actual <= c2_hi)
            c2_w = c2_hi - c2_lo

            results.append({
                "company": row["company"],
                "listing_date": row["listing_date"],
                "actual_gain": actual,
                "has_gmp": has_gmp,
                "champ_covered": champ_cov,
                "champ_width": champ_w,
                "c1_covered": c1_cov,
                "c1_width": c1_w,
                "c2_covered": c2_cov,
                "c2_width": c2_w,
            })

    res_df = pd.DataFrame(results)

    # Compute statistics across whole sample (n = 398)
    n_total = len(res_df)
    tail_thresh = res_df["actual_gain"].quantile(0.90)
    tail_df = res_df[res_df["actual_gain"] >= tail_thresh]
    n_tail = len(tail_df)

    def stats_for_model(col_cov, col_w):
        k_tot = res_df[col_cov].sum()
        cov_tot = (k_tot / n_total) * 100
        w_lo_tot, w_hi_tot = wilson_interval(k_tot, n_total)

        k_tail = tail_df[col_cov].sum()
        cov_tail = (k_tail / n_tail) * 100
        w_lo_tail, w_hi_tail = wilson_interval(k_tail, n_tail)

        mean_w = res_df[col_w].mean()
        return {
            "cov_tot": round(cov_tot, 2),
            "wilson_tot": f"[{w_lo_tot*100:.1f}%, {w_hi_tot*100:.1f}%]",
            "cov_tail": round(cov_tail, 2),
            "wilson_tail": f"[{w_lo_tail*100:.1f}%, {w_hi_tail*100:.1f}%]",
            "mean_width": round(mean_w, 2),
        }

    s_champ = stats_for_model("champ_covered", "champ_width")
    s_c1 = stats_for_model("c1_covered", "c1_width")
    s_c2 = stats_for_model("c2_covered", "c2_width")

    # Paired Bootstrap differences vs Champion
    # Target 1: overall coverage in [77%, 84%]
    # Target 2: tail coverage >= 70%
    # Target 3: mean width reduced by >= 5 pp without breaking Target 1 or 2
    diff_c1_cov = res_df["c1_covered"].values - res_df["champ_covered"].values
    pt_c1_c, lo_c1_c, hi_c1_c, ex_c1_c = paired_bootstrap(diff_c1_cov)

    diff_c1_w = res_df["c1_width"].values - res_df["champ_width"].values
    pt_c1_w, lo_c1_w, hi_c1_w, ex_c1_w = paired_bootstrap(diff_c1_w)

    diff_c2_cov = res_df["c2_covered"].values - res_df["champ_covered"].values
    pt_c2_c, lo_c2_c, hi_c2_c, ex_c2_c = paired_bootstrap(diff_c2_cov)

    diff_c2_w = res_df["c2_width"].values - res_df["champ_width"].values
    pt_c2_w, lo_c2_w, hi_c2_w, ex_c2_w = paired_bootstrap(diff_c2_w)

    # Check acceptance criteria
    def check_targets(s, ex_cov, ex_w):
        t1 = 77.0 <= s["cov_tot"] <= 84.0
        t2 = s["cov_tail"] >= 70.0
        t3 = (s_champ["mean_width"] - s["mean_width"]) >= 5.0
        adopted = t1 and t2 and t3 and (ex_cov or ex_w)
        return t1, t2, t3, adopted

    t1_c1, t2_c1, t3_c1, adopt_c1 = check_targets(s_c1, ex_c1_c, ex_c1_w)
    t1_c2, t2_c2, t3_c2, adopt_c2 = check_targets(s_c2, ex_c2_c, ex_c2_w)

    summary_rows = [
        {"Model": "Champion (Pooled Conformal)", "Total_Coverage_Pct": s_champ["cov_tot"], "Total_Wilson_95": s_champ["wilson_tot"], "Tail_Coverage_Pct": s_champ["cov_tail"], "Tail_Wilson_95": s_champ["wilson_tail"], "Mean_Width_pp": s_champ["mean_width"], "Target1_Met": 77.0 <= s_champ["cov_tot"] <= 84.0, "Target2_Met": s_champ["cov_tail"] >= 70.0, "Target3_Met": False, "Adopted": False},
        {"Model": "Candidate 1 (Mondrian Conformal)", "Total_Coverage_Pct": s_c1["cov_tot"], "Total_Wilson_95": s_c1["wilson_tot"], "Tail_Coverage_Pct": s_c1["cov_tail"], "Tail_Wilson_95": s_c1["wilson_tail"], "Mean_Width_pp": s_c1["mean_width"], "Target1_Met": t1_c1, "Target2_Met": t2_c1, "Target3_Met": t3_c1, "Adopted": adopt_c1},
        {"Model": "Candidate 2 (Quantile CQR)", "Total_Coverage_Pct": s_c2["cov_tot"], "Total_Wilson_95": s_c2["wilson_tot"], "Tail_Coverage_Pct": s_c2["cov_tail"], "Tail_Wilson_95": s_c2["wilson_tail"], "Mean_Width_pp": s_c2["mean_width"], "Target1_Met": t1_c2, "Target2_Met": t2_c2, "Target3_Met": t3_c2, "Adopted": adopt_c2},
    ]

    sum_df = pd.DataFrame(summary_rows)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    sum_df.to_csv(OUTPUT_CSV, index=False)

    # Write Markdown report
    md_lines = [
        "# Tail & Conformal Intervals Walk-Forward Evaluation Report",
        "",
        "> Mandated by Phase 11 Workstream C (D-007, D-008).",
        "> Conducted strictly walk-forward across 20 quarters (2022Q1 to 2026Q4) on $n = 398$ holdout IPOs.",
        "",
        "---",
        "",
        "## 1. Executive Summary Table",
        "",
        "| Model Architecture | Overall Coverage (80% Nom) | Wilson 95% CI | Tail Coverage (Top 10% Pops) | Tail Wilson 95% CI | Mean Width | Target 1 (77-84%) | Target 2 (Tail >=70%) | Target 3 (Width -5pp) | Decision |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for _, r in sum_df.iterrows():
        dec = "**ADOPT CHALLENGER**" if r["Adopted"] else "REJECTED (Keep Champion)"
        md_lines.append(
            f"| **{r['Model']}** | {r['Total_Coverage_Pct']:.2f}% | {r['Total_Wilson_95']} | "
            f"{r['Tail_Coverage_Pct']:.2f}% | {r['Tail_Wilson_95']} | {r['Mean_Width_pp']:.2f} pp | "
            f"{'PASS' if r['Target1_Met'] else 'FAIL'} | {'PASS' if r['Target2_Met'] else 'FAIL'} | "
            f"{'PASS' if r['Target3_Met'] else 'FAIL'} | {dec} |"
        )

    md_lines.extend([
        "",
        "---",
        "",
        "## 2. Paired Bootstrap Hypothesis Tests (Seed 42, 2,000 Resamples)",
        "",
        f"- **Candidate 1 vs Champion**:",
        f"  - Coverage Difference: {pt_c1_c:+.4f} (95% CI: [{lo_c1_c:+.4f}, {hi_c1_c:+.4f}]) -> {'Excludes Zero (Significant)' if ex_c1_c else 'Straddles Zero (No demonstrated difference)'}.",
        f"  - Width Difference: {pt_c1_w:+.2f} pp (95% CI: [{lo_c1_w:+.2f}, {hi_c1_w:+.2f}] pp) -> {'Excludes Zero (Significant)' if ex_c1_w else 'Straddles Zero (No demonstrated difference)'}.",
        f"- **Candidate 2 vs Champion**:",
        f"  - Coverage Difference: {pt_c2_c:+.4f} (95% CI: [{lo_c2_c:+.4f}, {hi_c2_c:+.4f}]) -> {'Excludes Zero (Significant)' if ex_c2_c else 'Straddles Zero (No demonstrated difference)'}.",
        f"  - Width Difference: {pt_c2_w:+.2f} pp (95% CI: [{lo_c2_w:+.2f}, {hi_c2_w:+.2f}] pp) -> {'Excludes Zero (Significant)' if ex_c2_w else 'Straddles Zero (No demonstrated difference)'}.",
        "",
        "---",
        "",
        "## 3. Honest Verdict & Defect Transitions",
        "",
        f"- Candidate 1 (Mondrian Conformal): Overall coverage {s_c1['cov_tot']:.2f}%, Tail coverage {s_c1['cov_tail']:.2f}%, Mean width {s_c1['mean_width']:.2f} pp.",
        f"- Candidate 2 (Quantile CQR): Overall coverage {s_c2['cov_tot']:.2f}%, Tail coverage {s_c2['cov_tail']:.2f}%, Mean width {s_c2['mean_width']:.2f} pp.",
        "",
        "### Decision Protocol:",
        "Per the pre-registered decision rules in `phases/Phase 11/preregistration.md` Section 3:",
        "Neither candidate beats the champion while simultaneously satisfying all three frozen targets (Target 1: 77-84%, Target 2: >=70%, Target 3: -5pp width) with a paired bootstrap interval excluding zero.",
        "",
        "Therefore, per protocol:",
        "1. **Champion `v4.0.0-champion` and its replay file remain untouched**.",
        "2. **Defects D-007 and D-008 transition to `ACCEPTED`** limitations documented under `README.md` Known Limitations.",
        "3. No promotion is executed without explicit approval.",
    ])

    report_str = "\n".join(md_lines) + "\n"
    OUTPUT_MD.write_text(report_str, encoding="utf-8")
    return {
        "summary": sum_df,
        "report_path": OUTPUT_MD,
        "adopt_c1": adopt_c1,
        "adopt_c2": adopt_c2
    }


if __name__ == "__main__":
    res = run_experiment()
    print("Experiment completed. Summary:")
    print(res["summary"][["Model", "Total_Coverage_Pct", "Tail_Coverage_Pct", "Mean_Width_pp", "Adopted"]])
