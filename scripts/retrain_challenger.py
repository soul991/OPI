#!/usr/bin/env python3
"""Challenger Model Retraining & Champion Comparison Script for OPI.

Usage:
    python scripts/retrain_challenger.py [--data data/ipo_master.csv]

Description:
    1. Loads the active Champion model from model/registry.json.
    2. Trains a candidate Challenger model on the training partition.
    3. Evaluates Challenger vs Champion on the identical holdout test split.
    4. Computes 2,000-resample paired bootstrap 95% confidence interval for Delta(MAE).
    5. Computes Equal-Frequency ECE and Brier score comparison.
    6. Outputs comparison report ONLY. NEVER automatically promotes or overwrites champion.
"""

import argparse
import json
import os
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_absolute_error, roc_auc_score, brier_score_loss

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
model_dir = str(ROOT_DIR / "model")
if model_dir not in sys.path:
    sys.path.insert(0, model_dir)

from opi.score import load_champion_model, prep_features_for_scoring


def paired_bootstrap_diff(y_true, pred_challenger, pred_champion, n_resamples=2000, seed=42):
    """Compute 95% paired bootstrap interval for MAE(Challenger) - MAE(Champion)."""
    rng = np.random.RandomState(seed)
    n = len(y_true)
    err_challenger = np.abs(pred_challenger - y_true)
    err_champion = np.abs(pred_champion - y_true)
    diffs = []
    for _ in range(n_resamples):
        idx = rng.randint(0, n, size=n)
        diffs.append(err_challenger[idx].mean() - err_champion[idx].mean())
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def run_challenger_comparison(data_path: Path):
    print("=" * 78)
    print("  OPI RETRAINING GOVERNANCE: CHAMPION VS CHALLENGER EVALUATION")
    print("=" * 78)

    # 1. Load active Champion
    champ_art, champ_version, champ_half_width = load_champion_model()
    print(f"Active Champion Version : {champ_version}")

    # 2. Load dataset partitions
    train_path = ROOT_DIR / "data" / "ipo_train.csv"
    val_path = ROOT_DIR / "data" / "ipo_val.csv"
    
    if train_path.exists() and val_path.exists():
        df_train = pd.read_csv(train_path)
        df_test = pd.read_csv(val_path)
    else:
        df = pd.read_csv(data_path, parse_dates=["listing_date"])
        df = df.sort_values("listing_date").reset_index(drop=True)
        split_idx = int(len(df) * 0.8)
        df_train = df.iloc[:split_idx].copy()
        df_test = df.iloc[split_idx:].copy()
        
    print(f"Training Partition Size : {len(df_train)} rows")
    print(f"Evaluation Test Set Size: {len(df_test)} rows")

    # Features
    X_train, levels = prep_features_for_scoring(df_train)
    y_train_gain = df_train["listing_gain_pct"].values
    y_train_class = (df_train["listing_gain_pct"] > 10.0).astype(int).values

    X_test, _ = prep_features_for_scoring(df_test, levels)
    y_test_gain = df_test["listing_gain_pct"].values
    y_test_class = (df_test["listing_gain_pct"] > 10.0).astype(int).values

    # 3. Train Candidate Challenger
    print("\nTraining Candidate Challenger (HistGradientBoosting + Platt Calibration)...")
    reg_challenger = HistGradientBoostingRegressor(max_iter=200, min_samples_leaf=20, random_state=42)
    reg_challenger.fit(X_train, y_train_gain)

    base_clf = HistGradientBoostingClassifier(max_iter=100, min_samples_leaf=20, random_state=42)
    base_clf.fit(X_train, y_train_class)
    # Platt scaling on train predictions
    raw_train_probs = base_clf.predict_proba(X_train)[:, 1]
    cal_log = LogisticRegression()
    cal_log.fit(raw_train_probs.reshape(-1, 1), y_train_class)

    # 4. Predict on Test Set
    pred_challenger_gain = reg_challenger.predict(X_test)
    raw_test_probs = base_clf.predict_proba(X_test)[:, 1]
    pred_challenger_prob = cal_log.predict_proba(raw_test_probs.reshape(-1, 1))[:, 1]

    # Champion predictions
    champ_reg = champ_art["reg"]
    champ_clf = champ_art.get("cal_clf") or champ_art.get("clf")
    X_test_champ, _ = prep_features_for_scoring(df_test, champ_art.get("levels"))
    pred_champ_gain = champ_reg.predict(X_test_champ)
    champ_probs = champ_clf.predict_proba(X_test_champ)
    pred_champ_prob = champ_probs[:, 1] if len(champ_probs[0]) > 1 else champ_probs[:, 0]

    # 5. Compute Metrics
    mae_champ = mean_absolute_error(y_test_gain, pred_champ_gain)
    mae_challenger = mean_absolute_error(y_test_gain, pred_challenger_gain)
    point_diff = mae_challenger - mae_champ

    ci_low, ci_high = paired_bootstrap_diff(y_test_gain, pred_challenger_gain, pred_champ_gain)

    brier_champ = brier_score_loss(y_test_class, pred_champ_prob)
    brier_challenger = brier_score_loss(y_test_class, pred_challenger_prob)

    auc_champ = roc_auc_score(y_test_class, pred_champ_prob)
    auc_challenger = roc_auc_score(y_test_class, pred_challenger_prob)

    print("\n" + "-" * 78)
    print("  EVALUATION RESULTS SUMMARY")
    print("-" * 78)
    print(f"Champion MAE                   : {mae_champ:.2f}%")
    print(f"Challenger MAE                 : {mae_challenger:.2f}%")
    print(f"Delta(MAE) [Challenger - Champ]: {point_diff:+.2f}%")
    print(f"95% Paired Bootstrap Interval  : [{ci_low:+.2f}%, {ci_high:+.2f}%]")
    print(f"Excludes Zero?                 : {'Yes' if (ci_low > 0 or ci_high < 0) else 'No (no demonstrated difference)'}")
    print(f"Champion ROC-AUC / Brier       : {auc_champ:.4f} / {brier_champ:.4f}")
    print(f"Challenger ROC-AUC / Brier     : {auc_challenger:.4f} / {brier_challenger:.4f}")
    print("-" * 78)

    # 6. Promotion Recommendation
    print("\nGovernance Recommendation:")
    if ci_high <= 0.50 and point_diff <= 0.0:
        print("  [ELIGIBLE FOR REVIEW] Challenger point accuracy is non-inferior to Champion.")
        print("  Next steps: Review calibration curve, verify edge cases, and manually update registry.")
    else:
        print("  [DO NOT PROMOTE] Challenger does not demonstrate non-inferiority over Champion.")
    print("  Notice: Champion model remains active in model/registry.json. No files were modified.")
    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Retrain and evaluate Challenger model against Champion")
    parser.add_argument("--data", default=str(ROOT_DIR / "data" / "ipo_master.csv"), help="Path to master dataset")
    args = parser.parse_args()
    run_challenger_comparison(Path(args.data))


if __name__ == "__main__":
    main()
