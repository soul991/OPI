"""Tests for Workstream B forward errors post-mortem (D-041)."""

from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]

from scripts.forward_postmortem import generate_postmortem


def test_forward_postmortem_table_generated():
    """D-041: forward_postmortem.md must be generated and contain all required audit fields."""
    content = generate_postmortem()
    out_file = ROOT_DIR / "phases" / "Phase 11" / "forward_postmortem.md"
    assert out_file.exists(), "phases/Phase 11/forward_postmortem.md must exist"

    # Verify table headers
    assert "| Company |" in content
    assert "Model Err (pp)" in content
    assert "GMP Err (pp)" in content
    assert "Nifty Move on Listing Day" in content
    assert "Sub (QIB / NII / Retail / Total)" in content

    # Verify Bonfiglioli and Zetwerk post-mortems are present
    assert "Bonfiglioli Transmissions Limited" in content
    assert "21.10 pp" in content
    assert "Zetwerk Manufacturing Business Limited" in content

    # Verify epistemic discipline
    assert "Hypothesis (untested)" in content
    assert "n = 6 < 30" in content or "n=6" in content
