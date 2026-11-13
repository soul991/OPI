"""
Telegram notification module for OPI.
Supports message splitting (4096-char Telegram limit), exponential backoff,
timeout controls, dry-run CLI mode, and zero-token-leak sanitization.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import List, Optional

logger = logging.getLogger(__name__)

TELEGRAM_MAX_CHARS = 4096
DEFAULT_TIMEOUT_SEC = 10
DEFAULT_MAX_RETRIES = 3


def sanitize_text(text: str, secrets: Optional[List[str]] = None) -> str:
    """Mask known secrets and general Telegram bot token patterns from text."""
    if not text:
        return text
    sanitized = text
    if secrets:
        for s in secrets:
            if s and len(s) > 4:
                sanitized = sanitized.replace(s, "***REDACTED***")
    # Mask bot token patterns like 123456789:ABCdefGhI...
    sanitized = re.sub(r"\b\d{8,12}:[A-Za-z0-9_-]{30,50}\b", "***REDACTED_BOT_TOKEN***", sanitized)
    return sanitized


def split_message(text: str, limit: int = TELEGRAM_MAX_CHARS) -> List[str]:
    """Split text into chunks of at most `limit` characters, breaking at newlines if possible."""
    if not text:
        return []
    if len(text) <= limit:
        return [text]

    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break

        # Look for the last newline within the limit
        split_point = remaining.rfind("\n", 0, limit)
        if split_point == -1 or split_point < limit // 3:
            # Look for the last space within the limit
            split_point = remaining.rfind(" ", 0, limit)

        if split_point == -1 or split_point < limit // 3:
            # Hard split at character limit if no suitable boundary
            split_point = limit

        chunks.append(remaining[:split_point].rstrip())
        remaining = remaining[split_point:].lstrip("\r\n ")

    return chunks


def send_telegram(
    text: str,
    token: Optional[str] = None,
    chat_id: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SEC,
    max_retries: int = DEFAULT_MAX_RETRIES,
    dry_run: bool = False,
) -> bool:
    """
    Send a message to Telegram with retry, chunking, and secret sanitization.

    Returns:
        bool: True if all message chunks were delivered successfully, False otherwise.
    """
    if dry_run:
        print("[DRY RUN] Telegram message:")
        print(text)
        return True

    bot_token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    target_chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN: token must be provided or set in environment.")
    if not target_chat_id:
        raise ValueError("Missing TELEGRAM_CHAT_ID: chat_id must be provided or set in environment.")

    chunks = split_message(text)
    if not chunks:
        return True

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    headers = {"Content-Type": "application/json; charset=utf-8"}

    for chunk in chunks:
        payload = json.dumps({"chat_id": str(target_chat_id), "text": chunk}).encode("utf-8")
        success = False

        for attempt in range(1, max_retries + 1):
            try:
                req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    if resp_data.get("ok"):
                        success = True
                        break
                    else:
                        desc = sanitize_text(str(resp_data.get("description", "")), [bot_token])
                        logger.warning(f"Telegram API response not ok (attempt {attempt}/{max_retries}): {desc}")
            except urllib.error.HTTPError as e:
                err_body = ""
                try:
                    err_body = sanitize_text(e.read().decode("utf-8", errors="replace"), [bot_token])
                except Exception:
                    pass
                logger.warning(
                    f"HTTPError {e.code} on Telegram send (attempt {attempt}/{max_retries}): {err_body}"
                )
                # Retry on rate limit (429) or server error (5xx)
                if e.code not in (429, 500, 502, 503, 504):
                    logger.error(f"Non-retryable HTTP error {e.code}: {err_body}")
                    return False
            except urllib.error.URLError as e:
                clean_err = sanitize_text(str(e.reason), [bot_token])
                logger.warning(f"URLError on Telegram send (attempt {attempt}/{max_retries}): {clean_err}")
            except Exception as e:
                clean_err = sanitize_text(str(e), [bot_token])
                logger.warning(f"Unexpected error on Telegram send (attempt {attempt}/{max_retries}): {clean_err}")

            if attempt < max_retries:
                time.sleep(1.5 * attempt)

        if not success:
            logger.error("Failed to deliver message chunk after retries.")
            return False

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="OPI Telegram Alert Dispatcher")
    parser.add_argument("--message", type=str, required=True, help="Message text to deliver")
    parser.add_argument("--dry-run", action="store_true", help="Print message and exit without sending")
    args = parser.parse_args()

    try:
        ok = send_telegram(args.message, dry_run=args.dry_run)
        if ok:
            print("Telegram alert sent successfully.")
            sys.exit(0)
        else:
            print("Failed to send Telegram alert.", file=sys.stderr)
            sys.exit(1)
    except Exception as exc:
        print(f"Error: {sanitize_text(str(exc))}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
