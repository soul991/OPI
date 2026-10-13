#!/usr/bin/env python3
"""Phase 3 Execution Pipeline: Multi-Dataset Training & Out-of-Sample Backtesting.

Runs systematic experiments training models across separated datasets:
  1. Landmark Historical IPOs (10 independent models, zero data leakage)
  2. Dedicated Paytm Pre-IPO Scenario Analysis
  3. Market Regime Cross-Testing (Era 1: 2010-2019, Era 2: 2020-2021, Era 3: 2022-2023, Era 4: 2024-2026)

Saves all outputs and metric tables in phases/Phase 3/outputs/.
"""

import os
import sys
import shutil
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, accuracy_score, roc_auc_score

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, REPO_ROOT)
from model.train import prep, CAT

OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

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


def part_a_landmark_backtest(df):
    """Part A: Train 10 distinct out-of-sample models for 10 landmark IPOs."""
    print("=" * 80)
    print("  PART A: 10 HISTORICAL LANDMARK OUT-OF-SAMPLE BACKTEST MODELS")
    print("=" * 80)

    results = []
    for item in TARGET_IPOS:
        idx = item["index_in_master"]
        target_row = df.loc[idx]
        company = target_row["company"]
        ipo_date = target_row["listing_date"]
        actual_gain = float(target_row["listing_gain_pct"])

        # Strictly pre-IPO slice
        train_df = df[df["listing_date"] < ipo_date].copy().reset_index(drop=True)

        Xtr, levels = prep(train_df)
        valid_cols = [c for c in Xtr.columns if len(Xtr[c].dropna().unique()) >= 2]
        Xtr = Xtr[valid_cols]
        ytr_r = train_df["listing_gain_pct"]
        ytr_c = (ytr_r > 10.0).astype(int)

        valid_cats = [c for c in CAT if c in valid_cols]
        cat_idx = [list(Xtr.columns).index(c) for c in valid_cats]

        reg = HistGradientBoostingRegressor(
            loss="absolute_error", max_depth=4, learning_rate=0.03, max_iter=350,
            min_samples_leaf=15, l2_regularization=0.1, categorical_features=cat_idx, random_state=42
        ).fit(Xtr, ytr_r)

        clf = HistGradientBoostingClassifier(
            max_depth=4, learning_rate=0.03, max_iter=300,
            min_samples_leaf=15, l2_regularization=0.5, categorical_features=cat_idx, random_state=42
        ).fit(Xtr, ytr_c)

        Xt, _ = prep(pd.DataFrame([target_row]), levels)
        Xt = Xt[valid_cols]

        pred_gain = float(reg.predict(Xt)[0])
        pred_prob = float(clf.predict_proba(Xt)[0][1])

        if pred_prob >= 0.70 and pred_gain >= 15.0:
            signal = "APPLY (High Conviction)"
        elif pred_prob >= 0.50 and pred_gain >= 8.0:
            signal = "APPLY (Moderate)"
        elif pred_prob <= 0.20 or pred_gain < 2.0:
            signal = "AVOID (High Risk / Flop)"
        else:
            signal = "NEUTRAL / CAUTION"

        direction_correct = (
            (pred_gain > 5.0 and actual_gain > 0.0) or
            (pred_gain <= 5.0 and actual_gain <= 5.0)
        )

        results.append({
            "company_name": company,
            "listing_date": str(ipo_date.date()),
            "train_samples": len(train_df),
            "category": item["category"],
            "issue_price": float(target_row["issue_price"]),
            "listing_price": float(target_row["listing_price"]),
            "sub_total": float(target_row["sub_total"]),
            "predicted_gain_pct": round(pred_gain, 2),
            "actual_gain_pct": round(actual_gain, 2),
            "error_pct": round(pred_gain - actual_gain, 2),
            "prob_gain_gt_10pct": round(pred_prob * 100, 1),
            "model_signal": signal,
            "direction_correct": direction_correct,
            "description": item["description"]
        })

    res_df = pd.DataFrame(results)
    out_file = os.path.join(OUTPUTS_DIR, "historical_10_backtest.csv")
    res_df.to_csv(out_file, index=False)
    print(f"Saved: {out_file}")
    acc = res_df["direction_correct"].mean() * 100
    print(f"Directional Accuracy: {acc:.1f}% ({res_df['direction_correct'].sum()}/10)\n")
    return res_df


def part_b_paytm_scenarios(df):
    """Part B: In-depth Paytm pre-IPO testing across feature scenarios."""
    print("=" * 80)
    print("  PART B: PAYTM OUT-OF-SAMPLE SCENARIOS")
    print("=" * 80)

    pre_paytm = df[df["listing_date"] < "2021-11-18"].copy().reset_index(drop=True)
    Xtr, levels = prep(pre_paytm)
    valid_cols = [c for c in Xtr.columns if len(Xtr[c].dropna().unique()) >= 2]
    Xtr = Xtr[valid_cols]

    ytr_r = pre_paytm["listing_gain_pct"]
    ytr_c = (ytr_r > 10.0).astype(int)

    valid_cats = [c for c in CAT if c in valid_cols]
    cat_idx = [list(Xtr.columns).index(c) for c in valid_cats]

    reg = HistGradientBoostingRegressor(
        loss="absolute_error", max_depth=4, learning_rate=0.03, max_iter=350,
        min_samples_leaf=15, l2_regularization=0.1, categorical_features=cat_idx, random_state=42
    ).fit(Xtr, ytr_r)

    clf = HistGradientBoostingClassifier(
        max_depth=4, learning_rate=0.03, max_iter=300,
        min_samples_leaf=15, l2_regularization=0.5, categorical_features=cat_idx, random_state=42
    ).fit(Xtr, ytr_c)

    scenarios = [
        {
            "scenario": "Final Pre-Listing Setup (With GMP -1.4%)",
            "data": {
                "company": "One97 Communications (Paytm)", "sector": "IT & Technology", "exchange": "BOTH",
                "issue_price": 2150.0, "issue_size_cr": 18915.9, "lot_size": 6.0,
                "sub_qib": 2.79, "sub_nii": 0.24, "sub_retail": 1.66, "sub_total": 2.01,
                "fresh_issue_pct": 44.0, "ofs_pct": 56.0, "gmp_pct": -1.40,
                "nifty_30d_return": 0.40, "india_vix": 15.22, "recent_ipo_avg_gain": 55.16
            }
        },
        {
            "scenario": "Bidding Day 3 (Zero GMP Knowledge / Naive)",
            "data": {
                "company": "One97 Communications (Paytm)", "sector": "Financial Services", "exchange": "BOTH",
                "issue_price": 2150.0, "issue_size_cr": 18915.9, "lot_size": 6.0,
                "sub_qib": 2.79, "sub_nii": 0.24, "sub_retail": 1.66, "sub_total": 2.01,
                "fresh_issue_pct": 44.0, "ofs_pct": 56.0, "gmp_pct": np.nan,
                "nifty_30d_return": 0.40, "india_vix": 15.22, "recent_ipo_avg_gain": 55.16
            }
        },
        {
            "scenario": "Pre-Issue Announcement (Hype Scenario / Synthetic +10% GMP)",
            "data": {
                "company": "One97 Communications (Paytm)", "sector": "IT & Technology", "exchange": "BOTH",
                "issue_price": 2150.0, "issue_size_cr": 18915.9, "lot_size": 6.0,
                "sub_qib": 2.79, "sub_nii": 0.24, "sub_retail": 1.66, "sub_total": 2.01,
                "fresh_issue_pct": 44.0, "ofs_pct": 56.0, "gmp_pct": 10.0,
                "nifty_30d_return": 0.40, "india_vix": 15.22, "recent_ipo_avg_gain": 55.16
            }
        }
    ]

    p_results = []
    for s in scenarios:
        p_df = pd.DataFrame([s["data"]])
        Xp, _ = prep(p_df, levels)
        Xp = Xp[valid_cols]
        pred_gain = float(reg.predict(Xp)[0])
        pred_prob = float(clf.predict_proba(Xp)[0][1])

        p_results.append({
            "scenario": s["scenario"],
            "predicted_gain_pct": round(pred_gain, 2),
            "prob_gain_gt_10pct": round(pred_prob * 100, 1),
            "actual_open_discount_pct": -9.07,
            "actual_day_close_crash_pct": -27.25,
            "model_recommendation": "AVOID" if pred_prob < 20 else "NEUTRAL"
        })

    p_df_out = pd.DataFrame(p_results)
    out_file = os.path.join(OUTPUTS_DIR, "paytm_scenario_eval.csv")
    p_df_out.to_csv(out_file, index=False)
    print(f"Saved: {out_file}\n")
    return p_df_out


def part_c_regime_partitions(df):
    """Part C: Train models across distinct historical market regimes."""
    print("=" * 80)
    print("  PART C: MARKET REGIME CROSS-TESTING ACROSS HISTORICAL ERAS")
    print("=" * 80)

    regimes = [
        {"name": "Era 1: Pre-COVID Value (2010-2019)", "start": "2010-01-01", "end": "2019-12-31"},
        {"name": "Era 2: COVID Stimulus & Tech Euphoria (2020-2021)", "start": "2020-01-01", "end": "2021-12-31"},
        {"name": "Era 3: Global Rate Hikes & Reset (2022-2023)", "start": "2022-01-01", "end": "2023-12-31"},
        {"name": "Era 4: Retail Renaissance Wave (2024-2026)", "start": "2024-01-01", "end": "2026-12-31"}
    ]

    regime_metrics = []
    for reg_meta in regimes:
        sub = df[(df["listing_date"] >= reg_meta["start"]) & (df["listing_date"] <= reg_meta["end"])].copy().reset_index(drop=True)
        count = len(sub)
        mean_gain = sub["listing_gain_pct"].mean()
        median_gain = sub["listing_gain_pct"].median()
        win_rate = (sub["listing_gain_pct"] > 10.0).mean() * 100
        flop_rate = (sub["listing_gain_pct"] < 0.0).mean() * 100

        # Train a regime-dedicated model using 70/30 chronological split within the regime
        split_idx = int(count * 0.7)
        train_slice = sub.iloc[:split_idx]
        test_slice = sub.iloc[split_idx:]

        if len(test_slice) > 0:
            Xtr, levels = prep(train_slice)
            valid_cols = [c for c in Xtr.columns if len(Xtr[c].dropna().unique()) >= 2]
            Xtr = Xtr[valid_cols]
            ytr_r = train_slice["listing_gain_pct"]
            ytr_c = (ytr_r > 10.0).astype(int)

            valid_cats = [c for c in CAT if c in valid_cols]
            cat_idx = [list(Xtr.columns).index(c) for c in valid_cats]

            reg = HistGradientBoostingRegressor(
                loss="absolute_error", max_depth=3, learning_rate=0.03, max_iter=200,
                min_samples_leaf=10, categorical_features=cat_idx, random_state=42
            ).fit(Xtr, ytr_r)

            clf = HistGradientBoostingClassifier(
                max_depth=3, learning_rate=0.03, max_iter=150,
                min_samples_leaf=10, categorical_features=cat_idx, random_state=42
            ).fit(Xtr, ytr_c)

            Xt, _ = prep(test_slice, levels)
            Xt = Xt[valid_cols]
            pred_r = reg.predict(Xt)
            pred_c = clf.predict(Xt)

            mae = mean_absolute_error(test_slice["listing_gain_pct"], pred_r)
            acc = accuracy_score((test_slice["listing_gain_pct"] > 10.0).astype(int), pred_c)
        else:
            mae = np.nan
            acc = np.nan

        regime_metrics.append({
            "regime": reg_meta["name"],
            "date_range": f"{reg_meta['start']} to {reg_meta['end']}",
            "total_ipos": count,
            "mean_gain_pct": round(mean_gain, 2),
            "median_gain_pct": round(median_gain, 2),
            "actual_win_rate_pct": round(win_rate, 1),
            "actual_flop_rate_pct": round(flop_rate, 1),
            "regime_model_test_mae": round(mae, 2) if pd.notnull(mae) else np.nan,
            "regime_model_test_acc": round(acc * 100, 1) if pd.notnull(acc) else np.nan
        })

    reg_df = pd.DataFrame(regime_metrics)
    out_file = os.path.join(OUTPUTS_DIR, "regime_partition_metrics.csv")
    reg_df.to_csv(out_file, index=False)
    print(f"Saved: {out_file}\n")
    return reg_df


def main():
    master_path = os.path.join(REPO_ROOT, "data/ipo_master.csv")
    df = pd.read_csv(master_path, parse_dates=["listing_date"]).sort_values("listing_date")

    print("\nStarting Phase 3 Multi-Dataset & Out-of-Sample Evaluation Pipeline...")
    part_a_landmark_backtest(df)
    part_b_paytm_scenarios(df)
    part_c_regime_partitions(df)

    # Sync interactive chart to Phase 3 outputs
    src_chart = os.path.expanduser("~/.gemini/antigravity/brain/7cc8d153-69ef-4f5e-86be-0a63f8c30cfc/historical_10_backtest_chart.html")
    dst_chart = os.path.join(OUTPUTS_DIR, "historical_10_backtest_chart.html")
    if os.path.exists(src_chart):
        shutil.copyfile(src_chart, dst_chart)
        print(f"Synced chart to: {dst_chart}")

    print("\nPhase 3 execution complete! All outputs persisted to phases/Phase 3/outputs/.")


if __name__ == "__main__":
    main()
