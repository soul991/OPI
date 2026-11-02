import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from opi.score import score_ipo

df = pd.read_csv("predictions/prediction_log.csv")
nov1_rows = df[df["scored_at"].str.startswith("2026-11-01")].copy()

gmps = {
    "M.K.Sons Fine Jewels": 3.70,
    "BLS Polymers": 45.33,
    "SFC Environmental Technologies": 5.76,
    "EAAA India Alternatives": 1.68
}

print("=== Nov 1 Scored Rows: Model-Only vs With-GMP Comparison ===")
for _, row in nov1_rows.iterrows():
    comp = row["company"]
    feats = json.loads(row["features_snapshot_json"])
    gmp_val = gmps.get(comp)
    
    orig_gain = row["pred_gain_pct"]
    orig_prob = row["pred_prob_gt10"]
    
    feats_with_gmp = dict(feats)
    feats_with_gmp["gmp_pct"] = gmp_val
    res_gmp = score_ipo(feats_with_gmp)
    
    print(f"Company: {comp}")
    print(f"  Model-only (logged): Gain = {orig_gain}%, P(>10%) = {orig_prob}")
    print(f"  Discovered GMP: {gmp_val}%")
    print(f"  With GMP: Gain = {res_gmp['predicted_gain_pct']}%, P(>10%) = {res_gmp['prob_gt10']}, Rule = {res_gmp['rule_applied']}")
