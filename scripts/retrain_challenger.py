#!/usr/bin/env python3
"""Challenger Model Retraining & Champion Comparison Script for OPI.

Usage:
    python scripts/retrain_challenger.py [--data data/ipo_master.csv] [--no-rolling]

Description:
    1. Loads the active Champion model from model/registry.json.
    2. Implements walk-forward expanding rolling-origin evaluation across historical
       test quarters (2022Q1 to 2026Q4) matching docs/retraining_policy.md.
    3. Trains Challenger model on historical partitions and scores out-of-sample issues.
    4. Evaluates Challenger vs Champion on identical out-of-sample issues.
    5. Computes 2,000-resample paired bootstrap 95% confidence interval for Delta(MAE).
    6. Computes Equal-Frequency ECE (10 bins), Brier score, and 80% Conformal Coverage.
    7. Evaluates against all 4 promotion criteria in docs/retraining_policy.md.
    8. Outputs comparison report ONLY. NEVER automatically promotes or overwrites champion.
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


def ece_eqfreq(p, y, k=10):
    """Compute Equal-Frequency Expected Calibration Error with k bins."""
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(p) == 0:
        return 0.0
    o = np.argsort(p)
    chunks = np.array_split(o, k)
    t = 0.0
    for c in chunks:
        if len(c) > 0:
            t += (len(c) / len(p)) * abs(p[c].mean() - y[c].mean())
    return float(t)


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


def run_challenger_comparison(data_path: Path, rolling: bool = True):
    print("=" * 78)
    print("  OPI RETRAINING GOVERNANCE: CHAMPION VS CHALLENGER EVALUATION")
    print("=" * 78)

    # 1. Load active Champion
    champ_art, champ_version, champ_half_width = load_champion_model()
    print(f"Active Champion Version : {champ_version}")

    if not data_path.exists():
        raise FileNotFoundError(f"Dataset path not found: {data_path}")

    df_raw = pd.read_csv(data_path)
    df_raw["listing_date"] = pd.to_datetime(df_raw["listing_date"], errors="coerce")
    df = df_raw.dropna(subset=["listing_date", "listing_gain_pct"]).sort_values("listing_date").reset_index(drop=True)
    df["actual_gain"] = pd.to_numeric(df["listing_gain_pct"], errors="coerce")
    df["actual_class"] = (df["actual_gain"] > 10.0).astype(int)

    if rolling:
        df["quarter"] = df["listing_date"].dt.to_period("Q")
        test_quarters = sorted([q for q in df["quarter"].dropna().unique() if q >= pd.Period("2022Q1")])
        print(f"Dataset Master Rows     : {len(df)} rows")
        print(f"Rolling Test Quarters   : {len(test_quarters)} ({test_quarters[0]} to {test_quarters[-1]})")

        all_y_true = []
        all_y_class = []
        all_pred_champ_gain = []
        all_pred_champ_prob = []
        all_pred_chall_gain = []
        all_pred_chall_prob = []

        champ_reg = champ_art["reg"]
        champ_clf = champ_art.get("cal_clf") or champ_art.get("clf")
        champ_levels = champ_art.get("levels")

        for q in test_quarters:
            q_start = q.start_time
            q_end = q.end_time

            train_df = df[df["listing_date"] < q_start].copy().reset_index(drop=True)
            test_df = df[(df["listing_date"] >= q_start) & (df["listing_date"] <= q_end)].copy().reset_index(drop=True)

            if len(test_df) == 0 or len(train_df) < 50:
                continue

            # Feature matrices for Challenger
            X_tr, tr_levels = prep_features_for_scoring(train_df)
            y_tr_gain = train_df["actual_gain"].values
            y_tr_class = train_df["actual_class"].values

            X_te, _ = prep_features_for_scoring(test_df, tr_levels)
            y_te_gain = test_df["actual_gain"].values
            y_te_class = test_df["actual_class"].values

            # Filter columns with at least 2 distinct non-null values for HistGradientBoosting binning
            valid_cols = [c for c in X_tr.columns if X_tr[c].dropna().nunique() >= 2]
            X_tr_f = X_tr[valid_cols]
            X_te_f = X_te[valid_cols]

            # Train Challenger regressor + classifier on train_df
            chall_reg = HistGradientBoostingRegressor(max_iter=200, min_samples_leaf=20, random_state=42)
            chall_reg.fit(X_tr_f, y_tr_gain)

            chall_clf = HistGradientBoostingClassifier(max_iter=100, min_samples_leaf=20, random_state=42)
            chall_clf.fit(X_tr_f, y_tr_class)

            raw_tr_probs = chall_clf.predict_proba(X_tr_f)[:, 1]
            cal_log = LogisticRegression()
            cal_log.fit(raw_tr_probs.reshape(-1, 1), y_tr_class)

            pred_chall_gain = chall_reg.predict(X_te_f)
            raw_te_probs = chall_clf.predict_proba(X_te_f)[:, 1]
            pred_chall_prob = cal_log.predict_proba(raw_te_probs.reshape(-1, 1))[:, 1]

            # Champion predictions on test_df
            X_te_champ, _ = prep_features_for_scoring(test_df, champ_levels)
            pred_champ_g = champ_reg.predict(X_te_champ)
            champ_probs = champ_clf.predict_proba(X_te_champ)
            pred_champ_p = champ_probs[:, 1] if len(champ_probs[0]) > 1 else champ_probs[:, 0]

            all_y_true.extend(y_te_gain)
            all_y_class.extend(y_te_class)
            all_pred_champ_gain.extend(pred_champ_g)
            all_pred_champ_prob.extend(pred_champ_p)
            all_pred_chall_gain.extend(pred_chall_gain)
            all_pred_chall_prob.extend(pred_chall_prob)

        y_test_gain = np.array(all_y_true)
        y_test_class = np.array(all_y_class)
        pred_champ_gain = np.array(all_pred_champ_gain)
        pred_champ_prob = np.array(all_pred_champ_prob)
        pred_challenger_gain = np.array(all_pred_chall_gain)
        pred_challenger_prob = np.array(all_pred_chall_prob)
        print(f"Pooled Evaluated Issues : {len(y_test_gain)} rows")

    else:
        split_idx = int(len(df) * 0.8)
        df_train = df.iloc[:split_idx].copy()
        df_test = df.iloc[split_idx:].copy()
        print(f"Static Split Train/Test : {len(df_train)} / {len(df_test)} rows")

        X_train, levels = prep_features_for_scoring(df_train)
        y_train_gain = df_train["actual_gain"].values
        y_train_class = df_train["actual_class"].values

        X_test, _ = prep_features_for_scoring(df_test, levels)
        y_test_gain = df_test["actual_gain"].values
        y_test_class = df_test["actual_class"].values

        reg_challenger = HistGradientBoostingRegressor(max_iter=200, min_samples_leaf=20, random_state=42)
        reg_challenger.fit(X_train, y_train_gain)

        base_clf = HistGradientBoostingClassifier(max_iter=100, min_samples_leaf=20, random_state=42)
        base_clf.fit(X_train, y_train_class)
        raw_train_probs = base_clf.predict_proba(X_train)[:, 1]
        cal_log = LogisticRegression()
        cal_log.fit(raw_train_probs.reshape(-1, 1), y_train_class)

        pred_challenger_gain = reg_challenger.predict(X_test)
        raw_test_probs = base_clf.predict_proba(X_test)[:, 1]
        pred_challenger_prob = cal_log.predict_proba(raw_test_probs.reshape(-1, 1))[:, 1]

        champ_reg = champ_art["reg"]
        champ_clf = champ_art.get("cal_clf") or champ_art.get("clf")
        X_test_champ, _ = prep_features_for_scoring(df_test, champ_art.get("levels"))
        pred_champ_gain = champ_reg.predict(X_test_champ)
        champ_probs = champ_clf.predict_proba(X_test_champ)
        pred_champ_prob = champ_probs[:, 1] if len(champ_probs[0]) > 1 else champ_probs[:, 0]

    # Metrics
    mae_champ = float(mean_absolute_error(y_test_gain, pred_champ_gain))
    mae_challenger = float(mean_absolute_error(y_test_gain, pred_challenger_gain))
    point_diff = mae_challenger - mae_champ

    ci_low, ci_high = paired_bootstrap_diff(y_test_gain, pred_challenger_gain, pred_champ_gain)

    brier_champ = float(brier_score_loss(y_test_class, pred_champ_prob))
    brier_challenger = float(brier_score_loss(y_test_class, pred_challenger_prob))

    auc_champ = float(roc_auc_score(y_test_class, pred_champ_prob))
    auc_challenger = float(roc_auc_score(y_test_class, pred_challenger_prob))

    ece_champ = ece_eqfreq(pred_champ_prob, y_test_class, k=10)
    ece_challenger = ece_eqfreq(pred_challenger_prob, y_test_class, k=10)

    # Conformal 80% coverage check
    champ_cov = float(np.mean(np.abs(y_test_gain - pred_champ_gain) <= champ_half_width))
    chall_cov = float(np.mean(np.abs(y_test_gain - pred_challenger_gain) <= champ_half_width))

    print("\n" + "-" * 78)
    print("  EVALUATION RESULTS SUMMARY")
    print("-" * 78)
    print(f"Champion MAE                   : {mae_champ:.2f}%")
    print(f"Challenger MAE                 : {mae_challenger:.2f}%")
    print(f"Delta(MAE) [Challenger - Champ]: {point_diff:+.2f}%")
    print(f"95% Paired Bootstrap Interval  : [{ci_low:+.2f}%, {ci_high:+.2f}%]")
    print(f"Excludes Zero?                 : {'Yes' if (ci_low > 0 or ci_high < 0) else 'No (no demonstrated difference)'}")
    print(f"Equal-Frequency ECE (Champ/Chall): {ece_champ:.4f} / {ece_challenger:.4f} (Delta: {ece_challenger - ece_champ:+.4f})")
    print(f"Brier Score Loss (Champ/Chall) : {brier_champ:.4f} / {brier_challenger:.4f}")
    print(f"ROC-AUC (Champ/Chall)          : {auc_champ:.4f} / {auc_challenger:.4f}")
    print(f"80% Conformal Coverage (Champ) : {champ_cov*100:.1f}% (half-width: {champ_half_width:.2f}%)")
    print(f"80% Conformal Coverage (Chall) : {chall_cov*100:.1f}%")
    print("-" * 78)

    # 4 Governance Promotion Criteria (Policy Section 4)
    crit_1_non_inferior = (ci_high <= 0.50) and (point_diff <= 0.0)
    crit_2_calibration = (ece_challenger <= ece_champ + 0.01)
    crit_3_brier = (brier_challenger <= brier_champ + 0.005)
    crit_4_coverage = (0.75 <= chall_cov <= 0.95)

    print("\nGovernance Policy Checklist (docs/retraining_policy.md Section 4):")
    print(f"  1. Non-inferior Point Accuracy (CI_high <= +0.50%, Delta <= 0.0) : {'PASS' if crit_1_non_inferior else 'FAIL'}")
    print(f"  2. Calibration ECE Safeguard (ECE_chall <= ECE_champ + 0.01)       : {'PASS' if crit_2_calibration else 'FAIL'}")
    print(f"  3. Brier Score Loss Parity                                        : {'PASS' if crit_3_brier else 'FAIL'}")
    print(f"  4. Conformal 80% Coverage in [75%, 95%]                           : {'PASS' if crit_4_coverage else 'FAIL'}")

    eligible = crit_1_non_inferior and crit_2_calibration and crit_3_brier and crit_4_coverage

    print("\nGovernance Recommendation:")
    if eligible:
        print("  [ELIGIBLE FOR REVIEW] Challenger satisfies all promotion gating criteria.")
        print("  Next steps: Review calibration curve, verify edge cases, and manually update registry.")
    else:
        print("  [DO NOT PROMOTE] Challenger does not demonstrate non-inferiority over Champion.")
    print("  Notice: Champion model remains active in model/registry.json. No files were modified.")
    print("=" * 78 + "\n")

    return {
        "mae_champ": mae_champ,
        "mae_challenger": mae_challenger,
        "point_diff": point_diff,
        "ci_95": [ci_low, ci_high],
        "ece_champ": ece_champ,
        "ece_challenger": ece_challenger,
        "brier_champ": brier_champ,
        "brier_challenger": brier_challenger,
        "auc_champ": auc_champ,
        "auc_challenger": auc_challenger,
        "champ_cov": champ_cov,
        "chall_cov": chall_cov,
        "eligible_for_review": eligible
    }


def main():
    parser = argparse.ArgumentParser(description="Retrain and evaluate Challenger model against Champion")
    parser.add_argument("--data", default=str(ROOT_DIR / "data" / "ipo_master.csv"), help="Path to master dataset")
    parser.add_argument("--no-rolling", action="store_true", help="Use single static 80/20 split instead of rolling origin")
    args = parser.parse_args()
    run_challenger_comparison(Path(args.data), rolling=not args.no_rolling)


if __name__ == "__main__":
    main()
