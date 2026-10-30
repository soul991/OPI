#!/usr/bin/env python3
"""opi/outcomes.py - Audited append-only outcome corrections engine (D-073).

Provides:
1. `effective_outcome`: Resolves the effective outcome for a prediction row,
   layering append-only corrections from `predictions/outcome_corrections.csv`
   over the immutable `predictions/prediction_log.csv`.
2. `get_effective_predictions_df`: Returns a copy of the prediction log with all
   effective outcomes applied.
3. `record_outcome_correction`: Appends an audited correction record with proof
   that the cited evidence file exists on disk.
4. `execute_tier2b_fetch`: Fetches two independent pages for listing price verification.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional, Tuple

import pandas as pd
import requests

from opi.log import IST, get_write_timestamp

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CORRECTIONS_PATH = ROOT_DIR / "predictions" / "outcome_corrections.csv"

CORRECTIONS_COLUMNS = [
    "company",
    "listing_date",
    "field",
    "old_value",
    "new_value",
    "reason",
    "evidence_path",
    "tier",
    "corrected_at",
]

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def get_corrections_path(custom_path: Optional[Path] = None) -> Path:
    """Return the active outcome corrections file path."""
    return custom_path or DEFAULT_CORRECTIONS_PATH


def load_corrections(corrections_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the outcome corrections ledger, returning an empty DataFrame if absent."""
    p = get_corrections_path(corrections_path)
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame(columns=CORRECTIONS_COLUMNS)
    try:
        df = pd.read_csv(p, dtype=str, keep_default_na=False)
        for col in CORRECTIONS_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[CORRECTIONS_COLUMNS]
    except Exception:
        return pd.DataFrame(columns=CORRECTIONS_COLUMNS)


def effective_outcome(
    row: dict | pd.Series,
    corrections_df: Optional[pd.DataFrame] = None,
    corrections_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Resolve the effective outcome for a prediction row.

    If a correction exists for `actual_gain_pct` for the matching (company, listing_date),
    the latest correction supersedes prior ones.
    """
    company = str(row.get("company", "")).strip()
    listing_date = str(row.get("listing_date", "")).strip()[:10]

    raw_gain_str = str(row.get("actual_gain_pct", "")).strip()
    raw_gain: Optional[float] = None
    if raw_gain_str and raw_gain_str.lower() != "nan":
        try:
            raw_gain = float(raw_gain_str)
        except ValueError:
            raw_gain = None

    notes_str = str(row.get("notes", ""))
    default_tier = "tier2" if "outcome_source=tier2" in notes_str else ("tier1" if "outcome_source=tier1" in notes_str else "unspecified")

    result = {
        "company": company,
        "listing_date": listing_date,
        "actual_gain_pct": raw_gain,
        "is_corrected": False,
        "old_value": None,
        "new_value": raw_gain,
        "reason": None,
        "tier": default_tier,
        "evidence_path": None,
        "corrected_at": None,
    }

    c_df = corrections_df if corrections_df is not None else load_corrections(corrections_path)
    if c_df.empty:
        return result

    # Match company and listing_date
    mask = (
        (c_df["company"].str.strip().str.lower() == company.lower())
        & (c_df["listing_date"].str.strip().str[:10] == listing_date)
        & (c_df["field"].str.strip() == "actual_gain_pct")
    )
    matches = c_df[mask]
    if not matches.empty:
        # Latest correction row wins (newest supersedes oldest)
        latest = matches.iloc[-1]
        try:
            effective_val = float(latest["new_value"])
        except ValueError:
            effective_val = None

        result.update({
            "actual_gain_pct": effective_val,
            "is_corrected": True,
            "old_value": latest["old_value"],
            "new_value": effective_val,
            "reason": latest["reason"],
            "tier": latest["tier"] or "tier2b",
            "evidence_path": latest["evidence_path"],
            "corrected_at": latest["corrected_at"],
        })

    return result


def get_effective_predictions_df(
    df: Optional[pd.DataFrame] = None,
    log_path: Optional[Path] = None,
    corrections_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Return a DataFrame of predictions with all effective outcomes resolved."""
    if df is None:
        p_log = log_path or (ROOT_DIR / "predictions" / "prediction_log.csv")
        if not p_log.exists():
            return pd.DataFrame()
        df = pd.read_csv(p_log, dtype=str, keep_default_na=False)

    c_df = load_corrections(corrections_path)
    out_rows = []
    for _, r in df.iterrows():
        r_dict = dict(r)
        eff = effective_outcome(r_dict, corrections_df=c_df)
        r_dict["raw_actual_gain_pct"] = r_dict.get("actual_gain_pct", "")
        r_dict["is_corrected"] = eff["is_corrected"]
        r_dict["effective_tier"] = eff["tier"]
        r_dict["correction_reason"] = eff["reason"] or ""
        r_dict["correction_evidence"] = eff["evidence_path"] or ""
        if eff["is_corrected"] and eff["actual_gain_pct"] is not None:
            r_dict["actual_gain_pct"] = f"{eff['actual_gain_pct']:.2f}"
        out_rows.append(r_dict)

    return pd.DataFrame(out_rows)


def record_outcome_correction(
    *,
    company: str,
    listing_date: str | date,
    field: str,
    old_value: Any,
    new_value: Any,
    reason: str,
    evidence_path: str | Path,
    tier: str = "tier2b",
    corrections_path: Optional[Path] = None,
    root_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """Append an audited correction to the corrections ledger.

    Strict Requirements:
    1. The cited evidence_path MUST exist on disk.
    2. Company, listing_date, reason must not be empty.
    3. File is append-only.
    """
    if not company or not str(company).strip():
        raise ValueError("Company name must not be empty")
    if not listing_date:
        raise ValueError("Listing date must not be empty")
    if not reason or not str(reason).strip():
        raise ValueError("Correction reason must not be empty")

    base_root = root_dir or ROOT_DIR
    ev_p = Path(evidence_path)
    if not ev_p.is_absolute():
        ev_p = base_root / ev_p

    if not ev_p.exists():
        raise ValueError(f"Evidence file does not exist on disk: {evidence_path}")

    # Relative path for portable storage
    rel_evidence = ev_p.relative_to(base_root).as_posix() if ev_p.is_relative_to(base_root) else str(ev_p)

    target_csv = get_corrections_path(corrections_path)
    target_csv.parent.mkdir(parents=True, exist_ok=True)

    date_str = listing_date.isoformat() if hasattr(listing_date, "isoformat") else str(listing_date)[:10]
    timestamp = datetime.now(timezone.utc).isoformat()

    row_data = {
        "company": str(company).strip(),
        "listing_date": date_str,
        "field": str(field).strip(),
        "old_value": str(old_value).strip(),
        "new_value": str(new_value).strip(),
        "reason": str(reason).strip(),
        "evidence_path": rel_evidence,
        "tier": str(tier).strip(),
        "corrected_at": timestamp,
    }

    file_exists = target_csv.exists() and target_csv.stat().st_size > 0
    with open(target_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CORRECTIONS_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)

    return row_data


def fetch_tier2b_independent_sources(
    source_a_url: str,
    source_b_url: str,
    headers: Optional[dict[str, str]] = None,
    mock_source_a_text: Optional[str] = None,
    mock_source_b_text: Optional[str] = None,
) -> Tuple[Optional[float], Optional[bytes], Optional[float], Optional[bytes], Optional[str]]:
    """Fetch two independent sources and verify listing prices within 1.0% tolerance."""
    hdrs = headers or DEFAULT_HEADERS

    # Source A
    if mock_source_a_text is not None:
        raw_a = mock_source_a_text.encode("utf-8")
        text_a = mock_source_a_text
    else:
        try:
            ra = requests.get(source_a_url, headers=hdrs, timeout=15)
            if ra.status_code != 200:
                return None, None, None, None, f"Source A returned HTTP {ra.status_code}"
            raw_a = ra.content
            text_a = ra.text
        except Exception as e:
            return None, None, None, None, f"Source A fetch failed: {e}"

    # Source B
    if mock_source_b_text is not None:
        raw_b = mock_source_b_text.encode("utf-8")
        text_b = mock_source_b_text
    else:
        try:
            rb = requests.get(source_b_url, headers=hdrs, timeout=15)
            if rb.status_code != 200:
                return None, None, None, None, f"Source B returned HTTP {rb.status_code}"
            raw_b = rb.content
            text_b = rb.text
        except Exception as e:
            return None, None, None, None, f"Source B fetch failed: {e}"

    # Extract price from Source A (Chittorgarh listing day table)
    price_a: Optional[float] = None
    m_row = re.search(r"<tr>\s*<td>Open</td>(.*?)</tr>", text_a, re.DOTALL | re.IGNORECASE)
    if m_row:
        clean_row = re.sub(r"<[^>]+>", " ", m_row.group(1))
        m_val = re.search(r"([0-9]+(?:\.[0-9]+)?)", clean_row)
        if m_val:
            price_a = float(m_val.group(1))
    if price_a is None:
        clean_a = re.sub(r"<[^>]+>", " ", text_a)
        m_open = re.search(r"Open\s*(?:₹|&#8377;)?\s*([0-9]+(?:\.[0-9]+)?)", clean_a, re.IGNORECASE)
        if m_open:
            price_a = float(m_open.group(1))

    # Extract price from Source B (e.g. Groww listing article)
    price_b: Optional[float] = None
    clean_b = re.sub(r"<[^>]+>", " ", text_b)
    m_list = re.search(r"(?:listed at|shares listed at|opening price of)\s*(?:₹|&#8377;|Rs\.?)?\s*([0-9]+(?:\.[0-9]+)?)", clean_b, re.IGNORECASE)
    if m_list:
        price_b = float(m_list.group(1))
    else:
        # Fallback to general price match
        m_gen = re.search(r"₹\s*([0-9]+(?:\.[0-9]+)?)\s*apiece", clean_b, re.IGNORECASE)
        if m_gen:
            price_b = float(m_gen.group(1))

    if price_a is None:
        return None, raw_a, price_b, raw_b, "Could not extract price from Source A"
    if price_b is None:
        return price_a, raw_a, None, raw_b, "Could not extract price from Source B"

    rel_diff = abs(price_a - price_b) / price_a * 100.0
    if rel_diff > 1.0:
        return price_a, raw_a, price_b, raw_b, f"Sources diverge beyond 1.0%: A={price_a} vs B={price_b} (diff={rel_diff:.2f}%)"

    return price_a, raw_a, price_b, raw_b, None
