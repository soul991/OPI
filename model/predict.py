#!/usr/bin/env python3
"""Score a new IPO with calibrated probability, 80% conformal prediction interval, and regime routing.

Usage:
    python model/predict.py [new_ipo.csv]

Rules:
    - If GMP is observed: outputs expected return based on GMP, displays rule:
      "GMP observed: GMP is the primary signal, model is context"
    - If GMP is not available: outputs model estimate with regime-specific interval, displays rule:
      "no GMP: model estimate with the regime-specific interval"
"""
import os
import sys
import joblib
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "model"))

from train import prep, FEATURES

# Pre-registered regime conformal 80% interval half-width from out-of-sample residuals (Phase 7)
CONFORMAL_HALF_WIDTH_OBS_80 = 23.13
CONFORMAL_HALF_WIDTH_UNAVAIL_80 = 23.13  # Fallback when unavailable n < 40


def load_model():
    p4_path = os.path.join(ROOT_DIR, "model", "ipo_model_phase4.joblib")
    p2_path = os.path.join(ROOT_DIR, "model", "ipo_model.joblib")
    if os.path.exists(p4_path):
        return joblib.load(p4_path), "Phase 4 (Calibrated)"
    elif os.path.exists(p2_path):
        return joblib.load(p2_path), "Baseline"
    raise FileNotFoundError("No trained model artifact found in model/")


from opi.score import score_ipo, load_champion_model


def predict_ipo(df, art=None):
    for idx, row in df.iterrows():
        scored = score_ipo(row, custom_artifact=art)
        company = scored["company"]
        has_gmp = scored["gmp_pct"] is not None

        print(f"\n{'='*78}")
        print(f"  PREDICTION FOR: {company}")
        print(f"{'='*78}")

        if has_gmp:
            gmp_val = scored["gmp_pct"]
            print(f"Rule Applied            : {scored['rule_applied']}")
            print(f"Primary Expected Return : {gmp_val:+.2f}% (Raw GMP)")
            print(f"Model Point Estimate    : {scored['predicted_gain_pct']:+.2f}% (for context)")
            print(f"80% Conformal Interval  : [{scored['conformal_interval_80'][0]:+.2f}%, {scored['conformal_interval_80'][1]:+.2f}%] (width: {2*scored['conformal_half_width_80']:.1f}%)")
        else:
            print(f"Rule Applied            : {scored['rule_applied']}")
            print(f"Model Expected Return   : {scored['predicted_gain_pct']:+.2f}%")
            print(f"80% Conformal Interval  : [{scored['conformal_interval_80'][0]:+.2f}%, {scored['conformal_interval_80'][1]:+.2f}%] (width: {2*scored['conformal_half_width_80']:.1f}%)")
            print(f"Regime Note             : Insufficient historical unquoted issues (n < 40); interval uses pooled calibration.")

        print(f"Calibrated P(Gain > 10%): {scored['prob_gt10']*100:.1f}%")
        print(f"Reliability Guidance    : Do not rely on probabilities above ~0.85 or below ~0.10 as certainty.")

        missing = [c for c in FEATURES if pd.isna(row.get(c)) or str(row.get(c)).strip() == ""]
        print(f"Missing Inputs ({len(missing)}): {', '.join(missing) if missing else 'None'}")
        if len(missing) > 6:
            print("WARNING: Multiple inputs missing. Confidence in model output is reduced.")

        print(f"Disclaimer              : Decision aid only, not financial advice.")
        print(f"{'='*78}")


def main(path):
    if not os.path.exists(path):
        print(f"Error: file not found: {path}")
        sys.exit(1)
    art, version = load_model()
    df = pd.read_csv(path)
    predict_ipo(df, art)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "new_ipo.csv")
