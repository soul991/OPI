#!/usr/bin/env python3
"""Download all high-authority raw IPO datasets from official/verified repositories and APIs.

Saves into data/raw/:
1. Moneycontrol Mainline IPOs JSON/CSV (2020-2026)
2. samip9898 Indian_IPO_Data.csv (BSE/NSE exchange archives 2006-2020)
3. bansal28 master_ipo_dataset.csv (2019-2026 thesis dataset)
4. bansal28 raw_ipo_details.csv (fundamental & subscription details)
5. bansal28 raw_gmp_data.csv (418 IPOs with Grey Market Premium)
6. bansal28 chittorgarh/*.csv (yearly scraped Chittorgarh mainboard reports 2019-2026)
7. saqibsafdar Indian_IPO_Market_Data.csv (2010-2022)

Usage: python scripts/download_all_raw_data.py
"""
import os
import json
import requests
import pandas as pd

RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(os.path.join(RAW_DIR, "chittorgarh"), exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Origin": "https://www.moneycontrol.com",
    "Referer": "https://www.moneycontrol.com/"
}

def download_moneycontrol():
    print("Fetching Moneycontrol Mainline IPOs (2020-2026)...")
    all_ipos = []
    for start in range(0, 1500, 100):
        url = f"https://api.moneycontrol.com/mcapi/v1/ipo/get-listed-ipo?start={start}&limit=100"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            data = r.json().get("data", {}).get("listedIpo", [])
            if not data:
                break
            for item in data:
                all_ipos.append(item)
            if len(data) < 100:
                break
        except Exception as e:
            print(f"  Error at start={start}: {e}")
            break
    
    path_json = os.path.join(RAW_DIR, "moneycontrol_all.json")
    with open(path_json, "w") as f:
        json.dump(all_ipos, f, indent=2)
        
    df = pd.DataFrame(all_ipos)
    path_csv = os.path.join(RAW_DIR, "moneycontrol_all.csv")
    df.to_csv(path_csv, index=False)
    mainline_cnt = len(df[df["ipo_type"] == "Mainline"]) if "ipo_type" in df.columns else 0
    print(f"  Saved {len(all_ipos)} IPOs ({mainline_cnt} Mainline) to {path_csv}")

def download_samip():
    print("Fetching samip9898 Indian_IPO_Data.csv (BSE/NSE archives)...")
    url = "https://raw.githubusercontent.com/samip9898/Data-Analysis-of-Indian-stock-market-IPOs/master/Indian_IPO_Data.csv"
    r = requests.get(url, timeout=20)
    path = os.path.join(RAW_DIR, "samip_indian_ipo_data.csv")
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"  Saved samip dataset ({len(r.content)} bytes) to {path}")

def download_bansal():
    print("Fetching bansal28 thesis datasets...")
    files = {
        "master_ipo_dataset.csv": "https://raw.githubusercontent.com/bansal28/IPO_prediction_thesis/main/data/processed/master_ipo_dataset.csv",
        "raw_ipo_details.csv": "https://raw.githubusercontent.com/bansal28/IPO_prediction_thesis/main/data/raw/raw_ipo_details.csv",
        "raw_gmp_data.csv": "https://raw.githubusercontent.com/bansal28/IPO_prediction_thesis/main/data/raw/raw_gmp_data.csv",
    }
    for fname, url in files.items():
        r = requests.get(url, timeout=20)
        path = os.path.join(RAW_DIR, f"bansal_{fname}")
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"  Saved {fname} ({len(r.content)} bytes)")

    # Chittorgarh yearly reports in bansal repo
    years = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
    for y in years:
        if y in [2019, 2020]:
            c_name = f"ipo-performance-all-{y}.csv"
        else:
            c_name = f"ipo-performance-mainline-{y}.csv"
        url = f"https://raw.githubusercontent.com/bansal28/IPO_prediction_thesis/main/data/raw/chittorgarh/{c_name}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            path = os.path.join(RAW_DIR, "chittorgarh", c_name)
            with open(path, "wb") as f:
                f.write(r.content)
            print(f"  Saved Chittorgarh {y} report ({len(r.content)} bytes)")

def download_saqib():
    print("Fetching saqibsafdar Indian_IPO_Market_Data.csv...")
    url = "https://raw.githubusercontent.com/saqibsafdar11/Predicting-Listing-Gains-in-the-Indian-IPO-Market/master/Indian_IPO_Market_Data.csv"
    r = requests.get(url, timeout=15)
    path = os.path.join(RAW_DIR, "saqib_ipo_data.csv")
    with open(path, "wb") as f:
        f.write(r.content)
    print(f"  Saved saqib dataset ({len(r.content)} bytes) to {path}")

if __name__ == "__main__":
    download_moneycontrol()
    download_samip()
    download_bansal()
    download_saqib()
    print("\nAll raw sources downloaded successfully.")
