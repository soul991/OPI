"""
Unified Telegram alert runner entrypoint for OPI (Phase 21).
Dispatches announce, preview, or listing stage alerts with deduplication
and dry-run support.
"""

import argparse
import logging
import sys
from typing import List, Dict, Any

from opi.stage_announce import run_announce_stage
from opi.stage_preview import run_preview_stage
from opi.stage_listing import run_listing_stage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("opi.notify_run")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OPI Stage Notification Dispatcher")
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=["announce", "preview", "listing"],
        help="Stage to execute: announce (09:00/20:00 IST), preview (11:45 IST), or listing (11:30/16:30 IST)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print notification text to console and test scoring without sending Telegram messages",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    stage = args.stage.lower()
    logger.info(f"Starting OPI Notify Stage: {stage} (dry_run={args.dry_run})")

    try:
        if stage == "announce":
            sent = run_announce_stage(dry_run=args.dry_run)
            logger.info(f"Stage announce finished. Alerts dispatched: {len(sent)}")
        elif stage == "preview":
            sent = run_preview_stage(dry_run=args.dry_run)
            logger.info(f"Stage preview finished. Alerts dispatched: {len(sent)}")
        elif stage == "listing":
            sent = run_listing_stage(dry_run=args.dry_run)
            logger.info(f"Stage listing finished. Alerts dispatched: {len(sent)}")
        else:
            logger.error(f"Unknown stage: {stage}")
            return 1

        return 0
    except Exception as exc:
        logger.error(f"Error during stage {stage}: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
