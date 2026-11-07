import pandas as pd
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


def test_coverage_alert_threshold_boundaries(tmp_path):
    """D-080: Coverage check flags closed unlogged IPOs within 2 days of listing, warns for 5 days."""
    from scripts.watchdog import check_unlogged_closing_ipos
    log_csv = tmp_path / "synthetic_log.csv"
    log_csv.write_text("company,listing_date,status\nAlready Logged Co,2026-11-04,FORWARD\n", encoding="utf-8")
    missed_csv = tmp_path / "missed.csv"
    today = dt.date(2026, 11, 2)

    # 1. Closed, unlogged, listing in 2 days (boundary <= 2 days) -> FAIL
    cands_urgent = [
        {
            "company": "Urgent Listing Ltd",
            "close_date": "2026-11-01",
            "listing_date": "2026-11-04",  # (2026-11-04 - 2026-11-02) = 2 days
            "status": "CLOSED_UNLISTED"
        }
    ]
    ok1, msg1, urgent1 = check_unlogged_closing_ipos(
        candidates=cands_urgent, log_path=log_csv, missed_path=missed_csv, current_date=today, threshold_days=2
    )
    assert ok1 is False
    assert len(urgent1) == 1
    assert urgent1[0]["company"] == "Urgent Listing Ltd"
    assert urgent1[0]["type"] == "IMPENDING_LISTING_UNSCORED"
    assert "Urgent Listing Ltd" in msg1

    # 2. Closed, unlogged, listing in 5 days (boundary > 2 days) -> PASS with warning
    cands_warn = [
        {
            "company": "Future Listing Ltd",
            "close_date": "2026-11-01",
            "listing_date": "2026-11-07",  # 5 days
            "status": "CLOSED_UNLISTED"
        }
    ]
    ok2, msg2, urgent2 = check_unlogged_closing_ipos(
        candidates=cands_warn, log_path=log_csv, missed_path=missed_csv, current_date=today, threshold_days=2
    )
    assert ok2 is True
    assert len(urgent2) == 0
    assert "[WARN]" in msg2
    assert "Future Listing Ltd" in msg2

    # 3. Candidate already logged in prediction_log.csv -> PASS
    cands_logged = [
        {
            "company": "Already Logged Co",
            "close_date": "2026-11-01",
            "listing_date": "2026-11-04",
            "status": "CLOSED_UNLISTED"
        }
    ]
    ok3, msg3, urgent3 = check_unlogged_closing_ipos(
        candidates=cands_logged, log_path=log_csv, missed_path=missed_csv, current_date=today, threshold_days=2
    )
    assert ok3 is True
    assert len(urgent3) == 0

    # 4. Candidate with bidding open -> PASS
    cands_open = [
        {
            "company": "Bidding Open Ltd",
            "close_date": "2026-11-05",
            "listing_date": "2026-11-10",
            "status": "BIDDING_OPEN"
        }
    ]
    ok4, msg4, urgent4 = check_unlogged_closing_ipos(
        candidates=cands_open, log_path=log_csv, missed_path=missed_csv, current_date=today, threshold_days=2
    )
    assert ok4 is True
    assert len(urgent4) == 0


def test_missed_forward_csv_recording(tmp_path):
    """D-080: Listed unlogged IPOs are recorded into missed_forward.csv as MISSED_FORWARD."""
    from scripts.watchdog import check_unlogged_closing_ipos
    log_csv = tmp_path / "synthetic_log.csv"
    log_csv.write_text("company,listing_date,status\n", encoding="utf-8")
    missed_csv = tmp_path / "missed.csv"
    today = dt.date(2026, 11, 2)

    cands = [
        {
            "company": "Overdue Unscored Ltd",
            "close_date": "2026-10-25",
            "listing_date": "2026-10-28",  # Listed 5 days ago!
            "status": "LISTED"
        }
    ]
    ok, msg, urgent = check_unlogged_closing_ipos(
        candidates=cands, log_path=log_csv, missed_path=missed_csv, current_date=today
    )
    assert ok is False
    assert len(urgent) == 1
    assert urgent[0]["type"] == "MISSED_FORWARD"
    assert missed_csv.exists()

    content = missed_csv.read_text(encoding="utf-8")
    assert "Overdue Unscored Ltd" in content
    assert "MISSED_FORWARD" in content

    # Test idempotence: running again doesn't duplicate
    check_unlogged_closing_ipos(candidates=cands, log_path=log_csv, missed_path=missed_csv, current_date=today)
    lines = [l for l in missed_csv.read_text(encoding="utf-8").splitlines() if "Overdue Unscored Ltd" in l]
    assert len(lines) == 1


def test_watchdog_runs_verify_extra_and_reports_failure():
    """D-086: Watchdog executes verify_extra.py and reports failing check lines."""
    from scripts.watchdog import check_verify_extra

    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stdout = (
        "[PASS] subscription figures in Phase 11+ reports equal prediction_log values\n"
        "[FAIL] each listed date has a parsed Nifty evidence file: missing: 2026-11-02\n"
        "\nSUMMARY: 6 pass, 0 warn, 1 fail\n"
    )
    mock_res.stderr = ""

    with patch("subprocess.run", return_value=mock_res):
        ok, msg, failing = check_verify_extra()
        assert ok is False
        assert len(failing) >= 1
        assert "each listed date has a parsed Nifty evidence file" in msg
        assert "missing: 2026-11-02" in msg



def test_missing_outcomes_alert_does_not_block_run_daily(tmp_path):
    """D-095: Overdue outcomes or coverage alerts must not make run_daily raise.

    (a) run_daily exits 0 and records MISSING_OUTCOME_ALERT in run_log.csv for overdue row.
    (b) daily.yml runs check_overdue_outcomes_and_coverage after commit_and_push with no continue-on-error.
    (c) Real exceptions inside discovery/scoring/outcomes still cause run_daily to fail.
    """
    from opi.run_daily import run_daily_forward_test
    from scripts.watchdog import run_overdue_and_coverage_check

    # 1. Setup synthetic environment with an overdue unrecorded listing (>2 days ago)
    log_file = tmp_path / "prediction_log.csv"
    run_log_file = tmp_path / "run_log.csv"
    
    overdue_df = pd.DataFrame([{
        "scored_at": "2026-10-25T18:30:00+05:30",
        "company": "Overdue Corp",
        "open_date": "2026-10-20",
        "close_date": "2026-10-24",
        "listing_date": "2026-10-28",  # >2 days ago
        "features_snapshot_json": '{"issue_price": 100.0}',
        "pred_gain_pct": "12.0",
        "pred_prob_gt10": "0.60",
        "gmp_pct_at_scoring": "10.0",
        "actual_gain_pct": "",
        "status": "FORWARD",
        "notes": "synthetic row"
    }])
    overdue_df.to_csv(log_file, index=False)

    with patch("opi.log.LOG_PATH", log_file), \
         patch("opi.log.RUN_LOG_PATH", run_log_file), \
         patch("opi.discover.discover_ipos", return_value=[]), \
         patch("opi.market.ensure_market_evidence_for_listed_dates", return_value={"status": "OK"}), \
         patch("opi.report.render_dashboard_html", return_value=tmp_path / "dash.html"), \
         patch("opi.report.render_pre_listing_markdown", return_value=""), \
         patch("opi.actuals.execute_two_tier_outcome_chain", return_value={"status": "SKIPPED_NO_MATCH", "reason": "test mock"}):
        
        # run_daily must NOT raise RuntimeError
        run_daily_forward_test(dry_run=False, log_path=log_file, run_log_path=run_log_file, missed_path=tmp_path / 'missed.csv')

    # Verify run_log contains MISSING_OUTCOME_ALERT
    assert run_log_file.exists()
    rl_df = pd.read_csv(run_log_file)
    alert_rows = rl_df[(rl_df["company"] == "Overdue Corp") & (rl_df["status"] == "MISSING_OUTCOME_ALERT")]
    assert len(alert_rows) >= 1

    # Verify watchdog CLI function returns 1 (alert condition exists)
    with patch("opi.log.LOG_PATH", log_file), patch("opi.log.RUN_LOG_PATH", run_log_file):
        missed_file = tmp_path / 'missed_forward.csv'
        ret_alert = run_overdue_and_coverage_check(log_path=log_file, candidates=[], missed_path=missed_file)
        assert ret_alert == 1

    # 2. Workflow-order test
    daily_wf = ROOT_DIR / ".github" / "workflows" / "daily.yml"
    assert daily_wf.exists()
    wf_text = daily_wf.read_text(encoding="utf-8")
    assert "id: commit_and_push" in wf_text
    assert "id: check_overdue_outcomes_and_coverage" in wf_text
    assert "id: alert_on_failure" in wf_text
    
    idx_commit = wf_text.index("id: commit_and_push")
    idx_alert_step = wf_text.index("id: check_overdue_outcomes_and_coverage")
    idx_failure = wf_text.index("id: alert_on_failure")
    
    assert idx_commit < idx_alert_step < idx_failure, "Alert step must run after commit_and_push and before alert_on_failure"
    
    # Assert alert step has no continue-on-error
    alert_step_block = wf_text[idx_alert_step:idx_failure]
    assert "continue-on-error: true" not in alert_step_block

    # 3. Verify real exception inside execution chain still fails run_daily
    with patch("opi.log.LOG_PATH", log_file), \
         patch("opi.log.RUN_LOG_PATH", run_log_file), \
         patch("opi.discover.discover_ipos", return_value=[]), \
         patch("opi.run_daily.execute_two_tier_outcome_chain", side_effect=RuntimeError("Simulated outcome crash")):
        with pytest.raises(RuntimeError, match="Simulated outcome crash"):
            run_daily_forward_test(dry_run=False, log_path=log_file, run_log_path=run_log_file, missed_path=tmp_path / 'missed.csv')

def test_overdue_outcomes_alert_thresholds(tmp_path):
    """D-109: Overdue outcomes between 3-7 days do not fail watchdog; 8+ days fail."""
    from scripts.watchdog import run_overdue_and_coverage_check
    import datetime as dt
    log_file = tmp_path / "prediction_log.csv"
    cur_date = dt.date(2026, 11, 10)

    # 1. 3 days overdue (listed 2026-11-07 vs cur_date 2026-11-10): PASS (returns 0)
    df_3d = pd.DataFrame([{
        "scored_at": "2026-11-05T18:30:00+05:30",
        "company": "Three Day Corp",
        "listing_date": "2026-11-07",
        "status": "FORWARD",
        "actual_gain_pct": "",
    }])
    df_3d.to_csv(log_file, index=False)
    ret_3d = run_overdue_and_coverage_check(log_path=log_file, candidates=[], missed_path=tmp_path / "m1.csv", current_date=cur_date)
    assert ret_3d == 0, "3 days overdue outcome must not fail the workflow"

    # 2. 8 days overdue (listed 2026-11-02 vs cur_date 2026-11-10): FAIL (returns 1)
    df_8d = pd.DataFrame([{
        "scored_at": "2026-10-31T18:30:00+05:30",
        "company": "Eight Day Corp",
        "listing_date": "2026-11-02",
        "status": "FORWARD",
        "actual_gain_pct": "",
    }])
    df_8d.to_csv(log_file, index=False)
    ret_8d = run_overdue_and_coverage_check(log_path=log_file, candidates=[], missed_path=tmp_path / "m2.csv", current_date=cur_date)
    assert ret_8d == 1, "8 days overdue outcome must fail the workflow"

