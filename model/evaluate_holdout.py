#!/usr/bin/env python3
"""
Evaluate the trained IPO model strictly on the out-of-sample holdout dataset.
Compares the model's predictions with the actual listing gains, issue prices, and GMP.
Outputs a detailed CSV report: data/holdout_comparison_report.csv
"""
import sys
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, accuracy_score, roc_auc_score, r2_score

# Add model directory to path to reuse prep
sys.path.insert(0, os.path.dirname(__file__))
from train import prep

def main(holdout_path="data/ipo_holdout_test.csv", model_path="model/ipo_model.joblib"):
    if not os.path.exists(holdout_path):
        print(f"Error: holdout data '{holdout_path}' not found. Run train.py first.")
        sys.exit(1)
    if not os.path.exists(model_path):
        print(f"Error: model artifact '{model_path}' not found. Run train.py first.")
        sys.exit(1)
        
    art = joblib.load(model_path)
    df = pd.read_csv(holdout_path, parse_dates=["listing_date"]).sort_values("listing_date").reset_index(drop=True)
    
    X, _ = prep(df, art["levels"])
    pred_gains = art["reg"].predict(X)
    pred_probs = art["clf"].predict_proba(X)[:, 1]
    
    # Build evaluation dataframe
    res = pd.DataFrame({
        "company": df["company"],
        "sector": df["sector"],
        "listing_date": df["listing_date"].dt.strftime("%Y-%m-%d"),
        "issue_price": df["issue_price"],
        "listing_price": df["listing_price"],
        "actual_gain_pct": df["listing_gain_pct"],
        "predicted_gain_pct": pred_gains.round(2),
        "gmp_pct": df["gmp_pct"],
        "predicted_prob_good": (pred_probs * 100).round(1),
        "actual_good": df["label_good"],
        "predicted_good": (pred_probs > 0.5).astype(int),
        "sub_total": df["sub_total"],
        "sub_qib": df["sub_qib"],
        "sub_nii": df["sub_nii"],
        "sub_retail": df["sub_retail"],
        "issue_size_cr": df["issue_size_cr"],
    })
    
    res["model_abs_error"] = (res["predicted_gain_pct"] - res["actual_gain_pct"]).abs().round(2)
    res["gmp_abs_error"] = (res["gmp_pct"] - res["actual_gain_pct"]).abs().round(2)
    res["model_beats_gmp"] = res["model_abs_error"] < res["gmp_abs_error"]
    res["direction_correct"] = np.sign(res["predicted_gain_pct"]) == np.sign(res["actual_gain_pct"])
    res["classification_correct"] = res["predicted_good"] == res["actual_good"]
    
    report_path = "data/holdout_comparison_report.csv"
    res.to_csv(report_path, index=False)
    
    print("\n" + "="*80)
    print("       HOLDOUT DATASET EVALUATION: MODEL vs ACTUAL IPO OUTCOMES")
    print("="*80)
    print(f"Total unseen test IPOs evaluated : {len(res)}")
    print(f"Date range of unseen IPOs        : {res['listing_date'].min()} to {res['listing_date'].max()}")
    print(f"Model trained on                 : {art.get('train_rows', '?')} historical IPOs ({art.get('train_date_range', '?')})")
    
    print("\n--- OVERALL PERFORMANCE METRICS ---")
    mae_model = res["model_abs_error"].mean()
    print(f"Model Mean Absolute Error (MAE)  : {mae_model:.2f}%")
    
    valid_gmp = res.dropna(subset=["gmp_pct"])
    if len(valid_gmp) > 0:
        mae_gmp = valid_gmp["gmp_abs_error"].mean()
        mae_model_on_gmp = valid_gmp["model_abs_error"].mean()
        print(f"GMP-Only Baseline MAE            : {mae_gmp:.2f}%")
        print(f"Model MAE on same subset         : {mae_model_on_gmp:.2f}%")
        print(f"Advantage of Model over GMP      : {mae_gmp - mae_model_on_gmp:+.2f}% lower error")
        beats_cnt = valid_gmp["model_beats_gmp"].sum()
        print(f"IPOs where Model beat GMP        : {beats_cnt} / {len(valid_gmp)} ({beats_cnt/len(valid_gmp)*100:.1f}%)")
        
    acc = res["classification_correct"].mean() * 100
    dir_acc = res["direction_correct"].mean() * 100
    auc = roc_auc_score(res["actual_good"], pred_probs)
    print(f"Accuracy for Gain > 10%          : {acc:.1f}%")
    print(f"Directional Accuracy (+ / -)     : {dir_acc:.1f}%")
    print(f"ROC-AUC Score                    : {auc:.3f}")
    
    print("\n--- SAMPLE COMPARISONS: PREDICTED vs ACTUAL (Top 15 Recent IPOs) ---")
    sample_cols = ["company", "listing_date", "issue_price", "listing_price", "actual_gain_pct", "predicted_gain_pct", "gmp_pct", "model_abs_error"]
    print(res[sample_cols].tail(15).to_string(index=False))
    
    print(f"\nDetailed company-by-company report saved to: {report_path}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/ipo_holdout_test.csv")
