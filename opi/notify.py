"""Telegram notification client for OPI alerts (Phase 21 WS-A).

Strict secret hygiene:
- Token read only from TELEGRAM_BOT_TOKEN environment variable.
- Bot token is never printed, logged, or included in exception messages.
"""

import os
import sys
import time
import json
import logging
import argparse
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

logger = logging.getLogger("opi.notify")

TELEGRAM_MAX_LENGTH = 4096
DEFAULT_TIMEOUT_SEC = 10.0
MAX_RETRIES = 3
INITIAL_BACKOFF_SEC = 1.0


def _sanitize_error_message(msg: str, token: Optional[str]) -> str:
    """Ensure bot token never leaks into error strings or logs."""
    if token and token in msg:
        msg = msg.replace(token, "<MASKED_BOT_TOKEN>")
    return msg


def split_message(text: str, max_len: int = TELEGRAM_MAX_LENGTH) -> List[str]:
    """Split text into chunks not exceeding max_len characters."""
    if not text:
        return []
    if len(text) <= max_len:
        return [text]

    chunks = []
    remaining = text
    while len(remaining) > max_len:
        # Prefer breaking at line breaks within the limit
        split_idx = remaining.rfind("\n", 0, max_len)
        if split_idx == -1 or split_idx == 0:
            # Prefer breaking at whitespace
            split_idx = remaining.rfind(" ", 0, max_len)
        if split_idx == -1 or split_idx == 0:
            # Hard break if no whitespace found
            split_idx = max_len
        chunks.append(remaining[:split_idx].strip())
        remaining = remaining[split_idx:].strip()

    if remaining:
        chunks.append(remaining)
    return chunks


def send_telegram(
    text: str,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None,
    dry_run: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    max_retries: int = MAX_RETRIES,
) -> List[Dict[str, Any]]:
    """Send a notification message to Telegram.

    Args:
        text: The message body to deliver.
        bot_token: Bot token (defaults to TELEGRAM_BOT_TOKEN env var).
        chat_id: Telegram chat ID (defaults to TELEGRAM_CHAT_ID env var).
        dry_run: If True, prints message and skips network call.
        timeout: HTTP request timeout in seconds.
        max_retries: Maximum retry attempts for transient errors.

    Returns:
        List of Telegram API response dicts (one per chunk).

    Raises:
        ValueError: If token or chat_id is missing.
        RuntimeError: If delivery fails after retries.
    """
    if dry_run:
        print(f"[DRY-RUN TELEGRAM NOTIFICATION]\n{text}")
        return [{"ok": True, "dry_run": True, "text": text}]

    token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    target_chat = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not str(token).strip():
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in environment or arguments.")
    if not target_chat or not str(target_chat).strip():
        raise ValueError("Missing TELEGRAM_CHAT_ID in environment or arguments.")

    token = str(token).strip()
    target_chat = str(target_chat).strip()

    chunks = split_message(text, TELEGRAM_MAX_LENGTH)
    if not chunks:
        return []

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    responses = []

    for chunk in chunks:
        payload = json.dumps({
            "chat_id": target_chat,
            "text": chunk,
            "disable_web_page_preview": True,
        }).encode("utf-8")

        success = False
        last_err: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "OPI-Telegram-Notifier"},
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    if resp_data.get("ok"):
                        responses.append(resp_data)
                        success = True
                        break
                    else:
                        desc = resp_data.get("description", "Unknown error")
                        raise RuntimeError(f"Telegram API ok:false - {desc}")
            except urllib.error.HTTPError as e:
                last_err = e
                # Check for rate limiting
                retry_after = None
                try:
                    err_json = json.loads(e.read().decode("utf-8"))
                    retry_after = err_json.get("parameters", {}).get("retry_after")
                except Exception:
                    pass

                if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    wait_sec = retry_after if retry_after else INITIAL_BACKOFF_SEC * (2 ** (attempt - 1))
                    logger.warning(f"Telegram HTTP {e.code}; retrying in {wait_sec:.1f}s (attempt {attempt}/{max_retries})...")
                    time.sleep(wait_sec)
                else:
                    safe_msg = _sanitize_error_message(f"HTTP {e.code}: {e.reason}", token)
                    raise RuntimeError(f"Failed to send Telegram message: {safe_msg}") from None
            except urllib.error.URLError as e:
                last_err = e
                if attempt < max_retries:
                    wait_sec = INITIAL_BACKOFF_SEC * (2 ** (attempt - 1))
                    logger.warning(f"Network error {e.reason}; retrying in {wait_sec:.1f}s (attempt {attempt}/{max_retries})...")
                    time.sleep(wait_sec)
                else:
                    safe_msg = _sanitize_error_message(str(e.reason), token)
                    raise RuntimeError(f"Network failure sending Telegram message: {safe_msg}") from None
            except Exception as e:
                safe_msg = _sanitize_error_message(str(e), token)
                raise RuntimeError(f"Unexpected error sending Telegram message: {safe_msg}") from None

        if not success:
            safe_msg = _sanitize_error_message(str(last_err), token)
            raise RuntimeError(f"Failed to deliver message chunk after {max_retries} attempts: {safe_msg}")

    return responses


def main():
    parser = argparse.ArgumentParser(description="Send Telegram alerts for OPI")
    parser.add_argument("--text", type=str, required=True, help="Message text to send")
    parser.add_argument("--dry-run", action="store_true", help="Print message without sending")
    args = parser.parse_args()

    try:
        results = send_telegram(args.text, dry_run=args.dry_run)
        print(f"Delivered {len(results)} message chunk(s).")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
