"""Tests for Phase 8 data integrity, outlier audits, and historical sample properties."""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def test_gmp_outliers_verified():
    """D-003/D-018: Mukka Proteins and extreme GMP values verified or reverted to NOT_RECORDED."""
    master_path = ROOT / "data" / "ipo_master.csv"
    review_path = ROOT / "phases" / "Phase 8" / "gmp_outlier_review.csv"
    
    assert master_path.exists(), "data/ipo_master.csv must exist"
    assert review_path.exists(), "phases/Phase 8/gmp_outlier_review.csv must exist"
    
    m = pd.read_csv(master_path)
    mukka = m[m.company == "Mukka Proteins"]
    assert len(mukka) == 1, "Mukka Proteins must exist in ipo_master.csv"
    # In Phase 9 Gate A9 V4 (D-018), Mukka was reverted to NOT_RECORDED due to lack of snapshot and invalid ID
    assert mukka.gmp_status.iloc[0] == "NOT_RECORDED" or mukka.gmp_pct.iloc[0] == 125.0
    
    # Check that any extreme values (>150% or <-30%) in master are resolved
    outliers = m[(m.gmp_pct > 150) | (m.gmp_pct < -30)]
    assert len(outliers) == 0, f"Unresolved outliers found in ipo_master.csv: {outliers.company.tolist()}"
    
    rev = pd.read_csv(review_path)
    assert len(rev) >= 9, f"Expected at least 9 reviewed outliers, got {len(rev)}"
    assert "Mukka Proteins" in rev.company.values


def test_extreme_gmp_have_snapshots():
    """D-018: Extreme GMP values (>100% or <-30%) must have a code-saved snapshot or be NOT_RECORDED."""
    import re
    master_path = ROOT / "data" / "ipo_master.csv"
    assert master_path.exists(), "data/ipo_master.csv must exist"
    m = pd.read_csv(master_path)
    ev = ROOT / "data" / "evidence" / "gmp"
    have = {p.stem for p in ev.iterdir()} if ev.exists() else set()
    
    def slug(s):
        return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
        
    o = m[(m.gmp_status == "OBSERVED") & ((m.gmp_pct > 100) | (m.gmp_pct < -30))]
    miss = [r.company for r in o.itertuples() if f"{pd.to_datetime(r.listing_date).date()}_{slug(r.company)}" not in have]
    assert len(miss) == 0, f"Found extreme GMP rows without snapshots: {miss}"



def test_sector_catchall_share_reported():
    """D-011: Verify exact share of Industrial & Manufacturing sector."""
    master_path = ROOT / "data" / "ipo_master.csv"
    m = pd.read_csv(master_path)
    
    total = len(m)
    im_count = (m["sector"] == "Industrial & Manufacturing").sum()
    share = im_count / total * 100
    
    # Verify share is documented accurately (~18.74%, definitely under 25% and not > 30%)
    assert 18.0 <= share <= 19.5, f"Expected Industrial & Manufacturing share ~18.74%, got {share:.2f}%"


def test_sparse_years_documented():
    """D-012: Verify counts for sparse capital market years 2012-2014."""
    master_path = ROOT / "data" / "ipo_master.csv"
    m = pd.read_csv(master_path)
    m["year"] = pd.to_datetime(m["listing_date"]).dt.year
    
    counts = m["year"].value_counts().to_dict()
    assert counts.get(2012, 0) == 11, f"Expected 11 IPOs in 2012, got {counts.get(2012)}"
    assert counts.get(2013, 0) == 3, f"Expected 3 IPOs in 2013, got {counts.get(2013)}"
    assert counts.get(2014, 0) == 5, f"Expected 5 IPOs in 2014, got {counts.get(2014)}"


def test_audit_samples_have_snapshots():
    """D-013: Verify that audit samples have snapshots under data/evidence/audit/ and prior_phase_recheck.csv."""
    audit_dir = ROOT / "data" / "evidence" / "audit"
    recheck_path = ROOT / "phases" / "Phase 8" / "prior_phase_recheck.csv"
    
    assert audit_dir.exists(), "data/evidence/audit directory must exist"
    assert recheck_path.exists(), "phases/Phase 8/prior_phase_recheck.csv must exist"
    
    snapshots = list(audit_dir.glob("*.html"))
    assert len(snapshots) >= 20, f"Expected at least 20 saved audit snapshots, got {len(snapshots)}"
    
    df = pd.read_csv(recheck_path)
    assert len(df) >= 30, f"Expected at least 30 recheck rows, got {len(df)}"
    
    # Audit samples must accurately record MISMATCH rather than fabricated MATCH
    samples = df[df["category"].str.contains("Sample", na=False)]
    assert (samples["result"].str.contains("MISMATCH")).all(), (
        "Phase 7 sample URLs must be accurately flagged as MISMATCH (wrong entity or 404)"
    )

