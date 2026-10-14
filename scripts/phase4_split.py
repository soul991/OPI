#!/usr/bin/env python3
"""Phase 4 Task 1: Three-Way Chronological Dataset Split & Baseline Evaluation.

Creates three strictly chronological partitions from the master dataset:
  1. Train: listing_date < 2025-06-01 (historical training foundation)
  2. Validation: 2025-06-01 <= listing_date < 2026-06-01 (tuning & probability calibration)
  3. Final Test (Frozen): listing_date >= 2026-06-01 (out-of-sample benchmark, evaluated once)

Saves:
  - data/ipo_train.csv
  - data/ipo_val.csv
  - data/ipo_final_test.csv

Scores the Phase 2 baseline model (model/ipo_model.joblib) on the frozen final test set
to establish reference benchmarks (MAE, ROC-AUC, Accuracy).

Usage:
    python scripts/phase4_split.py
"""
import os
import sys
import argparse
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, roc_auc_score, accuracy_score

# Ensure model directory is on import path for prep function
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "model"))

try:
    from train import prep
except ImportError:
    # Fallback definition if model.train cannot be imported directly
    ALL_NUM = [
        "issue_price", "issue_size_cr", "fresh_issue_pct", "ofs_pct", "lot_size",
        "sub_qib", "sub_nii", "sub_retail", "sub_total", "pe_ratio", "peer_median_pe",
        "roe", "roce", "debt_equity", "revenue_growth_pct", "pat_margin_pct",
        "gmp_pct", "nifty_30d_return", "india_vix", "recent_ipo_avg_gain"
    ]
    CAT = ["sector", "exchange"]
    NUM = [c for c in ALL_NUM if c not in ["roe", "roce", "revenue_growth_pct", "pat_margin_pct"]]

    def prep(df, cat_levels=None):
        X = pd.DataFrame(index=df.index)
        for c in NUM:
            X[c] = pd.to_numeric(df[c], errors="coerce") if c in df else np.nan
        levels = cat_levels or {c: sorted(df[c].dropna().astype(str).unique()) for c in CAT}
        for c in CAT:
            if c in df:
                X[c] = pd.Categorical(df[c].astype(str), categories=levels[c]).codes
            else:
                X[c] = -1
        X["pe_vs_peer"] = X["pe_ratio"] / X["peer_median_pe"].replace(0, np.nan)
        X["sub_retail_vs_qib"] = X["sub_retail"] / X["sub_qib"].replace(0, np.nan)
        X["sub_hni_vs_retail"] = X["sub_nii"] / X["sub_retail"].replace(0, np.nan)
        X["log_issue_size"] = np.log1p(X["issue_size_cr"].clip(lower=0))
        X["is_high_vix"] = (X["india_vix"] > 18.0).astype(float)
        X["gmp_vs_recent_avg"] = X["gmp_pct"] - X["recent_ipo_avg_gain"]
        X["log_sub_total"] = np.log1p(X["sub_total"].clip(lower=0))
        X["log_sub_qib"] = np.log1p(X["sub_qib"].clip(lower=0))
        X["log_sub_nii"] = np.log1p(X["sub_nii"].clip(lower=0))
        X["log_sub_retail"] = np.log1p(X["sub_retail"].clip(lower=0))
        X["qib_demand_share"] = X["sub_qib"] / (X["sub_total"].replace(0, np.nan))
        X["gmp_x_sub"] = X["gmp_pct"] * np.log1p(X["sub_total"].clip(lower=0))
        return X, levels


def create_splits(master_path="data/ipo_master.csv",
                  train_path="data/ipo_train.csv",
                  val_path="data/ipo_val.csv",
                  test_path="data/ipo_final_test.csv"):
    """Read master dataset, validate schema, split chronologically, and save files."""
    if not os.path.exists(master_path):
        raise FileNotFoundError(f"Master dataset not found at '{master_path}'")

    print(f"\n================================================================================")
    print(f"  PHASE 4 TASK 1: CREATING THREE-WAY CHRONOLOGICAL DATASET SPLIT")
    print(f"================================================================================")
    print(f"Reading master dataset from: {master_path}")
    df = pd.read_csv(master_path)
    total_raw = len(df)
    print(f"Total records in master: {total_raw}")

    # Standardize and sort chronologically
    if "listing_date" not in df.columns:
        raise ValueError("Missing required column 'listing_date' in master dataset")

    df["listing_date_dt"] = pd.to_datetime(df["listing_date"], errors="coerce")
    if df["listing_date_dt"].isna().any():
        bad_cnt = df["listing_date_dt"].isna().sum()
        raise ValueError(f"Found {bad_cnt} rows with invalid/missing 'listing_date'")

    df = df.sort_values("listing_date_dt").reset_index(drop=True)

    # Date split boundaries
    train_mask = df["listing_date_dt"] < pd.Timestamp("2025-06-01")
    val_mask = (df["listing_date_dt"] >= pd.Timestamp("2025-06-01")) & (df["listing_date_dt"] < pd.Timestamp("2026-06-01"))
    test_mask = df["listing_date_dt"] >= pd.Timestamp("2026-06-01")

    # Drop temporary datetime sorting column before saving
    train = df[train_mask].drop(columns=["listing_date_dt"]).copy().reset_index(drop=True)
    val = df[val_mask].drop(columns=["listing_date_dt"]).copy().reset_index(drop=True)
    test = df[test_mask].drop(columns=["listing_date_dt"]).copy().reset_index(drop=True)

    # Integrity verification
    assert len(train) + len(val) + len(test) == len(df), "Row count mismatch across splits!"
    assert len(train) > 0, "Train split is empty!"
    assert len(val) > 0, "Validation split is empty!"
    assert len(test) > 0, "Final test split is empty!"

    # Ensure parent output directories exist
    for p in [train_path, val_path, test_path]:
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)

    train.to_csv(train_path, index=False)
    val.to_csv(val_path, index=False)
    test.to_csv(test_path, index=False)

    print(f"\nSuccessfully generated and saved chronological partitions:")
    print(f"  [1] Train set      -> {train_path}")
    print(f"  [2] Validation set -> {val_path}")
    print(f"  [3] Final Test set -> {test_path} (FROZEN)")

    def print_split_summary(name, split_df):
        dates = pd.to_datetime(split_df["listing_date"])
        d_min = dates.min().strftime("%Y-%m-%d")
        d_max = dates.max().strftime("%Y-%m-%d")
        gmp_cnt = split_df["gmp_pct"].notna().sum()
        gmp_pct = (gmp_cnt / len(split_df)) * 100
        mean_g = split_df["listing_gain_pct"].mean()
        med_g = split_df["listing_gain_pct"].median()
        win_rate = (split_df["listing_gain_pct"] > 10.0).mean() * 100
        flop_rate = (split_df["listing_gain_pct"] < 0.0).mean() * 100

        print(f"\n--- {name.upper()} PARTITION SUMMARY ---")
        print(f"  Row Count         : {len(split_df)} IPOs ({len(split_df)/len(df)*100:.1f}% of master)")
        print(f"  Listing Date Range: {d_min}  to  {d_max}")
        print(f"  Mean Listing Gain : {mean_g:+.2f}%")
        print(f"  Median Gain       : {med_g:+.2f}%")
        print(f"  Win Rate (> 10%)  : {win_rate:.1f}%")
        print(f"  Flop Rate (< 0%)  : {flop_rate:.1f}%")
        print(f"  GMP Availability  : {gmp_cnt} / {len(split_df)} ({gmp_pct:.1f}%)")

    print_split_summary("Train (< 2025-06-01)", train)
    print_split_summary("Validation (2025-06-01 to 2026-05-31)", val)
    print_split_summary("Final Test (>= 2026-06-01, Frozen)", test)

    return train, val, test


def score_phase2_model(test_df, train_df, model_path="model/ipo_model.joblib"):
    """Evaluate Phase 2 model artifact on the frozen final test set for benchmark reference."""
    print(f"\n================================================================================")
    print(f"  PHASE 2 MODEL BENCHMARK EVALUATION ON FROZEN FINAL TEST SET")
    print(f"================================================================================")
    if not os.path.exists(model_path):
        print(f"Warning: Model artifact '{model_path}' not found. Skipping Phase 2 scoring.")
        return None

    art = joblib.load(model_path)
    print(f"Loaded Phase 2 artifact from: {model_path}")
    print(f"Artifact training history   : {art.get('train_rows', '?')} rows ({art.get('train_date_range', '?')})")

    y_true_r = test_df["listing_gain_pct"].astype(float)
    y_true_c = (y_true_r > 10.0).astype(int)

    X_test, _ = prep(test_df, art["levels"])
    pred_r = art["reg"].predict(X_test)
    pred_proba = art["clf"].predict_proba(X_test)[:, 1]
    pred_c = (pred_proba > 0.5).astype(int)

    # Core required metrics
    mae = mean_absolute_error(y_true_r, pred_r)
    auc = roc_auc_score(y_true_c, pred_proba)
    acc = accuracy_score(y_true_c, pred_c) * 100.0

    # Baselines
    train_mean = train_df["listing_gain_pct"].mean()
    baseline_mae_mean = mean_absolute_error(y_true_r, np.full(len(y_true_r), train_mean))
    baseline_mae_zero = mean_absolute_error(y_true_r, np.zeros(len(y_true_r)))
    majority_acc = max(y_true_c.mean(), 1.0 - y_true_c.mean()) * 100.0

    print("\n--- Regression (Listing Gain % Prediction) ---")
    print(f"  Phase 2 Model MAE          : {mae:.2f}%")
    print(f"  Baseline (Train Mean) MAE  : {baseline_mae_mean:.2f}% (train mean = {train_mean:+.2f}%)")
    print(f"  Baseline (Zero Gain) MAE   : {baseline_mae_zero:.2f}%")
    print(f"  Model Advantage vs Mean    : {baseline_mae_mean - mae:+.2f}% lower error")

    # GMP Subset evaluation
    gmp_mask = test_df["gmp_pct"].notna()
    gmp_cnt = gmp_mask.sum()
    if gmp_cnt > 0:
        y_gmp_r = y_true_r[gmp_mask]
        gmp_val = test_df.loc[gmp_mask, "gmp_pct"].astype(float)
        mae_raw_gmp = mean_absolute_error(y_gmp_r, gmp_val)
        mae_model_gmp = mean_absolute_error(y_gmp_r, pred_r[gmp_mask])
        print(f"\n  [On {gmp_cnt} Test IPOs with GMP]")
        print(f"    Raw GMP Baseline MAE     : {mae_raw_gmp:.2f}%")
        print(f"    Phase 2 Model MAE        : {mae_model_gmp:.2f}%")
        print(f"    Raw GMP Advantage        : {mae_model_gmp - mae_raw_gmp:+.2f}%")

    print("\n--- Classification (Probability Gain > 10%) ---")
    print(f"  Phase 2 Model ROC-AUC      : {auc:.4f} (0.50 = random guess, 1.00 = perfect)")
    print(f"  Phase 2 Model Accuracy     : {acc:.2f}% (threshold = 0.50)")
    print(f"  Majority Class Baseline    : {majority_acc:.2f}%")

    if gmp_cnt > 0:
        y_gmp_c = y_true_c[gmp_mask]
        gmp_val = test_df.loc[gmp_mask, "gmp_pct"].astype(float)
        auc_raw_gmp = roc_auc_score(y_gmp_c, gmp_val)
        print(f"  Raw GMP ROC-AUC (subset)   : {auc_raw_gmp:.4f}")

    print("\n================================================================================")
    print("  SUMMARY OF BENCHMARK METRICS TO BEAT IN PHASE 4 (FINAL TEST SET):")
    print(f"  * Regression Target : MAE <= {mae:.2f}%")
    print(f"  * Classif. Target   : ROC-AUC >= {auc:.4f}")
    print(f"  * Accuracy Target   : Accuracy >= {acc:.2f}%")
    print("================================================================================\n")

    return {
        "mae": round(mae, 4),
        "roc_auc": round(auc, 4),
        "accuracy_pct": round(acc, 2),
        "baseline_mae_mean": round(baseline_mae_mean, 4),
        "majority_acc_pct": round(majority_acc, 2),
        "test_rows": len(test_df)
    }


def main():
    parser = argparse.ArgumentParser(description="Create Phase 4 chronological splits and score Phase 2 model.")
    parser.add_argument("--master", default="data/ipo_master.csv", help="Path to master dataset")
    parser.add_argument("--train-out", default="data/ipo_train.csv", help="Path for train split output")
    parser.add_argument("--val-out", default="data/ipo_val.csv", help="Path for validation split output")
    parser.add_argument("--test-out", default="data/ipo_final_test.csv", help="Path for final test output")
    parser.add_argument("--model", default="model/ipo_model.joblib", help="Path to Phase 2 model artifact")
    args = parser.parse_args()

    train, val, test = create_splits(
        master_path=args.master,
        train_path=args.train_out,
        val_path=args.val_out,
        test_path=args.test_out
    )

    metrics = score_phase2_model(test, train, model_path=args.model)
    return metrics


if __name__ == "__main__":
    main()
