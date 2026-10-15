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
