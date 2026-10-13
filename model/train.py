#!/usr/bin/env python3
"""Train the IPO listing-gain model on a strictly partitioned training set.
Usage: python model/train.py data/ipo_master.csv

Separates an out-of-sample holdout test dataset (never used in training) to evaluate
true generalization capability against actual IPO listing performance and GMP.
Saves:
  - data/ipo_train.csv (Training partition)
  - data/ipo_holdout_test.csv (Unseen evaluation holdout partition)
  - model/ipo_model.joblib (Trained model artifact - strictly on train data)
"""
import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, roc_auc_score, accuracy_score

ALL_NUM = [
    "issue_price", "issue_size_cr", "fresh_issue_pct", "ofs_pct", "lot_size",
    "sub_qib", "sub_nii", "sub_retail", "sub_total", "pe_ratio", "peer_median_pe",
    "roe", "roce", "debt_equity", "revenue_growth_pct", "pat_margin_pct",
    "gmp_pct", "nifty_30d_return", "india_vix", "recent_ipo_avg_gain"
]
CAT = ["sector", "exchange"]

# Active numerical features with sufficient non-null variance
NUM = [c for c in ALL_NUM if c not in ["roe", "roce", "revenue_growth_pct", "pat_margin_pct"]]
FEATURES = NUM + CAT

def prep(df, cat_levels=None):
    """Transform raw dataframe into model feature matrix."""
    X = pd.DataFrame(index=df.index)
    for c in NUM:
        X[c] = pd.to_numeric(df[c], errors="coerce") if c in df else np.nan
        
    levels = cat_levels or {c: sorted(df[c].dropna().astype(str).unique()) for c in CAT}
    for c in CAT:
        if c in df:
            X[c] = pd.Categorical(df[c].astype(str), categories=levels[c]).codes
        else:
            X[c] = -1
            
    # Engineered domain features
    X["pe_vs_peer"] = X["pe_ratio"] / X["peer_median_pe"].replace(0, np.nan)
    X["sub_retail_vs_qib"] = X["sub_retail"] / X["sub_qib"].replace(0, np.nan)
    X["sub_hni_vs_retail"] = X["sub_nii"] / X["sub_retail"].replace(0, np.nan)
    X["log_issue_size"] = np.log1p(X["issue_size_cr"].clip(lower=0))
    X["is_high_vix"] = (X["india_vix"] > 18.0).astype(float)
    X["gmp_vs_recent_avg"] = X["gmp_pct"] - X["recent_ipo_avg_gain"]
    
    # Enhanced log-demand and non-linear interactions
    X["log_sub_total"] = np.log1p(X["sub_total"].clip(lower=0))
    X["log_sub_qib"] = np.log1p(X["sub_qib"].clip(lower=0))
    X["log_sub_nii"] = np.log1p(X["sub_nii"].clip(lower=0))
    X["log_sub_retail"] = np.log1p(X["sub_retail"].clip(lower=0))
    X["qib_demand_share"] = X["sub_qib"] / (X["sub_total"].replace(0, np.nan))
    X["gmp_x_sub"] = X["gmp_pct"] * np.log1p(X["sub_total"].clip(lower=0))
    return X, levels

def main(path="data/ipo_master.csv"):
    if not os.path.exists(path):
        print(f"Error: dataset file '{path}' not found.")
        sys.exit(1)
        
    df = pd.read_csv(path, parse_dates=["listing_date"]).sort_values("listing_date")
    df = df.dropna(subset=["listing_gain_pct"]).reset_index(drop=True)
    if len(df) < 100:
        print(f"WARNING: only {len(df)} labelled rows. Results will be unreliable; collect more data.")
        
    # Strict chronological partition: 80% train, 20% holdout
    cut = int(len(df) * 0.8)
    train = df.iloc[:cut].copy().reset_index(drop=True)
    holdout = df.iloc[cut:].copy().reset_index(drop=True)
    
    # Save partitioned datasets
    os.makedirs("data", exist_ok=True)
    train.to_csv("data/ipo_train.csv", index=False)
    holdout.to_csv("data/ipo_holdout_test.csv", index=False)
    print(f"Saved {len(train)} training IPOs to data/ipo_train.csv")
    print(f"Saved {len(holdout)} unseen holdout IPOs to data/ipo_holdout_test.csv")
    
    Xtr, levels = prep(train)
    Xte, _ = prep(holdout, levels)
    
    ytr_r, yte_r = train.listing_gain_pct, holdout.listing_gain_pct
    ytr_c, yte_c = (ytr_r > 10.0).astype(int), (yte_r > 10.0).astype(int)

    cat_idx = [list(Xtr.columns).index(c) for c in CAT]

    # Optimized HistGradientBoosting estimators:
    # 1. Regressor with absolute_error loss for robust prediction against listing spikes
    reg = HistGradientBoostingRegressor(
        loss="absolute_error",
        max_depth=4,
        learning_rate=0.03,
        max_iter=350,
        min_samples_leaf=15,
        l2_regularization=0.1,
        categorical_features=cat_idx,
        random_state=42
    ).fit(Xtr, ytr_r)

    # 2. Classifier tuned for maximum probability calibration and ROC-AUC
    clf = HistGradientBoostingClassifier(
        max_depth=4,
        learning_rate=0.03,
        max_iter=300,
        min_samples_leaf=15,
        l2_regularization=0.5,
        categorical_features=cat_idx,
        random_state=42
    ).fit(Xtr, ytr_c)

    print(f"\n=================================================================")
    print(f"  OPTIMIZED MODEL EVALUATION ON UNSEEN HOLDOUT (80/20 TIME SPLIT)")
    print(f"=================================================================")
    print(f"Train Dataset   : {len(train)} IPOs ({train.listing_date.min().date()} to {train.listing_date.max().date()})")
    print(f"Holdout Dataset : {len(holdout)} IPOs ({holdout.listing_date.min().date()} to {holdout.listing_date.max().date()})")
    
    print("\n--- Regression (Listing Gain % Prediction) ---")
    pred_r = reg.predict(Xte)
    mae_model = mean_absolute_error(yte_r, pred_r)
    mae_mean = mean_absolute_error(yte_r, np.full(len(yte_r), ytr_r.mean()))
    print(f"Model MAE        : {mae_model:.2f}%")
    print(f"Baseline (Mean)  : {mae_mean:.2f}%")
    print(f"MAE Improvement  : {mae_mean - mae_model:+.2f}% lower error than historical mean baseline")
    
    g = holdout.gmp_pct
    m = g.notna()
    if m.sum() > 5:
        mae_gmp = mean_absolute_error(yte_r[m], g[m])
        mae_model_gmp = mean_absolute_error(yte_r[m], pred_r[m])
        print(f"Baseline (GMP)   : {mae_gmp:.2f}% (on {m.sum()} holdout rows with GMP)")
        print(f"Model on GMP sub : {mae_model_gmp:.2f}%")

    print("\n--- Classification (Probability Gain > 10%) ---")
    pred_p = clf.predict_proba(Xte)[:, 1]
    acc = accuracy_score(yte_c, pred_p > 0.5)
    majority = max(yte_c.mean(), 1 - yte_c.mean())
    auc = roc_auc_score(yte_c, pred_p)
    print(f"Model Accuracy   : {acc*100:.1f}%")
    print(f"Majority Baseline: {majority*100:.1f}%")
    print(f"Model ROC-AUC    : {auc:.3f} (0.5 = random guess, 1.0 = perfect)")
    if m.sum() > 5:
        auc_gmp = roc_auc_score(yte_c[m], g[m])
        print(f"GMP-only ROC-AUC : {auc_gmp:.3f}")

    # Save the trained model artifact
    os.makedirs("model", exist_ok=True)
    joblib.dump({
        "reg": reg,
        "clf": clf,
        "levels": levels,
        "features": list(Xtr.columns),
        "base_features": FEATURES,
        "cat_idx": cat_idx,
        "train_rows": len(train),
        "holdout_rows": len(holdout),
        "train_date_range": f"{train.listing_date.min().date()} to {train.listing_date.max().date()}",
        "holdout_date_range": f"{holdout.listing_date.min().date()} to {holdout.listing_date.max().date()}"
    }, "model/ipo_model.joblib")
    
    print(f"\nModel saved to model/ipo_model.joblib.")
    print("NOTE: Model was trained strictly on data/ipo_train.csv and has NOT seen data/ipo_holdout_test.csv.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/ipo_master.csv")
