#!/usr/bin/env python3
"""opi.market - Evidence-backed market macro fetcher (D-048).

Fetches official exchange index (^NSEI) and volatility (^INDIAVIX) data via yfinance,
persisting raw payloads under data/evidence/market/<date>_nifty.raw with SHA-256 digests
and parsed market evidence in data/evidence/market/<date>_nifty.json.
Never estimates or mocks data; prints NOT_AVAILABLE if the source is unreachable.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
MARKET_EVIDENCE_DIR = ROOT_DIR / "data" / "evidence" / "market"


def fetch_market_history(start_date: str, end_date: str, save: bool = True) -> Dict[str, Dict[str, Any]]:
    """Fetch daily ^NSEI and ^INDIAVIX history for a date range and save evidence files.

    Args:
        start_date: YYYY-MM-DD
        end_date: YYYY-MM-DD
        save: Whether to persist .raw and .json evidence to data/evidence/market/

    Returns:
        Dict mapping date string (YYYY-MM-DD) to parsed dictionary.
    """
    try:
        import yfinance as yf
    except ImportError:
        print("NOT_AVAILABLE: yfinance is not installed", file=sys.stderr)
        return {}

    MARKET_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    # Extend start date backward slightly to ensure previous trading day's close is fetched
    start_dt = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
    fetch_start = (start_dt - dt.timedelta(days=7)).strftime("%Y-%m-%d")
    fetch_end = (end_dt + dt.timedelta(days=2)).strftime("%Y-%m-%d")

    try:
        nifty_ticker = yf.Ticker("^NSEI")
        nifty_hist = nifty_ticker.history(start=fetch_start, end=fetch_end)
    except Exception as exc:
        print(f"NOT_AVAILABLE: failed to fetch ^NSEI: {exc}", file=sys.stderr)
        return {}

    vix_hist = None
    try:
        vix_ticker = yf.Ticker("^INDIAVIX")
        vix_hist = vix_ticker.history(start=fetch_start, end=fetch_end)
    except Exception as exc:
        print(f"WARNING: failed to fetch ^INDIAVIX: {exc}", file=sys.stderr)

    if nifty_hist.empty or len(nifty_hist) < 2:
        print("NOT_AVAILABLE: insufficient ^NSEI data returned", file=sys.stderr)
        return {}

    results: Dict[str, Dict[str, Any]] = {}
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()

    for i in range(1, len(nifty_hist)):
        row_dt = nifty_hist.index[i].date()
        date_str = row_dt.strftime("%Y-%m-%d")

        # Filter within requested range
        if row_dt < start_dt or row_dt > end_dt:
            continue

        close_val = float(nifty_hist["Close"].iloc[i])
        prev_close_val = float(nifty_hist["Close"].iloc[i - 1])
        day_ret_pct = round(((close_val - prev_close_val) / prev_close_val) * 100.0, 2)

        vix_val = None
        if vix_hist is not None and not vix_hist.empty:
            vix_matches = vix_hist[vix_hist.index.date == row_dt]
            if not vix_matches.empty:
                vix_val = round(float(vix_matches["Close"].iloc[0]), 2)

        # Raw payload representing the full quote record
        raw_payload = {
            "symbol": "^NSEI",
            "date": date_str,
            "open": float(nifty_hist["Open"].iloc[i]),
            "high": float(nifty_hist["High"].iloc[i]),
            "low": float(nifty_hist["Low"].iloc[i]),
            "close": close_val,
            "prev_close": prev_close_val,
            "volume": int(nifty_hist["Volume"].iloc[i]) if "Volume" in nifty_hist else 0,
            "day_return_pct": day_ret_pct,
            "vix_close": vix_val,
            "source": "^NSEI / ^INDIAVIX via yfinance (public exchange data)",
            "fetched_at": now_iso,
        }

        raw_bytes = json.dumps(raw_payload, indent=2, sort_keys=True).encode("utf-8")
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        parsed_data = {
            "as_of_date": date_str,
            "nifty_close": close_val,
            "nifty_prev_close": prev_close_val,
            "nifty_day_return_pct": day_ret_pct,
            "india_vix": vix_val,
            "source": "^NSEI via yfinance (public exchange data)",
            "accessed_at": now_iso,
            "sha256": sha256_hash,
            "raw_file": f"{date_str}_nifty.raw",
        }

        if save:
            raw_path = MARKET_EVIDENCE_DIR / f"{date_str}_nifty.raw"
            json_path = MARKET_EVIDENCE_DIR / f"{date_str}_nifty.json"

            raw_path.write_bytes(raw_bytes)
            json_path.write_text(json.dumps(parsed_data, indent=2), encoding="utf-8")

        results[date_str] = parsed_data

    return results


def get_nifty_market_move(date_str: str) -> Optional[float]:
    """Retrieve evidenced Nifty day return percentage for a specific date.

    Reads parsed market evidence from data/evidence/market/<date>_nifty.json.
    Returns None if no evidence file exists or if day return cannot be computed.
    """
    json_path = MARKET_EVIDENCE_DIR / f"{date_str}_nifty.json"
    if not json_path.exists():
        # Fallback check for any other pattern in evidence dir
        matches = list(MARKET_EVIDENCE_DIR.glob(f"{date_str}*.json"))
        if matches:
            json_path = matches[0]
        else:
            return None

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if "nifty_day_return_pct" in data and data["nifty_day_return_pct"] is not None:
            return float(data["nifty_day_return_pct"])
        if "nifty_close" in data and "nifty_prev_close" in data:
            c = float(data["nifty_close"])
            p = float(data["nifty_prev_close"])
            return round(((c - p) / p) * 100.0, 2)
    except Exception:
        return None

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and record evidenced market data (D-048)")
    parser.add_argument("--start", default="2026-10-21", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2026-10-23", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    results = fetch_market_history(args.start, args.end, save=True)
    if not results:
        print("NOT_AVAILABLE")
        return 1

    print(f"Successfully recorded market evidence for {len(results)} dates:")
    for d, data in sorted(results.items()):
        print(f"  {d}: close={data['nifty_close']:.2f}, prev={data['nifty_prev_close']:.2f}, move={data['nifty_day_return_pct']:+.2f}%, vix={data.get('india_vix')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
