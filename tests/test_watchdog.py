"""Unit tests for watchdog staleness thresholds, checks, and keepalive logic (D-058)."""

import datetime as dt
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scripts.watchdog import (
    check_scheduled_run_freshness,
    check_dashboard_freshness,
    check_openrouter_free_models,
    execute_keepalive_if_needed,
    run_watchdog,
)

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_scheduled_run_freshness_fresh():
    """Verify check_scheduled_run_freshness returns True when last run is within threshold."""
    now_utc = dt.datetime.now(dt.timezone.utc)
    recent_time = (now_utc - dt.timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = json.dumps([{"createdAt": recent_time}])

    with patch("subprocess.run", return_value=mock_res):
        with patch("shutil.which", return_value="/usr/bin/gh"):
            ok, msg = check_scheduled_run_freshness(max_hours=36.0)
            assert ok is True
            assert "FRESH" in msg


def test_scheduled_run_freshness_stale():
    """Verify check_scheduled_run_freshness returns False when last run exceeds 36 hours."""
    now_utc = dt.datetime.now(dt.timezone.utc)
    stale_time = (now_utc - dt.timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")

    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = json.dumps([{"createdAt": stale_time}])

    with patch("subprocess.run", return_value=mock_res):
        with patch("shutil.which", return_value="/usr/bin/gh"):
            ok, msg = check_scheduled_run_freshness(max_hours=36.0)
            assert ok is False
            assert "STALE" in msg


def test_dashboard_freshness_not_checked_is_fail():
    """Rule: NOT_CHECKED is never PASS in the watchdog."""
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "[NOT_CHECKED] Live GitHub Pages unreachable from environment"
    mock_res.stderr = ""

    with patch("subprocess.run", return_value=mock_res):
        ok, msg = check_dashboard_freshness()
        assert ok is False
        assert "NOT_CHECKED" in msg


def test_dashboard_freshness_pass():
    """Verify successful dashboard verification returns True."""
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "[PASS] Live GitHub Pages dashboard verified (HTTP 200) - FRESH"
    mock_res.stderr = ""

    with patch("subprocess.run", return_value=mock_res):
        ok, msg = check_dashboard_freshness()
        assert ok is True
        assert "HTTP 200" in msg


def test_openrouter_free_models_matching():
    """Verify check_openrouter_free_models passes when configured models are in API response."""
    fake_api_data = {
        "data": [
            {"id": "nvidia/nemotron-3.5-super-vl:free"},
            {"id": "some/other-model"},
        ]
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_api_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        ok, msg = check_openrouter_free_models()
        assert ok is True
        assert "1 configured model(s) available" in msg


def test_openrouter_free_models_none_available():
    """Verify check_openrouter_free_models fails when none of the configured models are found."""
    fake_api_data = {
        "data": [
            {"id": "unrelated/model-a"},
            {"id": "unrelated/model-b"},
        ]
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_api_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        ok, msg = check_openrouter_free_models()
        assert ok is False
        assert "None of the configured research models" in msg


def test_keepalive_logic_under_threshold():
    """Verify keepalive does not trigger a commit when recent commits exist."""
    now_ts = int(dt.datetime.now(dt.timezone.utc).timestamp())
    recent_commit_ts = now_ts - (5 * 86400)  # 5 days ago

    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = str(recent_commit_ts)

    with patch("subprocess.run", return_value=mock_res):
        ok, msg = execute_keepalive_if_needed(dry_run=True)
        assert ok is True
        assert "Keepalive not needed" in msg


def test_keepalive_logic_over_threshold():
    """Verify keepalive triggers when repo inactivity reaches or exceeds 30 days."""
    now_ts = int(dt.datetime.now(dt.timezone.utc).timestamp())
    stale_commit_ts = now_ts - (35 * 86400)  # 35 days ago

    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = str(stale_commit_ts)

    with patch("subprocess.run", return_value=mock_res):
        ok, msg = execute_keepalive_if_needed(dry_run=True)
        assert ok is True
        assert "Would update heartbeat.txt" in msg
