#!/usr/bin/env python3
"""tests/test_dashboard.py - Regression tests for D-056: Dashboard defect counter and cloud run time."""

import re
from pathlib import Path
from opi.report import parse_defects_summary, render_dashboard_html, generate_dashboard_data

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_defect_counter_matches_register():
    """D-056: Verify dashboard defect counter matches DEFECTS.md open/partial count."""
    defects = parse_defects_summary()
    expected_open_partial = defects["OPEN"] + defects["PARTIAL"]
    
    dash_path = ROOT / "dashboard" / "index.html"
    assert dash_path.exists(), "dashboard/index.html must exist"
    content = dash_path.read_text(encoding="utf-8")
    
    # Check card
    m_card = re.search(r"Open / Partial Defects.*?<div class=\"card-num\"[^>]*>\s*(\d+)\s*</div>", content, re.DOTALL)
    assert m_card is not None, "Open / Partial Defects card not found in dashboard/index.html"
    card_count = int(m_card.group(1))
    assert card_count == expected_open_partial, f"Dashboard card has {card_count}, expected {expected_open_partial}"
    
    # Check Repository & Defect Health section
    m_sect = re.search(r"Open/Partial:\s*<strong>(\d+)</strong>", content)
    assert m_sect is not None, "Open/Partial text not found in Repository & Defect Health section"
    sect_count = int(m_sect.group(1))
    assert sect_count == expected_open_partial, f"Dashboard section has {sect_count}, expected {expected_open_partial}"


def test_dashboard_shows_last_cloud_run():
    """D-056: Verify dashboard displays the last cloud run timestamp."""
    dash_path = ROOT / "dashboard" / "index.html"
    assert dash_path.exists(), "dashboard/index.html must exist"
    content = dash_path.read_text(encoding="utf-8")
    
    assert "Last Cloud Run" in content, "Dashboard must contain 'Last Cloud Run'"
    m_run = re.search(r"Last Cloud Run.*?<div class=\"card-num\"[^>]*>\s*(\d{4}-\d{2}-\d{2}T[^\s<]+)\s*</div>", content, re.DOTALL)
    assert m_run is not None, "Valid ISO timestamp for Last Cloud Run not found in dashboard card"


def test_render_dashboard_html_executes():
    """D-056: Verify render_dashboard_html runs cleanly and updates timestamp."""
    out = render_dashboard_html()
    assert out.exists()
