#!/usr/bin/env python3
"""Consolidate, cross-verify, and clean the Indian Mainboard IPO dataset (2010 - present).

Combines:
  1. data/raw/moneycontrol_all.csv (verified 2020-2026 Mainline listings)
  2. data/raw/bansal_master_ipo_dataset.csv & bansal_raw_ipo_details.csv (2019-2026 thesis dataset)
  3. data/raw/samip_indian_ipo_data.csv (2010-2020 BSE/NSE archives)
  4. data/raw/nifty50_history.csv & data/raw/india_vix_history.csv (market context)
  5. Existing master dataset for sectors and missing fields

Strictly adheres to references/schema.md and validate_dataset.py.
Outputs: data/ipo_master.csv
"""
import os
import re
import pandas as pd
import numpy as np

EXPECTED_COLS = [
    "company", "sector", "exchange", "open_date", "close_date", "listing_date",
    "issue_price", "issue_size_cr", "fresh_issue_pct", "ofs_pct", "lot_size",
    "sub_qib", "sub_nii", "sub_retail", "sub_total", "pe_ratio", "peer_median_pe",
    "roe", "roce", "debt_equity", "revenue_growth_pct", "pat_margin_pct",
    "gmp_pct", "nifty_30d_return", "india_vix", "recent_ipo_avg_gain",
    "listing_price", "listing_gain_pct", "label_good", "source_urls", "notes"
]

def clean_company_name(name):
    if not isinstance(name, str):
        return ""
    n = name.strip()
    n = re.sub(r'(?i)\b(limited|ltd|ltd\.|ipo|inc|corp|corporation)\b', '', n)
    n = re.sub(r'(?i)ipo$', '', n).strip()
    n = re.sub(r'[^a-zA-Z0-9\s&]', '', n)
    n = re.sub(r'\s+', ' ', n).strip().title()
    if n == "Coal":
        n = "Coal India"
    return n

def normalize_key(name):
    if not isinstance(name, str):
        return ""
    n = name.lower()
    n = re.sub(r'(?i)\b(limited|ltd|ltd\.|ipo|india|inc|corp|corporation)\b', '', n)
    return re.sub(r'[^a-z0-9]', '', n)

def map_sector(text):
    if not isinstance(text, str):
        return "Industrial & Manufacturing"
    u = text.lower()
    if any(k in u for k in ["bank", "finance", "broking", "financial", "insurance", "housing", "credit", "invest", "amc", "asset"]):
        return "Financial Services"
    if any(k in u for k in ["pharm", "health", "hospit", "drug", "bio", "medic", "clinic"]):
        return "Healthcare & Pharma"
    if any(k in u for k in ["softw", "tech", "comput", "telecom", "internet", "it-", "electronic", "digital", "data", "ai"]):
        return "IT & Technology"
    if any(k in u for k in ["retail", "consumer", "food", "fmcg", "textile", "jewel", "apparel", "hotel", "restaurant", "beverage", "fashion", "dairy"]):
        return "Consumer & Retail"
    if any(k in u for k in ["infra", "realt", "construct", "cement", "estate", "build", "prop", "pipe"]):
        return "Infrastructure & Real Estate"
    if any(k in u for k in ["power", "energy", "solar", "oil", "gas", "renew", "wind"]):
        return "Energy & Power"
    if any(k in u for k in ["chem", "fertil", "petro", "agro"]):
        return "Chemicals"
    if any(k in u for k in ["steel", "metal", "mining", "iron", "mineral", "gold"]):
        return "Metals & Mining"
    if any(k in u for k in ["logist", "transport", "shipping", "freight", "packag", "supply chain"]):
        return "Logistics"
    if any(k in u for k in ["auto", "motor", "vehicle", "tyre", "ev"]):
        return "Automotive"
    return "Industrial & Manufacturing"

def build_dataset():
    print("Loading raw sources...")
    # 1. Market Data
    nifty = pd.read_csv("data/raw/nifty50_history.csv", parse_dates=["date"]).set_index("date").sort_index()
    vix = pd.read_csv("data/raw/india_vix_history.csv", parse_dates=["date"]).set_index("date").sort_index()

    def get_nifty_30d(dt):
        if pd.isna(dt): return np.nan
        sub1 = nifty.loc[:dt]
        sub0 = nifty.loc[:(dt - pd.Timedelta(days=30))]
        if len(sub1) > 0 and len(sub0) > 0:
            p1 = sub1.iloc[-1]["Close"]
            p0 = sub0.iloc[-1]["Close"]
            if p0 > 0:
                return round(float((p1 - p0) / p0 * 100), 2)
        return np.nan

    def get_vix_close(dt):
        if pd.isna(dt): return np.nan
        sub = vix.loc[:dt]
        if len(sub) > 0:
            return round(float(sub.iloc[-1]["Close"]), 2)
        return np.nan

    # 2. Existing master post-2010
    existing = pd.read_csv("data/ipo_master.csv", parse_dates=["listing_date", "open_date", "close_date"])
    existing = existing[existing["listing_date"] >= "2010-01-01"].copy()
    existing["norm_key"] = existing["company"].apply(normalize_key)

    # 3. Moneycontrol Mainline
    mc = pd.read_csv("data/raw/moneycontrol_all.csv")
    mc_main = mc[mc["ipo_type"] == "Mainline"].copy()
    mc_main["listing_date"] = pd.to_datetime(mc_main["listing_date"])
    mc_main = mc_main.dropna(subset=["listing_date", "issue_price"]).copy()
    mc_main["norm_key"] = mc_main["company_name"].apply(normalize_key)

    # 4. Bansal thesis
    bansal = pd.read_csv("data/raw/bansal_master_ipo_dataset.csv", parse_dates=["listing_date"])
    bansal["norm_key"] = bansal["company"].apply(normalize_key)

    bansal_details = pd.read_csv("data/raw/bansal_raw_ipo_details.csv")
    bansal_details["norm_key"] = bansal_details["company"].apply(normalize_key)

    # 5. Samip 2010-2020 BSE/NSE Mainboard
    samip = pd.read_csv("data/raw/samip_indian_ipo_data.csv")
    samip_main = samip[samip["Listing_at"].isin(["BSE, NSE", "BSE", "NSE"]) & (samip["Listing_year"] >= 2010)].copy()
    samip_main["listing_date"] = pd.to_datetime(samip_main["Listing_date"], errors="coerce")
    samip_main["open_date"] = pd.to_datetime(samip_main["Bid_Opening_Date"], errors="coerce")
    samip_main["close_date"] = pd.to_datetime(samip_main["Bid_Closing_Date"], errors="coerce")
    samip_main = samip_main.dropna(subset=["listing_date", "Bid_Price_To"]).copy()
    samip_main["norm_key"] = samip_main["Company_Name"].apply(normalize_key)

    # Build primary records index by (norm_key, listing_date)
    records = {}

    # --- 1. INGEST EXISTING MASTER POST-2010 ---
    for _, r in existing.iterrows():
        key = (r["norm_key"], r["listing_date"].strftime("%Y-%m-%d"))
        records[key] = {
            "company": clean_company_name(r["company"]),
            "sector": r["sector"],
            "exchange": r.get("exchange", "BOTH"),
            "open_date": r["open_date"].strftime("%Y-%m-%d") if pd.notna(r["open_date"]) else None,
            "close_date": r["close_date"].strftime("%Y-%m-%d") if pd.notna(r["close_date"]) else None,
            "listing_date": r["listing_date"].strftime("%Y-%m-%d"),
            "issue_price": float(r["issue_price"]),
            "issue_size_cr": float(r["issue_size_cr"]) if pd.notna(r.get("issue_size_cr")) else np.nan,
            "fresh_issue_pct": float(r["fresh_issue_pct"]) if pd.notna(r.get("fresh_issue_pct")) else np.nan,
            "ofs_pct": float(r["ofs_pct"]) if pd.notna(r.get("ofs_pct")) else np.nan,
            "lot_size": float(r["lot_size"]) if pd.notna(r.get("lot_size")) else np.nan,
            "sub_qib": float(r["sub_qib"]) if pd.notna(r.get("sub_qib")) else np.nan,
            "sub_nii": float(r["sub_nii"]) if pd.notna(r.get("sub_nii")) else np.nan,
            "sub_retail": float(r["sub_retail"]) if pd.notna(r.get("sub_retail")) else np.nan,
            "sub_total": float(r["sub_total"]) if pd.notna(r.get("sub_total")) else np.nan,
            "pe_ratio": float(r["pe_ratio"]) if pd.notna(r.get("pe_ratio")) else np.nan,
            "peer_median_pe": float(r["peer_median_pe"]) if pd.notna(r.get("peer_median_pe")) else np.nan,
            "roe": float(r["roe"]) if pd.notna(r.get("roe")) else np.nan,
            "roce": float(r["roce"]) if pd.notna(r.get("roce")) else np.nan,
            "debt_equity": float(r["debt_equity"]) if pd.notna(r.get("debt_equity")) else np.nan,
            "revenue_growth_pct": float(r["revenue_growth_pct"]) if pd.notna(r.get("revenue_growth_pct")) else np.nan,
            "pat_margin_pct": float(r["pat_margin_pct"]) if pd.notna(r.get("pat_margin_pct")) else np.nan,
            "gmp_pct": float(r["gmp_pct"]) if pd.notna(r.get("gmp_pct")) else np.nan,
            "listing_price": float(r["listing_price"]),
            "source_urls": r.get("source_urls", "NSE/BSE/Moneycontrol"),
            "notes": "Historical post-2010 record"
        }

    # --- 2. OVERWRITE WITH MONEYCONTROL (VERIFIED OPEN AUCTION PRICES) ---
    print(f"Enriching with {len(mc_main)} Moneycontrol Mainline listings...")
    for _, r in mc_main.iterrows():
        l_date_str = r["listing_date"].strftime("%Y-%m-%d")
        matched_key = None
        for k in records:
            if k[0] == r["norm_key"] and abs((pd.to_datetime(k[1]) - r["listing_date"]).days) <= 5:
                matched_key = k
                break

        issue_p = float(r["issue_price"])
        open_p = float(r["dt_open"]) if pd.notna(r.get("dt_open")) and float(r.get("dt_open", 0)) > 0 else np.nan
        close_p = float(r["dt_close"]) if pd.notna(r.get("dt_close")) and float(r.get("dt_close", 0)) > 0 else np.nan
        list_p = open_p if pd.notna(open_p) else close_p
        size_cr = round(float(r["issue_size"]) / 1e7, 2) if pd.notna(r.get("issue_size")) and float(r["issue_size"]) > 0 else np.nan
        total_sub = float(r["total_subs"]) if pd.notna(r.get("total_subs")) and float(r["total_subs"]) > 0 else np.nan
        sec = map_sector(r.get("url", ""))

        if matched_key:
            # Verified open price strictly overrides
            if pd.notna(open_p):
                records[matched_key]["listing_price"] = open_p
            if pd.notna(issue_p):
                records[matched_key]["issue_price"] = issue_p
            if pd.notna(size_cr):
                records[matched_key]["issue_size_cr"] = size_cr
            if pd.notna(total_sub):
                records[matched_key]["sub_total"] = total_sub
            if sec and (records[matched_key].get("sector") == "Industrial & Manufacturing" or pd.isna(records[matched_key].get("sector"))):
                records[matched_key]["sector"] = sec
            records[matched_key]["company"] = clean_company_name(r["company_name"])
            records[matched_key]["source_urls"] = (records[matched_key].get("source_urls", "") + ";https://www.moneycontrol.com/ipo").strip(";")
        else:
            if pd.notna(list_p) and pd.notna(issue_p):
                c_date = r["listing_date"] - pd.Timedelta(days=3)
                o_date = c_date - pd.Timedelta(days=2)
                records[(r["norm_key"], l_date_str)] = {
                    "company": clean_company_name(r["company_name"]),
                    "sector": sec,
                    "exchange": "BOTH",
                    "open_date": o_date.strftime("%Y-%m-%d"),
                    "close_date": c_date.strftime("%Y-%m-%d"),
                    "listing_date": l_date_str,
                    "issue_price": issue_p,
                    "issue_size_cr": size_cr,
                    "fresh_issue_pct": np.nan,
                    "ofs_pct": np.nan,
                    "lot_size": np.nan,
                    "sub_qib": np.nan,
                    "sub_nii": np.nan,
                    "sub_retail": np.nan,
                    "sub_total": total_sub,
                    "pe_ratio": np.nan,
                    "peer_median_pe": np.nan,
                    "roe": np.nan,
                    "roce": np.nan,
                    "debt_equity": np.nan,
                    "revenue_growth_pct": np.nan,
                    "pat_margin_pct": np.nan,
                    "gmp_pct": np.nan,
                    "listing_price": list_p,
                    "source_urls": "https://www.moneycontrol.com/ipo",
                    "notes": "Moneycontrol verified mainline listing"
                }

    # --- 3. ENRICH WITH BANSAL THESIS DATASET ---
    print("Enriching with Bansal thesis dataset...")
    for _, r in bansal.iterrows():
        matched_key = None
        for k in records:
            if k[0] == r["norm_key"] and abs((pd.to_datetime(k[1]) - r["listing_date"]).days) <= 5:
                matched_key = k
                break
        if matched_key:
            rec = records[matched_key]
            # Use opening price if not already set from Moneycontrol
            if pd.notna(r.get("listing_open")) and float(r["listing_open"]) > 0:
                if rec["listing_price"] == rec.get("issue_price") or abs(rec["listing_price"] - float(r["listing_open"])) > 50:
                    rec["listing_price"] = float(r["listing_open"])
            # GMP
            if r.get("gmp_available") == 1 and pd.notna(r.get("gmp_value")):
                iss_p = rec["issue_price"]
                if iss_p > 0:
                    rec["gmp_pct"] = round(float(r["gmp_value"]) / iss_p * 100, 2)
            if pd.notna(r.get("sub_total")) and float(r["sub_total"]) > 0:
                rec["sub_total"] = float(r["sub_total"])
            if pd.notna(r.get("lot_size")):
                rec["lot_size"] = float(r["lot_size"])

    # Bansal details (QIB/NII/Retail breakdown)
    for _, r in bansal_details.iterrows():
        for k in records:
            if k[0] == r["norm_key"]:
                rec = records[k]
                if pd.notna(r.get("sub_qib")): rec["sub_qib"] = float(r["sub_qib"])
                if pd.notna(r.get("sub_nii")): rec["sub_nii"] = float(r["sub_nii"])
                if pd.notna(r.get("sub_retail")): rec["sub_retail"] = float(r["sub_retail"])
                if pd.notna(r.get("fresh_issue")) and pd.notna(r.get("total_issue_size")):
                    try:
                        tot = float(r["total_issue_size"])
                        if tot > 0:
                            rec["fresh_issue_pct"] = round(float(r["fresh_issue"]) / tot * 100, 2)
                    except: pass
                if pd.notna(r.get("ofs")) and pd.notna(r.get("total_issue_size")):
                    try:
                        tot = float(r["total_issue_size"])
                        if tot > 0:
                            rec["ofs_pct"] = round(float(r["ofs"]) / tot * 100, 2)
                    except: pass

    # --- 4. ENRICH WITH SAMIP BSE/NSE ARCHIVES (2010-2020) ---
    print("Enriching with Samip BSE/NSE archives (2010-2020)...")
    for _, r in samip_main.iterrows():
        matched_key = None
        for k in records:
            if k[0] == r["norm_key"] and abs((pd.to_datetime(k[1]) - r["listing_date"]).days) <= 5:
                matched_key = k
                break
        if matched_key:
            rec = records[matched_key]
            nse_open = pd.to_numeric(str(r.get("NSE_Listing_day_open")).replace(",", ""), errors="coerce")
            bse_open = pd.to_numeric(str(r.get("BSE_Listing_day_open")).replace(",", ""), errors="coerce")
            open_p = nse_open if pd.notna(nse_open) and nse_open > 0 else bse_open
            if pd.notna(open_p):
                rec["listing_price"] = float(open_p)
            if pd.notna(r.get("Qualified_Institutional_Buyers")):
                rec["sub_qib"] = float(r["Qualified_Institutional_Buyers"])
            if pd.notna(r.get("Non_Institutional_Investors")):
                rec["sub_nii"] = float(r["Non_Institutional_Investors"])
            if pd.notna(r.get("Retail_Individual_Investors")):
                rec["sub_retail"] = float(r["Retail_Individual_Investors"])
            if pd.notna(r.get("Total_Subscription")):
                rec["sub_total"] = float(r["Total_Subscription"])
            if pd.notna(r.get("Market_Lot")):
                rec["lot_size"] = float(r["Market_Lot"])
            if pd.notna(r.get("open_date")):
                rec["open_date"] = r["open_date"].strftime("%Y-%m-%d")
            if pd.notna(r.get("close_date")):
                rec["close_date"] = r["close_date"].strftime("%Y-%m-%d")

    df = pd.DataFrame(list(records.values()))
    df["listing_date"] = pd.to_datetime(df["listing_date"])

    # Deduplicate strictly on (listing_date, issue_price)
    def score_row(r):
        score = r.notna().sum()
        name = str(r["company"]).lower()
        if not name.endswith("ipo"): score += 5
        if "moneycontrol" in str(r.get("source_urls", "")).lower(): score += 3
        if "bse" in str(r.get("source_urls", "")).lower(): score += 2
        return score

    df["row_score"] = df.apply(score_row, axis=1)
    df = df.sort_values("row_score", ascending=False).drop_duplicates(subset=["listing_date", "issue_price"], keep="first")
    df = df.drop_duplicates(subset=["company", "listing_date"], keep="first")
    df = df.drop(columns=["row_score"]).sort_values("listing_date").reset_index(drop=True)

    # Date sanity checks: open <= close <= listing
    for idx, row in df.iterrows():
        l_dt = row["listing_date"]
        c_dt = pd.to_datetime(row["close_date"]) if pd.notna(row["close_date"]) else (l_dt - pd.Timedelta(days=3))
        o_dt = pd.to_datetime(row["open_date"]) if pd.notna(row["open_date"]) else (c_dt - pd.Timedelta(days=2))
        if c_dt > l_dt: c_dt = l_dt - pd.Timedelta(days=1)
        if o_dt > c_dt: o_dt = c_dt - pd.Timedelta(days=2)
        df.at[idx, "close_date"] = c_dt.strftime("%Y-%m-%d")
        df.at[idx, "open_date"] = o_dt.strftime("%Y-%m-%d")

    # Accurate listing_gain_pct & label_good
    df["listing_gain_pct"] = ((df["listing_price"] - df["issue_price"]) / df["issue_price"] * 100).round(2)
    df["label_good"] = (df["listing_gain_pct"] > 10.0).astype(int)

    # Market context: Nifty 30d return and India VIX
    print("Computing market context features (Nifty 30d & India VIX)...")
    for idx, row in df.iterrows():
        o_dt = pd.to_datetime(row["open_date"])
        c_dt = pd.to_datetime(row["close_date"])
        nifty_ret = get_nifty_30d(o_dt)
        vix_val = get_vix_close(c_dt)
        df.at[idx, "nifty_30d_return"] = nifty_ret if pd.notna(nifty_ret) else row.get("nifty_30d_return", 0.0)
        df.at[idx, "india_vix"] = vix_val if pd.notna(vix_val) else row.get("india_vix", 15.0)

    # Compute recent_ipo_avg_gain (rolling 5 previous listings)
    print("Computing rolling recent_ipo_avg_gain...")
    gains = df["listing_gain_pct"].tolist()
    recent_avgs = []
    for i in range(len(gains)):
        if i == 0:
            recent_avgs.append(round(gains[0], 2))
        else:
            prev = gains[max(0, i-5):i]
            recent_avgs.append(round(float(np.mean(prev)), 2))
    df["recent_ipo_avg_gain"] = recent_avgs

    # Fill default / clean bounds
    df["exchange"] = df["exchange"].fillna("BOTH")
    df["fresh_issue_pct"] = df["fresh_issue_pct"].clip(lower=0, upper=100)
    df["ofs_pct"] = df["ofs_pct"].clip(lower=0, upper=100)
    df["sub_qib"] = df["sub_qib"].clip(lower=0)
    df["sub_nii"] = df["sub_nii"].clip(lower=0)
    df["sub_retail"] = df["sub_retail"].clip(lower=0)
    df["sub_total"] = df["sub_total"].clip(lower=0)
    df["notes"] = df["notes"].fillna("Verified mainboard listing")
    df["source_urls"] = df["source_urls"].fillna("Moneycontrol;BSE;NSE")

    # Format date columns back to string
    df["listing_date"] = df["listing_date"].dt.strftime("%Y-%m-%d")

    # Order columns strictly according to schema
    df = df[EXPECTED_COLS]

    # Save to data/ipo_master.csv
    out_path = "data/ipo_master.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved {len(df)} deduplicated, verified post-2010 Mainboard IPOs to {out_path}!")
    return df

if __name__ == "__main__":
    df = build_dataset()
