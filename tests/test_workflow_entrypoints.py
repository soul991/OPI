#!/usr/bin/env python3
"""tests/test_workflow_entrypoints.py - Entry-point smoke test for workflow commands (D-075).

Parses all .github/workflows/*.yml files, extracts every python script/module entrypoint,
and verifies that each can execute with `--help` from the repository root without
depending on an inherited local PYTHONPATH unless explicitly set in the workflow step.

Also proves the test mechanism by verifying that the pre-fix watchdog code
(commit 06ff884, prior to 9dd1b7d) fails with ModuleNotFoundError when run without PYTHONPATH.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT_DIR / ".github" / "workflows"


def extract_workflow_python_commands() -> list[dict[str, str | bool]]:
    """Parse all workflow files and extract python invocation targets."""
    commands = []
    if not WORKFLOWS_DIR.exists():
        return commands

    for yml in sorted(WORKFLOWS_DIR.glob("*.yml")):
        content = yml.read_text(encoding="utf-8")
        # Split into steps
        steps = re.split(r"- name:", content)
        for s in steps:
            # Check if this step sets PYTHONPATH
            has_pythonpath = bool(re.search(r"PYTHONPATH:\s*\S+", s))
            
            # Find python invocations
            # Matches: python scripts/foo.py, python model/foo.py, python -m foo.bar
            matches = re.findall(r"(?:python\s+(?:-m\s+)?([a-zA-Z0-9_\/\.-]+))", s)
            for m in matches:
                target = m.strip()
                if target.startswith("pip") or target.startswith("-"):
                    continue
                # Only test scripts or internal modules
                if target.startswith("scripts/") or target.startswith("model/") or target.startswith("opi.") or target == "pytest":
                    commands.append({
                        "workflow": yml.name,
                        "target": target,
                        "is_module": target.startswith("opi.") or target == "pytest",
                        "has_pythonpath": has_pythonpath,
                    })
    return commands


def test_workflow_entrypoints_smoke():
    """D-075: Every python entrypoint used in GitHub workflows must execute standalone."""
    commands = extract_workflow_python_commands()
    assert len(commands) > 0, "No python commands found in workflows"

    tested_targets = set()

    for cmd in commands:
        target = cmd["target"]
        if target in tested_targets:
            continue
        tested_targets.add(target)

        env = os.environ.copy()
        if not cmd["has_pythonpath"]:
            env.pop("PYTHONPATH", None)

        if cmd["is_module"]:
            run_args = [sys.executable, "-m", target, "--help"]
        else:
            script_path = ROOT_DIR / target
            assert script_path.exists(), f"Workflow script {target} does not exist"
            run_args = [sys.executable, str(script_path), "--help"]

        res = subprocess.run(
            run_args,
            cwd=str(ROOT_DIR),
            env=env,
            capture_output=True,
            text=True,
        )

        assert res.returncode == 0, (
            f"Entry point {target} from {cmd['workflow']} failed standalone execution (exit {res.returncode}):\n"
            f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        )


def test_smoke_test_fails_on_prefix_watchdog(tmp_path: Path):
    """D-075: Prove test efficacy - pre-fix watchdog code (06ff884) fails without PYTHONPATH."""
    # Fetch watchdog.py content from commit 06ff884 (prior to 9dd1b7d fix)
    try:
        old_code = subprocess.check_output(
            ["git", "show", "06ff884:scripts/watchdog.py"],
            cwd=str(ROOT_DIR),
            text=True,
        )
    except subprocess.CalledProcessError:
        pytest.skip("Git history commit 06ff884 not available in shallow environment")

    temp_script = tmp_path / "old_watchdog.py"
    temp_script.write_text(old_code, encoding="utf-8")

    # Run with PYTHONPATH unset from ROOT_DIR
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    res_old = subprocess.run(
        [sys.executable, str(temp_script), "--help"],
        cwd=str(ROOT_DIR),
        env=env,
        capture_output=True,
        text=True,
    )

    # Must fail with ModuleNotFoundError: No module named 'scripts'
    assert res_old.returncode != 0, "Expected pre-fix watchdog to fail without PYTHONPATH"
    assert "ModuleNotFoundError" in res_old.stderr
    assert "scripts" in res_old.stderr

    # In contrast, current scripts/watchdog.py must pass with returncode 0
    res_cur = subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "watchdog.py"), "--help"],
        cwd=str(ROOT_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    assert res_cur.returncode == 0, f"Current watchdog.py failed standalone execution: {res_cur.stderr}"


if __name__ == "__main__":
    test_workflow_entrypoints_smoke()
    print("ALL WORKFLOW ENTRYPOINTS PASS STANDALONE SMOKE TEST")
