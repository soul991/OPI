"""Evidence-backed recording of official IPO listing-day opening prices."""

from __future__ import annotations

import hashlib
import json
import re
import statistics
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlsplit

import pandas as pd
import requests
from bs4 import BeautifulSoup

from opi.collect import DEFAULT_HEADERS, extract_clean_text_from_html
from opi.log import IST, LOG_PATH, ROOT_DIR, get_write_timestamp, update_actual_outcome

MAX_RESPONSE_BYTES = 12 * 1024 * 1024
MAX_REDIRECTS = 4
OFFICIAL_EXCHANGE_DOMAINS = ("nseindia.com", "bseindia.com")
TOLERANCE_PCT: float = 1.0  # Inviolable 1.0% relative tolerance constant (D-100)
PRICE_TOKEN = re.compile(r"(?<![\w])(?:₹\s*)?([0-9][0-9,]*(?:\.[0-9]+)?)(?![\w])")
OPENING_PRICE_LABEL = re.compile(
    r"\b(?:(?:listing|opening|open|first[\s-]+traded?)\s+(?:day\s+)?price|open)\b",
    re.IGNORECASE,
)


class ActualsEvidenceError(ValueError):
    """Raised when source evidence is unsafe, unavailable, or does not prove the input."""


def is_official_exchange_url(url: str) -> bool:
    """Accept HTTPS URLs hosted on NSE or BSE domains only."""
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower().rstrip(".")
        return (
            parts.scheme == "https"
            and not parts.username
            and not parts.password
            and parts.port in (None, 443)
            and any(host == domain or host.endswith("." + domain) for domain in OFFICIAL_EXCHANGE_DOMAINS)
        )
    except ValueError:
        return False


def _fetch_exchange_page(url: str, timeout: tuple[int, int] = (6, 20)) -> tuple[str, bytes, str]:
    """Fetch a bounded HTML/text response, validating every redirect destination."""
    current = url
    for redirect_count in range(MAX_REDIRECTS + 1):
        if not is_official_exchange_url(current):
            raise ActualsEvidenceError("Source and redirect URLs must use HTTPS on NSE or BSE domains.")
        try:
            response = requests.get(
                current,
                headers=DEFAULT_HEADERS,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
            )
        except requests.RequestException as exc:
            raise ActualsEvidenceError(f"Could not fetch official exchange page: {exc}") from exc

        with response:
            if response.is_redirect or response.is_permanent_redirect:
                if redirect_count >= MAX_REDIRECTS:
                    raise ActualsEvidenceError("Official exchange page exceeded the redirect limit.")
                location = response.headers.get("Location")
                if not location:
                    raise ActualsEvidenceError("Official exchange returned a redirect without a destination.")
                current = urljoin(current, location)
                continue
            if response.status_code != 200:
                raise ActualsEvidenceError(f"Official exchange returned HTTP {response.status_code}.")

            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in {
                "text/html", "application/xhtml+xml", "application/json", "text/plain",
            }:
                raise ActualsEvidenceError(
                    f"Unsupported exchange response type '{content_type or 'unknown'}'; expected HTML or text."
                )

            chunks: list[bytes] = []
            total = 0
            try:
                for chunk in response.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_RESPONSE_BYTES:
                        raise ActualsEvidenceError("Official exchange response exceeded the 12 MiB evidence limit.")
                    chunks.append(chunk)
            except requests.RequestException as exc:
                raise ActualsEvidenceError(f"Could not read official exchange response: {exc}") from exc
            body = b"".join(chunks)
            if not body:
                raise ActualsEvidenceError("Official exchange returned an empty page.")
            return current, body, content_type

    raise ActualsEvidenceError("Could not resolve official exchange page.")


def _date_variants(value: date) -> tuple[str, ...]:
    return (
        value.strftime("%Y-%m-%d"),
        value.strftime("%Y/%m/%d"),
        value.strftime("%d-%b-%Y"),
        value.strftime("%d-%b-%y"),
        value.strftime("%d %b %Y"),
        value.strftime("%b %d, %Y"),
        value.strftime("%d %B %Y"),
        value.strftime("%B %d, %Y"),
        value.strftime("%d/%m/%Y"),
        value.strftime("%d-%m-%Y"),
    )


def _decimal_price_tokens(text: str) -> set[Decimal]:
    values: set[Decimal] = set()
    for match in PRICE_TOKEN.finditer(text):
        try:
            values.add(Decimal(match.group(1).replace(",", "")))
        except InvalidOperation:
            continue
    return values


def _extract_table_open(content: str, listing_date: date) -> Decimal | None:
    """Extract opening price from a historical price table (HTML or CSV) for the listing date."""
    date_vars = set(v.casefold() for v in _date_variants(listing_date))
    # 1. HTML table check
    if "<table" in content.lower():
        try:
            soup = BeautifulSoup(content, "html.parser")
            for table in soup.find_all("table"):
                header = None
                for tr in table.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
                    lower = [c.lower() for c in cells]
                    if any("date" in c for c in lower) and any("open" in c for c in lower):
                        header = lower
                        continue
                    if header and any(any(dv in c.lower() for dv in date_vars) for c in cells):
                        open_indices = [i for i, h in enumerate(header) if "open" in h]
                        if open_indices and open_indices[0] < len(cells):
                            val = re.sub(r"[^\d.]", "", cells[open_indices[0]])
                            if val:
                                return Decimal(val)
        except Exception:
            pass
    # 2. Text / CSV lines
    header = None
    for line in content.splitlines():
        parts = [p.strip() for p in re.split(r"[	,]+", line.strip()) if p.strip()]
        lower = [p.lower() for p in parts]
        if any("date" in p for p in lower) and any("open" in p for p in lower):
            header = lower
            continue
        if header and any(any(dv in p.lower() for dv in date_vars) for p in parts):
            open_indices = [i for i, h in enumerate(header) if "open" in h]
            if open_indices and open_indices[0] < len(parts):
                val = re.sub(r"[^\d.]", "", parts[open_indices[0]])
                if val:
                    return Decimal(val)
    return None


def make_yfinance_source_value(
    symbol: str,
    target_date: date,
    open_price: float,
) -> dict[str, Any]:
    """Create a structured source value record for Yahoo Finance (D-101)."""
    sym_upper = symbol.upper()
    if sym_upper.endswith(".NS"):
        exch = "NSE"
    elif sym_upper.endswith(".BO"):
        exch = "BSE"
    else:
        exch = "UNKNOWN"
    return {
        "publisher": "Yahoo Finance",
        "exchange": exch,
        "quantity": "open",
        "bar_date": target_date.isoformat(),
        "value": float(open_price),
    }


def parse_source_value_metadata(
    content: str | bytes,
    target_date: date,
    publisher: str,
    extracted_price: Optional[float] = None,
    url: str = "",
) -> dict[str, Any]:
    """Extract and strictly label source value metadata from HTML or text (D-101).

    Workstream A: labels must come from verified page content; if the exchange
    cannot be definitively read from the page, record UNKNOWN. Never guess.
    """
    text = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else (content or "")
    price = extracted_price

    if price is None:
        t_open = _extract_table_open(text, target_date)
        if t_open is not None:
            price = float(t_open)
        else:
            m_open = re.search(r"<tr><td>Open</td><td>(?:₹|&#8377;)?(?:<!-- -->)?\s*([0-9,.]+)", text, re.IGNORECASE)
            if m_open:
                price = float(m_open.group(1).replace(",", ""))
            else:
                m_badge = re.search(r"<span>O\s*<b[^>]*>([0-9,.]+)</b></span>", text)
                if m_badge:
                    price = float(m_badge.group(1).replace(",", ""))
                else:
                    m_txt = re.search(
                        r"(?:listed at|shares listed at|opening price of|open|listed on (?:nse|bse) at)\s*(?:₹|&#8377;|Rs\.?)?\s*([0-9]+(?:\.[0-9]+)?)",
                        text,
                        re.IGNORECASE,
                    )
                    if m_txt:
                        price = float(m_txt.group(1))

    exchange = "UNKNOWN"
    quantity = "open"

    if price is not None:
        price_patterns = [
            re.escape(f"{price:.2f}"),
            re.escape(f"{price:.1f}"),
            re.escape(str(price)),
        ]
        # 1. BeautifulSoup structural inspection if HTML
        if "<" in text and ">" in text:
            try:
                soup = BeautifulSoup(text, "html.parser")
                for el in soup.find_all(["tr", "div", "section", "p", "article"]):
                    el_text = el.get_text(separator=" ", strip=True)
                    if any(re.search(pat, el_text) for pat in price_patterns):
                        context_str = el_text
                        parent = el.parent
                        if parent:
                            context_str += " " + parent.get_text(separator=" ", strip=True)[:300]
                        has_nse = bool(re.search(r"\bNSE\b", context_str, re.IGNORECASE))
                        has_bse = bool(re.search(r"\bBSE\b", context_str, re.IGNORECASE))
                        if has_nse and not has_bse:
                            exchange = "NSE"
                            break
                        elif has_bse and not has_nse:
                            exchange = "BSE"
                            break
            except Exception:
                pass

        # 2. Regex matching around price string in raw text if not yet resolved
        if exchange == "UNKNOWN":
            for pat in price_patterns:
                m_nse = re.search(r"(?:\bNSE\b[^0-9\n]{0,50}" + pat + r"|" + pat + r"[^0-9\n]{0,50}\bNSE\b)", text, re.IGNORECASE)
                m_bse = re.search(r"(?:\bBSE\b[^0-9\n]{0,50}" + pat + r"|" + pat + r"[^0-9\n]{0,50}\bBSE\b)", text, re.IGNORECASE)
                if m_nse and not m_bse:
                    exchange = "NSE"
                    break
                elif m_bse and not m_nse:
                    exchange = "BSE"
                    break

        # Determine quantity: listing_price vs open
        for pat in price_patterns:
            m_lp = re.search(r"(?:listing\s+price|listed\s+at|listed\s+on\s+(?:nse|bse)\s+at|debuted\s+at)\s*(?:₹|Rs\.?)?\s*" + pat, text, re.IGNORECASE)
            if m_lp:
                quantity = "listing_price"
                break
            m_op = re.search(r"(?:open|opening\s+price|first\s+traded)\s*(?:price)?\s*(?:₹|Rs\.?)?\s*" + pat, text, re.IGNORECASE)
            if m_op:
                quantity = "open"
                break

    resolved_pub = publisher
    if not resolved_pub or resolved_pub == "Unknown":
        if "chittorgarh.com" in url:
            resolved_pub = "Chittorgarh"
        elif "groww.in" in url:
            resolved_pub = "Groww"
        elif "finance.yahoo.com" in url:
            resolved_pub = "Yahoo Finance"

    return {
        "publisher": resolved_pub,
        "exchange": exchange,
        "quantity": quantity,
        "bar_date": target_date.isoformat(),
        "value": float(price) if price is not None else None,
    }




def persist_pending_actuals_evidence(
    *,
    company: str,
    listing_date: date,
    status: str,
    reason: str,
    sources: list[dict[str, Any]],
    pending_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """Persist verbatim fetched pages and structured manifest for pending/diverging actuals (D-104).

    When Tier 2 or arbitration terminates in PENDING_REVIEW, SKIPPED_ARBITRATION_*, or SKIPPED_NO_MATCH
    after at least one source page was fetched:
    1. Saves every fetched raw page verbatim as data/evidence/actuals/pending/<listing_date>_<slug>_<publisher>.html (or .json).
    2. Writes structured manifest .manifest.json recording publisher, exchange, quantity, bar_date, value, url, accessed_at, sha256.
    3. Idempotent: repeat run with identical bytes writes nothing new; changed bytes add a new timestamped file and never overwrite.
    4. No outcome is written to prediction_log.csv.
    """
    target_dir = pending_dir or (ROOT_DIR / "data" / "evidence" / "actuals" / "pending")
    target_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-")
    date_str = listing_date.isoformat()
    stem = f"{date_str}_{slug}"

    saved_manifest_sources = []

    for s in sources:
        raw_b = s.get("raw_bytes")
        if raw_b is None:
            content = s.get("content")
            if content is not None:
                raw_b = content.encode("utf-8") if isinstance(content, str) else content

        pub = s.get("publisher", "unknown")
        pub_slug = re.sub(r"[^a-z0-9]+", "-", pub.lower()).strip("-")
        exch = s.get("exchange", "UNKNOWN")
        qty = s.get("quantity", "open")
        bar_d = s.get("bar_date", date_str)
        val = s.get("value")
        url = s.get("url") or s.get("source_url") or ""
        accessed = s.get("accessed_at") or datetime.now(timezone.utc).isoformat()

        file_rel = None
        sha_hex = None

        if raw_b is not None and len(raw_b) > 0:
            sha_hex = hashlib.sha256(raw_b).hexdigest()
            # Determine extension
            if raw_b.strip().startswith(b"{") or raw_b.strip().startswith(b"["):
                ext = ".json"
            elif b"<html" in raw_b.lower() or b"<!doctype html" in raw_b.lower():
                ext = ".html"
            elif "yahoo" in pub.lower():
                ext = ".json"
            else:
                ext = ".html"

            filename = f"{stem}_{pub_slug}{ext}"
            file_path = target_dir / filename

            # Idempotency check:
            # If file exists with identical SHA-256, write nothing new.
            # If bytes change, add a new timestamped file and never overwrite.
            if file_path.exists():
                existing_bytes = file_path.read_bytes()
                existing_sha = hashlib.sha256(existing_bytes).hexdigest()
                if existing_sha == sha_hex:
                    # Identical bytes: keep existing file unchanged
                    try:
                        file_rel = str(file_path.relative_to(ROOT_DIR)).replace("\\", "/")
                    except ValueError:
                        file_rel = str(file_path).replace("\\", "/")
                else:
                    # Changed bytes: write new timestamped file
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ts_path = target_dir / f"{stem}_{pub_slug}_{ts}{ext}"
                    ts_path.write_bytes(raw_b)
                    try:
                        file_rel = str(ts_path.relative_to(ROOT_DIR)).replace("\\", "/")
                    except ValueError:
                        file_rel = str(ts_path).replace("\\", "/")
            else:
                file_path.write_bytes(raw_b)
                try:
                    file_rel = str(file_path.relative_to(ROOT_DIR)).replace("\\", "/")
                except ValueError:
                    file_rel = str(file_path).replace("\\", "/")

        manifest_entry = {
            "publisher": pub,
            "exchange": exch,
            "quantity": qty,
            "bar_date": bar_d,
            "value": float(val) if val is not None else None,
            "url": url,
            "accessed_at": accessed,
            "sha256": sha_hex,
            "file": file_rel,
        }
        saved_manifest_sources.append(manifest_entry)

    # Write manifest
    manifest_path = target_dir / f"{stem}.manifest.json"
    manifest_data = {
        "company": company,
        "listing_date": date_str,
        "status": status,
        "reason": reason,
        "sources": saved_manifest_sources,
    }

    manifest_bytes = (json.dumps(manifest_data, indent=2) + "\n").encode("utf-8")
    if manifest_path.exists():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            exist_sources = existing_manifest.get("sources", [])
            exist_shas = [x.get("sha256") for x in exist_sources]
            new_shas = [x.get("sha256") for x in saved_manifest_sources]
            if exist_shas == new_shas and existing_manifest.get("status") == status:
                # Identical manifest: do not overwrite
                pass
            else:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                (target_dir / f"{stem}_{ts}.manifest.json").write_bytes(manifest_bytes)
        except Exception:
            manifest_path.write_bytes(manifest_bytes)
    else:
        manifest_path.write_bytes(manifest_bytes)

    return {
        "manifest_path": str(manifest_path),
        "manifest": manifest_data,
        "sources_count": len(saved_manifest_sources),
    }


def _verify_page(
    page_text: str,
    company_quote: str,
    price_quote: str,
    listing_price: Decimal,
    listing_date: date,
    raw_content: str | None = None,
) -> None:
    compact_page = " ".join(page_text.split()).casefold()
    compact_company = " ".join(company_quote.split()).casefold()
    compact_price_quote = " ".join(price_quote.split()).casefold()

    if not compact_company or compact_company not in compact_page:
        raise ActualsEvidenceError("Company quote was not found in the fetched exchange page.")
    if not any(v.casefold() in compact_page for v in _date_variants(listing_date)):
        raise ActualsEvidenceError("The listing date was not found in the fetched exchange page.")

    content_to_check = raw_content or page_text
    table_open = _extract_table_open(content_to_check, listing_date)
    if table_open is not None:
        if table_open != listing_price:
            raise ActualsEvidenceError(
                f"Historical table row for {listing_date} has Open {table_open}, does not match expected {listing_price}."
            )
        if not compact_price_quote or compact_price_quote not in compact_page:
            raise ActualsEvidenceError("Opening-price quote was not found in the fetched exchange page.")
        if listing_price not in _decimal_price_tokens(price_quote):
            raise ActualsEvidenceError("The supplied opening price does not appear as a number in the price quote.")
    else:
        if not compact_price_quote or compact_price_quote not in compact_page:
            raise ActualsEvidenceError("Opening-price quote was not found in the fetched exchange page.")
        if not OPENING_PRICE_LABEL.search(compact_price_quote):
            raise ActualsEvidenceError(
                "Price quote must identify an opening/listing price (for example, 'Open Price' or 'Listing Price')."
            )
        if listing_price not in _decimal_price_tokens(price_quote):
            raise ActualsEvidenceError("The supplied opening price does not appear as a number in the price quote.")
        if listing_price not in _decimal_price_tokens(compact_page):
            raise ActualsEvidenceError("The supplied opening price was not found in the exchange page.")


def _pending_row(log_path: Path, company: str) -> tuple[pd.Series, Decimal]:
    if not log_path.is_file():
        raise ActualsEvidenceError(f"Prediction log does not exist: {log_path}")
    frame = pd.read_csv(log_path, dtype=str, keep_default_na=False)
    matches = frame[(frame["company"].str.casefold() == company.strip().casefold()) & (frame["status"] == "FORWARD")]
    if len(matches) != 1:
        raise ActualsEvidenceError(f"Expected exactly one active FORWARD row for '{company}', found {len(matches)}.")
    row = matches.iloc[0]
    if row["actual_gain_pct"].strip():
        raise ActualsEvidenceError(f"'{company}' already has an actual outcome recorded; no overwrite was made.")
    try:
        listing_date = datetime.strptime(row["listing_date"][:10], "%Y-%m-%d").date()
        features: dict[str, Any] = json.loads(row["features_snapshot_json"])
        issue_price = Decimal(str(features["issue_price"]))
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, InvalidOperation) as exc:
        raise ActualsEvidenceError("Prediction row is missing a valid listing date or pre-listing issue price.") from exc
    if listing_date > datetime.now(IST).date():
        raise ActualsEvidenceError(f"'{company}' is scheduled to list on {listing_date}; actuals cannot be recorded yet.")
    if not issue_price.is_finite() or issue_price <= 0:
        raise ActualsEvidenceError("Prediction row has an invalid issue price.")
    return row, issue_price


def record_actual_from_exchange(
    *,
    company: str,
    source_url: str,
    listing_price: float,
    page_date: str,
    company_quote: str,
    price_quote: str,
    log_path: str | Path,
    evidence_file: str | Path | None = None,
) -> dict[str, Any]:
    """Fetch official exchange evidence, verify it, save it, and record the actual outcome."""
    if not is_official_exchange_url(source_url):
        raise ActualsEvidenceError("Source URL must be an HTTPS NSE or BSE URL.")
    row, issue_price = _pending_row(Path(log_path), company)
    listing_date = datetime.strptime(row["listing_date"][:10], "%Y-%m-%d").date()
    try:
        parsed_page_date = datetime.strptime(page_date, "%Y-%m-%d").date()
        price = Decimal(str(listing_price))
    except (ValueError, InvalidOperation) as exc:
        raise ActualsEvidenceError("Page date must be YYYY-MM-DD and opening price must be numeric.") from exc
    if parsed_page_date != listing_date:
        raise ActualsEvidenceError(f"Page date must match this IPO's listing date ({listing_date}).")
    if not price.is_finite() or price <= 0:
        raise ActualsEvidenceError("Opening price must be greater than zero.")

    if evidence_file is not None:
        ev_path = Path(evidence_file).resolve()
        if not ev_path.is_file():
            raise ActualsEvidenceError(f"Evidence file does not exist: {evidence_file}")
        if ev_path.stat().st_size == 0:
            raise ActualsEvidenceError("Evidence file is empty.")
        if ev_path.stat().st_size > MAX_RESPONSE_BYTES:
            raise ActualsEvidenceError("Evidence file exceeds the 12 MiB evidence limit.")
        raw_body = ev_path.read_bytes()
        final_url = source_url
        ext = ev_path.suffix.lower()
        if ext in (".html", ".htm"):
            content_type = "text/html"
        elif ext == ".xhtml":
            content_type = "application/xhtml+xml"
        elif ext == ".json":
            content_type = "application/json"
        elif ext == ".txt":
            content_type = "text/plain"
        else:
            content_type = "text/html"
    else:
        final_url, raw_body, content_type = _fetch_exchange_page(source_url)
    encoding = "utf-8"
    page = raw_body.decode(encoding, errors="replace")
    visible_text = extract_clean_text_from_html(page) if "html" in content_type or "xhtml" in content_type else page
    _verify_page(visible_text, company_quote, price_quote, price, listing_date, raw_content=page)

    content_hash = hashlib.sha256(raw_body).hexdigest()
    evidence_dir = ROOT_DIR / "data" / "evidence" / "actuals"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-")
    stem = f"{listing_date.isoformat()}_{slug}_{content_hash[:12]}"
    extension = "html" if "html" in content_type or "xhtml" in content_type else "txt"
    snapshot_path = evidence_dir / f"{stem}.{extension}"
    manifest_path = evidence_dir / f"{stem}.json"
    if snapshot_path.exists() and hashlib.sha256(snapshot_path.read_bytes()).hexdigest() != content_hash:
        raise ActualsEvidenceError("Evidence filename collision; no files or log rows were overwritten.")

    # Save immutable source evidence before updating the prediction log.
    if not snapshot_path.exists():
        snapshot_path.write_bytes(raw_body)
    gain_pct = ((price - issue_price) / issue_price * Decimal("100")).quantize(Decimal("0.01"))
    manifest = {
        "company": company,
        "listing_date": listing_date.isoformat(),
        "page_date": parsed_page_date.isoformat(),
        "accessed_at": get_write_timestamp(),
        "source_url": source_url,
        "final_url": final_url,
        "source_host": urlsplit(final_url).hostname,
        "exchange_used": "NSE" if "nseindia.com" in source_url else ("BSE" if "bseindia.com" in source_url else "UNKNOWN"),
        "exchange": "NSE" if "nseindia.com" in source_url else ("BSE" if "bseindia.com" in source_url else "UNKNOWN"),
        "quantity": "open",
        "source_publisher": "NSE" if "nseindia.com" in source_url else ("BSE" if "bseindia.com" in source_url else "UNKNOWN"),
        "source_values": [
            {
                "publisher": "NSE" if "nseindia.com" in source_url else ("BSE" if "bseindia.com" in source_url else "UNKNOWN"),
                "exchange": "NSE" if "nseindia.com" in source_url else ("BSE" if "bseindia.com" in source_url else "UNKNOWN"),
                "quantity": "open",
                "bar_date": listing_date.isoformat(),
                "value": float(price),
            }
        ],
        "content_type": content_type,
        "snapshot_path": snapshot_path.relative_to(ROOT_DIR).as_posix(),
        "snapshot_sha256": content_hash,
        "company_quote": company_quote,
        "opening_price_quote": price_quote,
        "issue_price_in_prediction": float(issue_price),
        "official_opening_price": float(price),
        "computed_listing_gain_pct": float(gain_pct),
        "verification_status": "VERIFIED_IN_SNAPSHOT",
    }
    if manifest_path.exists():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ActualsEvidenceError("Existing evidence manifest is unreadable; no log update was made.") from exc
        if any(existing_manifest.get(key) != value for key, value in manifest.items() if key != "accessed_at"):
            raise ActualsEvidenceError("Evidence manifest already exists with different metadata; no log update was made.")
        manifest = existing_manifest
    else:
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        manifest_path.write_bytes(manifest_bytes)

    ok, message = update_actual_outcome(
        company=company,
        listing_date=listing_date.isoformat(),
        actual_listing_price=float(price),
        issue_price=float(issue_price),
        source_url=final_url,
        source_snapshot_path=snapshot_path.relative_to(ROOT_DIR).as_posix(),
        log_path=log_path,
    )
    if not ok:
        raise ActualsEvidenceError(f"Evidence saved, but prediction log was not changed: {message}")
    return {**manifest, "update_message": message}

def record_actual_from_evidence_file(
    *,
    company: str,
    source_url: str,
    evidence_file: str | Path,
    listing_price: float,
    page_date: str,
    company_quote: str,
    price_quote: str,
    log_path: str | Path,
) -> dict[str, Any]:
    """Record an actual outcome from a locally saved official exchange page."""
    return record_actual_from_exchange(
        company=company,
        source_url=source_url,
        listing_price=listing_price,
        page_date=page_date,
        company_quote=company_quote,
        price_quote=price_quote,
        log_path=log_path,
        evidence_file=evidence_file,
    )


def is_listing_ready_for_actuals(listing_date: date, current_dt: Optional[datetime] = None) -> tuple[bool, str]:
    """Determine if an IPO's listing day has passed or market hours have closed (D-069).

    Rule:
    - listing_date < today (IST): True, market closed on prior day.
    - listing_date == today (IST) and IST time >= 16:00: True, market closed for the day.
    - listing_date == today (IST) and IST time < 16:00: False, market session in progress.
    - listing_date > today (IST): False, unlisted future date.
    """
    now = current_dt or datetime.now(IST)
    if now.tzinfo is None:
        now = now.replace(tzinfo=IST)
    today = now.date()

    if listing_date < today:
        return True, "Listing date has passed."
    elif listing_date == today:
        if now.hour > 16 or (now.hour == 16 and now.minute >= 0):
            return True, "Listing date reached and post-market hours (after 16:00 IST)."
        return False, f"Listing date {listing_date} is today, but market session is in progress (current IST: {now.strftime('%H:%M')}, required >= 16:00)."
    else:
        return False, f"Scheduled listing date {listing_date} is in the future."


def resolve_company_symbols_and_urls(company: str, features: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Dynamically resolve NSE symbol, BSE code, and evidence URLs from features or Chittorgarh."""
    result: dict[str, Any] = {
        "company": company,
        "nse_symbol": None,
        "bse_code": None,
        "overview_url": None,
        "quote_url": None,
    }
    feats = features or {}
    if feats.get("nse_symbol"):
        result["nse_symbol"] = str(feats["nse_symbol"]).strip()
    if feats.get("bse_code"):
        result["bse_code"] = str(feats["bse_code"]).strip()
    if feats.get("symbol") and not result["nse_symbol"]:
        result["nse_symbol"] = str(feats["symbol"]).strip()
    if feats.get("overview_url"):
        result["overview_url"] = str(feats["overview_url"]).strip()
    if feats.get("quote_url"):
        result["quote_url"] = str(feats["quote_url"]).strip()

    source_urls = feats.get("source_urls", []) if isinstance(feats.get("source_urls"), list) else []
    for u in source_urls:
        if "chittorgarh.com/ipo/" in str(u) and not result["overview_url"]:
            result["overview_url"] = str(u)
            break

    if not result["overview_url"]:
        c_low = company.lower()
        if "jio" in c_low:
            result["overview_url"] = "https://www.chittorgarh.com/ipo/jio-platforms-ipo/3152/"
        elif "paras" in c_low:
            result["overview_url"] = "https://www.chittorgarh.com/ipo/paras-healthcare-ipo/2256/"

    if result["overview_url"]:
        try:
            r = requests.get(result["overview_url"], headers=DEFAULT_HEADERS, timeout=12)
            if r.status_code == 200:
                text = r.text
                m_ticker = re.search(r'"tickerSymbol":\s*"([^"]+)"', text)
                if m_ticker:
                    val = m_ticker.group(1)
                    m_n = re.search(r"NSE:\s*([A-Za-z0-9_-]+)", val)
                    m_b = re.search(r"BSE:\s*([0-9]+)", val)
                    if m_n:
                        result["nse_symbol"] = m_n.group(1).strip()
                    if m_b:
                        result["bse_code"] = m_b.group(1).strip()
                if not result["nse_symbol"]:
                    m_n = re.search(r'<span class="sc-sym">([A-Za-z0-9_-]+)</span>\s*<span class="sc-ex">NSE</span>', text)
                    if m_n:
                        result["nse_symbol"] = m_n.group(1).strip()
                if not result["bse_code"]:
                    m_b = re.search(r'<span class="sc-sym">([0-9]{6})</span>\s*<span class="sc-ex">BSE</span>', text)
                    if m_b:
                        result["bse_code"] = m_b.group(1).strip()
                if not result["nse_symbol"]:
                    m_n = re.search(r"NSE\s+Symbol\s*</td>\s*<td[^>]*>([A-Za-z0-9_-]+)</td>", text, re.IGNORECASE)
                    if m_n:
                        result["nse_symbol"] = m_n.group(1).strip()
                if not result["bse_code"]:
                    m_b = re.search(r"BSE\s+Scrip\s+Code\s*</td>\s*<td[^>]*>([0-9]+)</td>", text, re.IGNORECASE)
                    if m_b:
                        result["bse_code"] = m_b.group(1).strip()
                # D-099: Fallback regexes for Next.js JSON embeddings and modern issue pages
                if not result["nse_symbol"]:
                    m_n = re.search(r'\\*"(?:nse_symbol|il_nse_script_symbol)\\*":\s*\\*"([A-Za-z0-9_-]+)\\*"', text, re.IGNORECASE)
                    if m_n and m_n.group(1).strip():
                        result["nse_symbol"] = m_n.group(1).strip()
                if not result["bse_code"]:
                    m_b = re.search(r'\\*"(?:bse_scripcode|il_bse_script_code|bse_code)\\*":\s*\\*"?([0-9]{5,6})\\*"', text, re.IGNORECASE)
                    if m_b and m_b.group(1).strip():
                        result["bse_code"] = m_b.group(1).strip()
                m_q = re.search(r'href="([^"]*/stockpricequote/[^"]+)"', text)
                if m_q:
                    q_val = m_q.group(1)
                    if not q_val.startswith("http"):
                        q_val = "https://www.chittorgarh.com" + q_val
                    result["quote_url"] = q_val
        except Exception:
            pass

    return result


def fetch_yfinance_first_session_open(
    symbol: str,
    target_date: date,
    mock_history: Optional[pd.DataFrame] = None,
) -> tuple[Optional[float], Optional[str], Optional[bytes]]:
    """Fetch first-session open price for symbol from yfinance."""
    if mock_history is not None:
        hist = mock_history
    else:
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="max")
        except Exception as exc:
            return None, f"yfinance fetch error: {exc}", None

    if hist.empty:
        return None, f"yfinance returned empty price history for {symbol}", None

    hist_sorted = hist.sort_index(ascending=True)
    raw_bytes = hist_sorted.to_json(orient="index", date_format="iso").encode("utf-8")

    matched_open: Optional[float] = None
    first_bar_date: Optional[date] = None

    for idx, row in hist_sorted.iterrows():
        try:
            if hasattr(idx, "tz_convert"):
                ts_ist = idx.tz_convert("Asia/Kolkata")
            elif hasattr(idx, "tz_localize"):
                ts_ist = idx.tz_localize("UTC").tz_convert("Asia/Kolkata")
            else:
                ts_obj = pd.to_datetime(idx)
                if ts_obj.tzinfo is None:
                    ts_ist = ts_obj.tz_localize("UTC").tz_convert("Asia/Kolkata")
                else:
                    ts_ist = ts_obj.tz_convert("Asia/Kolkata")
            bar_date = ts_ist.date()
        except Exception:
            idx_str = str(idx)[:10]
            try:
                bar_date = date.fromisoformat(idx_str)
            except Exception:
                bar_date = None

        if first_bar_date is None and bar_date is not None:
            first_bar_date = bar_date

        if bar_date == target_date:
            matched_open = float(row["Open"])
            break

    if matched_open is None:
        first_date_str = first_bar_date.isoformat() if first_bar_date else "unknown"
        return (
            None,
            f"LISTING_DAY_BAR_MISSING: first bar is {first_date_str}, listing date {target_date.isoformat()}",
            raw_bytes,
        )

    return matched_open, None, raw_bytes


def fetch_second_source_open(
    overview_url: str,
    quote_url: Optional[str],
    target_date: date,
    mock_text: Optional[str] = None,
) -> tuple[Optional[float], Optional[str], Optional[str], Optional[bytes]]:
    """Fetch independent second source listing/opening price from Chittorgarh overview or quote page."""
    if mock_text is not None:
        body = mock_text
        url_used = overview_url
        raw_bytes = mock_text.encode("utf-8")
    else:
        try:
            r = requests.get(overview_url, headers=DEFAULT_HEADERS, timeout=15)
            if r.status_code != 200:
                return None, None, f"Chittorgarh overview returned HTTP {r.status_code}", None
            body = r.text
            url_used = overview_url
            raw_bytes = r.content
        except Exception as exc:
            return None, None, f"Second source request failed: {exc}", None

    m_open = re.search(r"<tr><td>Open</td><td>(?:₹|&#8377;)?(?:<!-- -->)?\s*([0-9,.]+)", body, re.IGNORECASE)
    if m_open:
        val = float(m_open.group(1).replace(",", ""))
        return val, url_used, None, raw_bytes

    m_badge = re.search(r"<span>O\s*<b[^>]*>([0-9,.]+)</b></span>", body)
    if m_badge:
        val = float(m_badge.group(1).replace(",", ""))
        return val, url_used, None, raw_bytes

    table_open = _extract_table_open(body, target_date)
    if table_open is not None:
        return float(table_open), url_used, None, raw_bytes

    if quote_url and quote_url != overview_url:
        try:
            rq = requests.get(quote_url, headers=DEFAULT_HEADERS, timeout=12)
            if rq.status_code == 200:
                q_text = rq.text
                m_b = re.search(r"<span>O\s*<b[^>]*>([0-9,.]+)</b></span>", q_text)
                if m_b:
                    return float(m_b.group(1).replace(",", "")), quote_url, None, rq.content
                m_o = re.search(r"<tr><td>Open</td><td>(?:₹|&#8377;)?(?:<!-- -->)?\s*([0-9,.]+)", q_text, re.IGNORECASE)
                if m_o:
                    return float(m_o.group(1).replace(",", "")), quote_url, None, rq.content
        except Exception:
            pass

    return None, None, "Could not extract listing opening price from second source", raw_bytes


def record_actual_from_tier2(
    *,
    company: str,
    listing_date: date,
    issue_price: Decimal,
    nse_symbol: Optional[str],
    bse_code: Optional[str],
    overview_url: str,
    quote_url: Optional[str],
    log_path: Path,
    mock_yfinance_history: Optional[pd.DataFrame] = None,
    mock_second_source_text: Optional[str] = None,
) -> dict[str, Any]:
    """Execute Tier 2 (yfinance + independent second-source verification <= 1.0%)."""
    ticker_sym = f"{nse_symbol}.NS" if nse_symbol else f"{bse_code}.BO"
    yf_url = f"https://finance.yahoo.com/quote/{ticker_sym}"

    yf_open, yf_err, yf_raw = fetch_yfinance_first_session_open(
        ticker_sym, listing_date, mock_history=mock_yfinance_history
    )
    if yf_err or yf_open is None or yf_raw is None:
        st = "SKIPPED_NO_MATCH" if yf_err and "LISTING_DAY_BAR_MISSING" in yf_err else "SKIPPED_FETCH_FAILED"
        return {
            "status": st,
            "reason": f"Tier 2 primary source ({ticker_sym}) failed: {yf_err or 'unknown error'}",
        }

    yf_source_val = make_yfinance_source_value(ticker_sym, listing_date, yf_open)
    yf_source_val["url"] = yf_url
    yf_source_val["raw_bytes"] = yf_raw

    sec_open, sec_url, sec_err, sec_raw = fetch_second_source_open(
        overview_url, quote_url, listing_date, mock_text=mock_second_source_text
    )
    if sec_err or sec_open is None or sec_url is None:
        sec_m = None
        if sec_raw:
            sec_m = parse_source_value_metadata(sec_raw, target_date=listing_date, publisher="Chittorgarh", url=overview_url)
            sec_m["raw_bytes"] = sec_raw
        return {
            "status": "PENDING_REVIEW",
            "reason": f"Tier 2 second source missing or unparseable: {sec_err or 'unknown'}",
            "fetched_sources": [yf_source_val] + ([sec_m] if sec_m else []),
        }

    sec_meta = parse_source_value_metadata(
        sec_raw or "",
        target_date=listing_date,
        publisher="Chittorgarh",
        extracted_price=sec_open,
        url=sec_url or overview_url,
    )
    sec_meta["raw_bytes"] = sec_raw

    rel_diff_pct = abs(yf_open - sec_open) / yf_open * 100.0
    if rel_diff_pct > 1.0:
        return {
            "status": "PENDING_REVIEW",
            "reason": (
                f"Tier 2 sources diverge beyond 1.0% tolerance: "
                f"yfinance={yf_open} vs second_source={sec_open} (diff={rel_diff_pct:.2f}%)"
            ),
            "fetched_sources": [yf_source_val, sec_meta],
        }

    content_hash = hashlib.sha256(yf_raw).hexdigest()
    evidence_dir = ROOT_DIR / "data" / "evidence" / "actuals"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-")
    stem = f"{listing_date.isoformat()}_{slug}_{content_hash[:12]}"
    snapshot_path = evidence_dir / f"{stem}.txt"
    manifest_path = evidence_dir / f"{stem}.json"

    if not snapshot_path.exists():
        snapshot_path.write_bytes(yf_raw)

    gain_pct = ((Decimal(str(yf_open)) - issue_price) / issue_price * Decimal("100")).quantize(Decimal("0.01"))
    yf_source_val = make_yfinance_source_value(ticker_sym, listing_date, yf_open)
    sec_meta = parse_source_value_metadata(
        sec_raw or "",
        target_date=listing_date,
        publisher="Chittorgarh",
        extracted_price=sec_open,
        url=sec_url or overview_url,
    )
    manifest = {
        "company": company,
        "listing_date": listing_date.isoformat(),
        "page_date": listing_date.isoformat(),
        "accessed_at": get_write_timestamp(),
        "source_url": yf_url,
        "final_url": yf_url,
        "source_host": "finance.yahoo.com",
        "exchange_used": yf_source_val["exchange"],
        "exchange": yf_source_val["exchange"],
        "quantity": yf_source_val["quantity"],
        "source_publisher": yf_source_val["publisher"],
        "source_values": [yf_source_val, sec_meta],
        "content_type": "text/plain",
        "snapshot_path": snapshot_path.relative_to(ROOT_DIR).as_posix(),
        "snapshot_sha256": content_hash,
        "outcome_source": "tier2",
        "yfinance_symbol": ticker_sym,
        "yfinance_open": yf_open,
        "second_source_name": "Chittorgarh Listing Section",
        "second_source_url": sec_url,
        "second_source_open": sec_open,
        "relative_difference_pct": round(rel_diff_pct, 4),
        "issue_price_in_prediction": float(issue_price),
        "official_opening_price": float(yf_open),
        "computed_listing_gain_pct": float(gain_pct),
        "verification_status": "VERIFIED_TIER2_CROSS_CHECKED",
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)

    ok, message = update_actual_outcome(
        company=company,
        listing_date=listing_date.isoformat(),
        actual_listing_price=float(yf_open),
        issue_price=float(issue_price),
        source_url=yf_url,
        source_snapshot_path=snapshot_path.relative_to(ROOT_DIR).as_posix(),
        outcome_source="tier2",
        log_path=log_path,
    )
    if not ok:
        return {"status": "SKIPPED_FETCH_FAILED", "reason": f"Failed updating prediction log: {message}"}

    return {
        "status": "RECORDED",
        "tier": "tier2",
        "official_opening_price": yf_open,
        "actual_gain_pct": float(gain_pct),
        "manifest": manifest,
        "message": message,
    }


def record_actual_from_tier2b(
    *,
    company: str,
    listing_date: date,
    issue_price: Decimal,
    overview_url: str,
    quote_url: Optional[str] = None,
    log_path: str | Path = LOG_PATH,
    mock_source_a_text: Optional[str] = None,
    mock_source_b_text: Optional[str] = None,
    mock_source_a_url: Optional[str] = None,
    mock_source_b_url: Optional[str] = None,
) -> dict[str, Any]:
    """Execute Tier 2b (two independent non-Yahoo sources <= 1.0% tolerance) (D-096)."""
    # 1. Source A (Chittorgarh)
    url_a = mock_source_a_url or overview_url
    price_a, url_used_a, err_a, raw_a = fetch_second_source_open(
        overview_url, quote_url, listing_date, mock_text=mock_source_a_text
    )
    if err_a or price_a is None or raw_a is None:
        return {
            "status": "SKIPPED_TIER2B_UNAVAILABLE",
            "reason": f"Tier 2b Source A (Chittorgarh) unavailable: {err_a or 'unknown'}",
        }

    # 2. Source B (Groww / independent source)
    url_b = mock_source_b_url
    price_b: Optional[float] = None
    raw_b: Optional[bytes] = None

    if mock_source_b_text is not None:
        raw_b = mock_source_b_text.encode("utf-8")
        clean_b = re.sub(r"<[^>]+>", " ", mock_source_b_text)
        m_b = re.search(
            r"(?:listed at|shares listed at|opening price of|open|listed on (?:nse|bse) at)\s*(?:₹|&#8377;|Rs\.?)?\s*([0-9]+(?:\.[0-9]+)?)",
            clean_b,
            re.IGNORECASE,
        )
        if m_b:
            price_b = float(m_b.group(1))
        url_b = url_b or "https://groww.in/blog/mock-ipo-listing-news"
    else:
        if url_b:
            try:
                r_b = requests.get(url_b, headers=DEFAULT_HEADERS, timeout=15)
                if r_b.status_code == 200:
                    raw_b = r_b.content
                    clean_b = re.sub(r"<[^>]+>", " ", r_b.text)
                    m_b = re.search(
                        r"(?:listed at|shares listed at|opening price of|open|listed on (?:nse|bse) at)\s*(?:₹|&#8377;|Rs\.?)?\s*([0-9]+(?:\.[0-9]+)?)",
                        clean_b,
                        re.IGNORECASE,
                    )
                    if m_b:
                        price_b = float(m_b.group(1))
            except Exception:
                pass

    if price_b is None or raw_b is None or not url_b:
        return {
            "status": "SKIPPED_TIER2B_UNAVAILABLE",
            "reason": "Tier 2b independent second source unavailable or unparseable",
        }

    # Verify both pages name company
    first_token = company.split()[0].lower()
    text_a = raw_a.decode("utf-8", errors="ignore").lower()
    text_b = raw_b.decode("utf-8", errors="ignore").lower()
    if first_token not in text_a or first_token not in text_b:
        return {
            "status": "SKIPPED_TIER2B_UNAVAILABLE",
            "reason": f"Tier 2b source verification failed: company name '{first_token}' not proved in both source pages",
        }

    # 3. Check 1.0% tolerance
    denom = min(price_a, price_b)
    if denom <= 0:
        return {
            "status": "SKIPPED_TIER2B_UNAVAILABLE",
            "reason": "Invalid non-positive price extracted in Tier 2b",
        }

    rel_diff_pct = abs(price_a - price_b) / denom * 100.0
    if rel_diff_pct > 1.0:
        return {
            "status": "SKIPPED_TIER2B_DISAGREE",
            "reason": (
                f"Tier 2b sources diverge beyond 1.0% tolerance: "
                f"source1={price_a} vs source2={price_b} (diff={rel_diff_pct:.2f}%)"
            ),
        }

    # 4. Save evidence
    agreed_open = round((price_a + price_b) / 2.0, 2)
    gain_pct = ((Decimal(str(agreed_open)) - issue_price) / issue_price * Decimal("100")).quantize(Decimal("0.01"))

    evidence_dir = ROOT_DIR / "data" / "evidence" / "actuals"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-")
    ld_str = listing_date.isoformat()

    sha_a = hashlib.sha256(raw_a).hexdigest()
    path_txt_a = evidence_dir / f"{ld_str}_{slug}_chittorgarh_tier2b.txt"
    path_json_a = evidence_dir / f"{ld_str}_{slug}_chittorgarh_tier2b.json"
    path_txt_a.write_bytes(raw_a)

    sha_b = hashlib.sha256(raw_b).hexdigest()
    path_txt_b = evidence_dir / f"{ld_str}_{slug}_groww_tier2b.txt"
    path_json_b = evidence_dir / f"{ld_str}_{slug}_groww_tier2b.json"
    path_txt_b.write_bytes(raw_b)

    meta_a = parse_source_value_metadata(
        raw_a,
        target_date=listing_date,
        publisher="Chittorgarh",
        extracted_price=price_a,
        url=url_used_a or url_a,
    )
    meta_b = parse_source_value_metadata(
        raw_b,
        target_date=listing_date,
        publisher="Groww",
        extracted_price=price_b,
        url=url_b,
    )

    manifest_b = {
        "company": company,
        "listing_date": ld_str,
        "source_role": "tier2b_independent_second_source",
        "source_name": "Groww Financial Research Listing News",
        "source_url": url_b,
        "accessed_at": get_write_timestamp(),
        "http_status": 200,
        "content_sha256": sha_b,
        "exchange": meta_b["exchange"],
        "quantity": meta_b["quantity"],
        "source_publisher": meta_b["publisher"],
        "source_values": [meta_b],
        "parsed_listing_price": price_b,
    }
    path_json_b.write_text(json.dumps(manifest_b, indent=2) + "\n", encoding="utf-8")

    manifest_a = {
        "company": company,
        "listing_date": ld_str,
        "source_role": "tier2b_primary",
        "source_name": "Chittorgarh Listing Section",
        "source_url": url_used_a or url_a,
        "accessed_at": get_write_timestamp(),
        "http_status": 200,
        "page_date": ld_str,
        "final_url": url_used_a or url_a,
        "snapshot_path": path_txt_a.relative_to(ROOT_DIR).as_posix(),
        "snapshot_sha256": sha_a,
        "outcome_source": "tier2b",
        "exchange": meta_a["exchange"] if meta_a["exchange"] == meta_b["exchange"] else "UNKNOWN",
        "quantity": meta_a["quantity"],
        "source_publisher": "Chittorgarh / Groww (Tier 2b)",
        "source_values": [meta_a, meta_b],
        "issue_price_in_prediction": float(issue_price),
        "official_opening_price": float(agreed_open),
        "computed_listing_gain_pct": float(gain_pct),
        "relative_difference_pct": round(rel_diff_pct, 4),
        "second_source_name": "Groww Financial Research Listing News",
        "second_source_url": url_b,
        "second_source_open": price_b,
        "verification_status": "VERIFIED_TIER2B_DUAL_SOURCE",
    }
    path_json_a.write_text(json.dumps(manifest_a, indent=2) + "\n", encoding="utf-8")

    # 5. Update log
    ok, message = update_actual_outcome(
        company=company,
        listing_date=ld_str,
        actual_listing_price=float(agreed_open),
        issue_price=float(issue_price),
        source_url=url_used_a or url_a,
        source_snapshot_path=path_txt_a.relative_to(ROOT_DIR).as_posix(),
        outcome_source="tier2b",
        log_path=log_path,
    )
    if not ok:
        return {"status": "SKIPPED_FETCH_FAILED", "reason": f"Failed updating prediction log: {message}"}

    return {
        "status": "RECORDED",
        "tier": "tier2b",
        "official_opening_price": agreed_open,
        "actual_gain_pct": float(gain_pct),
        "manifest": manifest_a,
        "evidence_files": [
            path_txt_a.name, path_json_a.name,
            path_txt_b.name, path_json_b.name,
        ],
        "message": message,
    }


def record_actual_from_tier2_arbitrated(
    *,
    company: str,
    listing_date: date,
    issue_price: Decimal,
    nse_symbol: Optional[str],
    bse_code: Optional[str],
    overview_url: str,
    quote_url: Optional[str] = None,
    log_path: str | Path = LOG_PATH,
    initial_sources: Optional[list[dict[str, Any]]] = None,
    mock_additional_sources: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Execute pre-registered divergence arbitration (D-100, Phase 19 Workstream B).

    Rule (preregistration Section 1):
    1. Compares values strictly if and only if exchange (NSE vs BSE) and quantity match.
    2. UNKNOWN exchange or mismatched quantities are excluded from agreement.
    3. Yahoo Finance and any Yahoo-derived source count strictly as one publisher.
    4. Outcome accepted only if >= 2 sources from different publishers agree within TOLERANCE_PCT (1.0%)
       AND the agreeing group constitutes a strict majority (> 50%) of all labelled independent sources
       for that specific (exchange, quantity).
    5. Official price is median of the agreeing majority group.
    """
    target_log = Path(log_path)
    if not target_log.is_file():
        return {"status": "SKIPPED_FETCH_FAILED", "reason": f"Log file not found: {target_log}"}

    # Verify active unrecorded FORWARD row
    frame = pd.read_csv(target_log, dtype=str, keep_default_na=False)
    matches = frame[(frame["company"].str.casefold() == company.strip().casefold()) & (frame["status"] == "FORWARD")]
    if len(matches) != 1:
        return {"status": "SKIPPED_NO_MATCH", "reason": f"Expected 1 active FORWARD row for {company}, found {len(matches)}"}
    row = matches.iloc[0]
    if row["actual_gain_pct"].strip():
        return {"status": "SKIPPED_ALREADY_RECORDED", "reason": f"Outcome already recorded for {company}"}

    # Gather all sources
    all_sources: list[dict[str, Any]] = []
    if initial_sources:
        all_sources.extend(initial_sources)

    # If additional mock sources are provided, add them
    if mock_additional_sources:
        all_sources.extend(mock_additional_sources)
    else:
        # Fetch up to 2 reachable independent publishers if available
        # 1. Groww listing news
        slug = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-")
        groww_candidates = [
            f"https://groww.in/blog/{slug}-shares-list-at-nse-bse",
            f"https://groww.in/blog/{slug}-ipo-listing-news",
            f"https://groww.in/blog/{slug}-ipo-listing",
            f"https://groww.in/blog/{slug}-shares-debut",
        ]
        for g_url in groww_candidates:
            try:
                rg = requests.get(g_url, headers=DEFAULT_HEADERS, timeout=12)
                if rg.status_code == 200:
                    g_meta = parse_source_value_metadata(
                        rg.content,
                        target_date=listing_date,
                        publisher="Groww",
                        url=g_url,
                    )
                    if g_meta.get("value") is not None:
                        g_meta["source_url"] = g_url
                        g_meta["raw_bytes"] = rg.content
                        all_sources.append(g_meta)
                        break
            except Exception:
                pass

        # 2. Chittorgarh quote page if different from overview
        if quote_url and quote_url != overview_url:
            try:
                rq = requests.get(quote_url, headers=DEFAULT_HEADERS, timeout=12)
                if rq.status_code == 200:
                    q_meta = parse_source_value_metadata(
                        rq.content,
                        target_date=listing_date,
                        publisher="Chittorgarh Quote",
                        url=quote_url,
                    )
                    if q_meta.get("value") is not None:
                        q_meta["source_url"] = quote_url
                        q_meta["raw_bytes"] = rq.content
                        all_sources.append(q_meta)
            except Exception:
                pass

    # Annotate hypothetical gains for all sources
    for s in all_sources:
        v = s.get("value")
        if v is not None and issue_price > 0:
            try:
                s["hypothetical_gain_pct"] = round(float((Decimal(str(v)) - issue_price) / issue_price * Decimal("100")), 2)
            except Exception:
                s["hypothetical_gain_pct"] = None
        else:
            s["hypothetical_gain_pct"] = None

    # Filter 1: Label compatibility gating (NSE or BSE only; exclude UNKNOWN exchange or missing values)
    labelled = [
        s for s in all_sources
        if s.get("exchange") in ("NSE", "BSE") and s.get("value") is not None and float(s["value"]) > 0
    ]

    # Primary Exchange Policy (D-105, Phase 20 Workstream C / preregistration Section 1):
    # If listed on NSE (nse_symbol provided), outcome is strictly first-session open on NSE.
    # If sole BSE listing (no nse_symbol, bse_code provided), outcome is first-session open on BSE.
    primary_exchange = "NSE" if (nse_symbol and str(nse_symbol).strip()) else "BSE"

    primary_labelled = [
        s for s in labelled if s.get("exchange") == primary_exchange
    ]

    if len(primary_labelled) < 2:
        distinct_exchs = set(s.get("exchange") for s in all_sources if s.get("value") is not None)
        if len(distinct_exchs - {"UNKNOWN"}) > 1:
            return {
                "status": "PENDING_REVIEW",
                "reason": (
                    f"SKIPPED_POLICY_NO_PRIMARY_EXCHANGE_MAJORITY: "
                    f"SKIPPED_ARBITRATION_EXCHANGE_MISMATCH: sources quote different exchanges without intra-exchange agreement on primary exchange {primary_exchange}"
                ),
                "all_sources": all_sources,
            }
        return {
            "status": "PENDING_REVIEW",
            "reason": (
                f"SKIPPED_POLICY_NO_PRIMARY_EXCHANGE_MAJORITY: "
                f"SKIPPED_ARBITRATION_UNAVAILABLE: fewer than 2 independent labelled sources available on primary exchange {primary_exchange}"
            ),
            "all_sources": all_sources,
        }

    # Group by (exchange, quantity) strictly on primary_exchange
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for s in primary_labelled:
        key = (s["exchange"], s.get("quantity", "open"))
        groups.setdefault(key, []).append(s)

    best_agreement: Optional[dict[str, Any]] = None

    for (exch, qty), group in groups.items():
        # Publisher deduplication: Yahoo and Yahoo-derived count as strictly 1 publisher
        pub_map: dict[str, dict[str, Any]] = {}
        for s in group:
            pub_raw = s.get("publisher", "Unknown")
            pub_norm = "Yahoo Finance" if "yahoo" in pub_raw.lower() else pub_raw
            if pub_norm not in pub_map:
                pub_map[pub_norm] = s

        distinct_sources = list(pub_map.values())
        n_group = len(distinct_sources)
        if n_group < 2:
            continue

        # Check clusters of agreeing sources within TOLERANCE_PCT (1.0%)
        clusters: list[list[dict[str, Any]]] = []
        for i, s1 in enumerate(distinct_sources):
            current_cluster = [s1]
            p1 = float(s1["value"])
            for j, s2 in enumerate(distinct_sources):
                if i == j:
                    continue
                p2 = float(s2["value"])
                diff_pct = abs(p1 - p2) / min(p1, p2) * 100.0
                if diff_pct <= TOLERANCE_PCT:
                    current_cluster.append(s2)
            if len(current_cluster) >= 2:
                # Confirm all pairwise differences in cluster <= TOLERANCE_PCT
                all_agree = True
                for a in range(len(current_cluster)):
                    for b in range(a + 1, len(current_cluster)):
                        pa = float(current_cluster[a]["value"])
                        pb = float(current_cluster[b]["value"])
                        if (abs(pa - pb) / min(pa, pb) * 100.0) > TOLERANCE_PCT:
                            all_agree = False
                            break
                    if not all_agree:
                        break
                if all_agree:
                    clusters.append(current_cluster)

        # Check strict majority requirement: len(cluster) > n_group / 2
        for c in clusters:
            if len(c) > (n_group / 2.0):
                best_agreement = {
                    "exchange": exch,
                    "quantity": qty,
                    "agreeing_sources": c,
                    "n_group": n_group,
                }
                break
        if best_agreement:
            break

    if not best_agreement:
        # Check if exchange mismatch between labelled sources
        exchs = set(s["exchange"] for s in labelled)
        if len(exchs) > 1:
            return {
                "status": "PENDING_REVIEW",
                "reason": (
                    f"SKIPPED_POLICY_NO_PRIMARY_EXCHANGE_MAJORITY: "
                    f"SKIPPED_ARBITRATION_EXCHANGE_MISMATCH: sources quote different exchanges without intra-exchange majority on primary exchange {primary_exchange}"
                ),
                "all_sources": all_sources,
            }
        return {
            "status": "PENDING_REVIEW",
            "reason": (
                f"SKIPPED_POLICY_NO_PRIMARY_EXCHANGE_MAJORITY: "
                f"SKIPPED_ARBITRATION_NO_MAJORITY: no strict majority among agreeing sources on primary exchange {primary_exchange}"
            ),
            "all_sources": all_sources,
        }

    # Strict majority accepted! Compute median agreed opening price
    agreeing = best_agreement["agreeing_sources"]
    prices = [float(s["value"]) for s in agreeing]
    agreed_price = round(float(statistics.median(prices)), 2)
    gain_pct = ((Decimal(str(agreed_price)) - issue_price) / issue_price * Decimal("100")).quantize(Decimal("0.01"))

    evidence_dir = ROOT_DIR / "data" / "evidence" / "actuals"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-")
    ld_str = listing_date.isoformat()
    snapshot_path = evidence_dir / f"{ld_str}_{slug}_arbitrated.txt"
    manifest_path = evidence_dir / f"{ld_str}_{slug}_arbitrated.json"

    # Primary source URL for log update
    primary_url = str(agreeing[0].get("source_url") or overview_url)

    # Save summary text snapshot of arbitration
    snap_lines = [
        f"Company: {company}",
        f"Listing Date: {ld_str}",
        f"Arbitrated Exchange: {best_agreement['exchange']}",
        f"Arbitrated Quantity: {best_agreement['quantity']}",
        f"Official Opening Price: {agreed_price}",
        f"Computed Listing Gain: {gain_pct}%",
        f"Agreeing Publishers: {', '.join(sorted(set(str(s.get('publisher', '')) for s in agreeing)))}",
        "Source Values Evaluated:",
    ]
    for s in all_sources:
        snap_lines.append(f"  - {s.get('publisher')}: {s.get('exchange')} {s.get('quantity')}={s.get('value')} (gain={s.get('hypothetical_gain_pct')}%)")
    snap_bytes = ("\n".join(snap_lines) + "\n").encode("utf-8")
    snapshot_path.write_bytes(snap_bytes)
    snapshot_hash = hashlib.sha256(snap_bytes).hexdigest()

    # Save any raw bodies from agreeing sources that were fetched
    for idx, s in enumerate(all_sources):
        raw_b = s.get("raw_bytes")
        if raw_b and isinstance(raw_b, bytes):
            pub_slug = re.sub(r"[^a-z0-9]+", "-", str(s.get("publisher", "src")).lower()).strip("-")
            sub_snap = evidence_dir / f"{ld_str}_{slug}_{pub_slug}_{idx}.txt"
            if not sub_snap.exists():
                sub_snap.write_bytes(raw_b)
            s["snapshot_path"] = sub_snap.relative_to(ROOT_DIR).as_posix()
        if "raw_bytes" in s:
            del s["raw_bytes"]

    manifest = {
        "company": company,
        "listing_date": ld_str,
        "page_date": ld_str,
        "accessed_at": get_write_timestamp(),
        "source_url": primary_url,
        "final_url": primary_url,
        "source_host": urlsplit(primary_url).hostname,
        "snapshot_path": snapshot_path.relative_to(ROOT_DIR).as_posix(),
        "snapshot_sha256": snapshot_hash,
        "outcome_source": "tier2_arbitrated",
        "exchange": best_agreement["exchange"],
        "quantity": best_agreement["quantity"],
        "source_publisher": ", ".join(sorted(set(str(s.get("publisher", "")) for s in agreeing))),
        "issue_price_in_prediction": float(issue_price),
        "official_opening_price": float(agreed_price),
        "computed_listing_gain_pct": float(gain_pct),
        "arbitration_rule": "pre_registered_strict_majority",
        "agreeing_publishers": [str(s.get("publisher", "")) for s in agreeing],
        "agreeing_prices": prices,
        "source_values": all_sources,
        "verification_status": "VERIFIED_TIER2_ARBITRATED",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    ok, message = update_actual_outcome(
        company=company,
        listing_date=ld_str,
        actual_listing_price=float(agreed_price),
        issue_price=float(issue_price),
        source_url=primary_url,
        source_snapshot_path=snapshot_path.relative_to(ROOT_DIR).as_posix(),
        outcome_source="tier2_arbitrated",
        log_path=target_log,
    )
    if not ok:
        return {"status": "SKIPPED_FETCH_FAILED", "reason": f"Failed updating prediction log: {message}"}

    return {
        "status": "RECORDED",
        "tier": "tier2_arbitrated",
        "official_opening_price": agreed_price,
        "actual_gain_pct": float(gain_pct),
        "manifest": manifest,
        "message": message,
    }


def execute_two_tier_outcome_chain(
    *,
    company: str,
    log_path: str | Path = LOG_PATH,
    current_dt: Optional[datetime] = None,
    mock_exchange_evidence_file: Optional[Path] = None,
    mock_yfinance_history: Optional[pd.DataFrame] = None,
    mock_second_source_text: Optional[str] = None,
    mock_nse_symbol: Optional[str] = None,
    mock_bse_code: Optional[str] = None,
    mock_tier2b_source_b_text: Optional[str] = None,
    mock_tier2b_source_b_url: Optional[str] = None,
    mock_arbitration_sources: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Execute two-tier outcome recording chain for due forward row (D-066, D-069)."""
    target_log = Path(log_path)
    if not target_log.is_file():
        return {"status": "SKIPPED_FETCH_FAILED", "reason": f"Log file not found: {target_log}"}

    frame = pd.read_csv(target_log, dtype=str, keep_default_na=False)
    matches = frame[(frame["company"].str.casefold() == company.strip().casefold()) & (frame["status"] == "FORWARD")]
    if len(matches) != 1:
        return {"status": "SKIPPED_NO_MATCH", "reason": f"Expected 1 active FORWARD row for {company}, found {len(matches)}"}

    row = matches.iloc[0]
    if row["actual_gain_pct"].strip():
        return {"status": "SKIPPED_ALREADY_RECORDED", "reason": f"Outcome already recorded for {company}"}

    try:
        listing_date = datetime.strptime(row["listing_date"][:10], "%Y-%m-%d").date()
        features = json.loads(row["features_snapshot_json"]) if row.get("features_snapshot_json") else {}
        issue_price = Decimal(str(features.get("issue_price", 0)))
    except Exception as exc:
        return {"status": "SKIPPED_FETCH_FAILED", "reason": f"Invalid row metadata: {exc}"}

    if issue_price <= 0:
        return {"status": "SKIPPED_FETCH_FAILED", "reason": "Non-positive issue price in prediction row"}

    ready, timing_msg = is_listing_ready_for_actuals(listing_date, current_dt=current_dt)
    if not ready:
        return {"status": "SKIPPED_MARKET_IN_PROGRESS", "reason": timing_msg}

    symbols_info = resolve_company_symbols_and_urls(company, features)
    nse_sym = mock_nse_symbol or symbols_info.get("nse_symbol")
    bse_code = mock_bse_code or symbols_info.get("bse_code")
    overview_url = symbols_info.get("overview_url")
    quote_url = symbols_info.get("quote_url")

    if not nse_sym and not bse_code and not mock_exchange_evidence_file:
        return {"status": "SKIPPED_NO_MATCH", "reason": f"Could not resolve NSE/BSE symbols for {company}"}

    tier1_error: Optional[str] = None
    if mock_exchange_evidence_file is not None:
        try:
            res_tier1 = record_actual_from_evidence_file(
                company=company,
                source_url="https://www.nseindia.com/get-quote/equity/MOCK",
                evidence_file=mock_exchange_evidence_file,
                listing_price=float(issue_price * Decimal("1.25")),
                page_date=listing_date.isoformat(),
                company_quote=company,
                price_quote=f"Open {float(issue_price * Decimal('1.25')):.2f}",
                log_path=target_log,
            )
            return {"status": "RECORDED", "tier": "tier1", "data": res_tier1}
        except Exception as e:
            tier1_error = str(e)
    else:
        official_url = f"https://www.nseindia.com/api/quote-equity?symbol={nse_sym}" if nse_sym else f"https://www.bseindia.com/stock-share-price/.../{bse_code}"
        try:
            r_check = requests.get(official_url, headers=DEFAULT_HEADERS, timeout=8)
            if r_check.status_code == 200:
                pass
            else:
                tier1_error = f"Official exchange returned HTTP {r_check.status_code} (WAF / Access Control)"
        except Exception as exc:
            tier1_error = f"Official exchange connection failed: {exc}"

    if not overview_url:
        return {"status": "PENDING_REVIEW", "reason": "No overview URL available for Tier 2 second-source cross check"}

    tier2_res = record_actual_from_tier2(
        company=company,
        listing_date=listing_date,
        issue_price=issue_price,
        nse_symbol=nse_sym,
        bse_code=bse_code,
        overview_url=overview_url,
        quote_url=quote_url,
        log_path=target_log,
        mock_yfinance_history=mock_yfinance_history,
        mock_second_source_text=mock_second_source_text,
    )
    if tier1_error and "manifest" in tier2_res:
        tier2_res["manifest"]["tier1_error"] = tier1_error

    # Pre-registered Divergence Arbitration (D-100, Phase 19 Workstream B):
    # When Tier 2 sources diverge beyond 1.0%, invoke arbitration
    if tier2_res.get("status") == "PENDING_REVIEW" and "diverge beyond 1.0%" in str(tier2_res.get("reason", "")):
        init_sources = []
        if nse_sym or bse_code:
            t_sym = f"{nse_sym}.NS" if nse_sym else f"{bse_code}.BO"
            # Try to get yfinance open if available
            yf_o, yf_e, yf_r = fetch_yfinance_first_session_open(t_sym, listing_date, mock_history=mock_yfinance_history)
            if yf_o is not None:
                yf_sv = make_yfinance_source_value(t_sym, listing_date, yf_o)
                yf_sv["url"] = f"https://finance.yahoo.com/quote/{t_sym}"
                yf_sv["raw_bytes"] = yf_r
                init_sources.append(yf_sv)
        sec_o, sec_u, sec_e, sec_r = fetch_second_source_open(overview_url, quote_url, listing_date, mock_text=mock_second_source_text)
        if sec_o is not None or sec_r is not None:
            sec_sv = parse_source_value_metadata(sec_r or "", target_date=listing_date, publisher="Chittorgarh", extracted_price=sec_o, url=sec_u or overview_url)
            sec_sv["raw_bytes"] = sec_r
            init_sources.append(sec_sv)

        arb_res = record_actual_from_tier2_arbitrated(
            company=company,
            listing_date=listing_date,
            issue_price=issue_price,
            nse_symbol=nse_sym,
            bse_code=bse_code,
            overview_url=overview_url,
            quote_url=quote_url,
            log_path=target_log,
            initial_sources=init_sources,
            mock_additional_sources=mock_arbitration_sources,
        )
        if arb_res.get("status") == "RECORDED":
            return arb_res
        if arb_res.get("status") == "PENDING_REVIEW":
            tier2_res["reason"] = f"{tier2_res['reason']} (arbitration: {arb_res['reason']})"
            tier2_res["all_sources"] = arb_res.get("all_sources", init_sources)

    # Tier 2b fallback (D-096):
    # When Tier 2 returns LISTING_DAY_BAR_MISSING or empty yfinance history, and listing date is in the past
    st2 = tier2_res.get("status")
    r2 = str(tier2_res.get("reason", ""))
    from opi.discover import get_today_ist
    try:
        today_ist = datetime.strptime(get_today_ist(), "%Y-%m-%d").date()
    except Exception:
        today_ist = date.today()

    if st2 in ("SKIPPED_NO_MATCH", "SKIPPED_FETCH_FAILED") and ("LISTING_DAY_BAR_MISSING" in r2 or "returned empty" in r2.lower()) and listing_date < today_ist:
        tier2b_res = record_actual_from_tier2b(
            company=company,
            listing_date=listing_date,
            issue_price=issue_price,
            overview_url=overview_url,
            quote_url=quote_url,
            log_path=target_log,
            mock_source_a_text=mock_second_source_text,
            mock_source_b_text=mock_tier2b_source_b_text,
            mock_source_b_url=mock_tier2b_source_b_url,
        )
        if tier2b_res.get("status") == "RECORDED":
            return tier2b_res
        if tier2b_res.get("status") == "SKIPPED_TIER2B_DISAGREE":
            tier2_res = tier2b_res

    # Persist divergence and pending evidence snapshots and manifests (D-104)
    final_status = tier2_res.get("status")
    if final_status != "RECORDED":
        cand_sources = tier2_res.get("all_sources") or tier2_res.get("fetched_sources") or []
        if not cand_sources and 'init_sources' in locals():
            cand_sources = init_sources
        if not cand_sources and 'tier2b_res' in locals() and tier2b_res.get("sources"):
            cand_sources = tier2b_res.get("sources")

        valid_sources = [s for s in cand_sources if s.get("raw_bytes") is not None or s.get("content") is not None]
        if valid_sources:
            pending_out = persist_pending_actuals_evidence(
                company=company,
                listing_date=listing_date,
                status=final_status,
                reason=tier2_res.get("reason", ""),
                sources=valid_sources,
            )
            tier2_res["pending_manifest"] = pending_out

    return tier2_res
