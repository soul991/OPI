"""
Unit tests for opi.notify_run (WS-F: Unified notification runner entrypoint).
"""

import subprocess
import sys
from unittest.mock import patch
import pytest

from opi.notify_run import main


def test_notify_run_cli_help():
    res = subprocess.run(
        [sys.executable, "-m", "opi.notify_run", "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "OPI Stage Notification Dispatcher" in res.stdout
    assert "--stage" in res.stdout


@patch("opi.notify_run.run_announce_stage", return_value=[])
def test_notify_run_announce(mock_announce):
    code = main(["--stage", "announce", "--dry-run"])
    assert code == 0
    mock_announce.assert_called_once_with(dry_run=True)


@patch("opi.notify_run.run_preview_stage", return_value=[])
def test_notify_run_preview(mock_preview):
    code = main(["--stage", "preview", "--dry-run"])
    assert code == 0
    mock_preview.assert_called_once_with(dry_run=True)


@patch("opi.notify_run.run_listing_stage", return_value=[])
def test_notify_run_listing(mock_listing):
    code = main(["--stage", "listing", "--dry-run"])
    assert code == 0
    mock_listing.assert_called_once_with(dry_run=True)


def test_notify_run_invalid_stage():
    with pytest.raises(SystemExit):
        main(["--stage", "invalid_stage"])
