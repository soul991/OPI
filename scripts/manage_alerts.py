#!/usr/bin/env python3
"""manage_alerts.py - Automated GitHub issue alerting and deduplication (D-057).

Handles failure notifications and resolution auto-closure for GitHub Actions workflows
(daily forward tests, watchdog freshness checks, and canary dependency builds).
Ensures zero secrets or keys are logged or submitted to issue tracking.
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
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "soul991/OPI"


def sanitize_text(text: str) -> str:
    """Scrub potential secret keys, API tokens, and credentials from text."""
    if not text:
        return ""
    # Mask any OpenRouter or standard OpenAI secret keys
    or_pat = r"sk" + r"-or-[A-Za-z0-9_\-]+"
    text = re.sub(or_pat, "[REDACTED_API_KEY]", text)
    text = re.sub(r"sk-[A-Za-z0-9_\-]{20,}", "[REDACTED_API_KEY]", text)
    # Mask GitHub personal access tokens
    text = re.sub(r"gh[pousr]_[A-Za-z0-9_]{20,}", "[REDACTED_GH_TOKEN]", text)
    text = re.sub(r"github_pat_[A-Za-z0-9_]{20,}", "[REDACTED_GH_TOKEN]", text)

    # Mask known environment secret values if present
    for secret_env in ("OPENROUTER_API_KEY", "GH_TOKEN", "GITHUB_TOKEN"):
        val = os.environ.get(secret_env)
        if val and len(val) >= 8:
            text = text.replace(val, "[REDACTED_SECRET]")

    return text


def get_target_repo(repo_arg: Optional[str] = None) -> str:
    """Resolve repository slug (owner/repo)."""
    if repo_arg and repo_arg.strip():
        return repo_arg.strip()
    env_repo = os.environ.get("GITHUB_REPOSITORY")
    if env_repo and env_repo.strip():
        return env_repo.strip()
    return DEFAULT_REPO


def run_gh_command(args: List[str], env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    """Execute gh CLI command with environment inheritance."""
    cmd_env = dict(os.environ)
    if env:
        cmd_env.update(env)
    # Ensure GH_TOKEN is set from GITHUB_TOKEN if present
    if "GH_TOKEN" not in cmd_env and "GITHUB_TOKEN" in cmd_env:
        cmd_env["GH_TOKEN"] = cmd_env["GITHUB_TOKEN"]

    gh_bin = shutil.which("gh")
    if not gh_bin:
        raise RuntimeError("GitHub CLI ('gh') is not installed or not in PATH.")

    return subprocess.run(
        [gh_bin] + args,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        env=cmd_env,
        check=False,
    )


def list_open_alert_issues(repo: str, title_prefix: str) -> List[Dict[str, Any]]:
    """Query open alert issues matching a title prefix."""
    res = run_gh_command(["issue", "list", "--repo", repo, "--state", "open", "--limit", "50", "--json", "number,title,body"])
    if res.returncode != 0:
        print(f"[WARN] Failed to list issues: {res.stderr.strip()}", file=sys.stderr)
        return []
    try:
        issues = json.loads(res.stdout)
        matches = [
            iss for iss in issues
            if str(iss.get("title", "")).startswith(title_prefix)
        ]
        return matches
    except Exception as e:
        print(f"[WARN] Error parsing gh issue list output: {e}", file=sys.stderr)
        return []


def handle_failure(
    repo: str,
    workflow_name: str,
    run_id: str,
    failed_step: Optional[str] = None,
    reason: Optional[str] = None,
    run_url: Optional[str] = None,
) -> int:
    """Open a new failure alert issue or append comment to existing open streak issue."""
    wf_label = "Daily" if "daily" in workflow_name.lower() else ("Watchdog" if "watchdog" in workflow_name.lower() else "Canary")
    title_prefix = f"{wf_label} run failed:"

    resolved_run_url = run_url or (f"https://github.com/{repo}/actions/runs/{run_id}" if run_id else "N/A")
    now_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    open_issues = list_open_alert_issues(repo, title_prefix)

    # Sanitize all inputs before building body
    clean_step = sanitize_text(failed_step or "Execution")
    clean_reason = sanitize_text(reason or "Workflow step returned non-zero exit code or validation failure")
    clean_run_id = sanitize_text(run_id or "unknown")

    if open_issues:
        # Deduplicate: append comment to the first open issue in the failure streak
        existing = open_issues[0]
        issue_num = existing["number"]
        comment_body = (
            f"### Failure Streak Continues: Run [{clean_run_id}]({resolved_run_url})\n\n"
            f"- **Timestamp**: `{now_utc}`\n"
            f"- **Workflow**: `{workflow_name}`\n"
            f"- **Failed Step / Component**: `{clean_step}`\n"
            f"- **Reason / Diagnosis**: {clean_reason}\n\n"
            f"*(This issue will be closed automatically when a scheduled run succeeds.)*"
        )
        comment_body = sanitize_text(comment_body)
        res = run_gh_command(["issue", "comment", str(issue_num), "--repo", repo, "--body", comment_body])
        if res.returncode == 0:
            print(f"[ALERT] Updated open issue #{issue_num} with failure streak run {clean_run_id}.")
            return 0
        else:
            print(f"[ERROR] Failed to comment on issue #{issue_num}: {res.stderr.strip()}", file=sys.stderr)
            return 1
    else:
        # Open a new issue
        issue_title = sanitize_text(f"{title_prefix} {clean_run_id}")
        issue_body = (
            f"## Automated Workflow Failure Notification\n\n"
            f"A scheduled or dispatched automated execution failed in repository `{repo}`.\n\n"
            f"- **Run ID**: [{clean_run_id}]({resolved_run_url})\n"
            f"- **Workflow**: `{workflow_name}`\n"
            f"- **Failed Step / Component**: `{clean_step}`\n"
            f"- **Timestamp**: `{now_utc}`\n"
            f"- **Failure Reason**: {clean_reason}\n\n"
            f"### Action Required\n"
            f"1. Check the [Actions run logs]({resolved_run_url}) for failure trace.\n"
            f"2. If an IPO data source was blocked or changed, refer to `docs/RUNBOOK.md`.\n"
            f"3. Note: This issue will automatically close on the next successful scheduled run."
        )
        issue_body = sanitize_text(issue_body)
        res = run_gh_command([
            "issue", "create",
            "--repo", repo,
            "--title", issue_title,
            "--body", issue_body,
        ])
        if res.returncode == 0:
            print(f"[ALERT] Opened new alert issue: {issue_title} ({res.stdout.strip()})")
            return 0
        else:
            print(f"[ERROR] Failed to create alert issue: {res.stderr.strip()}", file=sys.stderr)
            return 1


def handle_success(
    repo: str,
    workflow_name: str,
    run_id: str,
) -> int:
    """Automatically close any open alert issues for this workflow upon a green run."""
    wf_label = "Daily" if "daily" in workflow_name.lower() else ("Watchdog" if "watchdog" in workflow_name.lower() else "Canary")
    title_prefix = f"{wf_label} run failed:"

    open_issues = list_open_alert_issues(repo, title_prefix)
    if not open_issues:
        print(f"[OK] No open alert issues matching prefix '{title_prefix}'.")
        return 0

    now_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    clean_run_id = sanitize_text(run_id or "unknown")
    run_url = f"https://github.com/{repo}/actions/runs/{clean_run_id}"

    success_count = 0
    for iss in open_issues:
        issue_num = iss["number"]
        close_comment = sanitize_text(
            f"### Automated Resolution\n\n"
            f"Resolved by green run [{clean_run_id}]({run_url}) at `{now_utc}`.\n"
            f"All verification and pipeline steps completed successfully."
        )
        res = run_gh_command([
            "issue", "close", str(issue_num),
            "--repo", repo,
            "--comment", close_comment,
            "--reason", "completed",
        ])
        if res.returncode == 0:
            print(f"[RESOLVED] Closed alert issue #{issue_num}.")
            success_count += 1
        else:
            print(f"[WARN] Failed to close alert issue #{issue_num}: {res.stderr.strip()}", file=sys.stderr)

    return 0 if success_count == len(open_issues) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage automated GitHub issue failure alerts and resolution")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--on-failure", action="store_true", help="Record a failure: open issue or append comment")
    group.add_argument("--on-success", action="store_true", help="Record a success: auto-close open failure issues")

    parser.add_argument("--workflow-name", default="daily.yml", help="Name of workflow (e.g. daily.yml, watchdog.yml)")
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""), help="GitHub Actions run ID")
    parser.add_argument("--failed-step", default="", help="Step name that encountered failure")
    parser.add_argument("--reason", default="", help="Description or error code of failure")
    parser.add_argument("--reason-file", default="", help="Text file whose SUMMARY section (or last 1500 chars) is used as the failure reason")
    parser.add_argument("--run-url", default="", help="URL to the GitHub Actions run")
    parser.add_argument("--repo", default="", help="GitHub repository (owner/repo)")

    args = parser.parse_args()
    repo = get_target_repo(args.repo)
    if args.reason_file and not args.reason:
        try:
            txt = open(args.reason_file, encoding="utf-8", errors="replace").read()
            args.reason = (txt[txt.index("SUMMARY"):] if "SUMMARY" in txt else txt)[-1500:]
        except OSError:
            pass

    if args.on_failure:
        return handle_failure(
            repo=repo,
            workflow_name=args.workflow_name,
            run_id=args.run_id,
            failed_step=args.failed_step,
            reason=args.reason,
            run_url=args.run_url,
        )
    elif args.on_success:
        return handle_success(
            repo=repo,
            workflow_name=args.workflow_name,
            run_id=args.run_id,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
