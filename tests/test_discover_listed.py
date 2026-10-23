"""Offline tests for IPO discovery classification of already-listed IPOs (FIX 1 / D-038).

Verifies that companies already in data/ipo_master.csv or with listing dates on/before
reference date are classified as LISTED, never default to CLOSED_UNLISTED, and are
refused by the scoring modules.
"""

from __future__ import annotations

import pytest
from datetime import datetime, date
from pathlib import Path
import pandas as pd

from opi.discover import (
    parse_discovery_html,
    normalize_company_name,
    is_company_in_master,
    load_master_companies,
    get_today_ist,
)
from scripts.score_ipo import score_and_log_ipo

ROOT_DIR = Path(__file__).resolve().parents[1]

# HTML fixture containing the six listed IPOs plus an unknown-date IPO and upcoming/open IPOs
DISCOVERY_FIXTURE_HTML = """
<table>
    <tr>
        <th>Company</th><th>Open</th><th>Close</th><th>Listing Date</th><th>Price</th><th>Size</th><th>Type</th>
    </tr>
    <tr>
        <td><a href="/ipo/runwal-ipo/101/">Runwal Enterprises Limited</a></td>
        <td>2026-09-25</td><td>2026-09-29</td><td>2026-10-05</td><td>305</td><td>500</td><td>Mainboard</td>
    </tr>
    <tr>
        <td><a href="/ipo/orient-cables-ipo/102/">Orient Cables (India)</a></td>
        <td>2026-09-25</td><td>2026-09-29</td><td>2026-10-05</td><td>272</td><td>400</td><td>Mainboard</td>
    </tr>
    <tr>
        <td><a href="/ipo/german-green-steel-ipo/103/">German Green Steel</a></td>
        <td>2026-09-25</td><td>2026-09-29</td><td>2026-10-05</td><td>139</td><td>300</td><td>Mainboard</td>
    </tr>
    <tr>
        <td><a href="/ipo/acevector-ipo/104/">Acevector (Snapdeal)</a></td>
        <td>2026-09-25</td><td>2026-09-29</td><td>2026-10-05</td><td>32</td><td>200</td><td>Mainboard</td>
    </tr>
    <tr>
        <td><a href="/ipo/srit-india-ipo/105/">SRIT India</a></td>
        <td>2026-09-26</td><td>2026-09-30</td><td>2026-10-06</td><td>130</td><td>150</td><td>Mainboard</td>
    </tr>
    <tr>
        <td><a href="/ipo/shah-investors-home-ipo/106/">Shah Investor's Home</a></td>
        <td>2026-09-26</td><td>2026-09-30</td><td>2026-10-06</td><td>167</td><td>250</td><td>Mainboard</td>
    </tr>
    <tr>
        <td><a href="/ipo/mystery-unlisted-ipo/107/">Mystery Entity Without Listing Date</a></td>
        <td>2026-10-10</td><td>2026-10-15</td><td></td><td>100</td><td>100</td><td>Mainboard</td>
    </tr>
</table>
"""

# Two-column dashboard fixture (like Chittorgarh table 0)
DASHBOARD_FIXTURE_HTML = """
<table>
    <tr><td>Company</td><td>Status</td></tr>
    <tr>
        <td><a href="/ipo/runwal-ipo/101/">Runwal Enterprises</a></td>
        <td>P | 25 - 29 Sep</td>
    </tr>
    <tr>
        <td><a href="/ipo/orient-cables-ipo/102/">Orient Cables</a></td>
        <td>P | 25 - 29 Sep</td>
    </tr>
    <tr>
        <td><a href="/ipo/german-green-steel-ipo/103/">German Green Steel</a></td>
        <td>P | 25 - 29 Sep</td>
    </tr>
    <tr>
        <td><a href="/ipo/acevector-ipo/104/">Acevector</a></td>
        <td>P | 25 - 29 Sep</td>
    </tr>
    <tr>
        <td><a href="/ipo/srit-india-ipo/105/">Srit India</a></td>
        <td>P | 26 - 30 Sep</td>
    </tr>
    <tr>
        <td><a href="/ipo/shah-investors-home-ipo/106/">Shah Investors Home</a></td>
        <td>P | 26 - 30 Sep</td>
    </tr>
    <tr>
        <td><a href="/ipo/unknown-close-ipo/108/">Brand New Closed IPO</a></td>
        <td>P | 10 - 15 Oct</td>
    </tr>
</table>
"""


def test_six_listed_ipos_classified_as_listed_in_strategy1():
    """All 6 target IPOs must be classified as LISTED, never CLOSED_UNLISTED."""
    candidates = parse_discovery_html(DISCOVERY_FIXTURE_HTML, as_of_date="2026-10-24", confirm_overview=False)
    cand_by_name = {c["company"]: c for c in candidates}

    target_names = [
        "Runwal Enterprises Limited",
        "Orient Cables (India)",
        "German Green Steel",
        "Acevector (Snapdeal)",
        "SRIT India",
        "Shah Investor's Home",
    ]

    for name in target_names:
        assert name in cand_by_name, f"Expected {name} to be discovered"
        cand = cand_by_name[name]
        assert cand["status"] == "LISTED", f"{name} status was {cand['status']}, expected LISTED"

    # Unknown listing date candidate should NOT default to CLOSED_UNLISTED
    mystery = cand_by_name["Mystery Entity Without Listing Date"]
    assert mystery["status"] == "UNKNOWN_LISTING_DATE"


def test_six_listed_ipos_classified_as_listed_in_strategy2_dashboard():
    """Two-column table without listing dates must classify master IPOs as LISTED."""
    candidates = parse_discovery_html(DASHBOARD_FIXTURE_HTML, as_of_date="2026-10-24", confirm_overview=False)
    cand_by_name = {c["company"]: c for c in candidates}

    target_names = [
        "Runwal Enterprises",
        "Orient Cables",
        "German Green Steel",
        "Acevector",
        "Srit India",
        "Shah Investors Home",
    ]

    for name in target_names:
        assert name in cand_by_name, f"Expected {name} in dashboard discovery"
        assert cand_by_name[name]["status"] == "LISTED", f"{name} must be LISTED"

    # Unlisted closed IPO with unknown listing date must be UNKNOWN_LISTING_DATE, never CLOSED_UNLISTED
    assert cand_by_name["Brand New Closed IPO"]["status"] == "UNKNOWN_LISTING_DATE"


def test_score_ipo_refuses_already_listed_companies():
    """score_and_log_ipo must refuse to score companies present in data/ipo_master.csv."""
    target_names = [
        "Runwal Enterprises",
        "Orient Cables",
        "German Green Steel & Power",
        "Acevector",
        "Srit India",
        "Shah Investors Home",
    ]
    for comp in target_names:
        with pytest.raises(ValueError, match="SKIPPED_ALREADY_LISTED"):
            score_and_log_ipo(
                company=comp,
                listing_date="2026-10-30",
                close_date="2026-10-23",
                overview_url="https://example.com/overview",
                sub_url="https://example.com/sub",
                dry_run=True,
            )


def test_score_ipo_refuses_past_listing_date():
    """score_and_log_ipo must refuse to score companies whose listing date is on or before today."""
    with pytest.raises(ValueError, match="SKIPPED_ALREADY_LISTED"):
        score_and_log_ipo(
            company="Some Brand New Entity",
            listing_date="2026-10-20",  # past date
            close_date="2026-10-15",
            overview_url="https://example.com/overview",
            sub_url="https://example.com/sub",
            dry_run=True,
        )


def test_score_ipo_refuses_unknown_listing_date():
    """score_and_log_ipo must refuse to score companies with empty/unknown listing date."""
    for bad_date in ("", "UNKNOWN", "None"):
        with pytest.raises(ValueError, match="SKIPPED_UNKNOWN_LISTING_DATE"):
            score_and_log_ipo(
                company="Some Brand New Entity",
                listing_date=bad_date,
                close_date="2026-10-23",
                overview_url="https://example.com/overview",
                sub_url="https://example.com/sub",
                dry_run=True,
            )
