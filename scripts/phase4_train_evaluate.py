#!/usr/bin/env python3
"""Phase 4 Tasks 4-7: Retrain, Calibrate, GMP-Compare, and Final-Test Evaluate.

This script:
  Task 4 - Retrains HistGradientBoosting on ipo_train.csv with hyperparameter
           tuning on ipo_val.csv (validation only, never touches final test).
  Task 5 - Calibrates the >10% classifier (Platt/sigmoid) on validation.
           Reports reliability table, Brier score, and ECE before/after.
  Task 6 - GMP-aware comparison on validation GMP subset: raw GMP, model
           without GMP, model with GMP, optimal blend.
  Task 7 - One-time evaluation on the frozen final test set. Reports all
           metrics and saves results.

Usage: python scripts/phase4_train_evaluate.py
"""
import os, sys, json, warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, roc_auc_score, accuracy_score, brier_score_loss
from itertools import product

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "model"))
from train import PlattCalibrator

warnings.filterwarnings("ignore", category=UserWarning)
np.random.seed(42)

# ── Feature definitions (same as model/train.py) ──
ALL_NUM = [
    "issue_price", "issue_size_cr", "fresh_issue_pct", "ofs_pct", "lot_size",
    "sub_qib", "sub_nii", "sub_retail", "sub_total", "pe_ratio", "peer_median_pe",
    "roe", "roce", "debt_equity", "revenue_growth_pct", "pat_margin_pct",
    "gmp_pct", "nifty_30d_return", "india_vix", "recent_ipo_avg_gain"
]
# Exclude fundamentals with 0% coverage (Phase 4 Task 3 decision)
NUM = [c for c in ALL_NUM if c not in ["roe", "roce", "revenue_growth_pct", "pat_margin_pct"]]
NUM_NO_GMP = [c for c in NUM if c != "gmp_pct"]
CAT = ["sector", "exchange"]

def prep(df, cat_levels=None, include_gmp=True):
    """Transform raw dataframe into model feature matrix."""
    num_cols = NUM if include_gmp else NUM_NO_GMP
    X = pd.DataFrame(index=df.index)
    for c in num_cols:
        X[c] = pd.to_numeric(df[c], errors="coerce") if c in df.columns else np.nan

    levels = cat_levels or {c: sorted(df[c].dropna().astype(str).unique()) for c in CAT}
    for c in CAT:
        if c in df.columns:
            X[c] = pd.Categorical(df[c].astype(str), categories=levels[c]).codes
        else:
            X[c] = -1

    # Engineered features
    X["pe_vs_peer"] = X["pe_ratio"] / X["peer_median_pe"].replace(0, np.nan)
    X["sub_retail_vs_qib"] = X["sub_retail"] / X["sub_qib"].replace(0, np.nan)
    X["sub_hni_vs_retail"] = X["sub_nii"] / X["sub_retail"].replace(0, np.nan)
    X["log_issue_size"] = np.log1p(X["issue_size_cr"].clip(lower=0))
    X["is_high_vix"] = (X["india_vix"] > 18.0).astype(float)
    X["log_sub_total"] = np.log1p(X["sub_total"].clip(lower=0))
    X["log_sub_qib"] = np.log1p(X["sub_qib"].clip(lower=0))
    X["log_sub_nii"] = np.log1p(X["sub_nii"].clip(lower=0))
    X["log_sub_retail"] = np.log1p(X["sub_retail"].clip(lower=0))
    X["qib_demand_share"] = X["sub_qib"] / X["sub_total"].replace(0, np.nan)

    if include_gmp:
        X["gmp_vs_recent_avg"] = X["gmp_pct"] - X["recent_ipo_avg_gain"]
        X["gmp_x_sub"] = X["gmp_pct"] * np.log1p(X["sub_total"].clip(lower=0))

    return X, levels

def compute_ece(y_true, y_prob, n_bins=10):
    """Expected Calibration Error."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        lo, hi = bin_boundaries[i], bin_boundaries[i + 1]
        mask = (y_prob >= lo) & (y_prob < hi) if i < n_bins - 1 else (y_prob >= lo) & (y_prob <= hi)
        if mask.sum() == 0:
            continue
        ece += mask.sum() / len(y_true) * abs(y_prob[mask].mean() - y_true[mask].mean())
    return ece

def reliability_table(y_true, y_prob, n_bins=10):
    """Print a reliability table with n_bins bins."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    rows = []
    for i in range(n_bins):
        lo, hi = bin_boundaries[i], bin_boundaries[i + 1]
        mask = (y_prob >= lo) & (y_prob < hi) if i < n_bins - 1 else (y_prob >= lo) & (y_prob <= hi)
        n = mask.sum()
        avg_pred = y_prob[mask].mean() if n > 0 else np.nan
        avg_true = y_true[mask].mean() if n > 0 else np.nan
        rows.append({"bin": f"[{lo:.1f}, {hi:.1f})", "count": int(n),
                      "avg_predicted": round(avg_pred, 3) if n > 0 else "-",
                      "avg_actual": round(avg_true, 3) if n > 0 else "-",
                      "gap": round(abs(avg_pred - avg_true), 3) if n > 0 else "-"})
    return pd.DataFrame(rows)

# ══════════════════════════════════════════════════════════════════════════════
#  LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("  PHASE 4: MODEL RETRAINING, CALIBRATION & EVALUATION PIPELINE")
print("=" * 80)

train_df = pd.read_csv("data/ipo_train.csv", parse_dates=["listing_date"]).sort_values("listing_date").reset_index(drop=True)
val_df = pd.read_csv("data/ipo_val.csv", parse_dates=["listing_date"]).sort_values("listing_date").reset_index(drop=True)
test_df = pd.read_csv("data/ipo_final_test.csv", parse_dates=["listing_date"]).sort_values("listing_date").reset_index(drop=True)

print(f"\nTrain : {len(train_df)} IPOs ({train_df.listing_date.min().date()} to {train_df.listing_date.max().date()})")
print(f"Val   : {len(val_df)} IPOs ({val_df.listing_date.min().date()} to {val_df.listing_date.max().date()})")
print(f"Test  : {len(test_df)} IPOs ({test_df.listing_date.min().date()} to {test_df.listing_date.max().date()}) [FROZEN]")

ytr_r = train_df["listing_gain_pct"]
yva_r = val_df["listing_gain_pct"]
yte_r = test_df["listing_gain_pct"]
ytr_c = (ytr_r > 10.0).astype(int)
yva_c = (yva_r > 10.0).astype(int)
yte_c = (yte_r > 10.0).astype(int)

# ══════════════════════════════════════════════════════════════════════════════
#  TASK 4: RETRAIN WITH HYPERPARAMETER TUNING ON VALIDATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  TASK 4: HYPERPARAMETER TUNING (Validation Only)")
print("=" * 80)

Xtr, levels = prep(train_df)
Xva, _ = prep(val_df, levels)
cat_idx = [list(Xtr.columns).index(c) for c in CAT]

# Grid search on validation
param_grid = {
    "max_depth": [3, 4, 5],
    "learning_rate": [0.02, 0.03, 0.05],
    "max_iter": [300, 400, 500],
    "min_samples_leaf": [10, 15, 20],
}
keys = list(param_grid.keys())
combos = list(product(*param_grid.values()))
print(f"Searching {len(combos)} hyperparameter combinations...")

best_reg_mae = float("inf")
best_reg_params = {}
best_clf_auc = 0.0
best_clf_params = {}

for i, vals in enumerate(combos):
    params = dict(zip(keys, vals))
    try:
        r = HistGradientBoostingRegressor(
            loss="absolute_error", l2_regularization=0.1,
            categorical_features=cat_idx, random_state=42, **params
        ).fit(Xtr, ytr_r)
        mae = mean_absolute_error(yva_r, r.predict(Xva))
        if mae < best_reg_mae:
            best_reg_mae = mae
            best_reg_params = params.copy()

        c = HistGradientBoostingClassifier(
            l2_regularization=0.5,
            categorical_features=cat_idx, random_state=42, **params
        ).fit(Xtr, ytr_c)
        probs = c.predict_proba(Xva)[:, 1]
        auc = roc_auc_score(yva_c, probs)
        if auc > best_clf_auc:
            best_clf_auc = auc
            best_clf_params = params.copy()
    except Exception:
        continue

    if (i + 1) % 27 == 0:
        print(f"  ...{i + 1}/{len(combos)} done (best reg MAE={best_reg_mae:.2f}, best clf AUC={best_clf_auc:.3f})")

print(f"\n✓ Best Regressor params (val MAE={best_reg_mae:.2f}%): {best_reg_params}")
print(f"✓ Best Classifier params (val AUC={best_clf_auc:.3f}): {best_clf_params}")

# Train final models with best params
reg = HistGradientBoostingRegressor(
    loss="absolute_error", l2_regularization=0.1,
    categorical_features=cat_idx, random_state=42, **best_reg_params
).fit(Xtr, ytr_r)

clf = HistGradientBoostingClassifier(
    l2_regularization=0.5,
    categorical_features=cat_idx, random_state=42, **best_clf_params
).fit(Xtr, ytr_c)

# Train metrics
train_mae = mean_absolute_error(ytr_r, reg.predict(Xtr))
train_auc = roc_auc_score(ytr_c, clf.predict_proba(Xtr)[:, 1])
val_mae = mean_absolute_error(yva_r, reg.predict(Xva))
val_probs = clf.predict_proba(Xva)[:, 1]
val_auc = roc_auc_score(yva_c, val_probs)
val_acc = accuracy_score(yva_c, (val_probs > 0.5).astype(int))

print(f"\n--- Phase 4 Tuned Model Metrics ---")
print(f"Train MAE: {train_mae:.2f}% | Val MAE: {val_mae:.2f}%")
print(f"Train AUC: {train_auc:.3f} | Val AUC: {val_auc:.3f}")
print(f"Val Accuracy (>10%): {val_acc * 100:.1f}%")
print(f"Val Mean baseline MAE: {mean_absolute_error(yva_r, np.full(len(yva_r), ytr_r.mean())):.2f}%")

# ══════════════════════════════════════════════════════════════════════════════
#  TASK 5: PROBABILITY CALIBRATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  TASK 5: PROBABILITY CALIBRATION (Platt Scaling on Validation)")
print("=" * 80)

# Before calibration
brier_before = brier_score_loss(yva_c, val_probs)
ece_before = compute_ece(yva_c, val_probs)
print(f"\nBEFORE Calibration:")
print(f"  Brier Score: {brier_before:.4f}")
print(f"  ECE:         {ece_before:.4f}")
print(f"\nReliability Table (Before):")
rt_before = reliability_table(yva_c, val_probs)
print(rt_before.to_string(index=False))

# Calibrate using manual Platt scaling (LogisticRegression on raw probs)
raw_logits = np.log(val_probs.clip(1e-8, 1 - 1e-8) / (1 - val_probs.clip(1e-8, 1 - 1e-8)))
platt_lr = LogisticRegression(random_state=42, C=1e10, solver="lbfgs", max_iter=1000)
platt_lr.fit(raw_logits.reshape(-1, 1), yva_c)

cal_clf = PlattCalibrator(clf, platt_lr)

cal_probs = cal_clf.predict_proba(Xva)[:, 1]
brier_after = brier_score_loss(yva_c, cal_probs)
ece_after = compute_ece(yva_c, cal_probs)
print(f"\nAFTER Calibration (Platt/Sigmoid):")
print(f"  Brier Score: {brier_after:.4f}  (Δ = {brier_after - brier_before:+.4f})")
print(f"  ECE:         {ece_after:.4f}  (Δ = {ece_after - ece_before:+.4f})")
print(f"\nReliability Table (After):")
rt_after = reliability_table(yva_c, cal_probs)
print(rt_after.to_string(index=False))

# Landmark backtest (illustrative only - these are in the training set)
print("\n--- 10 Landmark IPOs (Illustrative Only, In Training Set) ---")
landmarks = [
    "Tata Technologies", "Happiest Minds", "Avenue Supermarts", "Irctc", "Zomato",
    "Sbi Cards", "Lic", "One 97", "Cl Educate", "Adlabs Entertainment"
]
for lm in landmarks:
    mask = train_df["company"].str.lower().str.contains(lm.lower().split()[0])
    if mask.any():
        idx = mask.idxmax()
        row = train_df.iloc[[idx]]
        Xlm, _ = prep(row, levels)
        pred_gain = reg.predict(Xlm)[0]
        raw_prob = clf.predict_proba(Xlm)[0][1]
        cal_prob = cal_clf.predict_proba(Xlm)[0][1]
        actual = row["listing_gain_pct"].values[0]
        print(f"  {row['company'].values[0]:30s} | Actual: {actual:+7.1f}% | Pred: {pred_gain:+7.1f}% | Raw P: {raw_prob*100:5.1f}% | Cal P: {cal_prob*100:5.1f}%")

# ══════════════════════════════════════════════════════════════════════════════
#  TASK 6: GMP-AWARE COMPARISON (Validation GMP Subset)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  TASK 6: GMP-AWARE COMPARISON (Validation Set)")
print("=" * 80)

gmp_mask = val_df["gmp_pct"].notna()
val_gmp = val_df[gmp_mask].copy().reset_index(drop=True)
y_gmp = val_gmp["listing_gain_pct"]
print(f"\nValidation IPOs with GMP: {len(val_gmp)} / {len(val_df)}")

# (a) Raw GMP
mae_raw_gmp = mean_absolute_error(y_gmp, val_gmp["gmp_pct"])
print(f"\n(a) Raw GMP MAE:              {mae_raw_gmp:.2f}%")

# (b) Model WITHOUT GMP
Xtr_nogmp, levels_nogmp = prep(train_df, include_gmp=False)
Xva_nogmp, _ = prep(val_gmp, levels_nogmp, include_gmp=False)
cat_idx_nogmp = [list(Xtr_nogmp.columns).index(c) for c in CAT]

reg_nogmp = HistGradientBoostingRegressor(
    loss="absolute_error", l2_regularization=0.1,
    categorical_features=cat_idx_nogmp, random_state=42, **best_reg_params
).fit(Xtr_nogmp, ytr_r)
pred_nogmp = reg_nogmp.predict(Xva_nogmp)
mae_nogmp = mean_absolute_error(y_gmp, pred_nogmp)
print(f"(b) Model (no GMP) MAE:       {mae_nogmp:.2f}%")

# (c) Model WITH GMP (full Phase 4 model)
Xva_gmp, _ = prep(val_gmp, levels)
pred_withgmp = reg.predict(Xva_gmp)
mae_withgmp = mean_absolute_error(y_gmp, pred_withgmp)
print(f"(c) Model (with GMP) MAE:     {mae_withgmp:.2f}%")

# (d) Blend: w * GMP + (1-w) * model_pred, optimize w on validation
best_w = 0.0
best_blend_mae = float("inf")
for w_int in range(0, 21):
    w = w_int / 20.0
    blend = w * val_gmp["gmp_pct"].values + (1 - w) * pred_withgmp
    mae_blend = mean_absolute_error(y_gmp, blend)
    if mae_blend < best_blend_mae:
        best_blend_mae = mae_blend
        best_w = w

print(f"(d) Optimal Blend MAE:        {best_blend_mae:.2f}%  (w_gmp={best_w:.2f})")
print(f"\n    Winner: ", end="")
results_gmp = {"Raw GMP": mae_raw_gmp, "Model (no GMP)": mae_nogmp,
               "Model (with GMP)": mae_withgmp, "Blend": best_blend_mae}
winner = min(results_gmp, key=results_gmp.get)
print(f"{winner} ({results_gmp[winner]:.2f}%)")

# ══════════════════════════════════════════════════════════════════════════════
#  TASK 7: FROZEN FINAL TEST EVALUATION (ONE-TIME)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  TASK 7: FROZEN FINAL TEST EVALUATION (ONE-TIME, 75 IPOs)")
print("=" * 80)

Xte, _ = prep(test_df, levels)
pred_test_r = reg.predict(Xte)
pred_test_p_raw = clf.predict_proba(Xte)[:, 1]
pred_test_p_cal = cal_clf.predict_proba(Xte)[:, 1]

mae_test = mean_absolute_error(yte_r, pred_test_r)
mae_mean_baseline = mean_absolute_error(yte_r, np.full(len(yte_r), ytr_r.mean()))
auc_test = roc_auc_score(yte_c, pred_test_p_cal)
acc_test = accuracy_score(yte_c, (pred_test_p_cal > 0.5).astype(int))
brier_test = brier_score_loss(yte_c, pred_test_p_cal)
ece_test = compute_ece(yte_c, pred_test_p_cal)

print(f"\n--- Phase 4 vs Phase 2 Comparison on Final Test ---")
print(f"{'Metric':<35} {'Phase 2':>10} {'Phase 4':>10} {'Δ':>10}")
print("-" * 67)
print(f"{'Regressor MAE':<35} {'12.23%':>10} {f'{mae_test:.2f}%':>10} {f'{mae_test - 12.23:+.2f}%':>10}")
print(f"{'Mean Baseline MAE':<35} {'17.62%':>10} {f'{mae_mean_baseline:.2f}%':>10} {'':>10}")
print(f"{'ROC-AUC':<35} {'0.829':>10} {f'{auc_test:.3f}':>10} {f'{auc_test - 0.829:+.3f}':>10}")
print(f"{'Accuracy (>10%)':<35} {'84.00%':>10} {f'{acc_test*100:.1f}%':>10} {f'{acc_test*100 - 84:+.1f}%':>10}")
print(f"{'Brier Score':<35} {'N/A':>10} {f'{brier_test:.4f}':>10} {'':>10}")
print(f"{'ECE':<35} {'N/A':>10} {f'{ece_test:.4f}':>10} {f'(target ≤ 0.10)':>10}")

# GMP subset of final test
gmp_test_mask = test_df["gmp_pct"].notna()
if gmp_test_mask.sum() > 0:
    test_gmp_df = test_df[gmp_test_mask]
    yte_gmp = test_gmp_df["listing_gain_pct"]
    Xte_gmp, _ = prep(test_gmp_df, levels)
    pred_gmp_test = reg.predict(Xte_gmp)
    mae_gmp_raw_test = mean_absolute_error(yte_gmp, test_gmp_df["gmp_pct"])
    mae_gmp_model_test = mean_absolute_error(yte_gmp, pred_gmp_test)
    blend_test = best_w * test_gmp_df["gmp_pct"].values + (1 - best_w) * pred_gmp_test
    mae_gmp_blend_test = mean_absolute_error(yte_gmp, blend_test)
    print(f"\n--- GMP Subset ({gmp_test_mask.sum()} IPOs) ---")
    print(f"Raw GMP MAE:    {mae_gmp_raw_test:.2f}%")
    print(f"Model MAE:      {mae_gmp_model_test:.2f}%")
    print(f"Blend MAE:      {mae_gmp_blend_test:.2f}%  (w_gmp={best_w:.2f})")

# Reliability table on final test
print(f"\nReliability Table (Final Test, Calibrated):")
rt_test = reliability_table(yte_c, pred_test_p_cal)
print(rt_test.to_string(index=False))

# Full holdout table
print(f"\n--- Full Final Test Holdout Table ---")
results_df = pd.DataFrame({
    "company": test_df["company"].values,
    "listing_date": test_df["listing_date"].dt.strftime("%Y-%m-%d").values,
    "actual_gain_pct": yte_r.values,
    "predicted_gain_pct": np.round(pred_test_r, 2),
    "pred_prob_gt10_cal": np.round(pred_test_p_cal * 100, 1),
    "gmp_pct": test_df["gmp_pct"].values,
    "model_error": np.round(np.abs(pred_test_r - yte_r.values), 2),
    "gmp_error": np.round(np.abs(test_df["gmp_pct"].values - yte_r.values), 2)
})
print(results_df.to_string(index=False))

# Save final test results
os.makedirs("phases/Phase 4", exist_ok=True)
results_df.to_csv("phases/Phase 4/final_test_results.csv", index=False)
print(f"\nSaved final test results to phases/Phase 4/final_test_results.csv")

# ══════════════════════════════════════════════════════════════════════════════
#  SAVE MODEL ARTIFACT
# ══════════════════════════════════════════════════════════════════════════════
artifact = {
    "reg": reg,
    "clf": clf,
    "cal_clf": cal_clf,
    "levels": levels,
    "features": list(Xtr.columns),
    "cat_idx": cat_idx,
    "best_reg_params": best_reg_params,
    "best_clf_params": best_clf_params,
    "blend_weight_gmp": best_w,
    "train_rows": len(train_df),
    "val_rows": len(val_df),
    "test_rows": len(test_df),
    "train_date_range": f"{train_df.listing_date.min().date()} to {train_df.listing_date.max().date()}",
    "val_date_range": f"{val_df.listing_date.min().date()} to {val_df.listing_date.max().date()}",
    "test_date_range": f"{test_df.listing_date.min().date()} to {test_df.listing_date.max().date()}",
    "val_mae": round(val_mae, 4),
    "val_auc": round(val_auc, 4),
    "test_mae": round(mae_test, 4),
    "test_auc": round(auc_test, 4),
    "brier_before_cal": round(brier_before, 4),
    "brier_after_cal": round(brier_after, 4),
    "ece_before_cal": round(ece_before, 4),
    "ece_after_cal": round(ece_after, 4),
    "gmp_comparison": results_gmp,
    "phase": 4,
}
joblib.dump(artifact, "model/ipo_model_phase4.joblib")
print(f"\n✓ Phase 4 model saved to model/ipo_model_phase4.joblib")

# Summary JSON for documentation
summary = {
    "best_reg_params": best_reg_params,
    "best_clf_params": best_clf_params,
    "blend_weight_gmp": best_w,
    "val_mae": round(val_mae, 2),
    "val_auc": round(val_auc, 3),
    "test_mae": round(mae_test, 2),
    "test_auc": round(auc_test, 3),
    "test_acc": round(acc_test * 100, 1),
    "brier_before": round(brier_before, 4),
    "brier_after": round(brier_after, 4),
    "ece_before": round(ece_before, 4),
    "ece_after": round(ece_after, 4),
    "brier_test": round(brier_test, 4),
    "ece_test": round(ece_test, 4),
    "mae_mean_baseline_test": round(mae_mean_baseline, 2),
    "gmp_comparison_val": {k: round(v, 2) for k, v in results_gmp.items()},
}
with open("phases/Phase 4/phase4_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"✓ Summary saved to phases/Phase 4/phase4_summary.json")
print("\n" + "=" * 80)
print("  PHASE 4 PIPELINE COMPLETE")
print("=" * 80)
