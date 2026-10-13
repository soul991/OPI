#!/usr/bin/env python3
"""
Automated collector and enricher for Indian Mainboard IPOs (2006 - 2026).
Compiles historical data from verified archives, cleans and harmonizes features,
fetches market context (Nifty 50 30-day return, India VIX) via Yahoo Finance,
and outputs a purified data/ipo_master.csv adhering to references/schema.md.
"""

import re
import difflib
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def clean_company_name(name):
    """Normalize company name for matching and deduplication."""
    s = str(name).strip()
    s = re.sub(r"\(.*?\)", "", s)  # Remove parenthetical info e.g. (NTPC FPO)
    s = re.sub(r"(?i)\s+ipo\b", "", s)
    s = re.sub(r"(?i)\b(ltd|limited|pvt|private|co|the|corp|corporation|inc)\b", "", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip().title()
    return s

def classify_sector(name):
    """Assign broad industry sector based on company name keywords."""
    name_lower = str(name).lower()
    if any(k in name_lower for k in ['bank', 'finan', 'capital', 'holdings', 'invest', 'insurance', 'wealth', 'credit', 'securities', 'amc']):
        return 'Financial Services'
    if any(k in name_lower for k in ['pharma', 'health', 'hospital', 'medic', 'bio', 'drug', 'diagnost', 'cure', 'life science', 'lab', 'remed']):
        return 'Healthcare & Pharma'
    if any(k in name_lower for k in ['tech', 'soft', 'info', 'digital', 'data', 'cloud', 'system', 'cyber', 'telecom', 'online']):
        return 'IT & Technology'
    if any(k in name_lower for k in ['chem', 'fertiliz', 'carbon', 'poly', 'petro']):
        return 'Chemicals'
    if any(k in name_lower for k in ['power', 'energy', 'oil', 'gas', 'solar', 'wind', 'renew']):
        return 'Energy & Power'
    if any(k in name_lower for k in ['auto', 'motor', 'tyre', 'tire', 'vehicle', 'automotive']):
        return 'Automotive'
    if any(k in name_lower for k in ['infra', 'build', 'construct', 'realty', 'estate', 'cement', 'pipe', 'engineer', 'project']):
        return 'Infrastructure & Real Estate'
    if any(k in name_lower for k in ['food', 'fmcg', 'retail', 'jewel', 'fashion', 'beverag', 'hotel', 'restaur', 'consumer', 'dairy', 'agro']):
        return 'Consumer & Retail'
    if any(k in name_lower for k in ['steel', 'metal', 'iron', 'copper', 'alumin', 'wire', 'cable', 'mineral', 'mine', 'forge']):
        return 'Metals & Mining'
    if any(k in name_lower for k in ['logistic', 'transport', 'cargo', 'freight', 'port', 'ship', 'air']):
        return 'Logistics'
    return 'Industrial & Manufacturing'

def extract_cr(val):
    """Extract INR Crores from text string."""
    if pd.isna(val): return None
    s = str(val).replace(',', '')
    m = re.search(r'[₹Rs\.]*\s*([0-9\.]+)\s*(?:Cr|cr|Crores|crores)', s)
    if m:
        try: return float(m.group(1))
        except: pass
    m = re.search(r'aggregating up to\s*[₹Rs\.]*\s*([0-9\.]+)', s)
    if m:
        try: return float(m.group(1))
        except: pass
    try:
        f = float(s)
        return f if f > 0 else None
    except:
        return None

def main():
    print("Step 1: Downloading primary raw datasets...")
    # Source 1: 2006-2020 historical mainboard dataset (samip9898)
    url_d1 = 'https://raw.githubusercontent.com/samip9898/Data-Analysis-of-Indian-stock-market-IPOs/master/Indian_IPO_Data.csv'
    d1 = pd.read_csv(url_d1)
    
    # Source 2: 2021 IPOs dataset (shubhankar-rai)
    url_d3 = 'https://raw.githubusercontent.com/shubhankar-rai/indian-stock-ipo-data-analysis/master/IPO.csv'
    d3 = pd.read_csv(url_d3)
    
    # Source 3: Dec 2021 supplement (saqibsafdar11)
    url_d2 = 'https://raw.githubusercontent.com/saqibsafdar11/Predicting-Listing-Gains-in-the-Indian-IPO-Market/main/Indian_IPO_Market_Data.csv'
    d2 = pd.read_csv(url_d2)
    d2.columns = [c.strip() for c in d2.columns]
    
    # Source 4: 2022-2026 recent mainboard dataset (abhnxvj)
    url_d4 = 'https://raw.githubusercontent.com/abhnxvj/ipo-listing-gain-predictor/main/data/raw/ipo_data.csv'
    d4 = pd.read_csv(url_d4)
    feat_d4 = pd.read_csv('https://raw.githubusercontent.com/abhnxvj/ipo-listing-gain-predictor/main/data/processed/ipo_features.csv')
    
    print("Step 2: Processing 2006-2020 dataset...")
    # Filter for Mainboard: NSE or BSE listing open present, and exclude SME rows
    d1_main = d1[d1['NSE_Listing_day_open'].notna() | d1['BSE_Listing_day_open'].notna()].copy()
    # Exclude FPOs
    d1_main = d1_main[~d1_main['Company_Name'].str.contains(r'\bFPO\b', case=False, na=False)].copy()
    
    rows_d1 = []
    for _, r in d1_main.iterrows():
        comp_raw = r['Company_Name']
        comp_clean = clean_company_name(comp_raw)
        
        open_d = pd.to_datetime(r['Bid_Opening_Date'], errors='coerce')
        close_d = pd.to_datetime(r['Bid_Closing_Date'], errors='coerce')
        list_d = pd.to_datetime(r['Listing_date'], errors='coerce')
        
        # Known typo fix for 20 Microns Ltd (listed on Oct 6, 2008, not Sep 6)
        if '20 Microns' in comp_clean and list_d == pd.Timestamp('2008-09-06'):
            list_d = pd.Timestamp('2008-10-06')
            
        if pd.isna(list_d):
            continue
        if pd.isna(close_d):
            close_d = list_d - pd.Timedelta(days=6)
        if pd.isna(open_d):
            open_d = close_d - pd.Timedelta(days=2)
            
        # Ensure chronological ordering
        if open_d > close_d:
            open_d = close_d - pd.Timedelta(days=2)
        if close_d > list_d:
            close_d = list_d - pd.Timedelta(days=3)
        if open_d > close_d:
            open_d = close_d - pd.Timedelta(days=2)
            
        ip = pd.to_numeric(str(r['Bid_Price_To']).replace(',', ''), errors='coerce')
        if pd.isna(ip) or ip <= 0:
            ip = pd.to_numeric(str(r['Bid_Price_From']).replace(',', ''), errors='coerce')
        if pd.isna(ip) or ip <= 0:
            continue
            
        nse_open = pd.to_numeric(str(r['NSE_Listing_day_open']).replace(',', ''), errors='coerce')
        bse_open = pd.to_numeric(str(r['BSE_Listing_day_open']).replace(',', ''), errors='coerce')
        lp = nse_open if pd.notna(nse_open) and nse_open > 0 else bse_open
        if pd.isna(lp) or lp <= 0:
            continue
            
        issue_size = extract_cr(r['Issue_size'])
        lot = pd.to_numeric(str(r['Market_Lot']).replace(',', ''), errors='coerce')
        if pd.isna(lot) or lot <= 0:
            lot = round(15000 / ip) if ip > 0 else 1
            
        # Subscriptions
        sq = pd.to_numeric(str(r['Qualified_Institutional_Buyers']).replace(',', '').replace('x', ''), errors='coerce')
        sn = pd.to_numeric(str(r['Non_Institutional_Investors']).replace(',', '').replace('x', ''), errors='coerce')
        sr = pd.to_numeric(str(r['Retail_Individual_Investors']).replace(',', '').replace('x', ''), errors='coerce')
        st = pd.to_numeric(str(r['Total_Subscription']).replace(',', '').replace('x', ''), errors='coerce')
        
        # Outlier correction for HDFC AMC (row 857 entered raw share count)
        if 'Hdfc Asset' in comp_clean:
            sq, sn, sr, st = 192.26, 226.00, 6.78, 83.05
            
        # Fresh / OFS %
        fresh_cr = extract_cr(r['Fresh_issue'])
        ofs_cr = extract_cr(r['Offer_for_sale'])
        fresh_pct = round((fresh_cr / issue_size * 100), 2) if fresh_cr and issue_size and issue_size > 0 else np.nan
        ofs_pct = round((ofs_cr / issue_size * 100), 2) if ofs_cr and issue_size and issue_size > 0 else np.nan
        if pd.notna(fresh_pct): fresh_pct = max(0.0, min(100.0, fresh_pct))
        if pd.notna(ofs_pct): ofs_pct = max(0.0, min(100.0, ofs_pct))
        
        # Exchange
        exch_str = str(r['Listing_at']).upper()
        if 'BSE' in exch_str and 'NSE' in exch_str:
            exch = 'BOTH'
        elif 'NSE' in exch_str:
            exch = 'NSE'
        elif 'BSE' in exch_str:
            exch = 'BSE'
        else:
            exch = 'BOTH'
            
        rows_d1.append({
            'company': comp_clean,
            'sector': classify_sector(comp_clean),
            'exchange': exch,
            'open_date': open_d.strftime('%Y-%m-%d'),
            'close_date': close_d.strftime('%Y-%m-%d'),
            'listing_date': list_d.strftime('%Y-%m-%d'),
            'issue_price': round(float(ip), 2),
            'issue_size_cr': round(float(issue_size), 2) if issue_size else np.nan,
            'fresh_issue_pct': fresh_pct,
            'ofs_pct': ofs_pct,
            'lot_size': int(lot),
            'sub_qib': round(float(sq), 2) if pd.notna(sq) and sq >= 0 else np.nan,
            'sub_nii': round(float(sn), 2) if pd.notna(sn) and sn >= 0 else np.nan,
            'sub_retail': round(float(sr), 2) if pd.notna(sr) and sr >= 0 else np.nan,
            'sub_total': round(float(st), 2) if pd.notna(st) and st >= 0 else np.nan,
            'pe_ratio': np.nan,
            'peer_median_pe': np.nan,
            'roe': np.nan,
            'roce': np.nan,
            'debt_equity': np.nan,
            'revenue_growth_pct': np.nan,
            'pat_margin_pct': np.nan,
            'gmp_pct': np.nan,
            'listing_price': round(float(lp), 2),
            'source_urls': 'https://github.com/samip9898/Data-Analysis-of-Indian-stock-market-IPOs',
            'notes': 'Historical mainboard record (2006-2020)'
        })
        
    df1 = pd.DataFrame(rows_d1)
    print(f"Processed {len(df1)} clean records from 2006-2020.")
    
    print("Step 3: Processing 2021 dataset...")
    d3['dt'] = pd.to_datetime(d3['Date'], format='%d-%m-%y', errors='coerce')
    d3_2021 = d3[d3['dt'].dt.year == 2021].copy()
    
    rows_d3 = []
    for _, r in d3_2021.iterrows():
        comp_clean = clean_company_name(r['IPO_Name'])
        list_d = r['dt']
        if pd.isna(list_d): continue
        close_d = list_d - pd.Timedelta(days=6)
        open_d = close_d - pd.Timedelta(days=2)
        
        ip = pd.to_numeric(r['Issue_price'], errors='coerce')
        lp = pd.to_numeric(r['Listing_Open'], errors='coerce')
        if pd.isna(ip) or pd.isna(lp) or ip <= 0 or lp <= 0: continue
        
        sz = pd.to_numeric(r['Issue_Size(crores)'], errors='coerce')
        sq = pd.to_numeric(r['QIB'], errors='coerce')
        sn = pd.to_numeric(r['HNI'], errors='coerce')
        sr = pd.to_numeric(r['RII'], errors='coerce')
        st = (sq * 0.5 + sn * 0.15 + sr * 0.35) if pd.notna(sq) and pd.notna(sn) and pd.notna(sr) else np.nan
        
        lot = round(15000 / ip) if ip > 0 else 1
        
        rows_d3.append({
            'company': comp_clean,
            'sector': classify_sector(comp_clean),
            'exchange': 'BOTH',
            'open_date': open_d.strftime('%Y-%m-%d'),
            'close_date': close_d.strftime('%Y-%m-%d'),
            'listing_date': list_d.strftime('%Y-%m-%d'),
            'issue_price': round(float(ip), 2),
            'issue_size_cr': round(float(sz), 2) if pd.notna(sz) and sz > 0 else np.nan,
            'fresh_issue_pct': np.nan,
            'ofs_pct': np.nan,
            'lot_size': int(lot),
            'sub_qib': round(float(sq), 2) if pd.notna(sq) and sq >= 0 else np.nan,
            'sub_nii': round(float(sn), 2) if pd.notna(sn) and sn >= 0 else np.nan,
            'sub_retail': round(float(sr), 2) if pd.notna(sr) and sr >= 0 else np.nan,
            'sub_total': round(float(st), 2) if pd.notna(st) and st >= 0 else np.nan,
            'pe_ratio': np.nan,
            'peer_median_pe': np.nan,
            'roe': np.nan,
            'roce': np.nan,
            'debt_equity': np.nan,
            'revenue_growth_pct': np.nan,
            'pat_margin_pct': np.nan,
            'gmp_pct': np.nan,
            'listing_price': round(float(lp), 2),
            'source_urls': 'https://github.com/shubhankar-rai/indian-stock-ipo-data-analysis',
            'notes': '2021 mainboard record'
        })
    df3 = pd.DataFrame(rows_d3)
    print(f"Processed {len(df3)} clean records from 2021.")
    
    # Process Dec 2021 from d2 (saqibsafdar11)
    d2['dt'] = pd.to_datetime(d2['Date'], format='%d/%m/%y', errors='coerce')
    dec_2021 = d2[(d2['dt'] >= '2021-12-01') & (d2['dt'] <= '2021-12-31')].copy()
    rows_dec = []
    for _, r in dec_2021.iterrows():
        comp_clean = clean_company_name(r['IPOName'])
        list_d = r['dt']
        close_d = list_d - pd.Timedelta(days=6)
        open_d = close_d - pd.Timedelta(days=2)
        ip = float(r['Issue_Price'])
        gain = float(r['Listing_Gains_Percent'])
        lp = round(ip * (1 + gain / 100), 2)
        sz = float(r['Issue_Size'])
        sq = float(r['Subscription_QIB'])
        sn = float(r['Subscription_HNI'])
        sr = float(r['Subscription_RII'])
        st = float(r['Subscription_Total'])
        lot = round(15000 / ip) if ip > 0 else 1
        
        rows_dec.append({
            'company': comp_clean,
            'sector': classify_sector(comp_clean),
            'exchange': 'BOTH',
            'open_date': open_d.strftime('%Y-%m-%d'),
            'close_date': close_d.strftime('%Y-%m-%d'),
            'listing_date': list_d.strftime('%Y-%m-%d'),
            'issue_price': round(ip, 2),
            'issue_size_cr': round(sz, 2),
            'fresh_issue_pct': np.nan,
            'ofs_pct': np.nan,
            'lot_size': int(lot),
            'sub_qib': round(sq, 2),
            'sub_nii': round(sn, 2),
            'sub_retail': round(sr, 2),
            'sub_total': round(st, 2),
            'pe_ratio': np.nan,
            'peer_median_pe': np.nan,
            'roe': np.nan,
            'roce': np.nan,
            'debt_equity': np.nan,
            'revenue_growth_pct': np.nan,
            'pat_margin_pct': np.nan,
            'gmp_pct': np.nan,
            'listing_price': lp,
            'source_urls': 'https://github.com/saqibsafdar11/Predicting-Listing-Gains-in-the-Indian-IPO-Market',
            'notes': 'December 2021 supplement'
        })
    df_dec = pd.DataFrame(rows_dec)
    print(f"Processed {len(df_dec)} records from Dec 2021.")

    print("Step 4: Processing 2022-2026 dataset...")
    feat_map = dict(zip(feat_d4['company'], feat_d4['list_date']))
    d4['list_date'] = d4['company'].map(feat_map)
    manual = {
        'Deepak Builders & Engineers India Ltd.': '2024-10-28',
        'Manba FinanceIPO': '2024-09-30',
        'Mukka ProteinsIPO': '2024-03-07',
        'KisshtIPO': '2026-05-08',
        'Aeroplane Basmati RiceIPO': '2026-04-02'
    }
    for k, v in manual.items():
        d4.loc[d4['company'] == k, 'list_date'] = v
        
    rows_d4 = []
    for _, r in d4.iterrows():
        comp_clean = clean_company_name(r['company'])
        list_d = pd.to_datetime(r['list_date'])
        
        # In India, SEBI shifted to T+3 in Sept 2023
        if list_d >= pd.Timestamp('2023-09-01'):
            close_d = list_d - pd.Timedelta(days=3)
        else:
            close_d = list_d - pd.Timedelta(days=6)
        open_d = close_d - pd.Timedelta(days=2)
        
        ip = float(r['issue_price'])
        lp = float(r['listing_price'])
        sz = float(r['issue_size_cr']) if pd.notna(r['issue_size_cr']) else np.nan
        
        fresh_cr = float(r['fresh_issue_cr']) if pd.notna(r['fresh_issue_cr']) else np.nan
        ofs_cr = float(r['ofs_cr']) if pd.notna(r['ofs_cr']) else np.nan
        fresh_pct = round((fresh_cr / sz * 100), 2) if pd.notna(fresh_cr) and pd.notna(sz) and sz > 0 else np.nan
        ofs_pct = round((ofs_cr / sz * 100), 2) if pd.notna(ofs_cr) and pd.notna(sz) and sz > 0 else np.nan
        if pd.notna(fresh_pct): fresh_pct = max(0.0, min(100.0, fresh_pct))
        if pd.notna(ofs_pct): ofs_pct = max(0.0, min(100.0, ofs_pct))
        
        sq = float(r['sub_qib_x']) if pd.notna(r['sub_qib_x']) else np.nan
        sn = float(r['sub_hni_x']) if pd.notna(r['sub_hni_x']) else np.nan
        sr = float(r['sub_retail_x']) if pd.notna(r['sub_retail_x']) else np.nan
        st = float(r['total_sub_x']) if pd.notna(r['total_sub_x']) else np.nan
        
        pe = float(r['ipo_pe']) if pd.notna(r['ipo_pe']) and r['ipo_pe'] > 0 else np.nan
        peer_pe = float(r['peer_pe']) if pd.notna(r['peer_pe']) and r['peer_pe'] > 0 else np.nan
        de = float(r['debt_equity']) if pd.notna(r['debt_equity']) else np.nan
        
        # Last bidding day GMP (gmp_day3_pct)
        gmp = float(r['gmp_day3_pct']) if pd.notna(r['gmp_day3_pct']) else np.nan
        lot = round(15000 / ip) if ip > 0 else 1
        
        url_src = str(r['url']) if pd.notna(r['url']) else 'https://github.com/abhnxvj/ipo-listing-gain-predictor'
        
        rows_d4.append({
            'company': comp_clean,
            'sector': classify_sector(comp_clean),
            'exchange': 'BOTH',
            'open_date': open_d.strftime('%Y-%m-%d'),
            'close_date': close_d.strftime('%Y-%m-%d'),
            'listing_date': list_d.strftime('%Y-%m-%d'),
            'issue_price': round(ip, 2),
            'issue_size_cr': round(sz, 2) if pd.notna(sz) else np.nan,
            'fresh_issue_pct': fresh_pct,
            'ofs_pct': ofs_pct,
            'lot_size': int(lot),
            'sub_qib': round(sq, 2) if pd.notna(sq) and sq >= 0 else np.nan,
            'sub_nii': round(sn, 2) if pd.notna(sn) and sn >= 0 else np.nan,
            'sub_retail': round(sr, 2) if pd.notna(sr) and sr >= 0 else np.nan,
            'sub_total': round(st, 2) if pd.notna(st) and st >= 0 else np.nan,
            'pe_ratio': round(pe, 2) if pd.notna(pe) else np.nan,
            'peer_median_pe': round(peer_pe, 2) if pd.notna(peer_pe) else np.nan,
            'roe': np.nan,
            'roce': np.nan,
            'debt_equity': round(de, 2) if pd.notna(de) else np.nan,
            'revenue_growth_pct': np.nan,
            'pat_margin_pct': np.nan,
            'gmp_pct': round(gmp, 2) if pd.notna(gmp) else np.nan,
            'listing_price': round(lp, 2),
            'source_urls': url_src,
            'notes': f'2022-2026 issue (year {r["year"]})'
        })
    df4 = pd.DataFrame(rows_d4)
    print(f"Processed {len(df4)} clean records from 2022-2026.")
    
    # Step 5: Merge and Deduplicate
    print("Step 5: Merging and deduplicating...")
    master = pd.concat([df1, df3, df_dec, df4], ignore_index=True)
    master['listing_date_dt'] = pd.to_datetime(master['listing_date'])
    master = master.sort_values('listing_date_dt').reset_index(drop=True)
    
    # Deduplicate on (company, listing_date) keeping row with fewest NaNs
    master['null_count'] = master.isna().sum(axis=1)
    master = master.sort_values(['company', 'listing_date', 'null_count']).drop_duplicates(subset=['company', 'listing_date'], keep='first')
    master = master.sort_values('listing_date_dt').reset_index(drop=True)
    
    print(f"Total merged unique IPO records: {len(master)}")
    
    # Step 6: Derive Targets and Math
    print("Step 6: Deriving listing gain and labels...")
    master['listing_gain_pct'] = ((master['listing_price'] - master['issue_price']) / master['issue_price'] * 100).round(2)
    master['label_good'] = (master['listing_gain_pct'] > 10.0).astype(int)
    
    # Step 7: Fetch Market Context (Nifty 50 and India VIX)
    print("Step 7: Fetching Nifty 50 & India VIX via Yahoo Finance...")
    min_date = (pd.to_datetime(master['open_date'].min()) - timedelta(days=45)).strftime('%Y-%m-%d')
    max_date = (pd.to_datetime(master['listing_date'].max()) + timedelta(days=5)).strftime('%Y-%m-%d')
    
    nifty_df = yf.download('^NSEI', start=min_date, end=max_date, progress=False)
    vix_df = yf.download('^INDIAVIX', start=min_date, end=max_date, progress=False)
    
    nifty_close = nifty_df['Close'].squeeze()
    vix_close = vix_df['Close'].squeeze()
    
    nifty_series = pd.Series(nifty_close.values, index=pd.to_datetime(nifty_close.index).tz_localize(None).normalize())
    vix_series = pd.Series(vix_close.values, index=pd.to_datetime(vix_close.index).tz_localize(None).normalize())
    
    def get_nifty_30d(open_d_str):
        d = pd.to_datetime(open_d_str).normalize()
        d_prior = d - timedelta(days=30)
        # Find closest available date on or before
        avail_now = nifty_series[nifty_series.index <= d]
        avail_prior = nifty_series[nifty_series.index <= d_prior]
        if len(avail_now) > 0 and len(avail_prior) > 0:
            c_now = avail_now.iloc[-1]
            c_prior = avail_prior.iloc[-1]
            if c_prior > 0:
                return round(float((c_now - c_prior) / c_prior * 100), 2)
        return np.nan

    def get_vix(close_d_str):
        d = pd.to_datetime(close_d_str).normalize()
        avail = vix_series[vix_series.index <= d]
        if len(avail) > 0:
            return round(float(avail.iloc[-1]), 2)
        return np.nan

    master['nifty_30d_return'] = master['open_date'].apply(get_nifty_30d)
    master['india_vix'] = master['close_date'].apply(get_vix)
    
    # Step 8: Compute rolling recent_ipo_avg_gain
    print("Step 8: Computing recent_ipo_avg_gain (previous 5 IPOs)...")
    recent_gains = []
    for idx, row in master.iterrows():
        open_d = row['open_date']
        # Find strictly earlier listed IPOs
        prior = master.iloc[:idx]
        prior_valid = prior[prior['listing_date'] <= open_d]['listing_gain_pct']
        if len(prior_valid) >= 1:
            recent_gains.append(round(float(prior_valid.tail(5).mean()), 2))
        else:
            recent_gains.append(np.nan)
    master['recent_ipo_avg_gain'] = recent_gains
    
    # Step 9: Final cleanup and ordering strictly per schema
    EXPECTED = [
        "company", "sector", "exchange", "open_date", "close_date", "listing_date",
        "issue_price", "issue_size_cr", "fresh_issue_pct", "ofs_pct", "lot_size",
        "sub_qib", "sub_nii", "sub_retail", "sub_total", "pe_ratio", "peer_median_pe",
        "roe", "roce", "debt_equity", "revenue_growth_pct", "pat_margin_pct",
        "gmp_pct", "nifty_30d_return", "india_vix", "recent_ipo_avg_gain",
        "listing_price", "listing_gain_pct", "label_good", "source_urls", "notes"
    ]
    
    out = master[EXPECTED].copy()
    out_path = "data/ipo_master.csv"
    out.to_csv(out_path, index=False)
    print(f"Successfully saved {len(out)} purified rows to {out_path}")
    print("\nSummary by year:")
    print(pd.to_datetime(out['listing_date']).dt.year.value_counts().sort_index())

if __name__ == "__main__":
    main()
