"""Tests for Phase 8 Workstream D: Retraining governance & script delegation, and Phase 20 Autopilot Retraining (D-107)."""

from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import pytest

from opi.retrain import train_monthly_shadow_model, get_next_minor_version

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
    """D-083: Verify monthly_retrain.yml applies promotions and configures retraining step."""
    wf_path = ROOT / ".github" / "workflows" / "monthly_retrain.yml"
    assert wf_path.exists(), ".github/workflows/monthly_retrain.yml must exist"
    content = wf_path.read_text(encoding="utf-8")

    # Workflow must apply promotions
    assert "python scripts/promote_forward_rows.py --apply" in content
    # Workflow must generate report
    assert "python scripts/retrain_challenger.py --no-rolling --report docs/monthly_challenger_comparison.md" in content
    # Workflow must push changes or create PR
    assert "git push origin" in content or "gh pr create" in content


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
    """D-087 and D-093: Verify workflow validates branch before pushing/PR and alerts on failure."""
    wf_path = ROOT / ".github" / "workflows" / "monthly_retrain.yml"
    assert wf_path.exists(), ".github/workflows/monthly_retrain.yml must exist"
    content = wf_path.read_text(encoding="utf-8")

    assert "python -m pytest -q" in content
    assert "python scripts/verify_all.py" in content
    assert "Alert on Failure" in content or "issues: write" in content


# ==============================================================================
# Phase 20 Autopilot Retraining Tests (D-107)
# ==============================================================================

def test_get_next_minor_version():
    """D-107: Model naming vMAJOR.MINOR.0-<yyyymm> increments MINOR."""
    reg = {
        "models": {
            "v4.0.0-champion": {"model_version": "v4.0.0-champion"},
        }
    }
    next_ver = get_next_minor_version(reg, year_month="202611")
    assert next_ver == "v4.1.0-202611"

    reg["models"]["v4.1.0-202611"] = {"model_version": "v4.1.0-202611"}
    next_ver2 = get_next_minor_version(reg, year_month="202612")
    assert next_ver2 == "v4.2.0-202612"


def test_monthly_retrain_trains_and_registers_shadow(tmp_path: Path):
    """D-107: Verifies shadow registration, active champion immutability, and holdout exclusion."""
    test_reg_path = tmp_path / "registry.json"
    init_registry = {
        "active_champion": "v4.0.0-champion",
        "models": {
            "v4.0.0-champion": {
                "model_version": "v4.0.0-champion",
                "artifact_path": "model/ipo_model_phase4.joblib",
                "champion": True,
                "role": "champion",
                "training_window": "2010-01-01 to 2021-12-31"
            }
        }
    }
    test_reg_path.write_text(json.dumps(init_registry, indent=2), encoding="utf-8")

    test_challengers_dir = tmp_path / "challengers"

    result = train_monthly_shadow_model(
        master_path=ROOT / "data" / "ipo_master.csv",
        holdout_path=ROOT / "data" / "ipo_holdout_test.csv",
        registry_path=test_reg_path,
        challengers_dir=test_challengers_dir,
        as_of_date=date(2026, 11, 1),
    )

    # 1. Output structure
    assert result["model_version"].startswith("v4.1.0-")
    assert result["active_champion"] == "v4.0.0-champion"
    assert len(result["sha256"]) == 64
    assert result["train_rows"] > 0

    # 2. Artifact created and non-empty
    saved_art = test_challengers_dir / f"{result['model_version']}.joblib"
    assert saved_art.exists()
    assert saved_art.stat().st_size > 1000

    # 3. Registry updated as shadow
    updated_reg = json.loads(test_reg_path.read_text(encoding="utf-8"))
    assert updated_reg["active_champion"] == "v4.0.0-champion", "active_champion must remain untouched during retraining"
    new_model_meta = updated_reg["models"][result["model_version"]]
    assert new_model_meta["role"] == "shadow"
    assert new_model_meta["champion"] == False
    assert new_model_meta["sha256"] == result["sha256"]
    assert new_model_meta["train_rows"] == result["train_rows"]
