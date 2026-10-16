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

