"""Unit tests for automated GitHub issue alerts and deduplication (D-057)."""

import json
import os
import subprocess
from unittest.mock import MagicMock, patch
import pytest

from scripts.manage_alerts import (
    sanitize_text,
    get_target_repo,
    list_open_alert_issues,
    handle_failure,
    handle_success,
)


def test_sanitize_text_redacts_keys():
    """Verify secret keys and tokens are strictly redacted and cannot leak into issues."""
    fake_openrouter_key = "sk-or-" + "v1-" + "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
    fake_gh_token = "ghp_" + "1234567890abcdef1234567890abcdef123456"
    raw_text = f"Error communicating with OpenRouter using key {fake_openrouter_key} and token {fake_gh_token}"

    sanitized = sanitize_text(raw_text)
    assert fake_openrouter_key not in sanitized
    assert fake_gh_token not in sanitized
    # Confirm prefix is scrubbed
    prefix = "sk-" + "or-"
    assert prefix not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert "[REDACTED_GH_TOKEN]" in sanitized


def test_sanitize_text_redacts_env_secrets(monkeypatch):
    """Verify environment variable values are scrubbed if present in error messages."""
    secret_val = "SuperSecretCustomVal9988!"
    monkeypatch.setenv("OPENROUTER_API_KEY", secret_val)
    raw_text = f"Failed to authenticate with bearer {secret_val}"
    sanitized = sanitize_text(raw_text)
    assert secret_val not in sanitized
    assert "[REDACTED_SECRET]" in sanitized


@patch("scripts.manage_alerts.run_gh_command")
def test_handle_failure_creates_new_issue_when_none_open(mock_gh):
    """When no failure issue is currently open, handle_failure must create a new issue."""
    # First call: list_open_alert_issues -> returns empty list []
    list_result = MagicMock()
    list_result.returncode = 0
    list_result.stdout = "[]"

    # Second call: issue create -> returns success
    create_result = MagicMock()
    create_result.returncode = 0
    create_result.stdout = "https://github.com/soul991/OPI/issues/123"

    mock_gh.side_effect = [list_result, create_result]

    ret = handle_failure(
        repo="soul991/OPI",
        workflow_name="daily.yml",
        run_id="999888777",
        failed_step="Daily Forward Test",
        reason="SKIPPED_BLOCKED_SOURCE: BSE feed unreachable",
    )

    assert ret == 0
    assert mock_gh.call_count == 2
    create_call_args = mock_gh.call_args_list[1][0][0]
    assert create_call_args[0] == "issue"
    assert create_call_args[1] == "create"
    assert "--title" in create_call_args
    idx = create_call_args.index("--title")
    assert "Daily run failed: 999888777" in create_call_args[idx + 1]


@patch("scripts.manage_alerts.run_gh_command")
def test_handle_failure_deduplicates_by_commenting(mock_gh):
    """When an issue for the failure streak is already open, it must comment, not open another issue."""
    # First call: list_open_alert_issues -> returns 1 existing issue
    list_result = MagicMock()
    list_result.returncode = 0
    list_result.stdout = json.dumps([
        {"number": 42, "title": "Daily run failed: 111222333", "body": "Initial failure"}
    ])

    # Second call: issue comment -> returns success
    comment_result = MagicMock()
    comment_result.returncode = 0
    comment_result.stdout = "https://github.com/soul991/OPI/issues/42#issuecomment-1"

    mock_gh.side_effect = [list_result, comment_result]

    ret = handle_failure(
        repo="soul991/OPI",
        workflow_name="daily.yml",
        run_id="444555666",
        failed_step="Repository Verification",
        reason="AssertionError in verify_all.py",
    )

    assert ret == 0
    assert mock_gh.call_count == 2
    comment_call_args = mock_gh.call_args_list[1][0][0]
    assert comment_call_args[0] == "issue"
    assert comment_call_args[1] == "comment"
    assert "42" in comment_call_args
    assert "--body" in comment_call_args
    idx = comment_call_args.index("--body")
    assert "Failure Streak Continues: Run [444555666]" in comment_call_args[idx + 1]


@patch("scripts.manage_alerts.run_gh_command")
def test_handle_success_closes_open_alert_issues(mock_gh):
    """When a scheduled run succeeds, any open alert issues for that workflow must be closed."""
    # First call: list_open_alert_issues -> returns 1 open issue
    list_result = MagicMock()
    list_result.returncode = 0
    list_result.stdout = json.dumps([
        {"number": 42, "title": "Daily run failed: 111222333", "body": "Failure body"}
    ])

    # Second call: issue close -> returns success
    close_result = MagicMock()
    close_result.returncode = 0
    close_result.stdout = "Closed #42"

    mock_gh.side_effect = [list_result, close_result]

    ret = handle_success(
        repo="soul991/OPI",
        workflow_name="daily.yml",
        run_id="777888999",
    )

    assert ret == 0
    assert mock_gh.call_count == 2
    close_call_args = mock_gh.call_args_list[1][0][0]
    assert close_call_args[0] == "issue"
    assert close_call_args[1] == "close"
    assert "42" in close_call_args
    assert "--reason" in close_call_args
    assert "completed" in close_call_args
