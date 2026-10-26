#!/usr/bin/env python3
"""watchdog.py - Freshness guard, provider health check, and keepalive heartbeat (D-058).

Monitors:
(a) Last successful scheduled daily.yml run freshness (<36 hours).
(b) Live GitHub Pages dashboard freshness (<36 hours, via scripts/verify_pages.py; NOT_CHECKED is never PASS).
(c) OpenRouter free models availability (at least one configured model available in API).
Keepalive:
Touches predictions/heartbeat.txt and commits at most once every 30 days if no commits occurred.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
MAX_STALENESS_HOURS = 36.0
KEEPALIVE_DAYS_THRESHOLD = 30.0


def check_scheduled_run_freshness(max_hours: float = MAX_STALENESS_HOURS) -> Tuple[bool, str]:
    """Check (a): last successful scheduled daily.yml run is younger than max_hours."""
    gh_bin = shutil.which("gh")
    run_time: Optional[dt.datetime] = None
    problem = ""

    if not gh_bin:
        problem = "GitHub CLI 'gh' is not installed."
    else:
        try:
            res = subprocess.run(
                [
                    gh_bin, "run", "list",
                    "--workflow", "daily.yml",
                    "--event", "schedule",
                    "--status", "success",
                    "--limit", "1",
                    "--json", "createdAt",
                ],
                cwd=str(ROOT_DIR),
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
            if res.returncode == 0:
                data = json.loads(res.stdout)
                if data and "createdAt" in data[0]:
                    ts_str = data[0]["createdAt"].replace("Z", "+00:00")
                    run_time = dt.datetime.fromisoformat(ts_str)
                else:
                    problem = "GitHub returned no successful scheduled daily.yml run."
            else:
                problem = f"gh exited with code {res.returncode}: {(res.stderr or '').strip()[:300]}"
        except Exception as e:
            problem = f"gh query failed: {e}"

    # D-064: never fall back to a date stored in the repo. A monitor that guesses gives a false PASS
    # (while the stored date is recent) and later a false FAIL. If GitHub cannot be queried, say so.
    if run_time is None:
        return False, (
            f"Could not determine last successful scheduled run time ({problem}) "
            "Check that the workflow sets GH_TOKEN and 'permissions: actions: read'."
        )

    now_utc = dt.datetime.now(dt.timezone.utc)
    delta_hours = (now_utc - run_time).total_seconds() / 3600.0

    if delta_hours > max_hours:
        return False, (
            f"Last successful scheduled daily run is STALE: {delta_hours:.1f}h ago "
            f"(threshold is {max_hours:.1f}h, run time was {run_time.isoformat()})"
        )

    return True, f"Last successful scheduled run is FRESH: {delta_hours:.1f}h ago (run: {run_time.isoformat()})"


def check_dashboard_freshness() -> Tuple[bool, str]:
    """Check (b): live dashboard freshness via scripts/verify_pages.py.
    
    NOT_CHECKED is explicitly treated as FAIL in the watchdog.
    """
    verify_script = ROOT_DIR / "scripts" / "verify_pages.py"
    if not verify_script.exists():
        return False, "scripts/verify_pages.py missing."

    res = subprocess.run(
        [sys.executable, str(verify_script), "--save-check", ""],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    combined_out = (res.stdout + "\n" + res.stderr).strip()

    if "[NOT_CHECKED]" in combined_out:
        return False, f"Dashboard check failed: verify_pages reported NOT_CHECKED (network unreachable or network error):\n{combined_out}"

    if res.returncode != 0 or "[FAIL]" in combined_out:
        return False, f"Dashboard check failed (exit {res.returncode}):\n{combined_out}"

    return True, f"Dashboard verified fresh (HTTP 200 and within staleness window)."


def check_openrouter_free_models(models_json_path: Optional[Path] = None) -> Tuple[bool, str]:
    """Check (c): at least one model configured in config/research_models.json is available."""
    cfg_path = models_json_path or (ROOT_DIR / "config" / "research_models.json")
    if not cfg_path.exists():
        return False, f"Configuration file {cfg_path} not found."

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    configured_models = cfg.get("models", [])
    if not configured_models:
        return False, "No models configured in config/research_models.json."

    models_url = cfg.get("openrouter_models_url", "https://openrouter.ai/api/v1/models")

    try:
        req = urllib.request.Request(
            models_url,
            headers={"User-Agent": "OPI-Watchdog/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as e:
        # If external API is unreachable in an airgapped test environment,
        # note network warning but check if configured list is syntactically valid
        return False, f"Failed to fetch OpenRouter models API at {models_url}: {e}"

    available_ids = {m.get("id") for m in data.get("data", []) if "id" in m}
    matching = [m for m in configured_models if m in available_ids]

    if not matching:
        return False, (
            f"None of the configured research models ({configured_models}) "
            f"were found in the live OpenRouter models list ({len(available_ids)} models available)."
        )

    return True, f"OpenRouter models verified: {len(matching)} configured model(s) available ({matching})."


def execute_keepalive_if_needed(dry_run: bool = False) -> Tuple[bool, str]:
    """Check keepalive: commit timestamp to predictions/heartbeat.txt if no commit in 30 days."""
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            check=True,
        )
        last_commit_ts = int(res.stdout.strip())
    except Exception as e:
        return False, f"Could not determine last commit timestamp: {e}"

    now_ts = int(dt.datetime.now(dt.timezone.utc).timestamp())
    days_since_commit = (now_ts - last_commit_ts) / 86400.0

    if days_since_commit < KEEPALIVE_DAYS_THRESHOLD:
        return True, f"Repository active ({days_since_commit:.1f} days since last commit; threshold {KEEPALIVE_DAYS_THRESHOLD} days). Keepalive not needed."

    heartbeat_file = ROOT_DIR / "predictions" / "heartbeat.txt"
    heartbeat_content = (
        f"# OPI Keepalive Heartbeat\n"
        f"last_heartbeat: {dt.datetime.now(dt.timezone.utc).isoformat()}\n"
        f"reason: prevent GitHub Actions 60-day schedule pause\n"
    )

    if dry_run:
        return True, f"[DRY-RUN] Would update heartbeat.txt (last commit was {days_since_commit:.1f} days ago)."

    heartbeat_file.write_text(heartbeat_content, encoding="utf-8")

    try:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=str(ROOT_DIR), check=True)
        subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=str(ROOT_DIR), check=True)
        subprocess.run(["git", "add", "predictions/heartbeat.txt"], cwd=str(ROOT_DIR), check=True)
        subprocess.run(
            ["git", "commit", "-m", "chore(keepalive): automated repository heartbeat [skip ci]"],
            cwd=str(ROOT_DIR),
            check=True,
        )
        subprocess.run(["git", "push"], cwd=str(ROOT_DIR), check=True)
        return True, f"Keepalive commit generated and pushed ({days_since_commit:.1f} days since previous commit)."
    except Exception as e:
        return False, f"Failed to commit keepalive heartbeat: {e}"


def run_watchdog(
    max_hours: float = MAX_STALENESS_HOURS,
    dry_run: bool = False,
    skip_network_for_testing: bool = False,
) -> int:
    """Run all watchdog audits and return 0 on pass or 1 on failure."""
    print(f"\n{'='*78}")
    print(f"  OPI AUTOMATED WATCHDOG AUDIT")
    print(f"{'='*78}\n")

    failures: List[str] = []

    # Check (a): Scheduled run freshness
    ok_a, msg_a = check_scheduled_run_freshness(max_hours=max_hours)
    print(f"Check (a) [Scheduled Run Freshness]: {'PASS' if ok_a else 'FAIL'}")
    print(f"  {msg_a}\n")
    if not ok_a:
        failures.append(f"Scheduled Run Staleness: {msg_a}")

    # Check (b): Dashboard freshness
    if skip_network_for_testing:
        print("Check (b) [Dashboard Freshness]: SKIPPED (testing flag)\n")
    else:
        ok_b, msg_b = check_dashboard_freshness()
        print(f"Check (b) [Dashboard Freshness]: {'PASS' if ok_b else 'FAIL'}")
        print(f"  {msg_b}\n")
        if not ok_b:
            failures.append(f"Dashboard Staleness: {msg_b}")

    # Check (c): OpenRouter free models
    if skip_network_for_testing:
        print("Check (c) [OpenRouter Free Models]: SKIPPED (testing flag)\n")
    else:
        ok_c, msg_c = check_openrouter_free_models()
        print(f"Check (c) [OpenRouter Free Models]: {'PASS' if ok_c else 'FAIL'}")
        print(f"  {msg_c}\n")
        if not ok_c:
            failures.append(f"OpenRouter Model Unavailability: {msg_c}")

    # Keepalive check
    ok_k, msg_k = execute_keepalive_if_needed(dry_run=dry_run)
    print(f"Keepalive Status: {'OK' if ok_k else 'WARN'}")
    print(f"  {msg_k}\n")
    if not ok_k:
        print(f"[WARN] Keepalive check encountered an issue: {msg_k}")

    print(f"{'='*78}")
    if failures:
        print(f"SUMMARY: Watchdog FAILED with {len(failures)} issue(s):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("SUMMARY: Watchdog ALL CHECKS PASSED.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OPI Watchdog and Freshness Auditor")
    parser.add_argument("--max-hours", type=float, default=MAX_STALENESS_HOURS, help="Maximum allowed staleness in hours")
    parser.add_argument("--dry-run", action="store_true", help="Do not commit keepalive heartbeat")
    parser.add_argument("--skip-network-for-testing", action="store_true", help="Skip remote network checks during offline testing")
    args = parser.parse_args()

    return run_watchdog(
        max_hours=args.max_hours,
        dry_run=args.dry_run,
        skip_network_for_testing=args.skip_network_for_testing,
    )


if __name__ == "__main__":
    sys.exit(main())
