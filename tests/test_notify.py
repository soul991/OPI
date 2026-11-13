"""
Unit tests for opi.notify module (WS-A: Telegram Sender).
"""

import io
import json
import logging
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from opi.notify import (
    TELEGRAM_MAX_CHARS,
    sanitize_text,
    send_telegram,
    split_message,
)

SAMPLE_TOKEN = "9196287140:TEST_TOKEN_1234567890abcdefghijklmnopqrstuvwxyz"
SAMPLE_CHAT_ID = "2006803662"


def test_sanitize_text():
    text = f"Calling https://api.telegram.org/bot{SAMPLE_TOKEN}/sendMessage for user"
    sanitized = sanitize_text(text, [SAMPLE_TOKEN])
    assert SAMPLE_TOKEN not in sanitized
    assert "***REDACTED" in sanitized


def test_sanitize_text_pattern_match():
    # Detects Telegram token structure even if not explicitly passed in secrets list
    text = "Error in token 1234567890:AAGM8X-6T_FakeDummyTokenForTesting12345 during request"
    sanitized = sanitize_text(text)
    assert "1234567890:AAGM8X-6T_FakeDummyTokenForTesting12345" not in sanitized
    assert "***REDACTED_BOT_TOKEN***" in sanitized


def test_split_message_short():
    short = "Hello Telegram!"
    assert split_message(short, limit=100) == ["Hello Telegram!"]
    assert split_message("", limit=100) == []


def test_split_message_long_newline():
    line = "A" * 50
    text = f"{line}\n{line}\n{line}"
    chunks = split_message(text, limit=60)
    assert len(chunks) == 3
    for c in chunks:
        assert len(c) <= 60
        assert "A" * 50 in c


def test_split_message_hard():
    text = "B" * 150
    chunks = split_message(text, limit=50)
    assert len(chunks) == 3
    assert chunks == ["B" * 50, "B" * 50, "B" * 50]


def test_send_telegram_dry_run(capsys):
    result = send_telegram("Test dry run message", dry_run=True)
    assert result is True
    captured = capsys.readouterr()
    assert "[DRY RUN]" in captured.out
    assert "Test dry run message" in captured.out


def test_send_telegram_missing_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", SAMPLE_CHAT_ID)
    with pytest.raises(ValueError, match="Missing TELEGRAM_BOT_TOKEN"):
        send_telegram("Message", token=None, chat_id=SAMPLE_CHAT_ID)


def test_send_telegram_missing_chat_id(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", SAMPLE_TOKEN)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with pytest.raises(ValueError, match="Missing TELEGRAM_CHAT_ID"):
        send_telegram("Message", token=SAMPLE_TOKEN, chat_id=None)


@patch("urllib.request.urlopen")
def test_send_telegram_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True, "result": {"message_id": 101}}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    success = send_telegram("Test Hello", token=SAMPLE_TOKEN, chat_id=SAMPLE_CHAT_ID)
    assert success is True
    assert mock_urlopen.call_count == 1


@patch("urllib.request.urlopen")
@patch("time.sleep")
def test_send_telegram_retry_on_500(mock_sleep, mock_urlopen):
    # First attempt raises 500, second succeeds
    err = urllib.error.HTTPError(
        url="http://mock",
        code=500,
        msg="Internal Error",
        hdrs={},
        fp=io.BytesIO(b'{"ok": false, "description": "Internal Server Error"}'),
    )
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.side_effect = [err, mock_resp]

    success = send_telegram("Retry message", token=SAMPLE_TOKEN, chat_id=SAMPLE_CHAT_ID)
    assert success is True
    assert mock_urlopen.call_count == 2
    mock_sleep.assert_called_once()


@patch("urllib.request.urlopen")
def test_send_telegram_fail_non_retryable(mock_urlopen):
    # HTTP 400 Bad Request should fail immediately without retries
    err = urllib.error.HTTPError(
        url="http://mock",
        code=400,
        msg="Bad Request",
        hdrs={},
        fp=io.BytesIO(b'{"ok": false, "description": "Chat not found"}'),
    )
    mock_urlopen.side_effect = err

    success = send_telegram("Bad chat message", token=SAMPLE_TOKEN, chat_id=SAMPLE_CHAT_ID)
    assert success is False
    assert mock_urlopen.call_count == 1


@patch("urllib.request.urlopen")
def test_send_telegram_token_never_in_logs(mock_urlopen, caplog):
    caplog.set_level(logging.DEBUG)
    err = urllib.error.HTTPError(
        url=f"https://api.telegram.org/bot{SAMPLE_TOKEN}/sendMessage",
        code=400,
        msg="Bad Request",
        hdrs={},
        fp=io.BytesIO(f'{{"description": "Token {SAMPLE_TOKEN} invalid"}}'.encode("utf-8")),
    )
    mock_urlopen.side_effect = err

    send_telegram("Message", token=SAMPLE_TOKEN, chat_id=SAMPLE_CHAT_ID)
    log_text = caplog.text
    assert SAMPLE_TOKEN not in log_text
