"""Unit tests for typed research schema and grounding status rules."""

import pytest
from opi.schema import FieldProposal, IPOCandidateSchema


def test_field_proposal_grounding_discipline():
    """Ensure values are strictly withheld unless verified in snapshot or confirmed by user."""
    # 1. Unverified proposal: must return None
    unverified = FieldProposal(value=250.0, grounding_status="UNVERIFIED")
    assert unverified.get_grounded_value() is None

    # 2. Not found in snapshot: must return None
    not_found = FieldProposal(value=250.0, grounding_status="NOT_FOUND_IN_SNAPSHOT")
    assert not_found.get_grounded_value() is None

    # 3. Fetch failed: must return None
    fetch_failed = FieldProposal(value=250.0, grounding_status="FETCH_FAILED")
    assert fetch_failed.get_grounded_value() is None

    # 4. Verified in snapshot: returns value
    verified = FieldProposal(value=250.0, grounding_status="VERIFIED_IN_SNAPSHOT")
    assert verified.get_grounded_value() == 250.0

    # 5. User-edited value: returns value even if originally unverified
    user_edited = FieldProposal(value=275.0, grounding_status="UNVERIFIED", edited_by_user=True)
    assert user_edited.get_grounded_value() == 275.0


def test_candidate_schema_export_to_model_features():
    """Ensure candidate schema correctly serializes to dictionary for model scoring."""
    candidate = IPOCandidateSchema(
        company="Alpha Technologies Limited",
        issue_price=FieldProposal(value=300.0, grounding_status="VERIFIED_IN_SNAPSHOT"),
        sub_total=FieldProposal(value=45.2, grounding_status="VERIFIED_IN_SNAPSHOT"),
        gmp_pct=FieldProposal(value=25.0, grounding_status="NOT_FOUND_IN_SNAPSHOT")  # Unverified
    )

    feat = candidate.to_model_features()
    assert feat["company"] == "Alpha Technologies Limited"
    assert feat["issue_price"] == 300.0
    assert feat["sub_total"] == 45.2
    assert feat["gmp_pct"] is None  # Suppressed because NOT_FOUND_IN_SNAPSHOT


def test_grounding_metrics_calculation():
    """Ensure verification coverage metrics are accurately computed."""
    candidate = IPOCandidateSchema(
        company="Beta Tech Limited",
        issue_price=FieldProposal(value=100.0, grounding_status="VERIFIED_IN_SNAPSHOT"),
        issue_size_cr=FieldProposal(value=500.0, grounding_status="VERIFIED_IN_SNAPSHOT"),
        sub_total=FieldProposal(value=10.0, grounding_status="NOT_FOUND_IN_SNAPSHOT"),
        gmp_pct=FieldProposal(value=15.0, grounding_status="FETCH_FAILED")
    )
    metrics = candidate.grounding_metrics()
    assert metrics["populated_fields"] == 4
    assert metrics["verified_fields"] == 2
    assert metrics["failed_grounding"] == 1
    assert metrics["fetch_failed"] == 1
    assert metrics["grounding_rate_pct"] == 50.0
