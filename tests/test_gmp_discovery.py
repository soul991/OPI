"""Tests for deterministic GMP page discovery and parsing (D-081)."""

import pytest
from pathlib import Path
from opi.gmp import (
    discover_gmp_url,
    normalize_gmp_company_name,
    parse_gmp_list_page,
    extract_gmp_from_chittorgarh_html,
)
from opi.ingest import parse_investorgain_gmp

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "investorgain_gmp_list.html"


def test_investorgain_list_page_discovery_saved_fixture():
    assert FIXTURE_PATH.exists(), f"Fixture missing: {FIXTURE_PATH}"
    html = FIXTURE_PATH.read_text(encoding="utf-8")

    expected_matches = {
        "Bombay Coated & Special Steels": "https://www.investorgain.com/gmp/bombay-coated-and-special-steels-ipo/1936/",
        "BLS Polymers": "https://www.investorgain.com/gmp/bls-polymers-ipo/1849/",
        "SFC Environmental Technologies": "https://www.investorgain.com/gmp/sfc-environmental-technologies-ipo/1642/",
        "M.K.Sons Fine Jewels": "https://www.investorgain.com/gmp/mksons-fine-jewels-ipo/2288/",
        "EAAA India Alternatives": "https://www.investorgain.com/gmp/eaaa-india-alternatives-ipo/1635/",
    }

    for comp, expected_url in expected_matches.items():
        discovered = discover_gmp_url(comp, list_html=html, allow_network=False)
        assert discovered == expected_url, f"Expected {expected_url} for {comp}, got {discovered}"


def test_exact_match_rejects_fuzzy_or_partial():
    assert FIXTURE_PATH.exists()
    html = FIXTURE_PATH.read_text(encoding="utf-8")

    # Partial / truncated names must not match
    assert discover_gmp_url("Bombay Coated", list_html=html, allow_network=False) is None
    assert discover_gmp_url("BLS", list_html=html, allow_network=False) is None
    assert discover_gmp_url("Polymers", list_html=html, allow_network=False) is None

    # Extra terms must not match
    assert discover_gmp_url("BLS Polymers International", list_html=html, allow_network=False) is None
    assert discover_gmp_url("Totally Nonexistent Company", list_html=html, allow_network=False) is None


def test_unpadded_date_gmp_parsing():
    # Test single-digit day (e.g. 2-Nov for 2026-11-02)
    single_digit_html = """
    <table>
        <tr><th>GMP Date</th><th>GMP</th><th>Est. Listing Price</th></tr>
        <tr><td>2-Nov 17:37Sub: 63.89xC</td><td>₹9.25(11.28%)─</td><td>₹91.25</td></tr>
        <tr><td>1-Nov 23:37</td><td>₹9(10.98%)▲</td><td>₹91</td></tr>
    </table>
    """
    gmp_val, as_of = parse_investorgain_gmp(single_digit_html, "2026-11-02")
    assert gmp_val == 11.28
    assert as_of is not None and "2-Nov" in as_of

    # Test two-digit day (e.g. 19-Oct for 2026-10-19)
    two_digit_html = """
    <table>
        <tr><th>GMP Date</th><th>GMP</th><th>Est. Listing Price</th></tr>
        <tr><td>19-Oct 23:37</td><td>₹45(30.26%)▲</td><td>₹195</td></tr>
        <tr><td>18-Oct 23:37</td><td>₹40(26.85%)▲</td><td>₹190</td></tr>
    </table>
    """
    gmp_val2, as_of2 = parse_investorgain_gmp(two_digit_html, "2026-10-19")
    assert gmp_val2 == 30.26
    assert as_of2 is not None and "19-Oct" in as_of2


def test_chittorgarh_crosslink_extraction():
    chittorgarh_html = """
    <div class="ipo-tab-item">
        <a href="https://www.investorgain.com/chr-gmp/bombay-coated-and-special-steels-ipo/2671" target="_blank" class="ipo-tab">GMP</a>
    </div>
    """
    link = extract_gmp_from_chittorgarh_html(chittorgarh_html)
    assert link == "https://www.investorgain.com/chr-gmp/bombay-coated-and-special-steels-ipo/2671"

    # Also test via discover_gmp_url fallback
    discovered = discover_gmp_url("Bombay Coated & Special Steels", list_html="<html></html>", allow_network=False, chittorgarh_html=chittorgarh_html)
    assert discovered == "https://www.investorgain.com/chr-gmp/bombay-coated-and-special-steels-ipo/2671"


def test_normalization_invariance():
    assert normalize_gmp_company_name("Bombay Coated & Special Steels Limited") == "bombay coated and special steels"
    assert normalize_gmp_company_name("Bombay Coated and Special Steels Ltd.") == "bombay coated and special steels"
    assert normalize_gmp_company_name("BLS Polymers (India) Pvt Ltd") == "bls polymers"
    assert normalize_gmp_company_name("M.K.Sons Fine Jewels") == "m k sons fine jewels"
