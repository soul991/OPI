"""Data collection and evidence snapshotting module for upcoming IPOs."""

import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup

import hashlib
import requests
from bs4 import BeautifulSoup

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}


def slugify(text: str) -> str:
    """Normalize text into filename-safe lowercase slug."""
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def fetch_and_save_research_snapshot(
    url: str,
    run_id: str,
    field_name: str,
    timeout: int = 15,
    html_override: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Fetch URL, save snapshot under data/evidence/research/<run_id>/, and return (rel_path, hash, content, error)."""
    evidence_dir = ROOT_DIR / "data" / "evidence" / "research" / run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(field_name)
    filename = f"{slug}.html"
    target_path = evidence_dir / filename

    if html_override is not None:
        content = html_override
    else:
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            if resp.status_code != 200:
                return None, None, None, f"HTTP {resp.status_code}"
            content = resp.text
        except Exception as e:
            return None, None, None, str(e)

    target_path.write_text(content, encoding="utf-8", errors="replace")
    content_hash = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()
    rel_path = str(target_path.relative_to(ROOT_DIR)).replace("\\", "/")
    return rel_path, content_hash, content, None


def extract_clean_text_from_html(html_content: str) -> str:
    """Extract stripped clean plain text from HTML content, removing script/style tags."""
    soup = BeautifulSoup(html_content, "html.parser")
    for s in soup(["script", "style", "noscript", "meta"]):
        s.decompose()
    return " ".join(soup.get_text(separator=" ").split())


def verify_value_in_html(
    value: Any,
    quote: Optional[str],
    html_content: str,
    tolerance: float = 0.05
) -> Tuple[bool, str]:
    """Verify that a proposed value or quote actually exists in the saved HTML text."""
    if html_content is None or str(html_content).strip() == "":
        return False, "Empty HTML content"
        
    plain_text = extract_clean_text_from_html(html_content)
    
    # Check verbatim quote if provided
    if quote and str(quote).strip():
        q_clean = " ".join(str(quote).split())
        if q_clean.lower() in plain_text.lower():
            return True, f"Verified via verbatim quote match: '{q_clean[:40]}...'"

    if value is None:
        return False, "Null value"

    # Float verification with tolerance
    if isinstance(value, float):
        # 1. Exact string search for standard representations
        val_str = f"{value:.2f}"
        if val_str in plain_text or f"{value:.1f}" in plain_text or str(value) in plain_text:
            return True, f"Exact numeric string match for {value}"
            
        # 2. Regex extract numbers and check tolerance
        tokens = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", plain_text)
        for t in tokens:
            try:
                num = float(t)
                if abs(num - value) <= tolerance:
                    return True, f"Numeric tolerance match: {num} ~= {value} (+/- {tolerance})"
            except ValueError:
                continue
        return False, f"Float {value} not found within +/- {tolerance} tolerance in text"

    # Integer verification
    if isinstance(value, int) and not isinstance(value, bool):
        val_str = str(value)
        # Check integer word boundary match in plain text
        if re.search(r"\b" + re.escape(val_str) + r"\b", plain_text):
            return True, f"Integer exact match for {value}"
        return False, f"Integer {value} not found in text"

    # String verification
    val_str = str(value).strip().lower()
    if val_str and val_str in plain_text.lower():
        return True, f"Substring match for '{value}'"

    return False, f"Value '{value}' not found in snapshot text"


def save_evidence_snapshot(
    content: str,
    category: str,
    listing_date: str,
    company: str,
    ext: str = "html"
) -> Path:
    """Save an evidence snapshot under data/evidence/<category>/<listing_date>_<slug>.<ext>."""
    evidence_dir = ROOT_DIR / "data" / "evidence" / category
    evidence_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(company)
    filename = f"{listing_date}_{slug}.{ext}"
    target_path = evidence_dir / filename
    target_path.write_text(content, encoding="utf-8", errors="replace")
    return target_path


def parse_chittorgarh_subscription(html_text: str) -> Dict[str, Optional[float]]:
    """Parse subscription rates (QIB, NII, Retail, Total) from Chittorgarh HTML."""
    soup = BeautifulSoup(html_text, "html.parser")
    subs = {"sub_qib": None, "sub_nii": None, "sub_retail": None, "sub_total": None}
    
    # Locate tables containing subscription details
    for table in soup.find_all("table"):
        text = table.get_text()
        if "QIB" in text or "Retail" in text or "Total" in text:
            for row in table.find_all("tr"):
                cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                if len(cells) >= 2:
                    label = cells[0].lower()
                    val_str = cells[-1].replace("x", "").replace(",", "").strip()
                    try:
                        val = float(val_str)
                        if "qualified institutional" in label or "qib" in label:
                            subs["sub_qib"] = val
                        elif "non-institutional" in label or "nii" in label or "hni" in label:
                            subs["sub_nii"] = val
                        elif "retail" in label:
                            subs["sub_retail"] = val
                        elif "total" in label:
                            subs["sub_total"] = val
                    except ValueError:
                        continue
    return subs


def parse_investorgain_gmp(html_text: str) -> Dict[str, Optional[float]]:
    """Parse GMP in INR and GMP percentage from InvestorGain HTML."""
    soup = BeautifulSoup(html_text, "html.parser")
    res = {"gmp_inr": None, "gmp_pct": None}
    
    # Search for GMP badges, tables, or text
    for text_elem in soup.find_all(["td", "span", "div", "p"]):
        txt = text_elem.get_text(strip=True)
        m = re.search(r"GMP\s*[:₹\s]*(?:rs\.?|inr)?\s*([0-9.]+)", txt, re.I)
        if m and res["gmp_inr"] is None:
            try:
                res["gmp_inr"] = float(m.group(1))
            except ValueError:
                pass
        m_pct = re.search(r"([0-9.]+)%", txt)
        if m_pct and "gmp" in txt.lower() and res["gmp_pct"] is None:
            try:
                res["gmp_pct"] = float(m_pct.group(1))
            except ValueError:
                pass
    return res


def collect_ipo_data(
    company: str,
    listing_date: str,
    subscription_url: Optional[str] = None,
    gmp_url: Optional[str] = None,
    html_fixture_sub: Optional[str] = None,
    html_fixture_gmp: Optional[str] = None,
) -> Dict[str, Any]:
    """Collect structured IPO details, saving page snapshots and returning verified attributes."""
    today_iso = date.today().isoformat()
    result: Dict[str, Any] = {
        "company": company,
        "listing_date": listing_date,
        "collected_at": datetime.now().isoformat(),
        "subscription": {},
        "gmp": {},
        "snapshots": {},
        "source_urls": [],
    }

    # 1. Subscription collection
    if html_fixture_sub:
        sub_html = html_fixture_sub
        sub_path = save_evidence_snapshot(sub_html, "subscription", listing_date, company)
        result["snapshots"]["subscription"] = str(sub_path.relative_to(ROOT_DIR)).replace("\\", "/")
        result["subscription"] = parse_chittorgarh_subscription(sub_html)
    elif subscription_url:
        result["source_urls"].append(subscription_url)
        try:
            resp = requests.get(subscription_url, headers=DEFAULT_HEADERS, timeout=12)
            if resp.status_code == 200:
                sub_path = save_evidence_snapshot(resp.text, "subscription", listing_date, company)
                result["snapshots"]["subscription"] = str(sub_path.relative_to(ROOT_DIR)).replace("\\", "/")
                result["subscription"] = parse_chittorgarh_subscription(resp.text)
            else:
                result["subscription_error"] = f"HTTP {resp.status_code}"
        except Exception as e:
            result["subscription_error"] = str(e)

    # 2. GMP collection
    if html_fixture_gmp:
        gmp_html = html_fixture_gmp
        gmp_path = save_evidence_snapshot(gmp_html, "gmp", listing_date, company)
        result["snapshots"]["gmp"] = str(gmp_path.relative_to(ROOT_DIR)).replace("\\", "/")
        result["gmp"] = parse_investorgain_gmp(gmp_html)
    elif gmp_url:
        result["source_urls"].append(gmp_url)
        try:
            resp = requests.get(gmp_url, headers=DEFAULT_HEADERS, timeout=12)
            if resp.status_code == 200:
                gmp_path = save_evidence_snapshot(resp.text, "gmp", listing_date, company)
                result["snapshots"]["gmp"] = str(gmp_path.relative_to(ROOT_DIR)).replace("\\", "/")
                result["gmp"] = parse_investorgain_gmp(resp.text)
            else:
                result["gmp_error"] = f"HTTP {resp.status_code}"
        except Exception as e:
            result["gmp_error"] = str(e)

    return result
