#!/usr/bin/env python3
"""Zoho Catalyst Serverless Function: opi_trigger

Scheduled cron and on-demand trigger that dispatches .github/workflows/notify.yml
via the GitHub Actions workflow_dispatch API with GITHUB_DISPATCH_TOKEN.

Design Rules (Section 5 & WS-G in 1_planning_and_goals.md):
1. Expects HTTP 204 on success.
2. Retries up to 2 times on non-204 or network error with backoff.
3. On final failure: dispatches fallback Telegram alert directly to TELEGRAM_CHAT_ID.
4. Secret hygiene: sanitize_text guarantees zero tokens in logs, prints, or exceptions.
5. Catalyst entrypoint `handler(*args, **kwargs)` gracefully handles any invocation mode:
   - Cron Function: handler(cron_details, context)
   - Basic I/O: handler(context, basicio)
   - Advanced I/O: handler(request, response)
   - Standalone CLI execution: python -m catalyst.opi_trigger.main
"""
import argparse
from datetime import datetime, timezone, timedelta
import json
import logging
import os
import re
import sys
import time
import urllib.request
import urllib.error

# IST timezone: UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))

REPO = "soul991/OPI"
WORKFLOW_FILE = "notify.yml"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
TELEGRAM_API_URL_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"

TOKEN_PATTERNS = [
    re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,50}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{36,255}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,255}\b"),
]

logger = logging.getLogger("opi_trigger")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def sanitize_text(text: str, explicit_tokens: list[str] = None) -> str:
    """Mask tokens and secrets from text strings, logs, and error messages."""
    if not text:
        return ""
    masked = str(text)
    if explicit_tokens:
        for t in explicit_tokens:
            if t and len(str(t).strip()) > 5:
                masked = masked.replace(str(t).strip(), "[REDACTED_SECRET]")
    for pat in TOKEN_PATTERNS:
        masked = pat.sub("[REDACTED_TOKEN]", masked)
    return masked


def get_secret(name: str, fallback_names: list[str] = None) -> str:
    """Read secret from environment variable safely."""
    val = os.environ.get(name)
    if val and val.strip():
        return val.strip()
    if fallback_names:
        for fb in fallback_names:
            val = os.environ.get(fb)
            if val and val.strip():
                return val.strip()
    return ""


def determine_stage(explicit_stage: str = None, now: datetime = None) -> str:
    """Determine the notification stage from explicit argument or IST clock.
    
    IST Schedule Mapping:
    - 08:30 to 09:30 or 19:30 to 20:30 IST -> 'announce'
    - 11:35 to 11:55 IST -> 'preview'
    - 11:15 to 11:35 or 16:15 to 16:45 IST -> 'listing'
    """
    valid_stages = {"announce", "preview", "listing"}
    if explicit_stage and explicit_stage.lower().strip() in valid_stages:
        return explicit_stage.lower().strip()

    if now is None:
        now = datetime.now(timezone.utc).astimezone(IST)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=IST)
    else:
        now = now.astimezone(IST)

    total_mins = now.hour * 60 + now.minute

    # 11:45 IST preview window: 11:35 - 11:55 (695 - 715 mins)
    if 695 <= total_mins <= 715:
        return "preview"
    # 11:30 IST listing window: 11:15 - 11:34 (675 - 694 mins)
    # 16:30 IST listing window: 16:15 - 16:45 (975 - 1005 mins)
    if (675 <= total_mins <= 694) or (975 <= total_mins <= 1005):
        return "listing"
    # 09:00 IST announce window: 08:30 - 09:30 (510 - 570 mins)
    # 20:00 IST announce window: 19:30 - 20:30 (1170 - 1230 mins)
    if (510 <= total_mins <= 570) or (1170 <= total_mins <= 1230):
        return "announce"

    # Default fallback
    return "announce"


def send_telegram_fallback(stage: str, error_msg: str, status_code: int = 0) -> bool:
    """Send emergency direct Telegram alert if GitHub Actions dispatch fails after retries."""
    bot_token = get_secret("TELEGRAM_BOT_TOKEN")
    chat_id = get_secret("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        logger.error("Cannot send fallback Telegram alert: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID unset")
        return False

    clean_err = sanitize_text(error_msg, [bot_token])
    text = (
        f"🚨 [OPI Catalyst Alert]\n"
        f"Trigger failed for stage: {stage}\n"
        f"HTTP Status: {status_code}\n"
        f"Error: {clean_err}\n"
        f"Action: Check Catalyst logs and GitHub Actions status."
    )
    url = TELEGRAM_API_URL_TEMPLATE.format(token=bot_token)
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_status = getattr(resp, "status", getattr(resp, "code", 200))
            if resp_status == 200:
                logger.info(sanitize_text(f"Telegram fallback alert delivered for stage {stage}"))
                return True
            logger.warning(f"Telegram fallback returned HTTP {resp_status}")
            return False
    except Exception as e:
        logger.error(sanitize_text(f"Telegram fallback delivery failed: {e}", [bot_token]))
        return False


def dispatch_github_workflow(
    stage: str,
    dry_run: bool = False,
    max_retries: int = 2,
    timeout: int = 15,
    dispatch_token: str = None
) -> dict:
    """Dispatch notify.yml via GitHub Actions workflow_dispatch endpoint with retries."""
    token = dispatch_token or get_secret("GITHUB_DISPATCH_TOKEN", ["GITHUB_PAT"])
    if not token:
        err = "Missing GITHUB_DISPATCH_TOKEN (or GITHUB_PAT) in environment"
        logger.error(err)
        send_telegram_fallback(stage, err, status_code=0)
        return {"success": False, "status": 0, "error": err, "attempts": 0}

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "OPI-Catalyst-Trigger",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "ref": "main",
        "inputs": {
            "stage": stage,
            "dry_run": "true" if dry_run else "false"
        }
    }).encode("utf-8")

    last_error = ""
    last_status = 0

    for attempt in range(1, max_retries + 2):
        logger.info(f"Dispatch attempt {attempt}/{max_retries + 1} for stage '{stage}' (dry_run={dry_run})")
        req = urllib.request.Request(GITHUB_API_URL, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_status = getattr(resp, "status", getattr(resp, "code", 200))
                if resp_status == 204:
                    logger.info(f"Dispatch SUCCESS (HTTP 204) on attempt {attempt}")
                    return {"success": True, "status": 204, "attempts": attempt, "stage": stage}
                last_status = resp_status
                last_error = f"Unexpected response status: {resp_status}"
                logger.warning(last_error)
        except urllib.error.HTTPError as e:
            last_status = e.code
            try:
                err_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                err_body = ""
            last_error = sanitize_text(f"HTTP {e.code}: {e.reason} - {err_body}", [token])
            logger.warning(f"Dispatch attempt {attempt} failed: {last_error}")
        except Exception as e:
            last_status = 0
            last_error = sanitize_text(f"Network error: {e}", [token])
            logger.warning(f"Dispatch attempt {attempt} failed: {last_error}")

        if attempt <= max_retries:
            backoff_secs = 1.0 * attempt
            logger.info(f"Retrying in {backoff_secs:.1f}s...")
            time.sleep(backoff_secs)

    # All attempts exhausted
    logger.error(f"All {max_retries + 1} dispatch attempts failed for stage '{stage}'. Triggering fallback.")
    send_telegram_fallback(stage, last_error, status_code=last_status)
    return {"success": False, "status": last_status, "error": last_error, "attempts": max_retries + 1, "stage": stage}


def handler(*args, **kwargs) -> dict:
    """Universal Catalyst function entry point.
    
    Accepts:
    - Cron function: handler(cron_details, context)
    - Basic I/O function: handler(context, basicio)
    - Advanced I/O function: handler(request, response)
    - Direct python calls: handler(stage="announce", dry_run=True)
    """
    logger.info("Catalyst opi_trigger invoked")
    explicit_stage = kwargs.get("stage")
    dry_run = kwargs.get("dry_run", False)

    context = None
    basicio = None

    # Inspect positional arguments
    for arg in args:
        if callable(getattr(arg, "get_cron_param", None)) and not callable(getattr(arg, "get_argument", None)):
            try:
                val = arg.get_cron_param("stage")
                if val and isinstance(val, str):
                    explicit_stage = str(val).strip()
                dr_val = arg.get_cron_param("dry_run")
                if dr_val is not None and isinstance(dr_val, (str, bool)):
                    dry_run = str(dr_val).lower() in ("true", "1", "yes")
            except Exception:
                pass
        elif callable(getattr(arg, "get_argument", None)):
            basicio = arg
            try:
                val = arg.get_argument("stage")
                if val and isinstance(val, str):
                    explicit_stage = str(val).strip()
                dr_val = arg.get_argument("dry_run")
                if dr_val is not None and isinstance(dr_val, (str, bool)):
                    dry_run = str(dr_val).lower() in ("true", "1", "yes")
            except Exception:
                pass
        elif hasattr(arg, "query_params") and isinstance(arg.query_params, dict):
            val = arg.query_params.get("stage")
            if val and isinstance(val, str):
                explicit_stage = str(val).strip()
            dr_val = arg.query_params.get("dry_run")
            if dr_val is not None and isinstance(dr_val, (str, bool)):
                dry_run = str(dr_val).lower() in ("true", "1", "yes")

        if hasattr(arg, "closeWithSuccess"):
            context = arg

    # Environment variable overrides
    if not explicit_stage and os.environ.get("STAGE"):
        explicit_stage = os.environ.get("STAGE")
    if not dry_run and os.environ.get("DRY_RUN"):
        dry_run = os.environ.get("DRY_RUN", "").lower() in ("true", "1", "yes")

    stage = determine_stage(explicit_stage)
    result = dispatch_github_workflow(stage=stage, dry_run=dry_run)

    # Response output to basicio if provided
    if basicio and hasattr(basicio, "write"):
        try:
            basicio.write(json.dumps(result))
        except Exception:
            pass

    # Context closing if provided
    if context:
        if result["success"] and hasattr(context, "closeWithSuccess"):
            context.closeWithSuccess()
        elif not result["success"] and hasattr(context, "closeWithFailure"):
            context.closeWithFailure()

    return result


def main():
    parser = argparse.ArgumentParser(description="OPI Catalyst Trigger CLI")
    parser.add_argument("--stage", choices=["announce", "preview", "listing"], default=None,
                        help="Specific stage to dispatch (defaults to IST time-of-day)")
    parser.add_argument("--dry-run", action="store_true", help="Pass dry_run=true to workflow")
    args = parser.parse_args()

    result = handler(stage=args.stage, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
