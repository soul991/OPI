"""
Alert state and idempotency manager for OPI.
Tracks dispatched Telegram alerts in predictions/alerts_sent.csv to guarantee
at-most-once delivery across duplicate triggers, reruns, or retries.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import os
from pathlib import Path
from typing import Optional, Set, Tuple
import pandas as pd

DEFAULT_ALERTS_CSV = Path("predictions/alerts_sent.csv")
ALERTS_COLUMNS = [
    "sent_at_ist",
    "company",
    "close_date",
    "listing_date",
    "alert_type",
    "stage",
    "message_digest",
    "run_id",
]
VALID_ALERT_TYPES = {"announce", "preview", "listing"}

# IST is UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))


def get_current_ist_str() -> str:
    """Return current IST timestamp formatted as ISO-like string."""
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def compute_message_digest(text: str) -> str:
    """Return truncated SHA-256 digest of message text for deduplication/audit."""
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def ensure_alerts_file(csv_path: Optional[Path] = None) -> Path:
    """Ensure the alerts_sent.csv file exists with proper headers."""
    target_path = Path(csv_path) if csv_path else DEFAULT_ALERTS_CSV
    if not target_path.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(",".join(ALERTS_COLUMNS) + "\n")
    return target_path


def load_sent_keys(csv_path: Optional[Path] = None) -> Set[Tuple[str, str, str]]:
    """Return set of normalized (company_slug/name, close_date, alert_type) tuples."""
    target_path = ensure_alerts_file(csv_path)
    try:
        df = pd.read_csv(target_path, dtype=str).fillna("")
        keys = set()
        for _, row in df.iterrows():
            comp = row.get("company", "").strip().lower()
            c_date = row.get("close_date", "").strip()
            a_type = row.get("alert_type", "").strip().lower()
            if comp and a_type:
                keys.add((comp, c_date, a_type))
        return keys
    except Exception:
        return set()


def already_sent(
    company: str,
    close_date: str,
    alert_type: str,
    csv_path: Optional[Path] = None,
) -> bool:
    """
    Check if an alert of the given type has already been sent for company and close date.
    Idempotency key: (company.lower(), close_date, alert_type.lower()).
    """
    if not company or not alert_type:
        return False
    keys = load_sent_keys(csv_path)
    lookup_key = (company.strip().lower(), str(close_date).strip(), alert_type.strip().lower())
    return lookup_key in keys


def record_alert_sent(
    company: str,
    close_date: str,
    listing_date: str,
    alert_type: str,
    stage: str,
    text: str,
    run_id: Optional[str] = None,
    csv_path: Optional[Path] = None,
) -> None:
    """
    Record a successfully delivered alert to the idempotency store.
    """
    a_type = alert_type.strip().lower()
    if a_type not in VALID_ALERT_TYPES:
        raise ValueError(f"Invalid alert_type '{alert_type}'. Must be one of {VALID_ALERT_TYPES}")

    target_path = ensure_alerts_file(csv_path)
    sent_at = get_current_ist_str()
    digest = compute_message_digest(text)
    effective_run_id = run_id or os.environ.get("GITHUB_RUN_ID", "local")

    new_row = pd.DataFrame(
        [
            {
                "sent_at_ist": sent_at,
                "company": company.strip(),
                "close_date": str(close_date).strip(),
                "listing_date": str(listing_date).strip() if listing_date else "",
                "alert_type": a_type,
                "stage": stage.strip(),
                "message_digest": digest,
                "run_id": str(effective_run_id),
            }
        ]
    )

    # Append safely
    new_row.to_csv(target_path, mode="a", header=not target_path.exists(), index=False)
