"""Unit tests for watchdog staleness thresholds, checks, and keepalive logic (D-058)."""

import datetime as dt
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from scripts.watchdog import (
    check_missing_outcomes,
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


# ---- D-064: regression tests for the 2026-10-26 watchdog false failure -------------------------
def test_check_a_never_falls_back_to_a_stored_date(tmp_path):
    """D-064: if gh cannot query Actions (no token), check (a) must FAIL with the reason,
    not read a date from phases/*.md (that gave a false PASS at 28 h and a false FAIL at 55 h)."""
    mock_res = MagicMock()
    mock_res.returncode = 4
    mock_res.stdout = ""
    mock_res.stderr = "gh: To use GitHub CLI in a GitHub Actions workflow, set the GH_TOKEN environment variable."
    with patch("subprocess.run", return_value=mock_res):
        with patch("shutil.which", return_value="/usr/bin/gh"):
            ok, msg = check_scheduled_run_freshness(max_hours=36.0)
    assert ok is False
    assert "Could not determine" in msg and "GH_TOKEN" in msg
    src = (ROOT_DIR / "scripts" / "watchdog.py").read_text(encoding="utf-8")
    assert "actions_status" not in src and "actions_schedule_lag" not in src


def test_watchdog_workflow_has_token_and_actions_read():
    """D-064: watchdog.yml gives the check step GH_TOKEN and 'actions: read', and passes details to the alert."""
    text = (ROOT_DIR / ".github" / "workflows" / "watchdog.yml").read_text(encoding="utf-8")
    assert "actions: read" in text
    step = text[text.index("Execute Watchdog Health Check"):text.index("Alert on Failure")]
    assert "GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}" in step
    assert "pipefail" in step and "watchdog_output.txt" in step
    assert "--reason-file watchdog_output.txt" in text


def _fake_page(ts: str):
    resp = MagicMock()
    resp.status = 200
    body = f"<html>Generated automatically by <code>opi.report</code> at {ts} IST</html>" if ts else "<html>no stamp</html>"
    resp.read.return_value = body.encode()
    cm = MagicMock()
    cm.__enter__.return_value = resp
    cm.__exit__.return_value = False
    return cm


def test_verify_pages_measures_age_against_now(capsys):
    """D-064: an old dashboard is STALE (vs now), a fresh one PASSes, a missing timestamp FAILs."""
    import scripts.verify_pages as vp
    ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    now_ist = dt.datetime.now(dt.timezone.utc).astimezone(ist)
    fresh = (now_ist - dt.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S.000000")
    old = (now_ist - dt.timedelta(hours=60)).strftime("%Y-%m-%dT%H:%M:%S.000000")
    with patch("urllib.request.urlopen", return_value=_fake_page(fresh)), patch.object(vp, "get_last_scheduled_run_time", return_value=None):
        assert vp.verify_pages() == 0
    assert "FRESH" in capsys.readouterr().out
    with patch("urllib.request.urlopen", return_value=_fake_page(old)), patch.object(vp, "get_last_scheduled_run_time", return_value=None):
        assert vp.verify_pages() == 1
    assert "STALE" in capsys.readouterr().out
    with patch("urllib.request.urlopen", return_value=_fake_page("")), patch.object(vp, "get_last_scheduled_run_time", return_value=None):
        assert vp.verify_pages() == 1


def test_alert_reason_file_is_used(tmp_path):
    """D-065: alert issues carry the watchdog SUMMARY text, not only a generic message."""
    import scripts.manage_alerts as ma
    f = tmp_path / "out.txt"
    f.write_text("noise\nSUMMARY: Watchdog FAILED with 1 issue(s):\n  - Scheduled Run Staleness: example reason\n", encoding="utf-8")
    captured = {}
    with patch.object(ma, "handle_failure", side_effect=lambda **kw: captured.update(kw) or 0), \
         patch("sys.argv", ["manage_alerts.py", "--on-failure", "--run-id", "1", "--workflow-name", "watchdog.yml", "--repo", "o/r", "--reason-file", str(f)]):
        assert ma.main() == 0
    assert "Scheduled Run Staleness: example reason" in captured["reason"]
    assert "noise" not in captured["reason"]

def test_missing_outcomes_threshold_boundary(tmp_path):
    """D-067: Threshold boundary check - exactly 2 days passes, 3 days fails."""
    log_csv = tmp_path / "synthetic_log.csv"
    run_log_csv = tmp_path / "synthetic_run_log.csv"

    # Synthetic log with one FORWARD row listed on 2026-10-28 lacking actual_gain_pct
    log_csv.write_text(
        "company,listing_date,status,pred_gain_pct,actual_gain_pct\n"
        "Boundary Tech Limited,2026-10-28,FORWARD,15.0,\n",
        encoding="utf-8"
    )
    run_log_csv.write_text(
        "timestamp,run_id,action,company,status,details\n"
        "2026-10-28T18:00:00+05:30,run_1,ACTUALS,Boundary Tech Limited,SKIPPED_FETCH_FAILED,403 Forbidden\n",
        encoding="utf-8"
    )

    # Day 0: 2026-10-28 (0 days) -> PASS
    ok0, _, overdue0 = check_missing_outcomes(log_path=log_csv, run_log_path=run_log_csv, current_date=dt.date(2026, 10, 28))
    assert ok0 is True
    assert len(overdue0) == 0

    # Day 2: 2026-10-30 (exactly 2 days) -> PASS
    ok2, _, overdue2 = check_missing_outcomes(log_path=log_csv, run_log_path=run_log_csv, current_date=dt.date(2026, 10, 30))
    assert ok2 is True
    assert len(overdue2) == 0

    # Day 3: 2026-10-31 (3 days) -> FAIL
    ok3, msg3, overdue3 = check_missing_outcomes(log_path=log_csv, run_log_path=run_log_csv, current_date=dt.date(2026, 10, 31))
    assert ok3 is False
    assert len(overdue3) == 1
    assert overdue3[0]["company"] == "Boundary Tech Limited"
    assert overdue3[0]["days_overdue"] == 3
    assert "Boundary Tech Limited" in msg3
    assert "403 Forbidden" in msg3


def test_missing_outcomes_recorded_rows_ignored(tmp_path):
    """D-067: Completed forward rows with outcomes recorded are ignored regardless of age."""
    log_csv = tmp_path / "synthetic_log.csv"
    log_csv.write_text(
        "company,listing_date,status,pred_gain_pct,actual_gain_pct\n"
        "Old Completed Corp,2026-09-01,FORWARD,20.0,22.5\n",
        encoding="utf-8"
    )
    ok, _, overdue = check_missing_outcomes(log_path=log_csv, current_date=dt.date(2026, 10, 30))
    assert ok is True
    assert len(overdue) == 0


def test_missing_outcomes_alert_names_company_and_no_key_material(tmp_path):
    """D-067: Alert message contains company name and sanitizes any sensitive API token."""
    log_csv = tmp_path / "synthetic_log.csv"
    run_log_csv = tmp_path / "synthetic_run_log.csv"

    log_csv.write_text(
        "company,listing_date,status,pred_gain_pct,actual_gain_pct\n"
        "Sensitive Data Corp,2026-10-20,FORWARD,10.0,\n",
        encoding="utf-8"
    )
    mock_key = "sk" + "-or-v1-abcdef0123456789abcdef0123456789"
    run_log_csv.write_text(
        f"timestamp,run_id,action,company,status,details\n"
        f"2026-10-21T18:00:00+05:30,run_2,ACTUALS,Sensitive Data Corp,SKIPPED_ERROR,Auth failed with {mock_key}\n",
        encoding="utf-8"
    )

    ok, msg, overdue = check_missing_outcomes(log_path=log_csv, run_log_path=run_log_csv, current_date=dt.date(2026, 10, 30))
    assert ok is False
    assert len(overdue) == 1
    assert "Sensitive Data Corp" in msg
    assert "sk" + "-or-" not in msg
    assert "[REDACTED_API_KEY]" in msg



def test_watchdog_script_standalone_execution():
    """Verify scripts/watchdog.py can be invoked directly as a script without PYTHONPATH set."""
    import os
    import subprocess
    import sys
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    res = subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / "watchdog.py"), "--help"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 0
    assert "watchdog.py" in res.stdout or "usage:" in res.stdout
