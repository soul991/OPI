"""Tests for Phase 8 GMP evidence standard compliance (D-001, D-002, Protocol Section 4)."""

import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")

def test_snapshot_for_every_sourced_gmp_row():
    """Verify that every row kept as sourced GMP has an existing snapshot in data/evidence/gmp/."""
    gmp_path = ROOT / "data" / "gmp_sourced.csv"
    ev_dir = ROOT / "data" / "evidence" / "gmp"
    
    assert gmp_path.exists(), "data/gmp_sourced.csv must exist"
    assert ev_dir.exists(), "data/evidence/gmp/ directory must exist"
    
    g = pd.read_csv(gmp_path)
    if len(g) == 0:
        # All unverified rows reverted to NOT_RECORDED
        return
        
    have = {p.stem for p in ev_dir.iterdir() if p.is_file()}
    for row in g.itertuples():
        expected_stem = f"{pd.to_datetime(row.listing_date).date()}_{slug(row.company)}"
        assert expected_stem in have, f"Missing snapshot for sourced GMP: {row.company} ({expected_stem})"
