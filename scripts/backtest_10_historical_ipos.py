#!/usr/bin/env python3
"""Out-of-sample backtest across 10 landmark historical Indian IPOs.

For each of the 10 selected landmark IPOs (5 major flops/losses and 5 blockbuster growth/pops),
this script trains an independent, fresh machine learning model using STRICTLY pre-listing data
(all IPOs listed strictly before the target IPO's listing date).

Zero data leakage: No target IPO or subsequent IPO data is ever seen by the model.

Outputs:
  - data/historical_10_backtest.csv
  - Detailed console performance summary and direction accuracy metrics.
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from model.train import prep, CAT

TARGET_IPOS = [
    {
        "symbol": "ADLABS",
        "name": "Adlabs Entertainment",
        "category": "Flop / Loss",
        "index_in_master": 126,
        "description": "Theme park operator, poor institutional interest and weak demand"
    },
    {
        "symbol": "DMART",
        "name": "Avenue Supermarts (D-Mart)",
        "category": "Blockbuster / Pop",
        "index_in_master": 174,
        "description": "Radhakishan Damani's retail chain, massive 104x oversubscription"
    },
    {
        "symbol": "CLEDUCATE",
        "name": "CL Educate (Career Launcher)",
        "category": "Flop / Loss",
        "index_in_master": 175,
        "description": "Edtech/test-prep firm, poor NII subscription (0.21x) and overpricing"
    },
    {
        "symbol": "IRCTC",
        "name": "IRCTC",
        "category": "Blockbuster / Pop",
        "index_in_master": 247,
        "description": "Railway monopoly, PSU digital moat, massive 112x oversubscription"
    },
    {
        "symbol": "SBICARD",
        "name": "SBI Cards & Payment Services",
        "category": "Flop / Loss",
        "index_in_master": 254,
        "description": "High demand (26x) crushed on listing day by global COVID-19 pandemic crash"
    },
    {
        "symbol": "HAPPIEST",
        "name": "Happiest Minds Technologies",
        "category": "Blockbuster / Pop",
        "index_in_master": 258,
        "description": "Ashok Soota's digital IT services firm, 151x subscription frenzy"
    },
    {
        "symbol": "ZOMATO",
        "name": "Zomato",
        "category": "High Growth / Pop",
        "index_in_master": 296,
        "description": "India's first major tech consumer unicorn listing, strong tech hype"
    },
    {
        "symbol": "PAYTM",
        "name": "One 97 Communications (Paytm)",
        "category": "Flop / Loss",
        "index_in_master": 319,
        "description": "Mega-size ₹18,916 Cr issue, severe valuation excess, NII snub (0.24x)"
    },
    {
        "symbol": "LIC",
        "name": "Life Insurance Corporation (LIC)",
        "category": "Flop / Loss",
        "index_in_master": 344,
        "description": "Largest Indian IPO ₹21,008 Cr, heavy retail float, weak macro timing"
    },
    {
        "symbol": "TATATECH",
        "name": "Tata Technologies",
        "category": "Blockbuster / Pop",
        "index_in_master": 428,
        "description": "First Tata group IPO in 19 years, global ER&D, massive 51x subscription"
    }
]


def run_10_backtests():
    master_path = "data/ipo_master.csv"
    if not os.path.exists(master_path):
        print(f"Error: {master_path} not found.")
        sys.exit(1)

    df = pd.read_csv(master_path, parse_dates=["listing_date"]).sort_values("listing_date")

    print("=" * 100)
    print("      BACKTESTING 10 HISTORICAL LANDMARK INDIAN IPOS WITH 10 DISTINCT PRE-IPO MODELS")
    print("=" * 100)
    print("Rule: Strictly out-of-sample training (listing_date < target_ipo_date). ZERO lookahead leakage.\n")

    results = []

    for item in TARGET_IPOS:
        idx = item["index_in_master"]
        target_row = df.loc[idx]
        company = target_row["company"]
        ipo_date = target_row["listing_date"]
        actual_gain = float(target_row["listing_gain_pct"])
        issue_price = float(target_row["issue_price"])
        listing_price = float(target_row["listing_price"])

        # Strictly pre-IPO slice
        train_df = df[df["listing_date"] < ipo_date].copy().reset_index(drop=True)
        train_count = len(train_df)

        # Feature prep
        Xtr, levels = prep(train_df)
        valid_cols = [c for c in Xtr.columns if len(Xtr[c].dropna().unique()) >= 2]
        Xtr = Xtr[valid_cols]

        ytr_r = train_df["listing_gain_pct"]
        ytr_c = (ytr_r > 10.0).astype(int)

        valid_cats = [c for c in CAT if c in valid_cols]
        cat_idx = [list(Xtr.columns).index(c) for c in valid_cats]

        # Fit Model
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

        clf = HistGradientBoostingClassifier(
            max_depth=4,
            learning_rate=0.03,
            max_iter=300,
            min_samples_leaf=15,
            l2_regularization=0.5,
            categorical_features=cat_idx,
            random_state=42
        ).fit(Xtr, ytr_c)

        # Feature prep for target
        target_df = pd.DataFrame([target_row])
        Xt, _ = prep(target_df, levels)
        Xt = Xt[valid_cols]

        pred_gain = float(reg.predict(Xt)[0])
        pred_prob_success = float(clf.predict_proba(Xt)[0][1])

        # Recommendation logic based on model signals
        if pred_prob_success >= 0.70 and pred_gain >= 15.0:
            signal = "APPLY (High Conviction)"
        elif pred_prob_success >= 0.50 and pred_gain >= 8.0:
            signal = "APPLY (Moderate)"
        elif pred_prob_success <= 0.20 or pred_gain < 2.0:
            signal = "AVOID (High Risk / Flop)"
        else:
            signal = "NEUTRAL / CAUTION"

        direction_correct = (
            (pred_gain > 5.0 and actual_gain > 0.0) or
            (pred_gain <= 5.0 and actual_gain <= 5.0)
        )

        results.append({
            "symbol": item["symbol"],
            "company_name": company,
            "category": item["category"],
            "listing_date": str(ipo_date.date()),
            "train_samples": train_count,
            "issue_price": issue_price,
            "listing_price": listing_price,
            "sub_total": float(target_row["sub_total"]) if pd.notnull(target_row["sub_total"]) else np.nan,
            "issue_size_cr": float(target_row["issue_size_cr"]) if pd.notnull(target_row["issue_size_cr"]) else np.nan,
            "predicted_gain_pct": round(pred_gain, 2),
            "actual_gain_pct": round(actual_gain, 2),
            "error_pct": round(pred_gain - actual_gain, 2),
            "prob_gain_gt_10pct": round(pred_prob_success * 100, 1),
            "model_signal": signal,
            "direction_correct": direction_correct,
            "description": item["description"]
        })

    res_df = pd.DataFrame(results)
    out_csv = "data/historical_10_backtest.csv"
    res_df.to_csv(out_csv, index=False)
    print(f"Results saved to {out_csv}\n")

    # Display clean table
    display_cols = [
        "company_name", "listing_date", "train_samples",
        "predicted_gain_pct", "actual_gain_pct", "prob_gain_gt_10pct",
        "model_signal", "direction_correct"
    ]
    print(res_df[display_cols].to_string(index=False))

    # Summary metrics
    n_correct = res_df["direction_correct"].sum()
    print("\n" + "=" * 100)
    print(f"OVERALL DIRECTIONAL ACCURACY ACROSS 10 EXTREME IPOS: {n_correct}/10 ({n_correct*10}%)")
    print("=" * 100)


if __name__ == "__main__":
    run_10_backtests()
