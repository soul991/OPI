"""Grounded ingestion and deterministic parsing for IPO candidate inputs.

Fetches overview, subscription, and GMP pages, saves immutable snapshots under
data/evidence/<type>/, hashes them, deterministically parses fields from HTML,
and compares any supplied/proposed values against parsed values, refusing on mismatch.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional, Dict, Tuple
import requests
from bs4 import BeautifulSoup

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class IngestionError(ValueError):
    """Raised when ingestion fails, values mismatch parsed snapshot, or sources are invalid."""


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def save_raw_market_data(
    raw_bytes: bytes,
    date_str: str,
    source: str = "yfinance",
    output_dir: Optional[Path] = None,
) -> tuple[Path, Path, str]:
    """Save raw market response bytes and metadata manifest with SHA-256 hash."""
    target_dir = Path(output_dir) if output_dir else (ROOT_DIR / "data" / "evidence" / "market")
    target_dir.mkdir(parents=True, exist_ok=True)

    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    raw_path = target_dir / f"{date_str}_market_macro.raw"
    raw_path.write_bytes(raw_bytes)

    meta = {
        "date": date_str,
        "source": source,
        "source_type": "unofficial" if source == "yfinance" else "official",
        "confidence": "medium" if source == "yfinance" else "high",
        "accessed_at": datetime.now().isoformat(),
        "sha256": sha256,
        "raw_file": raw_path.name,
    }
    meta_path = target_dir / f"{date_str}_market_macro.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return raw_path, meta_path, sha256


def parse_chittorgarh_subscription(html_text: str) -> Dict[str, float]:
    """Deterministically parse final category subscriptions from Chittorgarh subscription page."""
    soup = BeautifulSoup(html_text, "html.parser")
    results: Dict[str, float] = {}

    sub_tables = []
    for table in soup.find_all("table"):
        text = " ".join([th.get_text(strip=True).lower() for th in table.find_all(["th", "td"])[:15]])
        if "subscription" in text and ("(x)" in text or "times" in text):
            sub_tables.append(table)

    tables_to_search = sub_tables if sub_tables else soup.find_all("table")

    for table in tables_to_search:
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            label = cells[0].lower().strip()
            val_str = cells[1].replace(",", "").replace("x", "").strip()
            try:
                val = float(val_str)
            except ValueError:
                continue

            if "qualified institutional" in label or ("qib" in label and "anchor" in label):
                results["sub_qib"] = val
            elif label == "qib":
                results.setdefault("sub_qib", val)
            elif "non institutional" in label or label == "nii":
                results["sub_nii"] = val
            elif "retail" in label or "retail individual" in label:
                results["sub_retail"] = val
            elif "total" in label and ("**" in cells[0] or "subscription" in label):
                results["sub_total"] = val

    return results


def parse_investorgain_gmp(html_text: str, close_date: str) -> Tuple[Optional[float], Optional[str]]:
    """Select table row for the last bidding day evening (e.g. 19-Oct 23:37), never top row blindly."""
    soup = BeautifulSoup(html_text, "html.parser")
    try:
        dt = datetime.strptime(close_date, "%Y-%m-%d")
        close_prefix = dt.strftime("%d-%b").lower()  # e.g. "19-oct"
    except Exception:
        close_prefix = ""

    matched_gmp: Optional[float] = None
    matched_as_of: Optional[str] = None

    for tr in soup.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if len(cells) < 3:
            continue
        date_cell = cells[0].lower()
        # Look for the row matching the last bidding day
        if close_prefix and close_prefix in date_cell:
            gmp_cell = cells[1]
            m = re.search(r"\(([-+]?\d*\.?\d+)\s*%\)", gmp_cell)
            if m:
                matched_gmp = float(m.group(1))
                matched_as_of = cells[0]
                break

    return matched_gmp, matched_as_of


def parse_chittorgarh_overview(html_text: str) -> Dict[str, Any]:
    """Deterministically parse IPO parameters from Chittorgarh overview page."""
    soup = BeautifulSoup(html_text, "html.parser")
    out: Dict[str, Any] = {}

    for tr in soup.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if len(cells) != 2:
            continue
        k = cells[0].lower()
        v = cells[1]

        if "issue price" in k:
            m = re.search(r"(\d+(?:\.\d+)?)", v)
            if m:
                out["issue_price"] = float(m.group(1))
        elif "price band" in k:
            m = re.findall(r"(\d+(?:\.\d+)?)", v)
            if m:
                out.setdefault("issue_price", float(m[-1]))
        elif "lot size" in k:
            m = re.search(r"(\d+)", v)
            if m:
                out["lot_size"] = int(m.group(1))
        elif "total issue size" in k:
            m = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)\s*cr", v, re.IGNORECASE)
            if m:
                out["issue_size_cr"] = float(m.group(1).replace(",", ""))

    return out


def fetch_and_save_evidence(
    url: str,
    category: str,
    listing_date: str,
    company: str,
    timeout: int = 15,
) -> tuple[Path, str, str]:
    """Fetch URL, save to data/evidence/<category>/<listing_date>_<company-slug>.html, return (path, sha256, html)."""
    slug = slugify(company)
    target_dir = ROOT_DIR / "data" / "evidence" / category
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{listing_date}_{slug}.html"

    if target_file.exists():
        existing_html = target_file.read_text(encoding="utf-8", errors="replace")
        if "<table" in existing_html:
            sha256 = hashlib.sha256(existing_html.encode("utf-8", errors="replace")).hexdigest()
            return target_file, sha256, existing_html

    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    if resp.status_code != 200:
        raise IngestionError(f"HTTP {resp.status_code} fetching {url}")

    html = resp.text
    target_file.write_text(html, encoding="utf-8", errors="replace")
    sha256 = hashlib.sha256(html.encode("utf-8", errors="replace")).hexdigest()
    return target_file, sha256, html


def ingest_ipo_data(
    company: str,
    listing_date: str,
    close_date: str,
    overview_url: str,
    subscription_url: str,
    gmp_url: Optional[str] = None,
    proposed_values: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Ingest, snapshot, deterministically parse, and enforce that supplied values match parsed values."""
    # 1. Fetch & parse overview
    _, _, overview_html = fetch_and_save_evidence(overview_url, "research", listing_date, company)
    parsed_overview = parse_chittorgarh_overview(overview_html)

    # 2. Fetch & parse subscription
    _, _, sub_html = fetch_and_save_evidence(subscription_url, "subscription", listing_date, company)
    parsed_sub = parse_chittorgarh_subscription(sub_html)

    # 3. Fetch & parse GMP
    parsed_gmp = None
    gmp_as_of = None
    if gmp_url:
        _, _, gmp_html = fetch_and_save_evidence(gmp_url, "gmp", listing_date, company)
        parsed_gmp, gmp_as_of = parse_investorgain_gmp(gmp_html, close_date)

    combined_parsed: Dict[str, Any] = {
        **parsed_overview,
        **parsed_sub,
    }
    if parsed_gmp is not None:
        combined_parsed["gmp_pct"] = parsed_gmp
        combined_parsed["gmp_as_of_date"] = gmp_as_of

    # 4. Compare proposed/typed values against parsed values
    if proposed_values:
        for k, prop_val in proposed_values.items():
            if prop_val is None or k not in combined_parsed:
                continue
            parsed_val = combined_parsed[k]
            if isinstance(prop_val, (int, float)) and isinstance(parsed_val, (int, float)):
                if abs(float(prop_val) - float(parsed_val)) > 0.1:
                    raise IngestionError(
                        f"Refused mismatch for '{k}': proposed {prop_val} != parsed {parsed_val}"
                    )
            elif str(prop_val).strip() != str(parsed_val).strip():
                raise IngestionError(
                    f"Refused mismatch for '{k}': proposed {prop_val} != parsed {parsed_val}"
                )

    return combined_parsed
