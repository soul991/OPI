#!/usr/bin/env python3
"""Fetch Nifty 50 and India VIX historical data using yfinance.

Outputs:
  data/raw/nifty50_history.csv   – daily OHLCV for Nifty 50
  data/raw/india_vix_history.csv – daily OHLCV for India VIX

Usage: python scripts/fetch_market_data.py
"""
import os
import pandas as pd
import yfinance as yf

OUT_DIR = "data/raw"

def fetch_nifty():
    """Download Nifty 50 daily history from 2009-01-01 to today."""
    print("Fetching Nifty 50 history (^NSEI)...")
    nifty = yf.download("^NSEI", start="2009-01-01", progress=False)
    # Flatten multi-level columns if present
    if isinstance(nifty.columns, pd.MultiIndex):
        nifty.columns = nifty.columns.get_level_values(0)
    nifty.index.name = "date"
    path = os.path.join(OUT_DIR, "nifty50_history.csv")
    nifty.to_csv(path)
    print(f"  Saved {len(nifty)} rows to {path}")
    return nifty

def fetch_vix():
    """Download India VIX daily history from 2009-01-01 to today."""
    print("Fetching India VIX history (^INDIAVIX)...")
    vix = yf.download("^INDIAVIX", start="2009-01-01", progress=False)
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = vix.columns.get_level_values(0)
    vix.index.name = "date"
    path = os.path.join(OUT_DIR, "india_vix_history.csv")
    vix.to_csv(path)
    print(f"  Saved {len(vix)} rows to {path}")
    return vix

def compute_nifty_30d_return(nifty_df):
    """Precompute 30-calendar-day trailing returns for fast lookup."""
    close = nifty_df[["Close"]].copy()
    close.index = pd.to_datetime(close.index)
    close = close.sort_index()
    # For each date, compute return vs 30 calendar days earlier
    close["close_30d_ago"] = close["Close"].shift(22)  # ~22 trading days ≈ 30 calendar days
    close["nifty_30d_return"] = ((close["Close"] - close["close_30d_ago"]) / close["close_30d_ago"] * 100).round(2)
    path = os.path.join(OUT_DIR, "nifty_30d_returns.csv")
    close[["nifty_30d_return"]].dropna().to_csv(path)
    print(f"  Saved Nifty 30d returns to {path}")

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    nifty = fetch_nifty()
    vix = fetch_vix()
    compute_nifty_30d_return(nifty)
    print("\nDone. Market data ready for enrichment.")
