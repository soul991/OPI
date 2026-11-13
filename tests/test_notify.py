"""Unit tests for opi.notify Telegram notification client (Phase 21 WS-A)."""

import io
import json
import urllib.error
import urllib.request
import pytest
from unittest.mock import patch, MagicMock

from opi.notify import split_message, send_telegram, _sanitize_error_message, TELEGRAM_MAX_LENGTH


def test_split_message_empty():
    assert split_message("") == []
    assert split_message(None) == []


def test_split_message_short():
    msg = "Short alert message"
    chunks = split_message(msg)
    assert len(chunks) == 1
    assert chunks[0] == msg


def test_split_message_long_newline():
    line1 = "A" * 3000
    line2 = "B" * 2000
    text = f"{line1}\n{line2}"
    chunks = split_message(text, max_len=3500)
    assert len(chunks) == 2
    assert chunks[0] == line1
    assert chunks[1] == line2


def test_split_message_hard_break():
    text = "X" * 10000
    chunks = split_message(text, max_len=4000)
    assert len(chunks) == 3
    assert len(chunks[0]) == 4000
    assert len(chunks[1]) == 4000
    assert len(chunks[2]) == 2000


def test_send_telegram_dry_run(capsys):
    res = send_telegram("Test dry run message", dry_run=True)
    assert len(res) == 1
    assert res[0]["ok"] is True
    assert res[0]["dry_run"] is True
    captured = capsys.readouterr()
    assert "[DRY-RUN TELEGRAM NOTIFICATION]" in captured.out
    assert "Test dry run message" in captured.out


def test_send_telegram_missing_token_or_chat():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="Missing TELEGRAM_BOT_TOKEN"):
            send_telegram("Hello")

        with pytest.raises(ValueError, match="Missing TELEGRAM_CHAT_ID"):
            send_telegram("Hello", bot_token="fake_token")


def test_send_telegram_success():
    fake_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    fake_chat = "987654321"

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True, "result": {"message_id": 999}}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        res = send_telegram("Hello World", bot_token=fake_token, chat_id=fake_chat)
        assert len(res) == 1
        assert res[0]["ok"] is True
        assert res[0]["result"]["message_id"] == 999

        assert mock_urlopen.call_count == 1
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == f"https://api.telegram.org/bot{fake_token}/sendMessage"
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["chat_id"] == fake_chat
        assert payload["text"] == "Hello World"


def test_send_telegram_retries_on_500():
    fake_token = "123456:SECRET_TOKEN_DO_NOT_LEAK"
    fake_chat = "987654321"

    err_500 = urllib.error.HTTPError(
        url=f"https://api.telegram.org/bot{fake_token}/sendMessage",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=io.BytesIO(b'{"ok": false, "description": "internal server error"}')
    )

    mock_ok = MagicMock()
    mock_ok.read.return_value = json.dumps({"ok": True, "result": {"message_id": 1000}}).encode("utf-8")
    mock_ok.__enter__.return_value = mock_ok

    with patch("urllib.request.urlopen", side_effect=[err_500, mock_ok]) as mock_urlopen:
        with patch("time.sleep", return_value=None) as mock_sleep:
            res = send_telegram("Retry Test", bot_token=fake_token, chat_id=fake_chat, max_retries=3)
            assert len(res) == 1
            assert res[0]["result"]["message_id"] == 1000
            assert mock_urlopen.call_count == 2
            assert mock_sleep.call_count == 1


def test_token_never_leaks_in_exceptions():
    fake_token = "123456:SUPER_SECRET_TOKEN_XYZ"
    fake_chat = "987654321"

    err_401 = urllib.error.HTTPError(
        url=f"https://api.telegram.org/bot{fake_token}/sendMessage",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=io.BytesIO(b'{"ok": false, "description": "Unauthorized"}')
    )

    with patch("urllib.request.urlopen", side_effect=err_401):
        with pytest.raises(RuntimeError) as exc_info:
            send_telegram("Fail Test", bot_token=fake_token, chat_id=fake_chat, max_retries=1)

        err_str = str(exc_info.value)
        assert fake_token not in err_str, "Token leaked in exception message!"
        assert "HTTP 401" in err_str


def test_sanitize_error_message():
    token = "secret_tok_123"
    msg = f"Failed connecting to https://api.telegram.org/bot{token}/sendMessage with code 404"
    sanitized = _sanitize_error_message(msg, token)
    assert token not in sanitized
    assert "<MASKED_BOT_TOKEN>" in sanitized
