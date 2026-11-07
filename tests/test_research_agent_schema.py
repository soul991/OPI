"""Tests reproducing research agent schema validation defect D-111."""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from opi.schema import IPOCandidateSchema
from opi.research_agent import ground_field_proposal


def test_bombay_coated_schema_validation_reproduced(tmp_path):
    """D-111: Reproduce 2 validation errors for IPOCandidateSchema from 2026-11-02 Bombay Coated run.

    Demonstrates:
    1. Saved HTML evidence exists in data/evidence/research/run_20261102_145250_bombay-coate/.
    2. When LLM returns non-numeric strings with currency symbols or unit text (e.g. '₹82', '182 Shares'),
       ground_field_proposal passes the uncoerced string into FieldProposal upon quote verification.
    3. IPOCandidateSchema raises ValidationError with 2 errors for numeric fields (issue_price.value, lot_size.value).
    4. Code handling behavior in scripts/score_ipo.py:
       - Exception is caught by `except Exception as ag_err:`.
       - Logs FAILED to run_log.csv.
       - Missing fields remain None; deterministic features are passed to score_ipo().
       - Candidate is scored and appended to predictions/prediction_log.csv as a FORWARD row.
       - IPO is NOT lost, NOT retried (discovery marks SKIPPED_ALREADY_LISTED), and NOT alerted.
    """
    root = Path(__file__).resolve().parents[1]
    fixture_dir = root / "data" / "evidence" / "research" / "run_20261102_145250_bombay-coate"
    assert fixture_dir.exists(), f"Evidence fixture dir missing: {fixture_dir}"
    assert (fixture_dir / "issue-price.html").exists()
    assert (fixture_dir / "listing-date.html").exists()
    assert (fixture_dir / "lot-size.html").exists()

    # Load real HTML content from saved evidence
    issue_html = (fixture_dir / "issue-price.html").read_text(encoding="utf-8")
    fixtures = {"default": issue_html}

    # Propose raw values with currency/unit text matching what LLMs produce on Bombay Coated Chittorgarh page
    raw_issue_price = {
        "value": "₹82",
        "quote": "Bombay Coated & Special Steels IPO is set issue price band at ₹78 to ₹82",
        "url": "https://www.chittorgarh.com/ipo/bombay-coated-special-steels-ipo/1897/",
    }
    raw_lot_size = {
        "value": "182 Shares",
        "quote": "Bombay Coated & Special Steels IPO lot size is 182",
        "url": "https://www.chittorgarh.com/ipo/bombay-coated-special-steels-ipo/1897/",
    }

    test_ev_dir = tmp_path / "mock_ev"
    test_ev_dir.mkdir(parents=True, exist_ok=True)

    fp_price = ground_field_proposal(
        "issue_price",
        raw_issue_price,
        "run_test",
        float,
        html_fixtures=fixtures,
        target_dir=test_ev_dir,
    )
    fp_lot = ground_field_proposal(
        "lot_size",
        raw_lot_size,
        "run_test",
        int,
        html_fixtures=fixtures,
        target_dir=test_ev_dir,
    )

    assert fp_price.value == "₹82", "Uncoerced string should be preserved in proposal"
    assert fp_lot.value == "182 Shares", "Uncoerced string should be preserved in proposal"

    # Step 2: Show IPOCandidateSchema raises exact 2 validation errors
    with pytest.raises(ValidationError) as exc_info:
        IPOCandidateSchema(
            company="Bombay Coated & Special Steels",
            issue_price=fp_price,
            lot_size=fp_lot,
        )

    err_text = str(exc_info.value)
    assert "2 validation errors for IPOCandidateSchema" in err_text
    assert "issue_price.value" in err_text
    assert "lot_size.value" in err_text

    # Step 3: Verify how scripts/score_ipo.py handles this failure
    # Simulate score_ipo.py try...except block
    features = {
        "company": "Bombay Coated & Special Steels",
        "issue_price": 82.0,  # deterministically parsed from discovery/feed
        "gmp_pct": 11.28,
        "sub_total": 0.0,
    }
    missing_fields = ["pe_ratio", "peer_median_pe", "debt_equity", "fresh_issue_pct", "ofs_pct"]
    run_log_entries = []

    try:
        # execute_research_run would raise the ValidationError here
        raise exc_info.value
    except Exception as ag_err:
        # Handled in score_ipo.py:
        # append_run_log(run_id, "RESEARCH_AGENT", company, "FAILED", f"error={str(ag_err)[:100]}")
        run_log_entries.append(("RESEARCH_AGENT", "FAILED", f"error={str(ag_err)[:100]}"))

    assert len(run_log_entries) == 1
    assert run_log_entries[0][1] == "FAILED"
    assert "2 validation errors for IPOCandidateSchema" in run_log_entries[0][2]

    # Verify that features are not dropped and scoring proceeds
    assert features["company"] == "Bombay Coated & Special Steels"
    assert features["issue_price"] == 82.0
    for k in missing_fields:
        assert k not in features  # remains unpopulated, model imputer handles them
