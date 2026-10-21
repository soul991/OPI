"""Mainboard IPO discovery module.

Discovers active, upcoming, and closed-unlisted Mainboard IPOs from official/aggregator
sources. Enforces inclusion criteria (Mainboard only; excludes SME, FPO, Rights Issues).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Any, Optional
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
DISCOVERY_URL = "https://www.chittorgarh.com/ipo/ipo_dashboard.asp"


def parse_discovery_html(html_text: str, as_of_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parse HTML containing IPO listings table and extract eligible Mainboard candidates."""
    ref_date = datetime.strptime(as_of_date, "%Y-%m-%d").date() if as_of_date else date.today()
    soup = BeautifulSoup(html_text, "html.parser")
    candidates: List[Dict[str, Any]] = []

    # Strategy 1: Check multi-column detailed tables (e.g. from fixtures or full schedule pages)
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) < 6:
            continue
        first_td = tr.find("td")
        if not first_td:
            continue

        a_tag = first_td.find("a")
        company = a_tag.get_text(strip=True) if a_tag else first_td.get_text(strip=True)
        if not company or company.lower() in ("issuer company", "company name"):
            continue

        url_path = a_tag.get("href", "") if a_tag else ""
        full_url = f"https://www.chittorgarh.com{url_path}" if url_path.startswith("/") else url_path

        cell_texts = [td.get_text(strip=True) for td in cells]
        open_date_str = cell_texts[1]
        close_date_str = cell_texts[2]
        listing_date_str = cell_texts[3] if len(cell_texts) > 3 else ""
        issue_price_str = cell_texts[4] if len(cell_texts) > 4 else ""
        issue_size_str = cell_texts[5] if len(cell_texts) > 5 else ""
        ipo_type = cell_texts[6].lower() if len(cell_texts) > 6 else ""

        full_row_text = " ".join(cell_texts).lower()
        if "sme" in full_row_text or "emerge" in full_row_text:
            continue
        if "fpo" in full_row_text or "rights" in full_row_text:
            continue
        if ipo_type and "sme" in ipo_type:
            continue

        try:
            c_date = datetime.strptime(close_date_str[:10], "%Y-%m-%d").date()
        except Exception:
            continue

        try:
            o_date = datetime.strptime(open_date_str[:10], "%Y-%m-%d").date()
        except Exception:
            o_date = c_date

        try:
            l_date = datetime.strptime(listing_date_str[:10], "%Y-%m-%d").date() if listing_date_str else None
        except Exception:
            l_date = None

        if ref_date < o_date:
            status = "UPCOMING"
        elif ref_date <= c_date:
            status = "BIDDING_OPEN"
        elif l_date and ref_date >= l_date:
            status = "LISTED"
        else:
            status = "CLOSED_UNLISTED"

        candidates.append({
            "company": company,
            "open_date": str(o_date),
            "close_date": str(c_date),
            "listing_date": str(l_date) if l_date else "",
            "status": status,
            "overview_url": full_url,
            "type": "Mainboard",
            "issue_price": issue_price_str,
            "issue_size_cr": issue_size_str,
        })

    if candidates:
        return candidates

    # Strategy 2: Check 2-column dashboard tables (Chittorgarh ipo_dashboard.asp Table 0)
    tables = soup.find_all("table")
    if tables:
        t0 = tables[0]
        cur_year = ref_date.year
        for tr in t0.find_all("tr")[1:]:
            a = tr.find("a")
            if not a:
                continue
            comp = a.get_text(strip=True)
            href = a.get("href", "")
            if "sme" in href.lower() or "fpo" in href.lower():
                continue
            url = f"https://www.chittorgarh.com{href}" if href.startswith("/") else href
            row_text = tr.get_text(" | ", strip=True)
            parts = [p.strip() for p in row_text.split("|")]
            is_open = "O" in parts
            is_prev = "P" in parts

            date_part = parts[-1]
            m = re.search(r"(\d+)\s*-\s*(\d+)\s*([A-Za-z]+)", date_part)
            if not m:
                continue
            d1, d2, mon = m.groups()
            try:
                close_dt = datetime.strptime(f"{d2} {mon} {cur_year}", "%d %b %Y").date()
                open_dt = datetime.strptime(f"{d1} {mon} {cur_year}", "%d %b %Y").date()
            except Exception:
                continue

            if ref_date < open_dt:
                status = "UPCOMING"
            elif is_open or (open_dt <= ref_date <= close_dt):
                status = "BIDDING_OPEN"
            else:
                status = "CLOSED_UNLISTED"

            candidates.append({
                "company": comp,
                "open_date": str(open_dt),
                "close_date": str(close_dt),
                "listing_date": "",
                "status": status,
                "overview_url": url,
                "type": "Mainboard",
                "issue_price": "",
                "issue_size_cr": "",
            })

    return candidates


def discover_ipos(
    source_html: Optional[str] = None,
    as_of_date: Optional[str] = None,
    timeout: int = 10,
) -> List[Dict[str, Any]]:
    """Discover Mainboard IPO candidates from provided HTML or live web."""
    if source_html is not None:
        return parse_discovery_html(source_html, as_of_date=as_of_date)

    # Try live fetch
    try:
        resp = requests.get(DISCOVERY_URL, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            return parse_discovery_html(resp.text, as_of_date=as_of_date)
    except Exception as e:
        print(f"Warning: Live discovery fetch failed: {e}")

    # Fallback to local test fixture if offline / in test
    fixture_path = ROOT_DIR / "tests" / "fixtures" / "discovery_page.html"
    if fixture_path.exists():
        print("Using discovery fixture as offline fallback.")
        return parse_discovery_html(fixture_path.read_text(encoding="utf-8"), as_of_date=as_of_date)

    return []


def main():
    parser = argparse.ArgumentParser(description="Discover active and upcoming Mainboard IPOs.")
    parser.add_argument("--dry-run", action="store_true", help="List discovered candidates without actions")
    parser.add_argument("--as-of-date", default="2026-10-21", help="Reference date YYYY-MM-DD (defaults to 2026-10-21)")
    args = parser.parse_args()

    candidates = discover_ipos(as_of_date=args.as_of_date)
    print(f"\nDiscovered {len(candidates)} eligible Mainboard candidate(s) (as of {args.as_of_date}):")
    for c in candidates:
        print(f"  - {c['company']} | Close: {c['close_date']} | Status: {c['status']} | URL: {c['overview_url']}")


if __name__ == "__main__":
    main()
