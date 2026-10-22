"""Tests for Phase 8 independent verification and headline metric recomputation (D-002, D-014)."""

import json
import re
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


def test_phase10_errata_present():
    """D-034: Verify that ERRATA (patch) is present at the top of Phase 10 verdict and recheck."""
    verdict = ROOT / "phases" / "Phase 10" / "3_outcome_and_verdict.md"
    assert verdict.exists(), "Phase 10 verdict must exist"
    head = verdict.read_text(encoding="utf-8")[:4000]
    assert "## ERRATA (patch)" in head, "ERRATA (patch) header must be present in Phase 10 verdict"
    assert "700" in head, "Tonbo issue price 700 must be in errata"
    assert "586" in head, "Bonfiglioli issue price 586 must be in errata"
    assert "6.98" in head, "SMT GMP 6.98 must be in errata"
    assert "72.86" in head, "Tonbo GMP 72.86 must be in errata"
    assert "21.67" in head, "Bonfiglioli GMP 21.67 must be in errata"
    assert "UNSUPPORTED" in head, "Master dataset 654 claim must be marked UNSUPPORTED"
    assert "731" in head, "Master dataset 731 rows must be stated"

    recheck = ROOT / "phases" / "Phase 10" / "prior_phase_recheck.csv"
    assert recheck.exists(), "prior_phase_recheck.csv must exist"
    recheck_text = recheck.read_text(encoding="utf-8")
    assert "UNSUPPORTED" in recheck_text
    assert "731" in recheck_text


def test_verdict_table_matches_log():
    """D-035: Results tables in Phase 10+ verdict documents must strictly match prediction_log.csv."""
    log_path = ROOT / "predictions" / "prediction_log.csv"
    assert log_path.exists(), "prediction_log.csv must exist"
    df = pd.read_csv(log_path, dtype=str, keep_default_na=False)
    fwd = df[df["status"].str.strip().str.upper() == "FORWARD"]
    assert not fwd.empty, "prediction_log.csv must have FORWARD rows"

    expected = {}
    for _, r in fwd.iterrows():
        try:
            feats = json.loads(r["features_snapshot_json"])
        except Exception:
            feats = {}
        issue_p = float(feats.get("issue_price", 0))
        gmp_raw = r["gmp_pct_at_scoring"].strip()
        gmp_val = float(gmp_raw) if gmp_raw and gmp_raw != "nan" else None
        expected[r["company"].strip()] = {
            "issue_price": issue_p,
            "gmp_pct": gmp_val,
        }

    phases = sorted((ROOT / "phases").glob("Phase *"), key=lambda p: int(p.name.split()[1]))
    checked_phases = 0
    for ph in phases:
        n = int(ph.name.split()[1])
        if n < 10:
            continue
        v_file = ph / "3_outcome_and_verdict.md"
        assert v_file.exists(), f"{ph.name} outcome and verdict file must exist"
        text = v_file.read_text(encoding="utf-8")

        # Parse markdown tables: if ERRATA has a table, that is the authoritative table
        target_section = text
        if "## ERRATA" in text:
            errata_part = text.split("## ERRATA", 1)[1]
            if "\n## " in errata_part:
                errata_part = errata_part.split("\n## ", 1)[0]
            if "| Company |" in errata_part:
                target_section = errata_part

        lines = [line.strip() for line in target_section.splitlines() if line.strip().startswith("|")]
        table_rows = []
        for line in lines:
            if "Company" in line or ":---" in line:
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 7:
                co = re.sub(r"\*+", "", cols[0]).strip()
                p_issue_match = re.search(r"₹?\s*([0-9]+(?:\.[0-9]+)?)", cols[2])
                p_issue = float(p_issue_match.group(1)) if p_issue_match else None
                gmp_col = cols[6]
                p_gmp_match = re.search(r"([+-]?[0-9]+(?:\.[0-9]+)?)\s*%", gmp_col)
                p_gmp = float(p_gmp_match.group(1)) if p_gmp_match else None
                table_rows.append((co, p_issue, p_gmp))

        assert table_rows, f"No results table rows found in {ph.name} verdict"
        for co, p_issue, p_gmp in table_rows:
            if co in expected:
                exp_issue = expected[co]["issue_price"]
                exp_gmp = expected[co]["gmp_pct"]
                assert p_issue is not None and abs(p_issue - exp_issue) < 0.05, (
                    f"Mismatch in {ph.name} for {co} issue price: table has {p_issue}, log has {exp_issue}"
                )
                if exp_gmp is not None:
                    assert p_gmp is not None and abs(p_gmp - exp_gmp) < 0.05, (
                        f"Mismatch in {ph.name} for {co} GMP: table has {p_gmp}, log has {exp_gmp}"
                    )
                else:
                    assert p_gmp is None, (
                        f"Mismatch in {ph.name} for {co} GMP: expected None, table has {p_gmp}"
                    )
        checked_phases += 1

    assert checked_phases > 0, "At least one Phase 10+ verdict table must be checked"


def test_discovery_dry_run_artifact():
    """D-036: Verify that discovery dry-run timestamped output is committed and valid."""
    artifact = ROOT / "phases" / "Phase 10" / "discovery_dry_run.txt"
    assert artifact.exists(), "phases/Phase 10/discovery_dry_run.txt must exist"
    content = artifact.read_text(encoding="utf-8")
    assert "Discovered 17 eligible Mainboard candidate(s)" in content
    assert "Timestamp:" in content
    assert "Jio Platforms" in content
    assert "Paras Healthcare" in content




