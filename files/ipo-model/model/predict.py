#!/usr/bin/env python3
"""Score a new IPO. Usage: python model/predict.py new_ipo.csv"""
import sys
import joblib
import pandas as pd
sys.path.insert(0, "model")
from train import prep, FEATURES

def main(path):
    art = joblib.load("model/ipo_model.joblib")
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        one = pd.DataFrame([row])
        X, _ = prep(one, art["levels"])
        gain = art["reg"].predict(X)[0]
        prob = art["clf"].predict_proba(X)[0][1]
        missing = [c for c in FEATURES if pd.isna(row.get(c))]
        print(f"\n=== {row.get('company', 'IPO')} ===")
        print(f"Estimated listing gain : {gain:+.1f}%")
        print(f"P(gain > 10%)          : {prob*100:.0f}%")
        print(f"Missing inputs ({len(missing)}): {', '.join(missing) or 'none'}")
        if len(missing) > 6: print("WARNING: many inputs missing, treat this score as weak.")
        print("Decision aid only, not financial advice. Read the analyst notes for qualitative risks.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "new_ipo.csv")
