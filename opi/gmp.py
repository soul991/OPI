"""Deterministic GMP page discovery and parsing for IPO candidates (D-081).

Discovers InvestorGain GMP URLs deterministically by exact normalized company name
matching against the live IPO GMP report page or Chittorgarh cross-links, with
grounded agent fallback.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Dict
import requests
from bs4 import BeautifulSoup

ROOT_DIR = Path(__file__).resolve().parents[1]
INVESTORGAIN_LIST_URL = "https://www.investorgain.com/report/live-ipo-gmp/331/"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

_LIST_HTML_CACHE: Optional[str] = None


def normalize_gmp_company_name(name: str) -> str:
    """Normalize company name for strict exact matching between trackers."""
    s = str(name).lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"['\"’`]", "", s)
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(limited|ltd|pvt|private|india|co|corp|corporation)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_gmp_list_page(html_text: str) -> Dict[str, str]:
    """Parse InvestorGain live GMP report table into normalized_name -> gmp_url mapping."""
    soup = BeautifulSoup(html_text, "html.parser")
    mapping: Dict[str, str] = {}

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/gmp/" in href:
            text = a.get_text(strip=True)
            if not text:
                continue
            norm = normalize_gmp_company_name(text)
            if norm and norm not in mapping:
                if href.startswith("/"):
                    mapping[norm] = f"https://www.investorgain.com{href}"
                else:
                    mapping[norm] = href
    return mapping


def fetch_live_gmp_list(allow_network: bool = True, timeout: int = 12) -> Optional[str]:
    """Fetch live GMP list HTML from InvestorGain or return cached version."""
    global _LIST_HTML_CACHE
    if _LIST_HTML_CACHE:
        return _LIST_HTML_CACHE
    if not allow_network:
        return None
    try:
        resp = requests.get(INVESTORGAIN_LIST_URL, headers=DEFAULT_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            _LIST_HTML_CACHE = resp.text
            return resp.text
    except Exception:
        pass
    return None


def extract_gmp_from_chittorgarh_html(html_text: str) -> Optional[str]:
    """Extract InvestorGain cross-link (e.g. /chr-gmp/...) from Chittorgarh HTML if present."""
    soup = BeautifulSoup(html_text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "investorgain.com/chr-gmp/" in href or "investorgain.com/gmp/" in href:
            return href
    return None


def discover_gmp_url(
    company: str,
    list_html: Optional[str] = None,
    allow_network: bool = True,
    chittorgarh_html: Optional[str] = None,
) -> Optional[str]:
    """Discover the exact GMP URL for a company deterministically.
    
    1. Check InvestorGain live list page for exact normalized company name match.
    2. Check Chittorgarh HTML for direct cross-link.
    3. Return None if not found (caller may invoke grounded agent fallback).
    """
    target_norm = normalize_gmp_company_name(company)
    if not target_norm:
        return None

    # Step 1: InvestorGain live list page match
    html = list_html if list_html is not None else fetch_live_gmp_list(allow_network=allow_network)
    if html:
        mapping = parse_gmp_list_page(html)
        if target_norm in mapping:
            return mapping[target_norm]

    # Step 2: Chittorgarh cross-link check
    if chittorgarh_html:
        cross_link = extract_gmp_from_chittorgarh_html(chittorgarh_html)
        if cross_link:
            return cross_link

    return None
