"""
Stage 'announce' alert runner for OPI.
Discovers upcoming and open Mainboard IPOs, formats standardized announcements,
and delivers notifications via Telegram with deduplication.
"""

import logging
from typing import Any, Dict, List, Optional

from opi.alert_state import already_sent, record_alert_sent
from opi.discover import discover_ipos
from opi.notify import send_telegram

logger = logging.getLogger(__name__)


def format_announce_message(cand: Dict[str, Any]) -> str:
    """Format standardized Telegram announcement message per Phase 21 preregistration."""
    company = cand.get("company", "Unknown Company")
    open_date = cand.get("open_date") or "TBD"
    close_date = cand.get("close_date") or "TBD"
    listing_date = cand.get("listing_date") or "TBD"

    price_band = cand.get("price_band") or cand.get("issue_price") or "TBD"
    lot_size = cand.get("lot_size", "TBD")
    issue_size = cand.get("issue_size_cr") or cand.get("issue_size", "TBD")
    fresh_pct = cand.get("fresh_pct", "TBD")
    ofs_pct = cand.get("ofs_pct", "TBD")
    exchange = cand.get("exchange", "NSE / BSE")

    # If lot_size and issue_price are numeric, compute min bid amount
    min_bid = "TBD"
    try:
        p_val = float(str(price_band).replace("₹", "").replace(",", "").split("-")[-1].strip())
        l_val = int(str(lot_size).replace(",", "").strip())
        min_bid = f"₹{int(p_val * l_val):,}"
    except Exception:
        pass

    msg = (
        f"📢 OPI IPO ANNOUNCEMENT: {company}\n\n"
        f"📅 Issue Schedule:\n"
        f"  • Bidding Opens: {open_date}\n"
        f"  • Bidding Closes: {close_date}\n"
        f"  • Listing Date: {listing_date}\n"
        f"💰 Issue Structure:\n"
        f"  • Price Band / Price: ₹{price_band}\n"
        f"  • Lot Size: {lot_size} shares (Minimum Bid: {min_bid})\n"
        f"  • Issue Size: ₹{issue_size} Cr (Fresh: {fresh_pct}%, OFS: {ofs_pct}%)\n"
        f"🏢 Exchange: {exchange}\n\n"
        f"ℹ️ First-look notice. Full PREVIEW analysis will be delivered on close date at 11:45 AM IST.\n"
        f"Decision aid only, not financial advice."
    )
    return msg


def run_announce_stage(
    candidates: Optional[List[Dict[str, Any]]] = None,
    dry_run: bool = False,
    run_id: Optional[str] = None,
    alerts_csv: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Run announce stage: find eligible Mainboard IPOs, filter duplicates, send alerts.
    """
    if candidates is None:
        raw_candidates = discover_ipos()
    else:
        raw_candidates = candidates

    sent_alerts: List[Dict[str, Any]] = []

    for cand in raw_candidates:
        company = cand.get("company", "").strip()
        close_date = str(cand.get("close_date", "")).strip()
        listing_date = str(cand.get("listing_date", "")).strip()
        status = cand.get("status", "").upper()
        ipo_type = cand.get("type", "Mainboard")

        # Inclusions: Mainboard only, UPCOMING or BIDDING_OPEN, must have valid dates
        if not company or not close_date:
            continue
        if ipo_type and "sme" in ipo_type.lower():
            continue
        if status in ("LISTED", "SKIPPED_ALREADY_LISTED", "CLOSED_UNLISTED"):
            continue
        if status not in ("UPCOMING", "BIDDING_OPEN"):
            continue

        # Check idempotency
        if already_sent(company, close_date, "announce", csv_path=alerts_csv):
            logger.info(f"Skipping {company} (close {close_date}): announce alert already sent.")
            continue

        message_text = format_announce_message(cand)

        success = send_telegram(message_text, dry_run=dry_run)
        if success:
            record_alert_sent(
                company=company,
                close_date=close_date,
                listing_date=listing_date,
                alert_type="announce",
                stage="announce",
                text=message_text,
                run_id=run_id,
                csv_path=alerts_csv,
            )
            sent_alerts.append({"company": company, "close_date": close_date, "status": "SENT"})
            logger.info(f"Announce alert delivered for {company}.")
        else:
            logger.error(f"Failed to deliver announce alert for {company}.")

    return sent_alerts
