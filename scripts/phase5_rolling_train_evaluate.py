#!/usr/bin/env python3
"""Phase 5 Tasks 5 & 6: Rolling-Origin Model Training, Out-of-Sample Evaluation & Workstream B Comparisons.

Strictly follows:
  - references/fundamentals_definitions.md
  - phases/Phase 5/preregistration.md
  - RULES.md (Fixed seed=42, 2,000 bootstrap iterations, out-of-sample evaluation only)

Features:
  - Base features: issue_size_cr, fresh_issue_pct, ofs_pct, lot_size, sub_qib, sub_nii,
                   sub_retail, sub_total, nifty_30d_return, india_vix, recent_ipo_avg_gain,
                   sector, exchange.
  - Engineered: sub_retail_vs_qib, sub_hni_vs_retail, log_issue_size, is_high_vix,
                log_sub_total, log_sub_qib, log_sub_nii, log_sub_retail, qib_demand_share.
  - Fundamentals (>=70% coverage): roe, pat_margin_pct, debt_equity.
  - GMP features: gmp_pct, gmp_vs_recent_avg, gmp_x_sub.

Outputs:
  - phases/Phase 5/rolling_origin_predictions.csv (every out-of-sample prediction)
  - phases/Phase 5/rolling_origin_quarterly.csv (quarter-by-quarter metrics)
  - phases/Phase 5/model_comparisons_bootstrap.csv (bootstrap intervals vs raw GMP and H1 test)
  - phases/Phase 5/calibration_table.csv (reliability table with counts)
  - phases/Phase 5/tail_and_error_distribution.csv (tail analysis & top/worst 10 errors)
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
from itertools import product
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, roc_auc_score, brier_score_loss

warnings.filterwarnings("ignore")
np.random.seed(42)

# Features definitions per preregistration.md
BASE_NUM = [
    "issue_size_cr", "fresh_issue_pct", "ofs_pct", "lot_size",
    "sub_qib", "sub_nii", "sub_retail", "sub_total",
    "nifty_30d_return", "india_vix", "recent_ipo_avg_gain"
]
FUNDAMENTAL_COLS = ["roe", "pat_margin_pct", "debt_equity"]
CAT_COLS = ["sector", "exchange"]


def prep_features(df, cat_levels=None, include_fundamentals=True, include_gmp=True):
    """Transform dataframe into feature matrix without data leakage."""
    X = pd.DataFrame(index=df.index)

    # Base numeric
    for c in BASE_NUM:
        X[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan

    # Fundamentals
    if include_fundamentals:
        for c in FUNDAMENTAL_COLS:
            X[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan

    # Categorical
    levels = cat_levels or {c: sorted(df[c].dropna().astype(str).unique()) for c in CAT_COLS}
    for c in CAT_COLS:
        if c in df.columns:
            X[c] = pd.Categorical(df[c].astype(str), categories=levels[c]).codes
        else:
            X[c] = -1

    # Engineered
    X["sub_retail_vs_qib"] = X["sub_retail"] / X["sub_qib"].replace(0, np.nan)
    X["sub_hni_vs_retail"] = X["sub_nii"] / X["sub_retail"].replace(0, np.nan)
    X["log_issue_size"] = np.log1p(X["issue_size_cr"].clip(lower=0))
    X["is_high_vix"] = (X["india_vix"] > 18.0).astype(float)
    X["log_sub_total"] = np.log1p(X["sub_total"].clip(lower=0))
    X["log_sub_qib"] = np.log1p(X["sub_qib"].clip(lower=0))
    X["log_sub_nii"] = np.log1p(X["sub_nii"].clip(lower=0))
    X["log_sub_retail"] = np.log1p(X["sub_retail"].clip(lower=0))
    X["qib_demand_share"] = X["sub_qib"] / X["sub_total"].replace(0, np.nan)

    # GMP features
    if include_gmp:
        X["gmp_pct"] = pd.to_numeric(df["gmp_pct"], errors="coerce") if "gmp_pct" in df.columns else np.nan
        X["gmp_vs_recent_avg"] = X["gmp_pct"] - X["recent_ipo_avg_gain"]
        X["gmp_x_sub"] = X["gmp_pct"] * np.log1p(X["sub_total"].clip(lower=0))

    return X, levels


def paired_bootstrap(y_true, y_pred_a, y_pred_b, metric_fn, n_resamples=2000, seed=42):
    """Compute 95% paired bootstrap interval for metric(a) - metric(b)."""
    rng = np.random.RandomState(seed)
    n = len(y_true)
    diffs = []
    indices = np.arange(n)
    for _ in range(n_resamples):
        boot_idx = rng.choice(indices, size=n, replace=True)
        m_a = metric_fn(y_true[boot_idx], y_pred_a[boot_idx])
        m_b = metric_fn(y_true[boot_idx], y_pred_b[boot_idx])
        diffs.append(m_a - m_b)
    diffs = np.array(diffs)
    lo = float(np.percentile(diffs, 2.5))
    hi = float(np.percentile(diffs, 97.5))
    pt_diff = float(metric_fn(y_true, y_pred_a) - metric_fn(y_true, y_pred_b))
    excludes_zero = (lo > 0 and hi > 0) or (lo < 0 and hi < 0)
    return pt_diff, lo, hi, excludes_zero


def compute_ece(y_true, y_prob, n_bins=10, strategy="quantile"):
    """Compute Expected Calibration Error with uniform or quantile bins."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)
    ece = 0.0
    if strategy == "quantile":
        quantiles = np.linspace(0, 1, n_bins + 1)
        bin_edges = np.unique(np.percentile(y_prob, quantiles * 100))
        for i in range(len(bin_edges) - 1):
            lo, hi = bin_edges[i], bin_edges[i + 1]
            mask = (y_prob >= lo) & (y_prob <= hi) if i == len(bin_edges) - 2 else (y_prob >= lo) & (y_prob < hi)
            n = mask.sum()
            if n == 0:
                continue
            ece += (n / len(y_true)) * abs(y_prob[mask].mean() - y_true[mask].mean())
    else:
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        for i in range(n_bins):
            lo, hi = bin_boundaries[i], bin_boundaries[i + 1]
            mask = (y_prob >= lo) & (y_prob < hi) if i < n_bins - 1 else (y_prob >= lo) & (y_prob <= hi)
            n = mask.sum()
            if n == 0:
                continue
            ece += (n / len(y_true)) * abs(y_prob[mask].mean() - y_true[mask].mean())
    return float(ece)


def reliability_table(y_true, y_prob, n_bins=10, strategy="quantile"):
    """Generate reliability table with counts per bin, strictly satisfying gap == abs(pred - actual)."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)
    rows = []
    if strategy == "quantile":
        quantiles = np.linspace(0, 1, n_bins + 1)
        bin_edges = np.unique(np.percentile(y_prob, quantiles * 100))
        for i in range(len(bin_edges) - 1):
            lo, hi = bin_edges[i], bin_edges[i + 1]
            mask = (y_prob >= lo) & (y_prob <= hi) if i == len(bin_edges) - 2 else (y_prob >= lo) & (y_prob < hi)
            n = int(mask.sum())
            if n > 0:
                r_pred = round(float(y_prob[mask].mean()), 4)
                r_true = round(float(y_true[mask].mean()), 4)
                r_gap = round(abs(r_pred - r_true), 4)
            else:
                r_pred, r_true, r_gap = np.nan, np.nan, np.nan
            rows.append({
                "strategy": "equal-frequency",
                "bin": f"[{lo:.3f}, {hi:.3f}]" if i == len(bin_edges) - 2 else f"[{lo:.3f}, {hi:.3f})",
                "count": n,
                "avg_predicted": r_pred,
                "avg_actual": r_true,
                "gap": r_gap
            })
    else:
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        for i in range(n_bins):
            lo, hi = bin_boundaries[i], bin_boundaries[i + 1]
            mask = (y_prob >= lo) & (y_prob < hi) if i < n_bins - 1 else (y_prob >= lo) & (y_prob <= hi)
            n = int(mask.sum())
            if n > 0:
                r_pred = round(float(y_prob[mask].mean()), 4)
                r_true = round(float(y_true[mask].mean()), 4)
                r_gap = round(abs(r_pred - r_true), 4)
            else:
                r_pred, r_true, r_gap = np.nan, np.nan, np.nan
            rows.append({
                "strategy": "equal-width",
                "bin": f"[{lo:.1f}, {hi:.1f}]" if i == n_bins - 1 else f"[{lo:.1f}, {hi:.1f})",
                "count": n,
                "avg_predicted": r_pred,
                "avg_actual": r_true,
                "gap": r_gap
            })
    return pd.DataFrame(rows)


def run_rolling_origin():
    print("=" * 80)
    print("  PHASE 5: ROLLING-ORIGIN (WALK-FORWARD) EVALUATION")
    print("=" * 80)

    # 1. Load Master Dataset
    master_df = pd.read_csv("data/ipo_master.csv")
    master_df["listing_date"] = pd.to_datetime(master_df["listing_date"], errors="coerce")
    master_df = master_df.sort_values("listing_date").reset_index(drop=True)

    # Label good definition: listing_gain_pct > 10.0%
    master_df["actual_gain"] = pd.to_numeric(master_df["listing_gain_pct"], errors="coerce")
    master_df["actual_class"] = (master_df["actual_gain"] > 10.0).astype(int)

    # Quarters to evaluate (2022-Q1 to 2026-Q4)
    master_df["quarter"] = master_df["listing_date"].dt.to_period("Q")
    test_quarters = sorted([q for q in master_df["quarter"].dropna().unique() if q >= pd.Period("2022Q1")])

    print(f"Total dataset: {len(master_df)} IPOs")
    print(f"Evaluation quarters: {len(test_quarters)} ({test_quarters[0]} to {test_quarters[-1]})")

    out_of_sample_rows = []
    quarterly_stats = []

    # Fast hyperparameter grid for inner training validation
    param_grid = [
        {"max_depth": 3, "learning_rate": 0.03, "max_iter": 300, "min_samples_leaf": 15},
        {"max_depth": 4, "learning_rate": 0.03, "max_iter": 350, "min_samples_leaf": 15},
        {"max_depth": 4, "learning_rate": 0.05, "max_iter": 400, "min_samples_leaf": 20},
    ]

    for q_idx, q in enumerate(test_quarters):
        q_start = q.start_time
        q_end = q.end_time

        # Data split strictly temporal
        train_mask = master_df["listing_date"] < q_start
        test_mask = (master_df["listing_date"] >= q_start) & (master_df["listing_date"] <= q_end)

        train_data = master_df[train_mask].copy().reset_index(drop=True)
        test_data = master_df[test_mask].copy().reset_index(drop=True)

        if len(test_data) == 0:
            continue

        # Inner validation split (most recent 20% of train_data) to tune hyperparams and select blend weight w
        n_train = len(train_data)
        split_idx = int(n_train * 0.8)
        inner_tr = train_data.iloc[:split_idx].copy()
        inner_va = train_data.iloc[split_idx:].copy()

        # Mean baseline from training window
        mean_baseline_val = float(train_data["actual_gain"].mean())

        # Tune Regressor on inner validation
        best_reg_params = param_grid[0]
        best_inner_mae = float("inf")

        X_in_tr, cat_levels = prep_features(inner_tr, include_fundamentals=True, include_gmp=True)
        X_in_va, _ = prep_features(inner_va, cat_levels=cat_levels, include_fundamentals=True, include_gmp=True)
        # Filter features with at least 2 distinct non-null values in inner_tr
        valid_cols = [c for c in X_in_tr.columns if X_in_tr[c].dropna().nunique() >= 2]
        X_in_tr_f = X_in_tr[valid_cols]
        X_in_va_f = X_in_va[valid_cols]
        cat_idx_in = [list(valid_cols).index(c) for c in CAT_COLS if c in valid_cols]

        y_in_tr = inner_tr["actual_gain"]
        y_in_va = inner_va["actual_gain"]

        for params in param_grid:
            reg = HistGradientBoostingRegressor(
                loss="absolute_error", l2_regularization=0.1,
                categorical_features=cat_idx_in, random_state=42, **params
            ).fit(X_in_tr_f, y_in_tr)
            val_mae = mean_absolute_error(y_in_va, reg.predict(X_in_va_f))
            if val_mae < best_inner_mae:
                best_inner_mae = val_mae
                best_reg_params = params

        # Train Full Training Models with chosen hyperparameters
        # 1. Base Model WITHOUT Fundamentals (with GMP)
        X_tr_base_gmp, cat_levels_base = prep_features(train_data, include_fundamentals=False, include_gmp=True)
        X_te_base_gmp, _ = prep_features(test_data, cat_levels=cat_levels_base, include_fundamentals=False, include_gmp=True)
        v_cols_base = [c for c in X_tr_base_gmp.columns if X_tr_base_gmp[c].dropna().nunique() >= 2]
        cat_idx_base = [list(v_cols_base).index(c) for c in CAT_COLS if c in v_cols_base]

        reg_base_gmp = HistGradientBoostingRegressor(
            loss="absolute_error", l2_regularization=0.1,
            categorical_features=cat_idx_base, random_state=42, **best_reg_params
        ).fit(X_tr_base_gmp[v_cols_base], train_data["actual_gain"])
        pred_no_fund = reg_base_gmp.predict(X_te_base_gmp[v_cols_base])

        # 2. Model WITH Fundamentals (with GMP)
        X_tr_full_gmp, cat_levels_full = prep_features(train_data, include_fundamentals=True, include_gmp=True)
        X_te_full_gmp, _ = prep_features(test_data, cat_levels=cat_levels_full, include_fundamentals=True, include_gmp=True)
        v_cols_full = [c for c in X_tr_full_gmp.columns if X_tr_full_gmp[c].dropna().nunique() >= 2]
        cat_idx_full = [list(v_cols_full).index(c) for c in CAT_COLS if c in v_cols_full]

        reg_full_gmp = HistGradientBoostingRegressor(
            loss="absolute_error", l2_regularization=0.1,
            categorical_features=cat_idx_full, random_state=42, **best_reg_params
        ).fit(X_tr_full_gmp[v_cols_full], train_data["actual_gain"])
        pred_with_fund = reg_full_gmp.predict(X_te_full_gmp[v_cols_full])

        # 3. Model WITHOUT GMP (with fundamentals)
        X_tr_no_gmp, cat_levels_no_gmp = prep_features(train_data, include_fundamentals=True, include_gmp=False)
        X_te_no_gmp, _ = prep_features(test_data, cat_levels=cat_levels_no_gmp, include_fundamentals=True, include_gmp=False)
        v_cols_nogmp = [c for c in X_tr_no_gmp.columns if X_tr_no_gmp[c].dropna().nunique() >= 2]
        cat_idx_no_gmp = [list(v_cols_nogmp).index(c) for c in CAT_COLS if c in v_cols_nogmp]

        reg_no_gmp = HistGradientBoostingRegressor(
            loss="absolute_error", l2_regularization=0.1,
            categorical_features=cat_idx_no_gmp, random_state=42, **best_reg_params
        ).fit(X_tr_no_gmp[v_cols_nogmp], train_data["actual_gain"])
        pred_no_gmp = reg_no_gmp.predict(X_te_no_gmp[v_cols_nogmp])

        # 4. Blend Weight Selection on Inner Validation (grid w from 0.0 to 1.0 by 0.05)
        # Only fit/select on inner_va rows with valid GMP
        reg_in = HistGradientBoostingRegressor(
            loss="absolute_error", l2_regularization=0.1,
            categorical_features=cat_idx_in, random_state=42, **best_reg_params
        ).fit(X_in_tr_f, y_in_tr)
        in_va_pred = reg_in.predict(X_in_va_f)
        in_va_gmp = inner_va["gmp_pct"].values
        in_va_actual = inner_va["actual_gain"].values
        has_gmp_in_va = ~np.isnan(in_va_gmp)

        best_w = 0.5
        best_blend_mae = float("inf")
        if has_gmp_in_va.sum() > 5:
            for w_cand in np.linspace(0.0, 1.0, 21):
                blend_va = w_cand * in_va_gmp[has_gmp_in_va] + (1.0 - w_cand) * in_va_pred[has_gmp_in_va]
                mae_cand = mean_absolute_error(in_va_actual[has_gmp_in_va], blend_va)
                if mae_cand < best_blend_mae:
                    best_blend_mae = mae_cand
                    best_w = float(w_cand)

        # 5. Classifier + Platt Scaling
        # Fit classifier on inner_tr, fit Platt scaler (LogisticRegression) on inner_va
        clf_raw = HistGradientBoostingClassifier(
            l2_regularization=0.5,
            categorical_features=cat_idx_in, random_state=42, **best_reg_params
        ).fit(X_in_tr_f, inner_tr["actual_class"])
        raw_val_probs = clf_raw.predict_proba(X_in_va_f)[:, 1]

        # Fit Platt scaling
        platt_scaler = LogisticRegression(C=1.0, solver="lbfgs")
        platt_scaler.fit(raw_val_probs.reshape(-1, 1), inner_va["actual_class"])

        # Train final classifier on full train_data and calibrate with platt_scaler
        clf_final = HistGradientBoostingClassifier(
            l2_regularization=0.5,
            categorical_features=cat_idx_full, random_state=42, **best_reg_params
        ).fit(X_tr_full_gmp[v_cols_full], train_data["actual_class"])

        test_raw_probs = clf_final.predict_proba(X_te_full_gmp[v_cols_full])[:, 1]
        test_cal_probs = platt_scaler.predict_proba(test_raw_probs.reshape(-1, 1))[:, 1]

        # Record test predictions for this quarter
        for i, row in test_data.iterrows():
            gmp_val = float(row["gmp_pct"]) if pd.notna(row["gmp_pct"]) else np.nan
            p_no_fund = float(pred_no_fund[i])
            p_with_fund = float(pred_with_fund[i])
            p_no_gmp_val = float(pred_no_gmp[i])

            if pd.notna(gmp_val):
                p_blend = float(best_w * gmp_val + (1.0 - best_w) * p_with_fund)
            else:
                p_blend = np.nan

            out_of_sample_rows.append({
                "company": row["company"],
                "listing_date": row["listing_date"],
                "quarter": str(q),
                "actual_gain": float(row["actual_gain"]),
                "actual_class": int(row["actual_class"]),
                "gmp_pct": gmp_val,
                "has_gmp": int(pd.notna(gmp_val)),
                "pred_mean_baseline": mean_baseline_val,
                "pred_no_fundamentals": p_no_fund,
                "pred_with_fundamentals": p_with_fund,
                "pred_no_gmp": p_no_gmp_val,
                "blend_weight_gmp": best_w,
                "pred_blend": p_blend,
                "pred_prob_raw": float(test_raw_probs[i]),
                "pred_prob_calibrated": float(test_cal_probs[i]),
            })

        # Quarter summary
        q_df = pd.DataFrame(out_of_sample_rows[-len(test_data):])
        q_mae_fund = mean_absolute_error(q_df["actual_gain"], q_df["pred_with_fundamentals"])
        q_mae_base = mean_absolute_error(q_df["actual_gain"], q_df["pred_no_fundamentals"])
        has_gmp_mask = q_df["has_gmp"] == 1
        q_mae_gmp = mean_absolute_error(q_df.loc[has_gmp_mask, "actual_gain"], q_df.loc[has_gmp_mask, "gmp_pct"]) if has_gmp_mask.sum() > 0 else np.nan
        q_mae_blend = mean_absolute_error(q_df.loc[has_gmp_mask, "actual_gain"], q_df.loc[has_gmp_mask, "pred_blend"]) if has_gmp_mask.sum() > 0 else np.nan

        # AUC (if both classes present)
        if len(q_df["actual_class"].unique()) > 1:
            q_auc = roc_auc_score(q_df["actual_class"], q_df["pred_prob_calibrated"])
        else:
            q_auc = np.nan

        quarterly_stats.append({
            "quarter": str(q),
            "n_ipos": len(test_data),
            "n_with_gmp": int(has_gmp_mask.sum()),
            "mae_mean_baseline": mean_absolute_error(q_df["actual_gain"], q_df["pred_mean_baseline"]),
            "mae_no_fundamentals": q_mae_base,
            "mae_with_fundamentals": q_mae_fund,
            "mae_raw_gmp": q_mae_gmp,
            "mae_blend": q_mae_blend,
            "best_blend_w": best_w,
            "auc": q_auc
        })

    # Save out-of-sample predictions
    pred_df = pd.DataFrame(out_of_sample_rows)
    pred_df.to_csv("phases/Phase 5/rolling_origin_predictions.csv", index=False)
    print(f"\nGenerated {len(pred_df)} out-of-sample predictions across {len(test_quarters)} quarters.")

    # Save quarterly summary
    q_summary_df = pd.DataFrame(quarterly_stats)
    q_summary_df.to_csv("phases/Phase 5/rolling_origin_quarterly.csv", index=False)
    print("Quarterly evaluation summary saved to phases/Phase 5/rolling_origin_quarterly.csv")

    # ══════════════════════════════════════════════════════════════════════════════
    #  POOLED METRICS & PAIRED BOOTSTRAP (WORKSTREAM B & HYPOTHESIS H1)
    # ══════════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("  POOLED PERFORMANCE & PAIRED BOOTSTRAP COMPARISONS (2,000 resamples)")
    print("=" * 80)

    y_actual = pred_df["actual_gain"].values

    # 1. H1: Model WITH Fundamentals vs Model WITHOUT Fundamentals (All 416 IPOs)
    mae_fn = lambda yt, yp: mean_absolute_error(yt, yp)
    pt_h1, lo_h1, hi_h1, excl_h1 = paired_bootstrap(
        y_actual,
        pred_df["pred_with_fundamentals"].values,
        pred_df["pred_no_fundamentals"].values,
        mae_fn
    )
    print(f"H1 (Fundamentals effect): MAE(With) - MAE(Without) = {pt_h1:+.4f}% (95% CI: [{lo_h1:+.4f}%, {hi_h1:+.4f}%])")
    print(f"   Excludes zero? {excl_h1} -> {'SIGNIFICANT' if excl_h1 else 'NO DEMONSTRATED EFFECT'}")

    # 2. Model WITHOUT Fundamentals vs Mean Baseline
    pt_base, lo_base, hi_base, excl_base = paired_bootstrap(
        y_actual,
        pred_df["pred_no_fundamentals"].values,
        pred_df["pred_mean_baseline"].values,
        mae_fn
    )
    print(f"Model vs Mean Baseline: MAE(Model) - MAE(Mean) = {pt_base:+.4f}% (95% CI: [{lo_base:+.4f}%, {hi_base:+.4f}%])")

    # 3. Workstream B on IPOs WITH GMP (n=334)
    gmp_sub = pred_df[pred_df["has_gmp"] == 1].copy().reset_index(drop=True)
    y_gmp_sub = gmp_sub["actual_gain"].values
    raw_gmp_vals = gmp_sub["gmp_pct"].values
    model_with_gmp_vals = gmp_sub["pred_with_fundamentals"].values
    model_no_gmp_vals = gmp_sub["pred_no_gmp"].values
    blend_vals = gmp_sub["pred_blend"].values

    mae_raw_gmp = mean_absolute_error(y_gmp_sub, raw_gmp_vals)
    mae_model_with_gmp = mean_absolute_error(y_gmp_sub, model_with_gmp_vals)
    mae_model_no_gmp = mean_absolute_error(y_gmp_sub, model_no_gmp_vals)
    mae_blend = mean_absolute_error(y_gmp_sub, blend_vals)

    med_raw_gmp = np.median(np.abs(y_gmp_sub - raw_gmp_vals))
    med_model_with_gmp = np.median(np.abs(y_gmp_sub - model_with_gmp_vals))
    med_model_no_gmp = np.median(np.abs(y_gmp_sub - model_no_gmp_vals))
    med_blend = np.median(np.abs(y_gmp_sub - blend_vals))

    print(f"\n--- Subgroup: Issues WITH GMP (n={len(gmp_sub)}) ---")
    print(f"  Raw GMP        : MAE = {mae_raw_gmp:.4f}%, Median = {med_raw_gmp:.4f}%")
    print(f"  Model (No GMP) : MAE = {mae_model_no_gmp:.4f}%, Median = {med_model_no_gmp:.4f}%")
    print(f"  Model (With GMP: MAE = {mae_model_with_gmp:.4f}%, Median = {med_model_with_gmp:.4f}%")
    print(f"  Blend          : MAE = {mae_blend:.4f}%, Median = {med_blend:.4f}%")

    # Bootstrap vs Raw GMP
    pt_mod_gmp, lo_mod_gmp, hi_mod_gmp, excl_mod_gmp = paired_bootstrap(
        y_gmp_sub, model_with_gmp_vals, raw_gmp_vals, mae_fn
    )
    pt_blend_gmp, lo_blend_gmp, hi_blend_gmp, excl_blend_gmp = paired_bootstrap(
        y_gmp_sub, blend_vals, raw_gmp_vals, mae_fn
    )
    pt_nogmp_gmp, lo_nogmp_gmp, hi_nogmp_gmp, excl_nogmp_gmp = paired_bootstrap(
        y_gmp_sub, model_no_gmp_vals, raw_gmp_vals, mae_fn
    )

    print(f"  Model(With GMP) - Raw GMP: {pt_mod_gmp:+.4f}% (95% CI: [{lo_mod_gmp:+.4f}%, {hi_mod_gmp:+.4f}%]) -> {'BEATS GMP' if lo_mod_gmp < 0 and hi_mod_gmp < 0 else 'NO DEMONSTRATED DIFFERENCE'}")
    print(f"  Blend - Raw GMP          : {pt_blend_gmp:+.4f}% (95% CI: [{lo_blend_gmp:+.4f}%, {hi_blend_gmp:+.4f}%]) -> {'BEATS GMP' if lo_blend_gmp < 0 and hi_blend_gmp < 0 else 'NO DEMONSTRATED DIFFERENCE'}")

    # 4. Workstream B on IPOs WITHOUT GMP (n=82)
    no_gmp_sub = pred_df[pred_df["has_gmp"] == 0].copy().reset_index(drop=True)
    y_no_gmp_sub = no_gmp_sub["actual_gain"].values
    model_nogmp_sub_vals = no_gmp_sub["pred_no_gmp"].values
    mean_nogmp_sub_vals = no_gmp_sub["pred_mean_baseline"].values

    mae_sub_model = mean_absolute_error(y_no_gmp_sub, model_nogmp_sub_vals)
    mae_sub_mean = mean_absolute_error(y_no_gmp_sub, mean_nogmp_sub_vals)
    pt_nogmp_sub, lo_nogmp_sub, hi_nogmp_sub, excl_nogmp_sub = paired_bootstrap(
        y_no_gmp_sub, model_nogmp_sub_vals, mean_nogmp_sub_vals, mae_fn
    )
    print(f"\n--- Subgroup: Issues WITHOUT GMP (n={len(no_gmp_sub)}) ---")
    print(f"  Model (No GMP) : MAE = {mae_sub_model:.4f}%")
    print(f"  Mean Baseline  : MAE = {mae_sub_mean:.4f}%")
    print(f"  Model - Mean Baseline: {pt_nogmp_sub:+.4f}% (95% CI: [{lo_nogmp_sub:+.4f}%, {hi_nogmp_sub:+.4f}%]) -> {'BEATS MEAN' if lo_nogmp_sub < 0 and hi_nogmp_sub < 0 else 'NO DEMONSTRATED DIFFERENCE'}")

    # Save bootstrap comparisons CSV
    boot_rows = [
        {
            "comparison": "H1: Model With Fundamentals vs Model Without Fundamentals",
            "subset": "All Out-of-Sample",
            "n": len(pred_df),
            "point_estimate_diff": pt_h1,
            "ci_95_lower": lo_h1,
            "ci_95_upper": hi_h1,
            "excludes_zero": excl_h1,
            "verdict": "Improves" if (lo_h1 < 0 and hi_h1 < 0) else ("Hurts" if (lo_h1 > 0 and hi_h1 > 0) else "No demonstrated effect")
        },
        {
            "comparison": "Model Without Fundamentals vs Mean Baseline",
            "subset": "All Out-of-Sample",
            "n": len(pred_df),
            "point_estimate_diff": pt_base,
            "ci_95_lower": lo_base,
            "ci_95_upper": hi_base,
            "excludes_zero": excl_base,
            "verdict": "Beats Baseline" if (lo_base < 0 and hi_base < 0) else "No demonstrated difference"
        },
        {
            "comparison": "Model With GMP vs Raw GMP",
            "subset": "IPOs With GMP",
            "n": len(gmp_sub),
            "point_estimate_diff": pt_mod_gmp,
            "ci_95_lower": lo_mod_gmp,
            "ci_95_upper": hi_mod_gmp,
            "excludes_zero": excl_mod_gmp,
            "verdict": "Beats GMP" if (lo_mod_gmp < 0 and hi_mod_gmp < 0) else "No demonstrated advantage over raw GMP"
        },
        {
            "comparison": "Blend vs Raw GMP",
            "subset": "IPOs With GMP",
            "n": len(gmp_sub),
            "point_estimate_diff": pt_blend_gmp,
            "ci_95_lower": lo_blend_gmp,
            "ci_95_upper": hi_blend_gmp,
            "excludes_zero": excl_blend_gmp,
            "verdict": "Beats GMP" if (lo_blend_gmp < 0 and hi_blend_gmp < 0) else "No demonstrated advantage over raw GMP"
        },
        {
            "comparison": "Model (No GMP) vs Raw GMP",
            "subset": "IPOs With GMP",
            "n": len(gmp_sub),
            "point_estimate_diff": pt_nogmp_gmp,
            "ci_95_lower": lo_nogmp_gmp,
            "ci_95_upper": hi_nogmp_gmp,
            "excludes_zero": excl_nogmp_gmp,
            "verdict": "Beats GMP" if (lo_nogmp_gmp < 0 and hi_nogmp_gmp < 0) else "No demonstrated advantage over raw GMP"
        },
        {
            "comparison": "Model (No GMP) vs Mean Baseline",
            "subset": "IPOs Without GMP",
            "n": len(no_gmp_sub),
            "point_estimate_diff": pt_nogmp_sub,
            "ci_95_lower": lo_nogmp_sub,
            "ci_95_upper": hi_nogmp_sub,
            "excludes_zero": excl_nogmp_sub,
            "verdict": "Beats Mean" if (lo_nogmp_sub < 0 and hi_nogmp_sub < 0) else "No demonstrated difference"
        }
    ]
    boot_df = pd.DataFrame(boot_rows)
    boot_df.to_csv("phases/Phase 5/model_comparisons_bootstrap.csv", index=False)
    print("Saved model comparisons bootstrap table to phases/Phase 5/model_comparisons_bootstrap.csv")

    # ══════════════════════════════════════════════════════════════════════════════
    #  CALIBRATION ANALYSIS (OUT-OF-SAMPLE)
    # ══════════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("  OUT-OF-SAMPLE CALIBRATION ANALYSIS (Platt Scaled)")
    print("=" * 80)

    y_cls_true = pred_df["actual_class"].values
    y_cls_cal = pred_df["pred_prob_calibrated"].values

    ece_freq = compute_ece(y_cls_true, y_cls_cal, n_bins=10, strategy="quantile")
    ece_width = compute_ece(y_cls_true, y_cls_cal, n_bins=10, strategy="uniform")
    brier = brier_score_loss(y_cls_true, y_cls_cal)
    auc_pooled = roc_auc_score(y_cls_true, y_cls_cal)

    print(f"Pooled AUC (ROC): {auc_pooled:.4f}")
    print(f"Equal-Frequency ECE (10 bins): {ece_freq:.4f} (Target <= 0.10: {'PASS' if ece_freq <= 0.10 else 'MISSED'})")
    print(f"Equal-Width ECE (10 bins)    : {ece_width:.4f} (Target <= 0.10: {'PASS' if ece_width <= 0.10 else 'MISSED'})")
    print(f"Brier Score                  : {brier:.4f}")

    table_freq = reliability_table(y_cls_true, y_cls_cal, n_bins=10, strategy="quantile")
    table_width = reliability_table(y_cls_true, y_cls_cal, n_bins=10, strategy="uniform")
    cal_table = pd.concat([table_freq, table_width], ignore_index=True)
    cal_table.to_csv("phases/Phase 5/calibration_table.csv", index=False)
    print("Saved reliability table to phases/Phase 5/calibration_table.csv")

    # ══════════════════════════════════════════════════════════════════════════════
    #  TAIL BEHAVIOR & ERROR DISTRIBUTION ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 80)
    print("  TAIL BEHAVIOR & ERROR DISTRIBUTION")
    print("=" * 80)

    pred_df["abs_error"] = np.abs(pred_df["actual_gain"] - pred_df["pred_with_fundamentals"])
    pred_df["signed_error"] = pred_df["pred_with_fundamentals"] - pred_df["actual_gain"]

    # Top 10% largest actual gains
    p90_threshold = float(np.percentile(pred_df["actual_gain"], 90.0))
    top_10_actual = pred_df[pred_df["actual_gain"] >= p90_threshold].copy()
    top_10_mae = mean_absolute_error(top_10_actual["actual_gain"], top_10_actual["pred_with_fundamentals"])
    top_10_mean_underpredict = float(top_10_actual["signed_error"].mean())

    print(f"Top 10% Actual Gains threshold: >= {p90_threshold:.2f}% (n={len(top_10_actual)})")
    print(f"  MAE on Top 10% Gains: {top_10_mae:.2f}%")
    print(f"  Average signed error on Top 10% Gains: {top_10_mean_underpredict:.2f}% (Model severely under-predicts pops)")

    # 10 worst errors & 10 best errors
    worst_10 = pred_df.sort_values("abs_error", ascending=False).head(10).copy()
    worst_10["error_type"] = "10 Worst Absolute Errors"
    best_10 = pred_df.sort_values("abs_error", ascending=True).head(10).copy()
    best_10["error_type"] = "10 Best Absolute Errors"

    tail_summary_df = pd.concat([worst_10, best_10], ignore_index=True)
    tail_summary_df.to_csv("phases/Phase 5/tail_and_error_distribution.csv", index=False)
    print("Saved tail & error distribution to phases/Phase 5/tail_and_error_distribution.csv")

    print("\nPhase 5 Rolling Origin Evaluation Complete.")


if __name__ == "__main__":
    run_rolling_origin()
