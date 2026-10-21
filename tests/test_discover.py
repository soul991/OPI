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
