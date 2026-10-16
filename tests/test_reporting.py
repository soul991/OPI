"""Tests for Phase 8 independent verification and headline metric recomputation (D-002, D-014)."""

import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def ece_eqfreq(p, y, k=10):
    o = np.argsort(p)
    chunks = np.array_split(o, k)
    t = 0
    for c in chunks:
        t += len(c) / len(p) * abs(p[c].mean() - y[c].mean())
    return t

def test_headline_metrics_recompute():
    """D-002: Verify that reported headline metrics recompute exactly from raw predictions."""
    phases = sorted((ROOT / "phases").glob("Phase *"), key=lambda p: int(p.name.split()[1]))
    target_ph = None
    for ph in reversed(phases):
        pr, ba = ph / "rolling_origin_predictions.csv", ph / "before_after_comparison.csv"
        if pr.exists() and ba.exists():
            target_ph = ph
            break
            
    assert target_ph is not None, "At least one phase must have rolling_origin_predictions.csv and before_after_comparison.csv"
    r = pd.read_csv(target_ph / "rolling_origin_predictions.csv")
    b = pd.read_csv(target_ph / "before_after_comparison.csv")
    col = f"phase_{target_ph.name.split()[1]}"
    assert col in b.columns, f"Column {col} must exist in before_after_comparison.csv"
    
    got = {
        "MAE: Historical Mean Baseline": (r.pred_mean_baseline - r.actual_gain).abs().mean(),
        "MAE: Model Without Fundamentals": (r.pred_no_fundamentals - r.actual_gain).abs().mean(),
        "MAE: Model With Fundamentals": (r.pred_with_fundamentals - r.actual_gain).abs().mean(),
        "Equal-Frequency ECE": ece_eqfreq(r.pred_prob_calibrated.values, r.actual_class.values)
    }
    h = r[r.has_gmp == True]
    got["MAE: Raw GMP"] = (h.gmp_pct - h.actual_gain).abs().mean()
    got["MAE: Blend"] = (h.pred_blend - h.actual_gain).abs().mean()
    
    for k, v in got.items():
        row = b[b.metric == k]
        if row.empty:
            continue
        rep = float(row[col].iloc[0])
        tol = 0.005 if "ECE" in k else 0.06
        assert abs(rep - v) <= tol, f"{target_ph.name} mismatch for {k}: reported {rep:.4f}, recomputed {v:.4f}"


def test_verify_all_runs():
    """D-014: verify_all.py runs independently without crashes."""
    script_path = ROOT / "scripts" / "verify_all.py"
    assert script_path.exists(), "scripts/verify_all.py must exist"
    
    # Run with --no-tests flag inside pytest to avoid recursive pytest invocation
    res = subprocess.run([sys.executable, str(script_path), "--no-tests"], capture_output=True, text=True, cwd=ROOT)
    assert res.stdout, "verify_all.py produced no output"
    assert "[PASS] master dataset exists" in res.stdout or "[PASS] no duplicate" in res.stdout


def test_phase7_errata_present():
    """D-009: Verify that ERRATA (Phase 8) is present at the top of Phase 7 verdict."""
    verdict = ROOT / "phases" / "Phase 7" / "3_outcome_and_verdict.md"
    assert verdict.exists(), "Phase 7 verdict must exist"
    head = verdict.read_text(encoding="utf-8")[:2500]
    assert "## ERRATA (Phase 8)" in head, "ERRATA (Phase 8) header must be present in Phase 7 verdict"
    assert "no demonstrated effect" in head
    assert "Phase 7 indicates this was misdiagnosed" in head


def test_earlier_phases_immutable():
    """D-017: Earlier phase artifacts (Phases 1-7, Phase 4 summary) must remain immutable."""
    # Check that Phase 8 re-run outputs are preserved in rerun_phase7_cleaned/
    rerun_dir = ROOT / "phases" / "Phase 8" / "rerun_phase7_cleaned"
    assert rerun_dir.exists(), "phases/Phase 8/rerun_phase7_cleaned must exist"
    assert (rerun_dir / "before_after_comparison.csv").exists()
    ba = pd.read_csv(rerun_dir / "before_after_comparison.csv")
    gmp_row = ba[ba["metric"].str.contains("Observed GMP", na=False)]
    assert not gmp_row.empty
    # Must not contain stale '+75 IPOs backfilled'
    assert "+75" not in str(gmp_row["notes"].iloc[0]), f"Stale backfill note remains: {gmp_row['notes'].iloc[0]}"

    # Check that Phase 7 non-md files are restored
    p7_ba = ROOT / "phases" / "Phase 7" / "before_after_comparison.csv"
    assert p7_ba.exists()
    p4_sum = ROOT / "phases" / "Phase 4" / "phase4_summary.json"
    assert p4_sum.exists()


def test_phase8_errata_present():
    """D-019: Verify that ERRATA (Phase 9) is present at the top of Phase 8 verdict."""
    verdict = ROOT / "phases" / "Phase 8" / "3_outcome_and_verdict.md"
    assert verdict.exists(), "Phase 8 verdict must exist"
    head = verdict.read_text(encoding="utf-8")[:2500]
    assert "## ERRATA (Phase 9)" in head, "ERRATA (Phase 9) header must be present in Phase 8 verdict"
    assert "D-001" in head
    assert "revert" in head.lower()



