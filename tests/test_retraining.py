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


def test_retrain_challenger_generates_markdown_report(tmp_path):
    """D-083: Verify retrain_challenger.py writes comparison markdown report when requested."""
    from scripts.retrain_challenger import run_challenger_comparison
    report_file = tmp_path / "challenger_report.md"

    run_challenger_comparison(MASTER_DATA, rolling=False, report_path=report_file)
    assert report_file.exists(), "Markdown comparison report must be generated"
    content = report_file.read_text(encoding="utf-8")
    assert "# Monthly Challenger Model Evaluation Report" in content
    assert "Point MAE" in content
    assert "Governance Decision" in content
    assert "Champion Artifact" in content


def test_monthly_retrain_workflow_opens_pr():
    """D-083: Verify monthly_retrain.yml applies promotions and opens PR via GitHub CLI."""
    wf_path = ROOT / ".github" / "workflows" / "monthly_retrain.yml"
    assert wf_path.exists(), ".github/workflows/monthly_retrain.yml must exist"
    content = wf_path.read_text(encoding="utf-8")

    # Workflow must apply promotions
    assert "python scripts/promote_forward_rows.py --apply" in content
    # Workflow must generate report
    assert "python scripts/retrain_challenger.py --no-rolling --report docs/monthly_challenger_comparison.md" in content
    # Workflow must open PR
    assert "gh pr create" in content
    assert "Open Pull Request with Challenger Comparison" in content


def test_promote_forward_rows_byte_identical_existing(tmp_path):
    """D-092: Verify that promote_forward_rows --apply leaves existing rows 100% byte-identical."""
    from scripts.promote_forward_rows import promote_forward_rows, MASTER_COLUMNS

    tmp_master = tmp_path / "ipo_master.csv"
    tmp_promotions = tmp_path / "promotions.csv"
    tmp_log = tmp_path / "prediction_log.csv"

    orig_bytes = MASTER_DATA.read_bytes()
    tmp_master.write_bytes(orig_bytes)
    orig_lines = MASTER_DATA.read_text(encoding="utf-8").splitlines(keepends=True)

    tmp_log.write_text((ROOT / "predictions" / "prediction_log.csv").read_text(encoding="utf-8"), encoding="utf-8")

    promoted = promote_forward_rows(
        apply=True,
        log_path=tmp_log,
        master_path=tmp_master,
        promotions_path=tmp_promotions
    )

    new_content = tmp_master.read_text(encoding="utf-8")
    new_lines = new_content.splitlines(keepends=True)

    assert len(new_lines) >= len(orig_lines), "Master dataset lost lines during promotion"
    for i in range(len(orig_lines)):
        assert new_lines[i] == orig_lines[i], f"Line {i+1} changed! Expected:\n{orig_lines[i]!r}\nGot:\n{new_lines[i]!r}"

    import csv
    with open(tmp_master, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == MASTER_COLUMNS, "Header columns modified or order altered"
        assert "updated_at" not in header, "Illegal column updated_at added to master dataset"

        for row_idx, row in enumerate(reader):
            assert len(row) == len(MASTER_COLUMNS), f"Row {row_idx+2} has {len(row)} columns, expected {len(MASTER_COLUMNS)}"
            year_val = row[header.index("year")]
            if year_val:
                assert "." not in year_val, f"Year formatted as float '{year_val}' at row {row_idx+2}"


def test_monthly_retrain_workflow_branch_verification_and_alerting():
    """D-087 and D-093: Verify workflow validates branch before PR, flags drafts, and alerts exact admin setting."""
    wf_path = ROOT / ".github" / "workflows" / "monthly_retrain.yml"
    assert wf_path.exists(), ".github/workflows/monthly_retrain.yml must exist"
    content = wf_path.read_text(encoding="utf-8")

    assert "python -m pytest -q" in content
    assert "python scripts/verify_all.py" in content
    assert "PR_CHECKS_MD=" in content
    assert "--draft" in content

    assert "issues: write" in content
    assert "pull-requests: write" in content
    assert "Allow GitHub Actions to create and approve pull requests" in content
    assert "Settings -> Actions -> General -> Workflow permissions" in content
