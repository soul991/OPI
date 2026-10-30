"""Unit tests for n=30 prospective final evaluation and claim governance (D-060)."""

import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from scripts.final_evaluation import (
    compute_wilson_score_interval,
    run_paired_bootstrap,
    evaluate_cohort,
    generate_evaluation_report,
    TARGET_SAMPLE_SIZE,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT_DIR / "tests" / "fixtures" / "synthetic_n30_prediction_log.csv"


def test_final_evaluation_not_ready_below_30(capsys):
    """When n < 30 on real prediction_log.csv, final_evaluation.py prints NOT_READY and exits 0."""
    res = subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "final_evaluation.py")],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "NOT_READY" in res.stdout
    assert "of 30)" in res.stdout


def test_wilson_score_interval():
    """Verify Wilson score confidence interval calculation."""
    low, high = compute_wilson_score_interval(successes=27, total=30, confidence=0.95)
    assert 70.0 < low < 80.0
    assert 94.0 < high <= 98.0
    assert low < 90.0 < high


def test_paired_bootstrap_reproducibility():
    """Paired bootstrap must be deterministic given fixed seed=42."""
    m_err = np.array([5.0, 7.0, 3.0, 10.0, 2.0, 8.0, 4.0, 6.0])
    g_err = np.array([8.0, 10.0, 4.0, 12.0, 5.0, 9.0, 6.0, 7.0])

    diff1, low1, high1 = run_paired_bootstrap(m_err, g_err, n_resamples=500, seed=42)
    diff2, low2, high2 = run_paired_bootstrap(m_err, g_err, n_resamples=500, seed=42)

    assert diff1 == diff2
    assert low1 == low2
    assert high1 == high2
    assert diff1 > 0.0


def test_wording_governance_rules():
    """Verify strict preregistered wording: cannot claim 'beats' unless CI excludes zero."""
    # Case 1: CI includes zero -> statistically indistinguishable
    m_err_tie = np.array([5.0, 6.0, 7.0, 8.0])
    g_err_tie = np.array([6.0, 5.0, 8.0, 7.0])
    df_tie = pd.DataFrame({
        "actual_gain_pct": [10.0, 20.0, 30.0, 40.0],
        "pred_gain_pct": [10.0 + e for e in m_err_tie],
        "gmp_pct_at_scoring": [10.0 + e for e in g_err_tie],
        "pred_gain_q05": [5.0]*4,
        "pred_gain_q95": [45.0]*4,
        "pred_prob_gt10": [0.8]*4,
    })
    res_tie = evaluate_cohort(df_tie)
    assert res_tie["wording"] == "statistically indistinguishable"
    assert "statistically indistinguishable" in res_tie["verdict_claim"]
    assert "statistically outperformed" not in res_tie["verdict_claim"]


def test_full_evaluation_on_synthetic_fixture(tmp_path):
    """Verify full evaluation execution against the synthetic 30-row fixture."""
    assert FIXTURE_PATH.exists(), f"Synthetic fixture missing at {FIXTURE_PATH}"
    df = pd.read_csv(FIXTURE_PATH)
    assert len(df) == 30

    test_out = tmp_path / "final_report.md"

    res = subprocess.run(
        [
            sys.executable,
            str(ROOT_DIR / "scripts" / "final_evaluation.py"),
            "--log", str(FIXTURE_PATH),
            "--output", str(test_out),
        ],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )

    assert res.returncode == 0
    assert "[EVALUATION] Proceeding with formal evaluation" in res.stdout
    assert test_out.exists()

    report_text = test_out.read_text(encoding="utf-8")
    assert "# Formal Prospective Evaluation Report (n = 30)" in report_text
    assert "Full Cohort (n = 30)" in report_text
    assert "Core Cohort (n = 28)" in report_text
    assert "Model MAE" in report_text
    assert "GMP MAE" in report_text
    assert "Wilson CI" in report_text
    assert "95% Bootstrap CI" in report_text
