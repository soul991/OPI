"""Unit tests for Phase 5 Gate A remediation verification.

Covers requirements R1 to R8:
- R1: Error distribution CSV and summary metrics match final test results.
- R2: Paired bootstrap intervals straddle zero (no demonstrated advantage).
- R3: Calibration target missed on out-of-sample frozen final test.
- R4: Reliability table column arithmetic strictly satisfies gap == abs(avg_pred - avg_actual).
- R6: Prediction log status column enforces exclusion of TEST_* and INVALID rows.
- R7: Zero absolute file:/// or /Users/ links in phases, README, scripts, or model.
- R8: Phase 4 test renamed to ipo_phase4_test_used.csv; Phase 5 final test empty.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
sys.path.insert(0, os.path.join(ROOT_DIR, "model"))

from phase4_train_evaluate import reliability_table, compute_ece
from forward_report import generate_forward_report


def test_r1_error_distribution_file_and_summary():
    """R1: phase4_error_distribution.csv exists with 75 rows and matching summary statistics."""
    csv_path = os.path.join(ROOT_DIR, "phases", "Phase 5", "phase4_error_distribution.csv")
    assert os.path.exists(csv_path), "phases/Phase 5/phase4_error_distribution.csv must exist"
    
    df = pd.read_csv(csv_path)
    assert len(df) == 75, f"Expected 75 rows in error distribution, got {len(df)}"
    
    err = df["model_error"].values
    mean_err = round(float(np.mean(err)), 2)
    median_err = round(float(np.median(err)), 2)
    p75 = round(float(np.percentile(err, 75)), 2)
    p90 = round(float(np.percentile(err, 90)), 2)
    max_err = round(float(np.max(err)), 2)

    assert mean_err == 12.19, f"Expected mean error 12.19%, got {mean_err}%"
    assert median_err == 8.29, f"Expected median error 8.29%, got {median_err}%"
    assert p75 == 14.20, f"Expected p75 error 14.20%, got {p75}%"
    assert p90 == 27.80, f"Expected p90 error 27.80%, got {p90}%"
    assert max_err == 83.24, f"Expected max error 83.24%, got {max_err}%"


def test_r1_errata_header_present():
    """R1: Top 3 lines of Phase 4 verdict must show ERRATA header."""
    verdict_path = os.path.join(ROOT_DIR, "phases", "Phase 4", "3_outcome_and_verdict.md")
    with open(verdict_path, "r", encoding="utf-8") as f:
        head_lines = [f.readline() for _ in range(3)]
    
    combined = "".join(head_lines)
    assert "ERRATA (Phase 5)" in combined, f"Expected ERRATA (Phase 5) in top 3 lines, got:\n{combined}"


def test_r2_paired_bootstrap_intervals():
    """R2: Paired bootstrap difference intervals for Blend vs GMP must straddle zero."""
    test_path = os.path.join(ROOT_DIR, "phases", "Phase 5", "phase4_error_distribution.csv")
    df = pd.read_csv(test_path)
    test_gmp = df[df["gmp_pct"].notna()].copy()
    assert len(test_gmp) == 8, "Expected 8 test IPOs with GMP"

    y_true = test_gmp["actual_gain_pct"].values
    raw_gmp = test_gmp["gmp_pct"].values
    model_pred = test_gmp["predicted_gain_pct"].values
    blend_pred = 0.55 * raw_gmp + 0.45 * model_pred

    err_gmp = np.abs(raw_gmp - y_true)
    err_blend = np.abs(blend_pred - y_true)

    # 2,000 resamples with fixed seed
    rng = np.random.RandomState(42)
    diffs = []
    n = len(test_gmp)
    for _ in range(2000):
        idx = rng.randint(0, n, size=n)
        diffs.append(err_blend[idx].mean() - err_gmp[idx].mean())

    ci = np.percentile(diffs, [2.5, 97.5])
    assert ci[0] <= 0 <= ci[1], f"Bootstrap interval for Δ(Blend - GMP) must include 0, got [{ci[0]:.4f}, {ci[1]:.4f}]"


def test_r3_calibration_target_missed_on_final_test():
    """R3: Final test ECE must be > 0.10, showing the calibration target was missed."""
    test_path = os.path.join(ROOT_DIR, "phases", "Phase 5", "phase4_error_distribution.csv")
    df = pd.read_csv(test_path)
    y_true = (df["actual_gain_pct"] > 10.0).astype(int).values
    y_prob = (df["pred_prob_gt10_cal"] / 100.0).values

    ece_uniform = compute_ece(y_true, y_prob, n_bins=10, strategy="uniform")
    ece_quantile = compute_ece(y_true, y_prob, n_bins=10, strategy="quantile")

    assert ece_uniform > 0.10, f"Expected uniform ECE > 0.10 (missed target), got {ece_uniform:.4f}"
    assert ece_quantile > 0.10, f"Expected quantile ECE > 0.10 (missed target), got {ece_quantile:.4f}"


def test_r4_reliability_table_gap_equals_abs_difference():
    """R4: For every bin in a reliability table, gap must strictly equal abs(avg_pred - avg_actual)."""
    # Test on synthetic data covering empty bins, full bins, extreme probs
    rng = np.random.RandomState(42)
    y_prob = rng.uniform(0, 1, size=100)
    y_true = (y_prob + rng.normal(0, 0.2, size=100) > 0.5).astype(int)

    for strat in ["uniform", "quantile"]:
        rt = reliability_table(y_true, y_prob, n_bins=10, strategy=strat)
        for _, row in rt.iterrows():
            if row["count"] > 0:
                pred = float(row["avg_predicted"])
                act = float(row["avg_actual"])
                gap = float(row["gap"])
                expected_gap = round(abs(pred - act), 3)
                assert abs(gap - expected_gap) < 1e-4, (
                    f"Bin {row['bin']} arithmetic mismatch in {strat} mode: "
                    f"|{pred} - {act}| = {expected_gap}, but table shows {gap}"
                )


def test_r6_prediction_log_status_and_filtering():
    """R6: prediction_log.csv has status column and metrics scripts exclude TEST_* and INVALID rows."""
    log_path = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")
    assert os.path.exists(log_path), "prediction_log.csv must exist"
    
    df = pd.read_csv(log_path)
    assert "status" in df.columns, "prediction_log.csv must have a 'status' column"

    # Verify existing rows
    kissht_rows = df[df["company"].astype(str).str.contains("Kissht", case=False)]
    assert not kissht_rows.empty, "Kisshtipo rows must exist in log"
    for _, r in kissht_rows.iterrows():
        assert r["status"] == "TEST_NOT_FORWARD", f"Kisshtipo row must be TEST_NOT_FORWARD, got {r['status']}"

    hyundai_rows = df[df["company"].astype(str).str.contains("Hyundai", case=False)]
    assert not hyundai_rows.empty, "Hyundai row must exist in log"
    for _, r in hyundai_rows.iterrows():
        assert r["status"] == "INVALID", f"Hyundai row must be INVALID, got {r['status']}"

    # Verify forward_report script excludes them
    report = generate_forward_report(log_path)
    assert report is not None
    assert report["test_rows"] >= 2, f"Expected >= 2 test rows excluded, got {report['test_rows']}"
    assert report["forward_rows"] >= 0, f"Expected non-negative FORWARD rows, got {report['forward_rows']}"
    # Verify that forward rows exclusively have status == FORWARD
    forward_subset = df[df["status"] == "FORWARD"]
    assert len(forward_subset) == report["forward_rows"], "report['forward_rows'] must match count of status == 'FORWARD'"


def test_r7_no_absolute_user_links():
    """R7: Zero absolute file:/// or /Users/ paths exist in markdown, scripts, or model files."""
    import glob
    files_to_check = []
    for pattern in ["phases/**/*.md", "README.md", "scripts/**/*.py", "model/**/*.py"]:
        files_to_check.extend(glob.glob(os.path.join(ROOT_DIR, pattern), recursive=True))

    for path in files_to_check:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                # Allow self-referencing check expressions in Phase 5 planning file
                if "1_planning_and_goals.md" in path and ("grep" in line or "never" in line or "Defect" in line):
                    continue
                assert "file:///" not in line, f"Absolute file URI found in {path}:{line_no}\n  {line.strip()}"
                assert "/Users/" not in line, f"Absolute user path found in {path}:{line_no}\n  {line.strip()}"


def test_r8_test_set_partition_discipline():
    """R8: ipo_final_test.csv renamed to ipo_phase4_test_used.csv; new final test initialized empty."""
    used_test_path = os.path.join(ROOT_DIR, "data", "ipo_phase4_test_used.csv")
    assert os.path.exists(used_test_path), "data/ipo_phase4_test_used.csv must exist"
    df_used = pd.read_csv(used_test_path)
    assert len(df_used) == 75, f"Expected 75 rows in ipo_phase4_test_used.csv, got {len(df_used)}"

    p5_test_path = os.path.join(ROOT_DIR, "data", "ipo_phase5_final_test.csv")
    assert os.path.exists(p5_test_path), "data/ipo_phase5_final_test.csv must exist"
    df_p5 = pd.read_csv(p5_test_path)
    assert len(df_p5) == 0, f"data/ipo_phase5_final_test.csv must be initialized empty, got {len(df_p5)} rows"
    assert "listing_gain_pct" in df_p5.columns, "data/ipo_phase5_final_test.csv must contain standard schema columns"
