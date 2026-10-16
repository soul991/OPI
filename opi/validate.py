"""Validation module for IPO features, timing constraints, and data leakage checks."""

import re
from datetime import datetime, date, time
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd

REQUIRED_NUMERIC_FIELDS = [
    "issue_size_cr", "lot_size", "sub_qib", "sub_nii", "sub_retail", "sub_total"
]

def validate_timing_and_leakage(
    close_date_str: str,
    listing_date_str: str,
    scored_at_str: str,
    notes: Optional[str] = "",
    gmp_as_of_date_str: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """Validate timing order, bidding cutoff, and leakage rules.
    
    Rules:
    - Scored strictly after 18:00 on issue close date.
    - Scored strictly before listing date.
    - GMP as of date not after close date or on/after listing date.
    - Notes must not indicate interim / live bidding (Day 1 / Day 2 / live).
    """
    issues = []
    
    try:
        close_dt = pd.to_datetime(close_date_str).date()
        listing_dt = pd.to_datetime(listing_date_str).date()
        scored_dt = pd.to_datetime(scored_at_str)
    except Exception as e:
        return False, [f"Date parsing error: {e}"]

    # 1. Date order check
    if close_dt >= listing_dt:
        issues.append(f"Close date ({close_dt}) must be strictly before listing date ({listing_dt})")

    # 2. Scored before listing date
    if scored_dt.date() >= listing_dt:
        issues.append(f"Scored at timestamp ({scored_dt}) must be strictly before listing date ({listing_dt})")

    # 3. Scored after bidding closed (18:00 on close date)
    bidding_close_cutoff = datetime.combine(close_dt, time(18, 0))
    if scored_dt < bidding_close_cutoff:
        issues.append(f"Scored at ({scored_dt}) is before bidding closed at 18:00 IST on {close_dt}")

    # 4. Interim / live bidding flag
    if notes:
        if re.search(r"\bday\s*[12]\b|live\s+bidding", str(notes), re.IGNORECASE):
            issues.append(f"Interim/live subscription detected in notes ('{notes}'); only final subscription permitted")

    # 5. GMP leakage check
    if gmp_as_of_date_str:
        try:
            gmp_as_of = pd.to_datetime(gmp_as_of_date_str).date()
            if gmp_as_of > close_dt:
                issues.append(f"GMP as_of_date ({gmp_as_of}) cannot be after close date ({close_dt})")
            if gmp_as_of >= listing_dt:
                issues.append(f"GMP as_of_date ({gmp_as_of}) cannot be on or after listing date ({listing_dt})")
        except Exception as e:
            issues.append(f"Invalid GMP as_of_date: {e}")

    return len(issues) == 0, issues


def validate_ipo_features(features: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate feature availability, types, and plausible domain bounds."""
    issues = []

    # Check required numeric fields
    for field in REQUIRED_NUMERIC_FIELDS:
        val = features.get(field)
        if val is None or pd.isna(val):
            issues.append(f"Missing required numeric field: '{field}'")
        else:
            try:
                num = float(val)
                if field in ("issue_size_cr", "lot_size") and num <= 0:
                    issues.append(f"Field '{field}' must be positive, got {num}")
                elif "sub_" in field and num < 0:
                    issues.append(f"Field '{field}' cannot be negative, got {num}")
            except (ValueError, TypeError):
                issues.append(f"Field '{field}' could not be converted to float: {val}")

    # GMP range check if provided
    gmp_val = features.get("gmp_pct")
    if gmp_val is not None and not pd.isna(gmp_val) and str(gmp_val).strip() != "":
        try:
            gmp_num = float(gmp_val)
            if gmp_num < -50.0 or gmp_num > 300.0:
                issues.append(f"GMP percentage {gmp_num}% is outside plausible range [-50%, 300%]")
        except (ValueError, TypeError):
            issues.append(f"Invalid GMP value: {gmp_val}")

    return len(issues) == 0, issues


def validate_mainboard_eligibility(features: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate that the candidate issue is an Indian Mainboard IPO (not SME, FPO, or rights issue)."""
    issues = []
    company = str(features.get("company", "")).lower()
    notes = str(features.get("notes", "")).lower()
    exchange = str(features.get("exchange", "")).upper()
    
    # 1. Reject explicit SME / FPO keywords
    for keyword in ["sme", "fpo", "rights issue", "invit", "reit"]:
        if keyword in company.split() or f"({keyword})" in company:
            issues.append(f"Company name contains '{keyword}', indicating non-mainboard issue")
        if keyword in notes:
            issues.append(f"Notes indicate non-mainboard issue category: '{keyword}'")

    if "sme" in exchange.lower():
        issues.append(f"Exchange '{exchange}' indicates SME segment")

    # 2. Mainboard minimum capital / issue size check
    issue_size = features.get("issue_size_cr")
    if issue_size is not None and pd.notna(issue_size):
        try:
            size_num = float(issue_size)
            if size_num < 25.0:
                issues.append(f"Issue size (INR {size_num} Cr) is below standard Mainboard threshold (INR 25 Cr)")
        except (ValueError, TypeError):
            pass

    return len(issues) == 0, issues


def determine_prediction_mode(
    close_date_str: str,
    listing_date_str: str,
    scored_at_str: Optional[str] = None,
    notes: Optional[str] = ""
) -> Tuple[str, List[str]]:
    """Determine whether scoring is PREVIEW (bidding ongoing) or FORWARD_ELIGIBLE (post-close).
    
    Returns:
        mode: "PREVIEW", "FORWARD_ELIGIBLE", or "INVALID"
        reasons: list of explanatory reasons
    """
    reasons = []
    try:
        close_dt = pd.to_datetime(close_date_str).date()
        listing_dt = pd.to_datetime(listing_date_str).date()
        scored_dt = pd.to_datetime(scored_at_str) if scored_at_str else datetime.now()
    except Exception as e:
        return "INVALID", [f"Date parsing error: {e}"]

    # Check if listing date passed
    if scored_dt.date() >= listing_dt:
        return "INVALID", [f"Scored date ({scored_dt.date()}) is on or after listing date ({listing_dt})"]

    # Check bidding close cutoff (18:00 IST on close date)
    bidding_close_cutoff = datetime.combine(close_dt, time(18, 0))
    if scored_dt < bidding_close_cutoff or (notes and re.search(r"\bday\s*[12]\b|live", str(notes), re.I)):
        reasons.append("Bidding is ongoing (scored before 18:00 IST on close date or live data). PREVIEW mode only — cannot be logged as FORWARD.")
        return "PREVIEW", reasons

    reasons.append("Bidding closed and listing date is in future. Eligible for FORWARD prediction logging.")
    return "FORWARD_ELIGIBLE", reasons


def validate_candidate_for_forward_logging(features: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Comprehensive gate checking before writing a FORWARD row to prediction_log.csv."""
    all_issues = []
    
    # 1. Mainboard check
    mb_ok, mb_issues = validate_mainboard_eligibility(features)
    if not mb_ok:
        all_issues.extend(mb_issues)

    # 2. Timing and leakage check
    t_ok, t_issues = validate_timing_and_leakage(
        close_date_str=str(features.get("close_date", "")),
        listing_date_str=str(features.get("listing_date", "")),
        scored_at_str=datetime.now().isoformat(),
        notes=str(features.get("notes", "")),
        gmp_as_of_date_str=str(features.get("gmp_as_of_date", "")) if features.get("gmp_as_of_date") else None
    )
    if not t_ok:
        all_issues.extend(t_issues)

    # 3. Feature bounds
    f_ok, f_issues = validate_ipo_features(features)
    if not f_ok:
        all_issues.extend(f_issues)

    # 4. Mode must be FORWARD_ELIGIBLE
    mode, mode_reasons = determine_prediction_mode(
        close_date_str=str(features.get("close_date", "")),
        listing_date_str=str(features.get("listing_date", "")),
        notes=str(features.get("notes", ""))
    )
    if mode != "FORWARD_ELIGIBLE":
        all_issues.append(f"Candidate mode is '{mode}', not 'FORWARD_ELIGIBLE': {'; '.join(mode_reasons)}")

    return len(all_issues) == 0, all_issues

