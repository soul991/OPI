#!/usr/bin/env python3
"""
Comparison report: 11:45 AM PREVIEW estimate vs final FORWARD estimate vs actual listing gain.
Read-only research benchmark. Informs future exploration of intraday subscription modeling.
"""

from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
PREVIEW_LOG = ROOT_DIR / "predictions" / "preview_log.csv"
PREDICTION_LOG = ROOT_DIR / "predictions" / "prediction_log.csv"


def main() -> None:
    print("=" * 80)
    print("  OPI PREVIEW vs FORWARD ESTIMATE ACCURACY COMPARISON REPORT")
    print("=" * 80)

    if not PREVIEW_LOG.exists():
        print(f"No preview log found at {PREVIEW_LOG}. 0 preview records collected.")
        return

    preview_df = pd.read_csv(PREVIEW_LOG)
    if len(preview_df) == 0:
        print("preview_log.csv is empty (0 records).")
        return

    if not PREDICTION_LOG.exists():
        print("prediction_log.csv not found.")
        return

    pred_df = pd.read_csv(PREDICTION_LOG)
    forward_df = pred_df[pred_df["status"] == "FORWARD"].copy()

    # Merge on company and close_date
    merged = pd.merge(
        preview_df,
        forward_df[["company", "close_date", "pred_gain_pct", "actual_gain_pct"]],
        on=["company", "close_date"],
        suffixes=("_preview", "_forward"),
        how="inner",
    )

    if len(merged) == 0:
        print(f"Total preview rows: {len(preview_df)}. Matching listed FORWARD rows: 0.")
        print("No paired PREVIEW vs FORWARD records resolved with actuals yet.")
        return

    print(f"\nPaired IPOs evaluated: {len(merged)}\n")
    print("| Company | Close Date | Preview Est | Forward Est | Actual Gain | Preview Error | Forward Error |")
    print("|---|:---:|:---:|:---:|:---:|:---:|:---:|")

    for _, row in merged.iterrows():
        comp = row["company"]
        c_date = row["close_date"]
        p_est = float(row.get("pred_gain_pct_preview", 0.0))
        f_est = float(row.get("pred_gain_pct_forward", 0.0))
        act = row.get("actual_gain_pct")
        if pd.notna(act):
            act_val = float(act)
            p_err = abs(p_est - act_val)
            f_err = abs(f_est - act_val)
            print(f"| {comp} | {c_date} | {p_est:+.2f}% | {f_est:+.2f}% | {act_val:+.2f}% | {p_err:.2f} pp | {f_err:.2f} pp |")
        else:
            print(f"| {comp} | {c_date} | {p_est:+.2f}% | {f_est:+.2f}% | Pending | N/A | N/A |")

    resolved = merged[pd.notna(merged["actual_gain_pct"])]
    if len(resolved) > 0:
        p_mae = (resolved["pred_gain_pct_preview"].astype(float) - resolved["actual_gain_pct"].astype(float)).abs().mean()
        f_mae = (resolved["pred_gain_pct_forward"].astype(float) - resolved["actual_gain_pct"].astype(float)).abs().mean()
        print("\nSummary Statistics (Descriptive Only):")
        print(f"  • Resolved paired count: n = {len(resolved)}")
        print(f"  • Preview MAE: {p_mae:.4f} pp")
        print(f"  • Forward MAE: {f_mae:.4f} pp")
        print(f"  • Difference: {p_mae - f_mae:+.4f} pp")


if __name__ == "__main__":
    main()
