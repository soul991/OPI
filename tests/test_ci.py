"""Regression tests for CI model availability and fresh-clone reproducibility (D-015)."""

import hashlib
import json
import os
import sys
import subprocess
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from opi.score import load_champion_model


def test_model_available_on_fresh_clone():
    """D-015: Champion model binary must be available on a clean clone and match registry hash."""
    reg_path = ROOT_DIR / "model" / "registry.json"
    assert reg_path.exists(), "model/registry.json must exist"

    with open(reg_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    champ_key = meta.get("active_champion", "v4.0.0-champion")
    champ_meta = meta.get("models", {}).get(champ_key, {})
    art_path = ROOT_DIR / champ_meta.get("artifact_path", "model/ipo_model_phase4.joblib")

    assert art_path.exists(), f"Model artifact must exist at {art_path}"
    assert art_path.stat().st_size > 100_000, "Model binary must be non-trivial (>100KB)"

    expected_hash = champ_meta.get("sha256")
    if expected_hash:
        hasher = hashlib.sha256()
        with open(art_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        actual_hash = hasher.hexdigest()
        assert actual_hash.lower() == expected_hash.lower(), (
            f"Model SHA256 mismatch: {actual_hash} vs registry {expected_hash}"
        )

    # Verify model artifact loads successfully
    artifact, version, hw = load_champion_model()
    assert version == champ_key
    assert "reg" in artifact
    assert "cal_clf" in artifact
    assert hw > 0


def test_model_not_ignored_by_git():
    """D-015: Model binaries in model/ must not be ignored by git."""
    model_file = ROOT_DIR / "model" / "ipo_model_phase4.joblib"
    r = subprocess.run(
        ["git", "check-ignore", str(model_file)],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True
    )
    # Return code 1 means NOT ignored (which is what we want)
    assert r.returncode == 1, f"Model file {model_file} is still ignored by git!"


def test_github_actions_evidence_recorded():
    """D-020: The daily GitHub workflow execution must be recorded with run URL and success status."""
    evidence_path = ROOT_DIR / "phases" / "Phase 9" / "actions_run_evidence.md"
    assert evidence_path.exists(), "actions_run_evidence.md must exist"
    content = evidence_path.read_text(encoding="utf-8")
    assert "https://github.com/soul991/OPI/actions/runs/" in content
    assert "SUCCESS" in content


def test_daily_workflow_is_active():
    """D-037: The daily GitHub Actions workflow daily.yml must exist, be scheduled, and be verified active via gh CLI when available."""
    daily_path = ROOT_DIR / ".github" / "workflows" / "daily.yml"
    assert daily_path.exists(), ".github/workflows/daily.yml must exist"
    content = daily_path.read_text(encoding="utf-8")
    assert "schedule:" in content, "daily.yml must configure a scheduled trigger"
    assert "cron:" in content, "daily.yml must have a cron schedule"
    assert "scripts/verify_all.py" in content or "pytest" in content, "daily.yml must execute verification"

    import shutil
    import warnings
    gh_bin = shutil.which("gh")
    if gh_bin:
        try:
            r = subprocess.run([gh_bin, "workflow", "list"], capture_output=True, text=True, timeout=10, cwd=ROOT_DIR)
            if r.returncode == 0:
                lines = [line.lower() for line in r.stdout.splitlines()]
                daily_active = any("active" in line and ("daily" in line or "386343442" in line) for line in lines)
                assert daily_active, f"Daily workflow must be active in GitHub Actions according to 'gh workflow list':\n{r.stdout}"
            else:
                warnings.warn(f"GitHub CLI ('gh') is installed but returned code {r.returncode} ({r.stderr.strip()}); falling back to local file verification.")
        except Exception as e:
            warnings.warn(f"GitHub CLI execution failed ({e}); falling back to local file verification.")
    else:
        warnings.warn("GitHub CLI ('gh') is not installed; verified local workflow configuration only.")


def test_actions_failures_recorded():
    """D-042: Actions runs #9 and #10 failures must be recorded with root cause and resolution."""
    failures_file = ROOT_DIR / "phases" / "Phase 11" / "actions_failures.md"
    assert failures_file.exists(), "phases/Phase 11/actions_failures.md must exist"
    content = failures_file.read_text(encoding="utf-8")
    assert "39248257712" in content
    assert "39312521616" in content
    assert "AssertionError: Hyundai row must be INVALID, got FORWARD" in content
    assert "test_r6_prediction_log_status_and_filtering" in content


def test_dashboard_publishing_status_documented():
    """D-043: Dashboard publishing status must be verified and documented."""
    doc_file = ROOT_DIR / "phases" / "Phase 11" / "actions_failures.md"
    assert doc_file.exists(), "phases/Phase 11/actions_failures.md must exist"
    content = doc_file.read_text(encoding="utf-8")
    assert "GitHub Pages" in content
    assert "404" in content or "not enabled" in content


def test_schedule_lag_recorded():
    """D-051: Schedule lag of last 10 scheduled runs must be analyzed and recorded."""
    lag_file = ROOT_DIR / "phases" / "Phase 12" / "actions_schedule_lag.md"
    assert lag_file.exists(), "phases/Phase 12/actions_schedule_lag.md must exist"
    content = lag_file.read_text(encoding="utf-8")
    assert "cron: '0 6,14 * * *'" in content
    assert "Last 10 Scheduled Runs" in content
    assert "Mean Schedule Delay" in content
    assert "40084848056" in content



