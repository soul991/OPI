#!/usr/bin/env python3
"""ci_local.py - run the same steps as the daily GitHub Actions job, in a throwaway copy.

Why: Phase 13 pushed commits whose tests passed on a developer machine but failed in CI,
because CI runs `python -m opi.run_daily` (which rewrites the dashboard and logs) BEFORE pytest.
Run this before every push:  python scripts/ci_local.py
Order (same as .github/workflows/daily.yml): run_daily -> pytest -> verify_all.
The real repository is not modified; everything happens in a temp copy."""
import shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    ("entrypoints smoke test", [sys.executable, "tests/test_workflow_entrypoints.py"]),
    ("daily job", [sys.executable, "-m", "opi.run_daily"]),
    ("pytest", [sys.executable, "-m", "pytest", "-q"]),
    ("verify_all", [sys.executable, "scripts/verify_all.py"]),
]


def tracked_and_new_files():
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [Path(p) for p in out.splitlines() if (ROOT / p).is_file()]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="opi_ci_local_") as tmp:
        work = Path(tmp) / "repo"
        for rel in tracked_and_new_files():
            dst = work / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dst)
        # tests that inspect git history need a repository
        shutil.copytree(ROOT / ".git", work / ".git", symlinks=True)
        failed = []
        for name, cmd in STEPS:
            print(f"\n=== {name}: {' '.join(cmd[1:])}")
            r = subprocess.run(cmd, cwd=work)
            print(f"[{'PASS' if r.returncode == 0 else 'FAIL'}] {name}")
            if r.returncode != 0:
                failed.append(name)
        print("\nCI_LOCAL:", "FAIL (" + ", ".join(failed) + ")" if failed else "PASS")
        return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
