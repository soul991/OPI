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
import pandas as pd
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


def get_today_ist() -> str:
    """Return today's date in IST (YYYY-MM-DD)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")
    except Exception:
        return date.today().strftime("%Y-%m-%d")


def normalize_company_name(name: str) -> str:
    """Normalize company name ignoring legal/regional suffixes, punctuation, and extra spaces."""
    s = str(name).lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"['\"’`]", "", s)
    s = re.sub(r"[^a-z0-9&]+", " ", s)
    s = re.sub(r"\b(limited|ltd|pvt|private|india|co|corp|corporation)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_master_companies() -> dict[str, dict[str, Any]]:
    """Load normalized company lookup map from data/ipo_master.csv."""
    master_path = ROOT_DIR / "data" / "ipo_master.csv"
    lookup: dict[str, dict[str, Any]] = {}
    if master_path.exists():
        try:
            df = pd.read_csv(master_path)
            for _, row in df.iterrows():
                comp = str(row.get("company", ""))
                norm = normalize_company_name(comp)
                if norm:
                    lookup[norm] = {
                        "company": comp,
                        "listing_date": str(row.get("listing_date", "")),
                        "issue_price": str(row.get("issue_price", "")),
                        "listing_price": str(row.get("listing_price", "")),
                    }
        except Exception:
            pass
    return lookup


def load_logged_companies() -> dict[str, dict[str, Any]]:
    """Load normalized company lookup map from predictions/prediction_log.csv."""
    log_path = ROOT_DIR / "predictions" / "prediction_log.csv"
    lookup: dict[str, dict[str, Any]] = {}
    if log_path.exists():
        try:
            df = pd.read_csv(log_path)
            for _, row in df.iterrows():
                comp = str(row.get("company", ""))
                norm = normalize_company_name(comp)
                if norm:
                    lookup[norm] = {
                        "company": comp,
                        "listing_date": str(row.get("listing_date", "")),
                        "status": str(row.get("status", "")),
                    }
        except Exception:
            pass
    return lookup


def is_company_in_master(
    name: str,
    master_lookup: Optional[dict[str, dict[str, Any]]] = None,
) -> tuple[bool, Optional[dict[str, Any]]]:
    """Check if company exists in data/ipo_master.csv with flexible normalized matching."""
    if master_lookup is None:
        master_lookup = load_master_companies()
    n = normalize_company_name(name)
    if not n:
        return False, None
    if n in master_lookup:
        return True, master_lookup[n]
    for norm_m, info in master_lookup.items():
        if len(n) >= 5 and (n == norm_m or n.startswith(norm_m) or norm_m.startswith(n)):
            return True, info
    return False, None


def parse_listing_date_from_overview_html(html_text: str) -> Optional[date]:
    """Parse listing date from Chittorgarh overview page HTML."""
    soup = BeautifulSoup(html_text, "html.parser")
    for tr in soup.find_all("tr"):
        row_text = tr.get_text(" | ", strip=True)
        if re.search(r"\b(listing\s+date|listed\s+on)\b", row_text, re.I):
            m = re.search(r"(?:[A-Za-z]+,\s*)?([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})", row_text)
            if m:
                mon, day, yr = m.groups()
                try:
                    return datetime.strptime(f"{day} {mon[:3]} {yr}", "%d %b %Y").date()
                except Exception:
                    pass
            m2 = re.search(r"(\d{4})-(\d{2})-(\d{2})", row_text)
            if m2:
                try:
                    return datetime.strptime(m2.group(0), "%Y-%m-%d").date()
                except Exception:
                    pass
    return None


def confirm_listing_date_from_overview(overview_url: str, timeout: int = 5) -> Optional[date]:
    """Try to extract listing date from overview page HTML or local evidence snapshot."""
    if not overview_url:
        return None
    # Check if a snapshot exists in data/evidence/research
    research_dir = ROOT_DIR / "data" / "evidence" / "research"
    if research_dir.exists():
        m_slug = re.search(r"/ipo/([^/]+)/", overview_url.lower())
        slug = m_slug.group(1).replace("-ipo", "") if m_slug else re.sub(r"[^a-z0-9]+", "-", overview_url.lower()).strip("-")
        for snap in research_dir.glob("*.html"):
            if slug in snap.name:
                try:
                    # Check filename prefix YYYY-MM-DD
                    m_file = re.match(r"^(\d{4}-\d{2}-\d{2})_", snap.name)
                    if m_file:
                        return datetime.strptime(m_file.group(1), "%Y-%m-%d").date()
                    txt = snap.read_text(encoding="utf-8")
                    parsed = parse_listing_date_from_overview_html(txt)
                    if parsed:
                        return parsed
                except Exception:
                    pass
    # Live fetch attempt if URL is valid
    if overview_url.startswith("http"):
        try:
            resp = requests.get(overview_url, headers=DEFAULT_HEADERS, timeout=timeout)
            if resp.status_code == 200:
                return parse_listing_date_from_overview_html(resp.text)
        except Exception:
            pass
    return None


def parse_discovery_html(
    html_text: str,
    as_of_date: Optional[str] = None,
    master_lookup: Optional[dict[str, dict[str, Any]]] = None,
    confirm_overview: bool = True,
) -> List[Dict[str, Any]]:
    """Parse HTML containing IPO listings table and extract eligible Mainboard candidates."""
    if master_lookup is None:
        master_lookup = load_master_companies()
    logged_lookup = load_logged_companies()

    ref_date_str = as_of_date or get_today_ist()
    ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d").date()
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

        in_master, m_info = is_company_in_master(company, master_lookup)
        if in_master and not l_date and m_info and m_info.get("listing_date"):
            try:
                l_date = datetime.strptime(m_info["listing_date"][:10], "%Y-%m-%d").date()
            except Exception:
                pass

        # Check logged companies if not in master
        norm_c = normalize_company_name(company)
        if not l_date and norm_c in logged_lookup and logged_lookup[norm_c].get("listing_date"):
            try:
                l_date = datetime.strptime(logged_lookup[norm_c]["listing_date"][:10], "%Y-%m-%d").date()
            except Exception:
                pass

        if ref_date < o_date:
            status = "UPCOMING"
        elif ref_date <= c_date:
            status = "BIDDING_OPEN"
        elif in_master or (l_date and ref_date >= l_date):
            status = "LISTED"
        elif l_date and ref_date < l_date:
            status = "CLOSED_UNLISTED"
        else:
            conf_l_date = confirm_listing_date_from_overview(full_url) if confirm_overview else None
            if conf_l_date:
                l_date = conf_l_date
                if ref_date >= conf_l_date:
                    status = "LISTED"
                else:
                    status = "CLOSED_UNLISTED"
            else:
                status = "UNKNOWN_LISTING_DATE"

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

            in_master, m_info = is_company_in_master(comp, master_lookup)
            l_date_str = ""
            if in_master and m_info and m_info.get("listing_date"):
                l_date_str = m_info["listing_date"]

            norm_c = normalize_company_name(comp)
            if not l_date_str and norm_c in logged_lookup and logged_lookup[norm_c].get("listing_date"):
                l_date_str = logged_lookup[norm_c]["listing_date"]

            if ref_date < open_dt:
                status = "UPCOMING"
            elif is_open or (open_dt <= ref_date <= close_dt):
                status = "BIDDING_OPEN"
            elif in_master:
                status = "LISTED"
            elif l_date_str:
                try:
                    l_dt = datetime.strptime(l_date_str[:10], "%Y-%m-%d").date()
                    if ref_date >= l_dt:
                        status = "LISTED"
                    else:
                        status = "CLOSED_UNLISTED"
                except Exception:
                    status = "UNKNOWN_LISTING_DATE"
            else:
                conf_l_date = confirm_listing_date_from_overview(url) if confirm_overview else None
                if conf_l_date:
                    l_date_str = str(conf_l_date)
                    if ref_date >= conf_l_date:
                        status = "LISTED"
                    else:
                        status = "CLOSED_UNLISTED"
                else:
                    status = "UNKNOWN_LISTING_DATE"

            candidates.append({
                "company": comp,
                "open_date": str(open_dt),
                "close_date": str(close_dt),
                "listing_date": l_date_str,
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
    confirm_overview: bool = True,
) -> List[Dict[str, Any]]:
    """Discover Mainboard IPO candidates from provided HTML or live web."""
    if source_html is not None:
        return parse_discovery_html(source_html, as_of_date=as_of_date, confirm_overview=confirm_overview)

    # Try live fetch
    try:
        resp = requests.get(DISCOVERY_URL, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            return parse_discovery_html(resp.text, as_of_date=as_of_date, confirm_overview=confirm_overview)
    except Exception as e:
        print(f"Warning: Live discovery fetch failed: {e}")

    # Fallback to local test fixture if offline / in test
    fixture_path = ROOT_DIR / "tests" / "fixtures" / "discovery_page.html"
    if fixture_path.exists():
        print("Using discovery fixture as offline fallback.")
        return parse_discovery_html(
            fixture_path.read_text(encoding="utf-8"),
            as_of_date=as_of_date,
            confirm_overview=confirm_overview,
        )

    return []


def main():
    today_ist = get_today_ist()
    parser = argparse.ArgumentParser(description="Discover active and upcoming Mainboard IPOs.")
    parser.add_argument("--dry-run", action="store_true", help="List discovered candidates without actions")
    parser.add_argument(
        "--as-of-date",
        default=today_ist,
        help=f"Reference date YYYY-MM-DD (defaults to today in IST: {today_ist})",
    )
    args = parser.parse_args()

    candidates = discover_ipos(as_of_date=args.as_of_date)
    print(f"\nDiscovered {len(candidates)} eligible Mainboard candidate(s) (as of {args.as_of_date}):")
    for c in candidates:
        print(f"  - {c['company']} | Close: {c['close_date']} | Status: {c['status']} | URL: {c['overview_url']}")


if __name__ == "__main__":
    main()
