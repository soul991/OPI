"""Tests for mainboard IPO discovery and filtering rules."""

from pathlib import Path
import pytest
from opi.discover import discover_ipos

ROOT = Path(__file__).resolve().parents[1]


def test_discovers_closed_unlisted_mainboard_ipos_from_fixture():
    """D-027: Test that discovery finds open/closed-unlisted Mainboard IPOs and excludes SME/FPO from fixture."""
    fixture_path = ROOT / "tests" / "fixtures" / "discovery_page.html"
    assert fixture_path.exists(), "tests/fixtures/discovery_page.html must exist"

    html = fixture_path.read_text(encoding="utf-8")
    candidates = discover_ipos(source_html=html, as_of_date="2026-10-21")

    # Check discovered count
    companies = [c["company"] for c in candidates]
    assert "Jio Platforms Limited" in companies
    assert "Paras Healthcare Limited" in companies
    assert "Zetwerk Manufacturing Business Limited" in companies
    assert "Sahajanand Medical Technologies Limited" in companies

    # Check exclusions (SME and FPO must be excluded)
    assert "Apex Solar Energy Limited" not in companies
    assert "ABC Power FPO" not in companies

    # Check status classifications on 2026-10-21
    jio = next(c for c in candidates if c["company"] == "Jio Platforms Limited")
    assert jio["status"] == "BIDDING_OPEN"

    paras = next(c for c in candidates if c["company"] == "Paras Healthcare Limited")
    assert paras["status"] == "BIDDING_OPEN"

    zet = next(c for c in candidates if c["company"] == "Zetwerk Manufacturing Business Limited")
    assert zet["status"] == "CLOSED_UNLISTED"

    sah = next(c for c in candidates if c["company"] == "Sahajanand Medical Technologies Limited")
    assert sah["status"] == "CLOSED_UNLISTED"


def test_derive_subscription_url_from_overview_url():
    """D-077: Verify derivation of Chittorgarh subscription URL from overview URL using Jio's real URLs."""
    from opi.discover import derive_subscription_url, discover_ipos

    # Jio Platforms real URLs from repo evidence and historical prediction log
    jio_overview = "https://www.chittorgarh.com/ipo/jio-platforms-ipo/3152/"
    expected_jio_sub = "https://www.chittorgarh.com/ipo_subscription/jio-platforms-ipo/3152/"

    # Verify standard absolute URL transformation
    assert derive_subscription_url(jio_overview) == expected_jio_sub

    # Verify URL without trailing slash
    assert derive_subscription_url("https://www.chittorgarh.com/ipo/jio-platforms-ipo/3152") == expected_jio_sub

    # Verify relative URL transformation
    assert derive_subscription_url("/ipo/jio-platforms-ipo/3152/") == expected_jio_sub
    assert derive_subscription_url("/ipo/jio-platforms-ipo/3152") == expected_jio_sub

    # Verify other real IPO URLs from discovery candidates
    mksons_overview = "https://www.chittorgarh.com/ipo/mksons-fine-jewels-ipo/3100/"
    assert derive_subscription_url(mksons_overview) == "https://www.chittorgarh.com/ipo_subscription/mksons-fine-jewels-ipo/3100/"

    # Verify non-matching and empty inputs return None
    assert derive_subscription_url("") is None
    assert derive_subscription_url(None) is None
    assert derive_subscription_url("https://www.chittorgarh.com/ipo_dashboard.asp") is None

    # Verify discovery output populates sub_url for candidate IPOs
    fixture_path = ROOT / "tests" / "fixtures" / "discovery_page.html"
    candidates = discover_ipos(source_html=fixture_path.read_text(encoding="utf-8"), as_of_date="2026-10-21")
    jio_cand = next(c for c in candidates if c["company"] == "Jio Platforms Limited")
    assert jio_cand["sub_url"] == "https://www.chittorgarh.com/ipo_subscription/jio-platforms-ipo/3095/"

