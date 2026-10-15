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


def predict_ipo(df, art):
    reg = art.get("reg")
    clf = art.get("cal_clf") or art.get("clf")
    levels = art.get("levels")

    for idx, row in df.iterrows():
        company = str(row.get("company", f"IPO_{idx+1}"))
        one = pd.DataFrame([row])
        X, _ = prep(one, levels)

        gain_pred = float(reg.predict(X)[0])
        probs = clf.predict_proba(X)[0]
        prob_gt10 = float(probs[1]) if len(probs) > 1 else float(probs[0])

        raw_gmp = row.get("gmp_pct")
        has_gmp = pd.notna(raw_gmp) and str(raw_gmp).strip() != ""

        print(f"\n{'='*78}")
        print(f"  PREDICTION FOR: {company}")
        print(f"{'='*78}")

        if has_gmp:
            gmp_val = float(raw_gmp)
            lower_bound = gmp_val - CONFORMAL_HALF_WIDTH_OBS_80
            upper_bound = gmp_val + CONFORMAL_HALF_WIDTH_OBS_80
            print(f"Rule Applied            : GMP observed: GMP is the primary signal, model is context")
            print(f"Primary Expected Return : {gmp_val:+.2f}% (Raw GMP)")
            print(f"Model Point Estimate    : {gain_pred:+.2f}% (for context)")
            print(f"80% Conformal Interval  : [{lower_bound:+.2f}%, {upper_bound:+.2f}%] (width: {2*CONFORMAL_HALF_WIDTH_OBS_80:.1f}%)")
        else:
            lower_bound = gain_pred - CONFORMAL_HALF_WIDTH_UNAVAIL_80
            upper_bound = gain_pred + CONFORMAL_HALF_WIDTH_UNAVAIL_80
            print(f"Rule Applied            : no GMP: model estimate with the regime-specific interval")
            print(f"Model Expected Return   : {gain_pred:+.2f}%")
            print(f"80% Conformal Interval  : [{lower_bound:+.2f}%, {upper_bound:+.2f}%] (width: {2*CONFORMAL_HALF_WIDTH_UNAVAIL_80:.1f}%)")
            print(f"Regime Note             : Insufficient historical unquoted issues (n < 40); interval uses pooled calibration.")

        print(f"Calibrated P(Gain > 10%): {prob_gt10*100:.1f}%")
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
