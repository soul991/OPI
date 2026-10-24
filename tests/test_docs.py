"""Unit tests for documentation and maintainer runbook integrity (D-061)."""

from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_runbook_sections_and_headings():
    """D-061: Verify docs/RUNBOOK.md exists and contains all required operating sections."""
    runbook_path = ROOT_DIR / "docs" / "RUNBOOK.md"
    assert runbook_path.exists(), "docs/RUNBOOK.md must exist"

    text = runbook_path.read_text(encoding="utf-8")

    # Verify all 9 required sections are present
    required_phrases = [
        "What the System Does",
        "The Three Places to Look",
        "What Each Alert Issue Means",
        "Rotate the OpenRouter API Key",
        "Re-Run a Failed Day Manually",
        "Add or Change a Free Model",
        "Read the Final Evaluation",
        "Monthly 10-Minute Maintainer Checklist",
        "Disclaimer and Prohibited Usage",
    ]

    for phrase in required_phrases:
        assert phrase.lower() in text.lower(), f"RUNBOOK.md must contain section covering '{phrase}'"

    # Specific operational requirements
    assert "OPENROUTER_API_KEY" in text, "RUNBOOK.md must explain OPENROUTER_API_KEY secret"
    assert "https://github.com/soul991/OPI/actions" in text, "RUNBOOK.md must link to Actions tab"
    assert "DEFECTS.md" in text, "RUNBOOK.md must reference DEFECTS.md"
    assert "investment advice" in text.lower(), "RUNBOOK.md must state prohibition on investment advice"


def test_readme_links_to_runbook():
    """D-061: Verify README.md links to docs/RUNBOOK.md."""
    readme_path = ROOT_DIR / "README.md"
    assert readme_path.exists(), "README.md must exist"
    readme_text = readme_path.read_text(encoding="utf-8")
    assert "docs/RUNBOOK.md" in readme_text, "README.md must contain a link to docs/RUNBOOK.md"
