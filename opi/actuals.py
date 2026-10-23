"""Evidence-backed recording of official IPO listing-day opening prices."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import pandas as pd
import requests
from bs4 import BeautifulSoup

from opi.collect import DEFAULT_HEADERS, extract_clean_text_from_html
from opi.log import IST, ROOT_DIR, get_write_timestamp, update_actual_outcome

MAX_RESPONSE_BYTES = 12 * 1024 * 1024
MAX_REDIRECTS = 4
OFFICIAL_EXCHANGE_DOMAINS = ("nseindia.com", "bseindia.com")
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
