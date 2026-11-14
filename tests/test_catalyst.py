"""tests/test_catalyst.py - Unit test suite for Zoho Catalyst trigger function (WS-G, D-121).

Tests:
1. determine_stage with explicit arguments and time-of-day IST clock fallbacks.
2. dispatch_github_workflow HTTP 204 success and request payload structure.
3. dispatch_github_workflow retries with exponential backoff on HTTP 500.
4. dispatch_github_workflow final failure triggering direct fallback Telegram alert.
5. sanitize_text secret masking for PATs, bot tokens, and sensitive error strings.
6. handler execution with mocked Catalyst Cron details and Context objects.
7. handler execution with mocked Catalyst Basic I/O objects.
"""
from datetime import datetime, timezone, timedelta
import json
import os
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from catalyst.opi_trigger.main import (
    determine_stage,
    dispatch_github_workflow,
    get_secret,
    handler,
    sanitize_text,
    send_telegram_fallback,
    IST,
)


def test_determine_stage_explicit():
    assert determine_stage("announce") == "announce"
    assert determine_stage("ANNOUNCE") == "announce"
    assert determine_stage("preview") == "preview"
    assert determine_stage("listing") == "listing"
    # Invalid explicit string falls back to clock
    t = datetime(2026, 11, 14, 11, 45, tzinfo=IST)
    assert determine_stage("invalid_stage", now=t) == "preview"


def test_determine_stage_by_ist_clock():
    # 09:00 IST -> announce
    t_0900 = datetime(2026, 11, 14, 9, 0, tzinfo=IST)
    assert determine_stage(now=t_0900) == "announce"

    # 20:00 IST -> announce
    t_2000 = datetime(2026, 11, 14, 20, 0, tzinfo=IST)
    assert determine_stage(now=t_2000) == "announce"

    # 11:45 IST -> preview
    t_1145 = datetime(2026, 11, 14, 11, 45, tzinfo=IST)
    assert determine_stage(now=t_1145) == "preview"

    # 11:30 IST -> listing
    t_1130 = datetime(2026, 11, 14, 11, 30, tzinfo=IST)
    assert determine_stage(now=t_1130) == "listing"

    # 16:30 IST -> listing
    t_1630 = datetime(2026, 11, 14, 16, 30, tzinfo=IST)
    assert determine_stage(now=t_1630) == "listing"


def test_sanitize_text_redacts_tokens():
    raw_token = "1234567890:AAGM8X-6T_FakeDummyTokenForTesting12345"
    pat = "ghp_FakeTokenForUnitTestingPurposesOnly12345"
    text = f"Error connecting with token {raw_token} and PAT {pat} to server"
    sanitized = sanitize_text(text, [raw_token, pat])
    assert raw_token not in sanitized
    assert pat not in sanitized
    assert "[REDACTED" in sanitized


def _make_mock_response(status=204):
    resp = MagicMock()
    resp.status = status
    resp.code = status
    resp.__enter__.return_value = resp
    return resp


def test_dispatch_github_workflow_success_204():
    mock_resp = _make_mock_response(204)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        res = dispatch_github_workflow(stage="preview", dry_run=True, dispatch_token="dummy_token")
        assert res["success"] is True
        assert res["status"] == 204
        assert res["attempts"] == 1
        assert res["stage"] == "preview"

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        assert req.get_method() == "POST"
        assert req.headers["Authorization"] == "Bearer dummy_token"
        assert req.headers["Accept"] == "application/vnd.github+json"
        body = json.loads(req.data.decode("utf-8"))
        assert body["ref"] == "main"
        assert body["inputs"]["stage"] == "preview"
        assert body["inputs"]["dry_run"] == "true"


def test_dispatch_github_workflow_retry_and_recover():
    fail_resp = urllib.error.HTTPError(
        url="http://mock", code=500, msg="Internal Server Error", hdrs={}, fp=MagicMock(read=lambda: b"Server error")
    )
    success_resp = _make_mock_response(204)

    with patch("urllib.request.urlopen", side_effect=[fail_resp, success_resp]) as mock_urlopen, \
         patch("time.sleep") as mock_sleep:
        res = dispatch_github_workflow(stage="announce", dry_run=False, max_retries=2, dispatch_token="dummy_token")
        assert res["success"] is True
        assert res["status"] == 204
        assert res["attempts"] == 2
        mock_sleep.assert_called_once_with(1.0)
        assert mock_urlopen.call_count == 2


def test_dispatch_github_workflow_exhausted_retries_calls_fallback():
    fail_resp = urllib.error.HTTPError(
        url="http://mock", code=502, msg="Bad Gateway", hdrs={}, fp=MagicMock(read=lambda: b"Bad Gateway")
    )

    with patch("urllib.request.urlopen", side_effect=[fail_resp, fail_resp, fail_resp]), \
         patch("time.sleep"), \
         patch("catalyst.opi_trigger.main.send_telegram_fallback") as mock_fallback:
        res = dispatch_github_workflow(stage="listing", dry_run=False, max_retries=2, dispatch_token="dummy_token")
        assert res["success"] is False
        assert res["status"] == 502
        assert res["attempts"] == 3
        mock_fallback.assert_called_once()
        call_stage, call_err = mock_fallback.call_args[0][0], mock_fallback.call_args[0][1]
        assert call_stage == "listing"
        assert "HTTP 502" in call_err


def test_send_telegram_fallback():
    mock_resp = _make_mock_response(200)

    env = {
        "TELEGRAM_BOT_TOKEN": "1234567890:AAGM8X-6T_FakeDummyTokenForTesting12345",
        "TELEGRAM_CHAT_ID": "2006803662"
    }
    with patch.dict(os.environ, env, clear=True), \
         patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        ok = send_telegram_fallback("preview", "Simulated GitHub dispatch outage", status_code=503)
        assert ok is True
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        assert "api.telegram.org" in req.full_url
        body = json.loads(req.data.decode("utf-8"))
        assert body["chat_id"] == "2006803662"
        assert "preview" in body["text"]
        assert "503" in body["text"]


def test_handler_with_cron_details_mock():
    class MockCronDetails:
        def get_cron_param(self, k):
            return "preview" if k == "stage" else "true"

    cron_mock = MockCronDetails()
    context_mock = MagicMock()
    mock_resp = _make_mock_response(204)

    with patch("urllib.request.urlopen", return_value=mock_resp), \
         patch.dict(os.environ, {"GITHUB_DISPATCH_TOKEN": "dummy_token"}, clear=True):
        res = handler(cron_mock, context_mock)
        assert res["success"] is True
        assert res["stage"] == "preview"
        context_mock.closeWithSuccess.assert_called_once()


def test_handler_with_basicio_mock():
    class MockBasicIO:
        def __init__(self):
            self.written = []
        def get_argument(self, k):
            return "announce" if k == "stage" else None
        def write(self, s):
            self.written.append(s)

    basicio_mock = MockBasicIO()
    context_mock = MagicMock()
    mock_resp = _make_mock_response(204)

    with patch("urllib.request.urlopen", return_value=mock_resp), \
         patch.dict(os.environ, {"GITHUB_DISPATCH_TOKEN": "dummy_token"}, clear=True):
        res = handler(context_mock, basicio_mock)
        assert res["success"] is True
        assert res["stage"] == "announce"
        assert len(basicio_mock.written) == 1
        written = json.loads(basicio_mock.written[0])
        assert written["success"] is True
