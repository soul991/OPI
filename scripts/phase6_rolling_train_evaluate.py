#!/usr/bin/env python3
"""Phase 6: Rolling-Origin Model Training, Out-of-Sample Evaluation, Conformal Intervals & Bootstrap Inference.

Strictly follows:
  - RULES.md (Fixed seed=42, 2,000 bootstrap iterations, out-of-sample evaluation only)
  - references/inclusion_criteria.md (Evaluated strictly on cleaned master data)
  - phases/Phase 6/preregistration.md (Pre-registered conformal intervals, metrics, bootstrap rules)

Features:
  - Base features: issue_size_cr, fresh_issue_pct, ofs_pct, lot_size, sub_qib, sub_nii,
                   sub_retail, sub_total, nifty_30d_return, india_vix, recent_ipo_avg_gain,
                   sector, exchange.
  - Engineered: sub_retail_vs_qib, sub_hni_vs_retail, log_issue_size, is_high_vix,
                log_sub_total, log_sub_qib, log_sub_nii, log_sub_retail, qib_demand_share.
  - Fundamentals (>=70% coverage): roe, pat_margin_pct, debt_equity.
  - GMP features: gmp_pct, gmp_vs_recent_avg, gmp_x_sub.

Outputs:
  - phases/Phase 6/rolling_origin_predictions.csv
  - phases/Phase 6/rolling_origin_quarterly.csv (quarters n>=20 or half-year buckets)
  - phases/Phase 6/model_comparisons_bootstrap.csv
  - phases/Phase 6/calibration_table.csv (with Wilson 95% intervals)
  - phases/Phase 6/conformal_intervals_coverage.csv
  - phases/Phase 6/tail_and_error_distribution.csv
  - phases/Phase 6/before_after_comparison.csv
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
from math import sqrt
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, roc_auc_score, brier_score_loss

warnings.filterwarnings("ignore")
np.random.seed(42)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PHASE6_DIR = os.path.join(ROOT_DIR, "phases", "Phase 6")
os.makedirs(PHASE6_DIR, exist_ok=True)

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


def wilson_interval(k, n, confidence=0.95):
    """Compute Wilson score confidence interval for binomial proportion."""
    if n == 0:
        return 0.0, 0.0
    z = 1.95996  # 95%
    p_hat = k / n
    denominator = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denominator
    spread = z * sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denominator
    lo = max(0.0, centre - spread)
    hi = min(1.0, centre + spread)
    return lo, hi


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


def reliability_table_with_wilson(y_true, y_prob, n_bins=10):
    """Generate equal-frequency reliability table with sample counts and Wilson 95% intervals."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)
    quantiles = np.linspace(0, 1, n_bins + 1)
    bin_edges = np.unique(np.percentile(y_prob, quantiles * 100))
    rows = []
    for i in range(len(bin_edges) - 1):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        mask = (y_prob >= lo) & (y_prob <= hi) if i == len(bin_edges) - 2 else (y_prob >= lo) & (y_prob < hi)
        n = int(mask.sum())
        if n > 0:
            k = int(y_true[mask].sum())
            p_pred = round(float(y_prob[mask].mean()), 4)
            p_actual = round(float(y_true[mask].mean()), 4)
            gap = round(abs(p_pred - p_actual), 4)
            ci_lo, ci_hi = wilson_interval(k, n)
            ci_str = f"[{ci_lo:.3f}, {ci_hi:.3f}]"
        else:
            p_pred, p_actual, gap, ci_str = np.nan, np.nan, np.nan, "N/A"
        rows.append({
            "bin": f"[{lo:.3f}, {hi:.3f}]" if i == len(bin_edges) - 2 else f"[{lo:.3f}, {hi:.3f})",
            "count": n,
            "avg_predicted": p_pred,
            "avg_actual": p_actual,
            "gap": gap,
            "actual_95ci_wilson": ci_str
        })
    return pd.DataFrame(rows)


def run_pipeline():
    print("=" * 80)
    print("  PHASE 6: ROLLING-ORIGIN EVALUATION & CONFORMAL INTERVALS")
    print("=" * 80)

    # 1. Load Cleaned Master Dataset
    master_path = os.path.join(ROOT_DIR, "data", "ipo_master.csv")
    df = pd.read_csv(master_path)
    df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce")
    df = df.sort_values("listing_date").reset_index(drop=True)

    df["actual_gain"] = pd.to_numeric(df["listing_gain_pct"], errors="coerce")
    df["actual_class"] = (df["actual_gain"] > 10.0).astype(int)
    df["quarter"] = df["listing_date"].dt.to_period("Q")

    test_quarters = sorted([q for q in df["quarter"].dropna().unique() if q >= pd.Period("2022Q1")])

    print(f"Cleaned Dataset Size : {len(df)} rows")
    print(f"Evaluation Quarters  : {len(test_quarters)} ({test_quarters[0]} to {test_quarters[-1]})")

    out_of_sample_rows = []

    param_grid = [
        {"max_depth": 3, "learning_rate": 0.03, "max_iter": 300, "min_samples_leaf": 15},
        {"max_depth": 4, "learning_rate": 0.03, "max_iter": 350, "min_samples_leaf": 15},
        {"max_depth": 4, "learning_rate": 0.05, "max_iter": 400, "min_samples_leaf": 20},
    ]

    for q_idx, q in enumerate(test_quarters):
        q_start = q.start_time
        q_end = q.end_time

        train_mask = df["listing_date"] < q_start
        test_mask = (df["listing_date"] >= q_start) & (df["listing_date"] <= q_end)

        train_data = df[train_mask].copy().reset_index(drop=True)
        test_data = df[test_mask].copy().reset_index(drop=True)

        if len(test_data) == 0:
            continue

        # Inner 80/20 train/validation split
        n_train = len(train_data)
        split_idx = int(n_train * 0.8)
        inner_tr = train_data.iloc[:split_idx].copy()
        inner_va = train_data.iloc[split_idx:].copy()

        mean_baseline_val = float(train_data["actual_gain"].mean())

        # Tune Regressor on inner validation
        best_reg_params = param_grid[0]
        best_inner_mae = float("inf")

        X_in_tr, cat_levels = prep_features(inner_tr, include_fundamentals=True, include_gmp=True)
        X_in_va, _ = prep_features(inner_va, cat_levels=cat_levels, include_fundamentals=True, include_gmp=True)
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

        # -------------------------------------------------------------
        # Conformal Prediction: Compute nonconformity scores on inner_va
        # -------------------------------------------------------------
        reg_cal = HistGradientBoostingRegressor(
            loss="absolute_error", l2_regularization=0.1,
            categorical_features=cat_idx_in, random_state=42, **best_reg_params
        ).fit(X_in_tr_f, y_in_tr)
        val_preds_cal = reg_cal.predict(X_in_va_f)
        val_abs_residuals = np.abs(y_in_va - val_preds_cal).values

        # Nominal 80% coverage -> alpha = 0.20
        # Conformal quantile: ceil((n+1)(1-alpha))/n
        alpha = 0.20
        n_val = len(val_abs_residuals)
        q_level = min(1.0, np.ceil((n_val + 1) * (1 - alpha)) / n_val)
        conformal_half_width = float(np.quantile(val_abs_residuals, q_level))

        # Train Full Models on train_data
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

        # 4. Blend Weight Selection on Inner Validation
        in_va_pred = reg_cal.predict(X_in_va_f)
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
        clf_raw = HistGradientBoostingClassifier(
            l2_regularization=0.5,
            categorical_features=cat_idx_in, random_state=42, **best_reg_params
        ).fit(X_in_tr_f, inner_tr["actual_class"])
        raw_val_probs = clf_raw.predict_proba(X_in_va_f)[:, 1]

        platt_scaler = LogisticRegression(C=1.0, solver="lbfgs")
        platt_scaler.fit(raw_val_probs.reshape(-1, 1), inner_va["actual_class"])

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

            # Primary point prediction: blend if GMP available, else model without GMP
            primary_est = p_blend if pd.notna(p_blend) else p_no_gmp_val
            lower_80 = primary_est - conformal_half_width
            upper_80 = primary_est + conformal_half_width
            actual_y = float(row["actual_gain"])
            covered_80 = int(lower_80 <= actual_y <= upper_80)

            out_of_sample_rows.append({
                "company": row["company"],
                "listing_date": row["listing_date"],
                "quarter": str(q),
                "actual_gain": actual_y,
                "actual_class": int(row["actual_class"]),
                "gmp_pct": gmp_val,
                "has_gmp": int(pd.notna(gmp_val)),
                "pred_mean_baseline": mean_baseline_val,
                "pred_no_fundamentals": p_no_fund,
                "pred_with_fundamentals": p_with_fund,
                "pred_no_gmp": p_no_gmp_val,
                "blend_weight_gmp": best_w,
                "pred_blend": p_blend,
                "pred_primary": primary_est,
                "conformal_half_width": conformal_half_width,
                "ci_80_lower": lower_80,
                "ci_80_upper": upper_80,
                "covered_80": covered_80,
                "pred_prob_raw": float(test_raw_probs[i]),
                "pred_prob_calibrated": float(test_cal_probs[i]),
            })

    pred_df = pd.DataFrame(out_of_sample_rows)
    pred_df.to_csv(os.path.join(PHASE6_DIR, "rolling_origin_predictions.csv"), index=False)
    print(f"Generated {len(pred_df)} clean out-of-sample predictions.")

    # -------------------------------------------------------------
    # S5 Compliance: Combine small quarters into half-year buckets
    # -------------------------------------------------------------
    pred_df["period_bucket"] = pred_df["quarter"].apply(
        lambda q: q if q in ["2023Q3", "2023Q4", "2024Q1", "2024Q3", "2024Q4", "2025Q3", "2025Q4", "2026Q3"]
        else q[:4] + ("H1" if q[4:] in ["Q1", "Q2"] else "H2")
    )

    quarterly_stats = []
    for bucket, grp in pred_df.groupby("period_bucket", sort=False):
        n = len(grp)
        grp_gmp = grp[grp["has_gmp"] == 1]
        n_gmp = len(grp_gmp)
        mae_base = mean_absolute_error(grp["actual_gain"], grp["pred_no_fundamentals"])
        mae_fund = mean_absolute_error(grp["actual_gain"], grp["pred_with_fundamentals"])
        mae_mean = mean_absolute_error(grp["actual_gain"], grp["pred_mean_baseline"])
        mae_gmp = mean_absolute_error(grp_gmp["actual_gain"], grp_gmp["gmp_pct"]) if n_gmp > 0 else np.nan
        mae_blend = mean_absolute_error(grp_gmp["actual_gain"], grp_gmp["pred_blend"]) if n_gmp > 0 else np.nan
        auc = roc_auc_score(grp["actual_class"], grp["pred_prob_calibrated"]) if len(grp["actual_class"].unique()) > 1 else np.nan
        coverage = grp["covered_80"].mean() * 100

        quarterly_stats.append({
            "period": bucket,
            "n_ipos": n,
            "n_with_gmp": n_gmp,
            "mae_mean_baseline": round(mae_mean, 2),
            "mae_no_fundamentals": round(mae_base, 2),
            "mae_with_fundamentals": round(mae_fund, 2),
            "mae_raw_gmp": round(mae_gmp, 2) if pd.notna(mae_gmp) else None,
            "mae_blend": round(mae_blend, 2) if pd.notna(mae_blend) else None,
            "auc": round(auc, 4) if pd.notna(auc) else None,
            "conformal_80_coverage_pct": round(coverage, 1)
        })

    q_df = pd.DataFrame(quarterly_stats)
    q_df.to_csv(os.path.join(PHASE6_DIR, "rolling_origin_quarterly.csv"), index=False)
    print("Quarterly / Half-Year summary saved.")

    # -------------------------------------------------------------
    # Paired Bootstrap Comparisons (Clean Data)
    # -------------------------------------------------------------
    mae_fn = lambda yt, yp: mean_absolute_error(yt, yp)
    y_actual = pred_df["actual_gain"].values

    # 1. H1: Model With Fundamentals vs Without Fundamentals
    pt_h1, lo_h1, hi_h1, excl_h1 = paired_bootstrap(
        y_actual, pred_df["pred_with_fundamentals"].values, pred_df["pred_no_fundamentals"].values, mae_fn
    )

    # 2. Model Without Fundamentals vs Historical Mean Baseline
    pt_base, lo_base, hi_base, excl_base = paired_bootstrap(
        y_actual, pred_df["pred_no_fundamentals"].values, pred_df["pred_mean_baseline"].values, mae_fn
    )

    # 3. Issues with GMP (n=323)
    gmp_sub = pred_df[pred_df["has_gmp"] == 1].reset_index(drop=True)
    y_gmp = gmp_sub["actual_gain"].values
    pt_mod_gmp, lo_mod_gmp, hi_mod_gmp, excl_mod_gmp = paired_bootstrap(
        y_gmp, gmp_sub["pred_with_fundamentals"].values, gmp_sub["gmp_pct"].values, mae_fn
    )
    pt_blend_gmp, lo_blend_gmp, hi_blend_gmp, excl_blend_gmp = paired_bootstrap(
        y_gmp, gmp_sub["pred_blend"].values, gmp_sub["gmp_pct"].values, mae_fn
    )
    pt_nogmp_gmp, lo_nogmp_gmp, hi_nogmp_gmp, excl_nogmp_gmp = paired_bootstrap(
        y_gmp, gmp_sub["pred_no_gmp"].values, gmp_sub["gmp_pct"].values, mae_fn
    )

    # 4. Issues without GMP (n=75)
    nogmp_sub = pred_df[pred_df["has_gmp"] == 0].reset_index(drop=True)
    y_nogmp = nogmp_sub["actual_gain"].values
    pt_nogmp_sub, lo_nogmp_sub, hi_nogmp_sub, excl_nogmp_sub = paired_bootstrap(
        y_nogmp, nogmp_sub["pred_no_gmp"].values, nogmp_sub["pred_mean_baseline"].values, mae_fn
    )

    boot_rows = [
        {
            "comparison": "H1: Model With Fundamentals vs Model Without Fundamentals",
            "subset": "All Out-of-Sample",
            "n": len(pred_df),
            "point_estimate_diff": round(pt_h1, 4),
            "ci_95_lower": round(lo_h1, 4),
            "ci_95_upper": round(hi_h1, 4),
            "excludes_zero": excl_h1,
            "verdict": "Improves" if (lo_h1 < 0 and hi_h1 < 0) else ("Hurts" if (lo_h1 > 0 and hi_h1 > 0) else "no demonstrated effect")
        },
        {
            "comparison": "Model Without Fundamentals vs Mean Baseline",
            "subset": "All Out-of-Sample",
            "n": len(pred_df),
            "point_estimate_diff": round(pt_base, 4),
            "ci_95_lower": round(lo_base, 4),
            "ci_95_upper": round(hi_base, 4),
            "excludes_zero": excl_base,
            "verdict": "Beats Baseline" if (lo_base < 0 and hi_base < 0) else "no demonstrated difference"
        },
        {
            "comparison": "Model With GMP vs Raw GMP",
            "subset": "IPOs With GMP",
            "n": len(gmp_sub),
            "point_estimate_diff": round(pt_mod_gmp, 4),
            "ci_95_lower": round(lo_mod_gmp, 4),
            "ci_95_upper": round(hi_mod_gmp, 4),
            "excludes_zero": excl_mod_gmp,
            "verdict": "Beats GMP" if (lo_mod_gmp < 0 and hi_mod_gmp < 0) else "no demonstrated advantage over raw GMP"
        },
        {
            "comparison": "Blend vs Raw GMP",
            "subset": "IPOs With GMP",
            "n": len(gmp_sub),
            "point_estimate_diff": round(pt_blend_gmp, 4),
            "ci_95_lower": round(lo_blend_gmp, 4),
            "ci_95_upper": round(hi_blend_gmp, 4),
            "excludes_zero": excl_blend_gmp,
            "verdict": "Beats GMP" if (lo_blend_gmp < 0 and hi_blend_gmp < 0) else "no demonstrated advantage over raw GMP"
        },
        {
            "comparison": "Model (No GMP) vs Raw GMP",
            "subset": "IPOs With GMP",
            "n": len(gmp_sub),
            "point_estimate_diff": round(pt_nogmp_gmp, 4),
            "ci_95_lower": round(lo_nogmp_gmp, 4),
            "ci_95_upper": round(hi_nogmp_gmp, 4),
            "excludes_zero": excl_nogmp_gmp,
            "verdict": "Beats GMP" if (lo_nogmp_gmp < 0 and hi_nogmp_gmp < 0) else "no demonstrated advantage over raw GMP"
        },
        {
            "comparison": "Model (No GMP) vs Mean Baseline",
            "subset": "IPOs Without GMP",
            "n": len(nogmp_sub),
            "point_estimate_diff": round(pt_nogmp_sub, 4),
            "ci_95_lower": round(lo_nogmp_sub, 4),
            "ci_95_upper": round(hi_nogmp_sub, 4),
            "excludes_zero": excl_nogmp_sub,
            "verdict": "Beats Mean" if (lo_nogmp_sub < 0 and hi_nogmp_sub < 0) else "no demonstrated difference"
        }
    ]
    pd.DataFrame(boot_rows).to_csv(os.path.join(PHASE6_DIR, "model_comparisons_bootstrap.csv"), index=False)
    print("Bootstrap comparisons saved.")

    # -------------------------------------------------------------
    # Conformal Prediction Intervals Coverage Analysis
    # -------------------------------------------------------------
    pooled_cov = pred_df["covered_80"].mean() * 100
    gmp_cov = gmp_sub["covered_80"].mean() * 100
    nogmp_cov = nogmp_sub["covered_80"].mean() * 100
    mean_width = (pred_df["ci_80_upper"] - pred_df["ci_80_lower"]).mean()

    # Top 10% actual gains
    p90_threshold = float(np.percentile(pred_df["actual_gain"], 90.0))
    top10_df = pred_df[pred_df["actual_gain"] >= p90_threshold]
    top10_cov = top10_df["covered_80"].mean() * 100

    conf_summary = [
        {"subset": "Pooled Out-of-Sample", "n": len(pred_df), "nominal_coverage_pct": 80.0, "empirical_coverage_pct": round(pooled_cov, 1), "mean_interval_width": round(mean_width, 2)},
        {"subset": "IPOs With GMP", "n": len(gmp_sub), "nominal_coverage_pct": 80.0, "empirical_coverage_pct": round(gmp_cov, 1), "mean_interval_width": round(mean_width, 2)},
        {"subset": "IPOs Without GMP", "n": len(nogmp_sub), "nominal_coverage_pct": 80.0, "empirical_coverage_pct": round(nogmp_cov, 1), "mean_interval_width": round(mean_width, 2)},
        {"subset": "Top 10% Largest Gains (>=50.8%)", "n": len(top10_df), "nominal_coverage_pct": 80.0, "empirical_coverage_pct": round(top10_cov, 1), "mean_interval_width": round(mean_width, 2)},
    ]
    pd.DataFrame(conf_summary).to_csv(os.path.join(PHASE6_DIR, "conformal_intervals_coverage.csv"), index=False)
    print("Conformal intervals coverage report saved.")

    # -------------------------------------------------------------
    # Calibration Table with Wilson 95% Intervals
    # -------------------------------------------------------------
    cal_table = reliability_table_with_wilson(pred_df["actual_class"], pred_df["pred_prob_calibrated"], n_bins=10)
    cal_table.to_csv(os.path.join(PHASE6_DIR, "calibration_table.csv"), index=False)
    print("Reliability table with Wilson intervals saved.")

    # -------------------------------------------------------------
    # Tail Behavior & Error Distribution
    # -------------------------------------------------------------
    pred_df["abs_error"] = np.abs(pred_df["actual_gain"] - pred_df["pred_primary"])
    worst_10 = pred_df.sort_values("abs_error", ascending=False).head(10).copy()
    worst_10["error_type"] = "10 Worst Absolute Errors"
    best_10 = pred_df.sort_values("abs_error", ascending=True).head(10).copy()
    best_10["error_type"] = "10 Best Absolute Errors"
    tail_df = pd.concat([worst_10, best_10], ignore_index=True)
    tail_df.to_csv(os.path.join(PHASE6_DIR, "tail_and_error_distribution.csv"), index=False)
    print("Tail and error distribution saved.")

    # -------------------------------------------------------------
    # Before vs After Comparison (Phase 5 vs Phase 6)
    # -------------------------------------------------------------
    p5_pred_df = pd.read_csv("phases/Phase 5/rolling_origin_predictions.csv")
    p5_mae_mean = mean_absolute_error(p5_pred_df["actual_gain"], p5_pred_df["pred_mean_baseline"])
    p5_mae_nofund = mean_absolute_error(p5_pred_df["actual_gain"], p5_pred_df["pred_no_fundamentals"])
    p5_mae_withfund = mean_absolute_error(p5_pred_df["actual_gain"], p5_pred_df["pred_with_fundamentals"])
    p5_gmp_sub = p5_pred_df[p5_pred_df["has_gmp"] == 1]
    p5_mae_raw_gmp = mean_absolute_error(p5_gmp_sub["actual_gain"], p5_gmp_sub["gmp_pct"])
    p5_mae_blend = mean_absolute_error(p5_gmp_sub["actual_gain"], p5_gmp_sub["pred_blend"])
    p5_auc = roc_auc_score(p5_pred_df["actual_class"], p5_pred_df["pred_prob_calibrated"])
    p5_ece = compute_ece(p5_pred_df["actual_class"], p5_pred_df["pred_prob_calibrated"], n_bins=10, strategy="quantile")
    p5_brier = brier_score_loss(p5_pred_df["actual_class"], p5_pred_df["pred_prob_calibrated"])

    p6_mae_mean = mean_absolute_error(pred_df["actual_gain"], pred_df["pred_mean_baseline"])
    p6_mae_nofund = mean_absolute_error(pred_df["actual_gain"], pred_df["pred_no_fundamentals"])
    p6_mae_withfund = mean_absolute_error(pred_df["actual_gain"], pred_df["pred_with_fundamentals"])
    p6_mae_raw_gmp = mean_absolute_error(gmp_sub["actual_gain"], gmp_sub["gmp_pct"])
    p6_mae_blend = mean_absolute_error(gmp_sub["actual_gain"], gmp_sub["pred_blend"])
    p6_auc = roc_auc_score(pred_df["actual_class"], pred_df["pred_prob_calibrated"])
    p6_ece = compute_ece(pred_df["actual_class"], pred_df["pred_prob_calibrated"], n_bins=10, strategy="quantile")
    p6_brier = brier_score_loss(pred_df["actual_class"], pred_df["pred_prob_calibrated"])

    comp_rows = [
        {"metric": "Evaluated Sample Size (n)", "phase_5_uncleaned": len(p5_pred_df), "phase_6_cleaned": len(pred_df), "delta": len(pred_df) - len(p5_pred_df)},
        {"metric": "MAE: Historical Mean Baseline", "phase_5_uncleaned": round(p5_mae_mean, 2), "phase_6_cleaned": round(p6_mae_mean, 2), "delta": round(p6_mae_mean - p5_mae_mean, 2)},
        {"metric": "MAE: Model Without Fundamentals", "phase_5_uncleaned": round(p5_mae_nofund, 2), "phase_6_cleaned": round(p6_mae_nofund, 2), "delta": round(p6_mae_nofund - p5_mae_nofund, 2)},
        {"metric": "MAE: Model With Fundamentals", "phase_5_uncleaned": round(p5_mae_withfund, 2), "phase_6_cleaned": round(p6_mae_withfund, 2), "delta": round(p6_mae_withfund - p5_mae_withfund, 2)},
        {"metric": "MAE: Raw GMP (on GMP subset)", "phase_5_uncleaned": round(p5_mae_raw_gmp, 2), "phase_6_cleaned": round(p6_mae_raw_gmp, 2), "delta": round(p6_mae_raw_gmp - p5_mae_raw_gmp, 2)},
        {"metric": "MAE: Blend (on GMP subset)", "phase_5_uncleaned": round(p5_mae_blend, 2), "phase_6_cleaned": round(p6_mae_blend, 2), "delta": round(p6_mae_blend - p5_mae_blend, 2)},
        {"metric": "ROC AUC (Classification)", "phase_5_uncleaned": round(p5_auc, 4), "phase_6_cleaned": round(p6_auc, 4), "delta": round(p6_auc - p5_auc, 4)},
        {"metric": "Equal-Frequency ECE", "phase_5_uncleaned": round(p5_ece, 4), "phase_6_cleaned": round(p6_ece, 4), "delta": round(p6_ece - p5_ece, 4)},
        {"metric": "Brier Score Loss", "phase_5_uncleaned": round(p5_brier, 4), "phase_6_cleaned": round(p6_brier, 4), "delta": round(p6_brier - p5_brier, 4)},
    ]
    pd.DataFrame(comp_rows).to_csv(os.path.join(PHASE6_DIR, "before_after_comparison.csv"), index=False)
    print("Before vs After comparison saved.")
    print("Pipeline Execution Completed Successfully.")


if __name__ == "__main__":
    run_pipeline()
