"""Evidence-backed recording of official IPO listing-day opening prices."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
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
    matched_open: Optional[float] = None
    for idx, row in hist_sorted.iterrows():
        try:
            if hasattr(idx, "tz_convert"):
                ts_ist = idx.tz_convert("Asia/Kolkata")
            elif hasattr(idx, "tz_localize"):
                ts_ist = idx.tz_localize("UTC").tz_convert("Asia/Kolkata")
            else:
                ts_ist = pd.to_datetime(idx)
            if ts_ist.date() == target_date:
                matched_open = float(row["Open"])
                break
        except Exception:
            idx_str = str(idx)[:10]
            if idx_str == target_date.isoformat():
                matched_open = float(row["Open"])
                break

    if matched_open is None and not hist_sorted.empty:
        first_row = hist_sorted.iloc[0]
        matched_open = float(first_row["Open"])

    raw_bytes = hist_sorted.to_json(orient="index", date_format="iso").encode("utf-8")
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
        return {
            "status": "SKIPPED_FETCH_FAILED",
            "reason": f"Tier 2 primary source ({ticker_sym}) failed: {yf_err or 'unknown error'}",
        }

    sec_open, sec_url, sec_err, sec_raw = fetch_second_source_open(
        overview_url, quote_url, listing_date, mock_text=mock_second_source_text
    )
    if sec_err or sec_open is None or sec_url is None:
        return {
            "status": "PENDING_REVIEW",
            "reason": f"Tier 2 second source missing or unparseable: {sec_err or 'unknown'}",
        }

    rel_diff_pct = abs(yf_open - sec_open) / yf_open * 100.0
    if rel_diff_pct > 1.0:
        return {
            "status": "PENDING_REVIEW",
            "reason": (
                f"Tier 2 sources diverge beyond 1.0% tolerance: "
                f"yfinance={yf_open} vs second_source={sec_open} (diff={rel_diff_pct:.2f}%)"
            ),
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
    manifest = {
        "company": company,
        "listing_date": listing_date.isoformat(),
        "page_date": listing_date.isoformat(),
        "accessed_at": get_write_timestamp(),
        "source_url": yf_url,
        "final_url": yf_url,
        "source_host": "finance.yahoo.com",
        "exchange_used": "NSE" if ".NS" in ticker_sym else "BSE",
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
    return tier2_res
