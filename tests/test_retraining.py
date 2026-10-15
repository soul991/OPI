"""Tests for Phase 8 Workstream D: Retraining governance & script delegation."""

import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "model" / "registry.json"
MASTER_DATA = ROOT / "data" / "ipo_master.csv"


def test_retrain_challenger_preserves_champion():
    """Verify that retrain_challenger.py runs cleanly and NEVER alters champion artifacts."""
    script_path = ROOT / "scripts" / "retrain_challenger.py"
    assert script_path.exists(), "scripts/retrain_challenger.py must exist"
    assert REGISTRY_PATH.exists(), "model/registry.json must exist"

    reg_before = REGISTRY_PATH.read_text(encoding="utf-8")

    # Run challenger comparison in fast mode (--no-rolling) for test suite
    res = subprocess.run(
        [sys.executable, str(script_path), "--data", str(MASTER_DATA), "--no-rolling"],
        capture_output=True,
        text=True,
        cwd=ROOT
    )
    assert res.returncode == 0, f"retrain_challenger.py failed with code {res.returncode}:\n{res.stderr}"
    assert "OPI RETRAINING GOVERNANCE: CHAMPION VS CHALLENGER EVALUATION" in res.stdout
    assert "Governance Policy Checklist" in res.stdout
    assert "Champion model remains active in model/registry.json" in res.stdout

    reg_after = REGISTRY_PATH.read_text(encoding="utf-8")
    assert reg_before == reg_after, "retrain_challenger.py illegally modified model/registry.json!"


def test_retrain_challenger_returns_governance_metrics():
    """Verify that run_challenger_comparison returns all policy checklist metrics."""
    from scripts.retrain_challenger import run_challenger_comparison

    res = run_challenger_comparison(MASTER_DATA, rolling=False)
    required_keys = [
        "mae_champ", "mae_challenger", "point_diff", "ci_95",
        "ece_champ", "ece_challenger", "brier_champ", "brier_challenger",
        "auc_champ", "auc_challenger", "champ_cov", "chall_cov",
        "eligible_for_review"
    ]
    for k in required_keys:
        assert k in res, f"Missing key '{k}' in challenger evaluation output dictionary"
        assert res[k] is not None, f"Key '{k}' in challenger output must not be None"


def test_refactored_scripts_run_cleanly():
    """Verify that scripts/log_prediction.py, update_actuals.py, and forward_report.py execute cleanly."""
    scripts = [
        "scripts/log_prediction.py",
        "scripts/update_actuals.py",
        "scripts/forward_report.py",
    ]
    for rel_path in scripts:
        p = ROOT / rel_path
        assert p.exists(), f"{rel_path} must exist"
        res = subprocess.run(
            [sys.executable, str(p), "--help"],
            capture_output=True,
            text=True,
            cwd=ROOT
        )
        assert res.returncode == 0, f"{rel_path} --help failed:\n{res.stderr}"
        assert "usage:" in res.stdout.lower()
