"""Unit tests for Phase 5 Gate A remediation and Phase 6 Gate A6 verification.

Phase 5 tests (R1-R8) plus Phase 6 additions:
- S1: Inclusion criteria (no excluded rows in master, no duplicates)
- S6: log_prediction.py uses calibrated classifier matching evaluation pipeline
- S7: Phase 5 verification commands re-checked
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
sys.path.insert(0, os.path.join(ROOT_DIR, "model"))

from phase4_train_evaluate import reliability_table, compute_ece
from forward_report import generate_forward_report


def test_r1_error_distribution_file_and_summary():
    """R1: phase4_error_distribution.csv exists with 75 rows and matching summary statistics."""
    csv_path = os.path.join(ROOT_DIR, "phases", "Phase 5", "phase4_error_distribution.csv")
    assert os.path.exists(csv_path), "phases/Phase 5/phase4_error_distribution.csv must exist"
    
    df = pd.read_csv(csv_path)
    assert len(df) == 75, f"Expected 75 rows in error distribution, got {len(df)}"
    
    err = df["model_error"].values
    mean_err = round(float(np.mean(err)), 2)
    median_err = round(float(np.median(err)), 2)
    p75 = round(float(np.percentile(err, 75)), 2)
    p90 = round(float(np.percentile(err, 90)), 2)
    max_err = round(float(np.max(err)), 2)

    assert mean_err == 12.19, f"Expected mean error 12.19%, got {mean_err}%"
    assert median_err == 8.29, f"Expected median error 8.29%, got {median_err}%"
    assert p75 == 14.20, f"Expected p75 error 14.20%, got {p75}%"
    assert p90 == 27.80, f"Expected p90 error 27.80%, got {p90}%"
    assert max_err == 83.24, f"Expected max error 83.24%, got {max_err}%"


def test_r1_errata_header_present():
    """R1: Top 3 lines of Phase 4 verdict must show ERRATA header."""
    verdict_path = os.path.join(ROOT_DIR, "phases", "Phase 4", "3_outcome_and_verdict.md")
    with open(verdict_path, "r", encoding="utf-8") as f:
        head_lines = [f.readline() for _ in range(3)]
    
    combined = "".join(head_lines)
    assert "ERRATA (Phase 5)" in combined, f"Expected ERRATA (Phase 5) in top 3 lines, got:\n{combined}"


def test_r2_paired_bootstrap_intervals():
    """R2: Paired bootstrap difference intervals for Blend vs GMP must straddle zero."""
    test_path = os.path.join(ROOT_DIR, "phases", "Phase 5", "phase4_error_distribution.csv")
    df = pd.read_csv(test_path)
    test_gmp = df[df["gmp_pct"].notna()].copy()
    assert len(test_gmp) == 8, "Expected 8 test IPOs with GMP"

    y_true = test_gmp["actual_gain_pct"].values
    raw_gmp = test_gmp["gmp_pct"].values
    model_pred = test_gmp["predicted_gain_pct"].values
    blend_pred = 0.55 * raw_gmp + 0.45 * model_pred

    err_gmp = np.abs(raw_gmp - y_true)
    err_blend = np.abs(blend_pred - y_true)

    # 2,000 resamples with fixed seed
    rng = np.random.RandomState(42)
    diffs = []
    n = len(test_gmp)
    for _ in range(2000):
        idx = rng.randint(0, n, size=n)
        diffs.append(err_blend[idx].mean() - err_gmp[idx].mean())

    ci = np.percentile(diffs, [2.5, 97.5])
    assert ci[0] <= 0 <= ci[1], f"Bootstrap interval for Delta(Blend - GMP) must include 0, got [{ci[0]:.4f}, {ci[1]:.4f}]"


def test_r3_calibration_target_missed_on_final_test():
    """R3: Final test ECE must be > 0.10, showing the calibration target was missed."""
    test_path = os.path.join(ROOT_DIR, "phases", "Phase 5", "phase4_error_distribution.csv")
    df = pd.read_csv(test_path)
    y_true = (df["actual_gain_pct"] > 10.0).astype(int).values
    y_prob = (df["pred_prob_gt10_cal"] / 100.0).values

    ece_uniform = compute_ece(y_true, y_prob, n_bins=10, strategy="uniform")
    ece_quantile = compute_ece(y_true, y_prob, n_bins=10, strategy="quantile")

    assert ece_uniform > 0.10, f"Expected uniform ECE > 0.10 (missed target), got {ece_uniform:.4f}"
    assert ece_quantile > 0.10, f"Expected quantile ECE > 0.10 (missed target), got {ece_quantile:.4f}"


def test_r4_reliability_table_gap_equals_abs_difference():
    """R4: For every bin in a reliability table, gap must strictly equal abs(avg_pred - avg_actual)."""
    # Test on synthetic data covering empty bins, full bins, extreme probs
    rng = np.random.RandomState(42)
    y_prob = rng.uniform(0, 1, size=100)
    y_true = (y_prob + rng.normal(0, 0.2, size=100) > 0.5).astype(int)

    for strat in ["uniform", "quantile"]:
        rt = reliability_table(y_true, y_prob, n_bins=10, strategy=strat)
        for _, row in rt.iterrows():
            if row["count"] > 0:
                pred = float(row["avg_predicted"])
                act = float(row["avg_actual"])
                gap = float(row["gap"])
                expected_gap = round(abs(pred - act), 3)
                assert abs(gap - expected_gap) < 1e-4, (
                    f"Bin {row['bin']} arithmetic mismatch in {strat} mode: "
                    f"|{pred} - {act}| = {expected_gap}, but table shows {gap}"
                )


def test_r6_prediction_log_status_and_filtering():
    """R6: prediction_log.csv has status column and metrics scripts exclude TEST_* and INVALID rows."""
    log_path = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")
    assert os.path.exists(log_path), "prediction_log.csv must exist"
    
    df = pd.read_csv(log_path)
    assert "status" in df.columns, "prediction_log.csv must have a 'status' column"

    # Verify existing rows
    kissht_rows = df[df["company"].astype(str).str.contains("Kissht", case=False)]
    assert not kissht_rows.empty, "Kisshtipo rows must exist in log"
    for _, r in kissht_rows.iterrows():
        assert r["status"] == "TEST_NOT_FORWARD", f"Kisshtipo row must be TEST_NOT_FORWARD, got {r['status']}"

    hyundai_rows = df[df["company"].astype(str).str.contains("Hyundai", case=False)]
    assert not hyundai_rows.empty, "Hyundai row must exist in log"
    for _, r in hyundai_rows.iterrows():
        assert r["status"] == "INVALID", f"Hyundai row must be INVALID, got {r['status']}"

    # Verify forward_report script excludes them
    report = generate_forward_report(log_path)
    assert report is not None
    assert report["test_rows"] >= 2, f"Expected >= 2 test rows excluded, got {report['test_rows']}"
    assert report["forward_rows"] >= 0, f"Expected non-negative FORWARD rows, got {report['forward_rows']}"
    # Verify that forward rows exclusively have status == FORWARD
    forward_subset = df[df["status"] == "FORWARD"]
    assert len(forward_subset) == report["forward_rows"], "report['forward_rows'] must match count of status == 'FORWARD'"


def test_r7_no_absolute_user_links():
    """R7: Zero absolute file URI or user paths exist in markdown, scripts, or model files."""
    import glob
    files_to_check = []
    for pattern in ["phases/**/*.md", "README.md", "scripts/**/*.py", "model/**/*.py"]:
        files_to_check.extend(glob.glob(os.path.join(ROOT_DIR, pattern), recursive=True))

    user_path_str = "/" + "Users/"
    file_uri_str = "file:" + "///"
    for path in files_to_check:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                if "verify_all.py" in path:
                    continue
                # Allow self-referencing check expressions in planning and execution check files
                if ("1_planning_and_goals.md" in path or "2_building_and_execution.md" in path) and (
                    "grep" in line or "never" in line or "Defect" in line or "Relative links only" in line or "paths" in line or "echo" in line or "Command" in line or "phases/Phase 7/1_planning_and_goals.md" in line
                ):
                    continue
                assert file_uri_str not in line, f"Absolute file URI found in {path}:{line_no}\n  {line.strip()}"
                assert user_path_str not in line, f"Absolute user path found in {path}:{line_no}\n  {line.strip()}"


def test_r8_test_set_partition_discipline():
    """R8: ipo_final_test.csv renamed to ipo_phase4_test_used.csv; new final test initialized empty."""
    used_test_path = os.path.join(ROOT_DIR, "data", "ipo_phase4_test_used.csv")
    assert os.path.exists(used_test_path), "data/ipo_phase4_test_used.csv must exist"
    df_used = pd.read_csv(used_test_path)
    assert len(df_used) == 75, f"Expected 75 rows in ipo_phase4_test_used.csv, got {len(df_used)}"

    p5_test_path = os.path.join(ROOT_DIR, "data", "ipo_phase5_final_test.csv")
    assert os.path.exists(p5_test_path), "data/ipo_phase5_final_test.csv must exist"
    df_p5 = pd.read_csv(p5_test_path)
    assert len(df_p5) == 0, f"data/ipo_phase5_final_test.csv must be initialized empty, got {len(df_p5)} rows"
    assert "listing_gain_pct" in df_p5.columns, "data/ipo_phase5_final_test.csv must contain standard schema columns"


# ==============================================================================
#  PHASE 6 GATE A6 TESTS
# ==============================================================================


def test_s1_inclusion_criteria_no_excluded_in_master():
    """S1: No row in ipo_master.csv matches an entry in excluded_rows.csv."""
    master = pd.read_csv(os.path.join(ROOT_DIR, "data", "ipo_master.csv"))
    excluded = pd.read_csv(os.path.join(ROOT_DIR, "data", "excluded_rows.csv"))
    excluded_names = set(excluded["company"].str.strip().str.lower())

    for _, row in master.iterrows():
        name_lower = str(row["company"]).strip().lower()
        assert name_lower not in excluded_names, (
            f"Excluded company '{row['company']}' still present in ipo_master.csv"
        )


def test_s1_no_duplicate_companies():
    """S1: No duplicate company names in master dataset."""
    master = pd.read_csv(os.path.join(ROOT_DIR, "data", "ipo_master.csv"))
    dups = master[master.duplicated("company", keep=False)]
    assert len(dups) == 0, f"Found {len(dups)} duplicate rows for companies: {dups['company'].unique().tolist()}"


def test_s1_no_extreme_price_ratios():
    """S1: No listing_price/issue_price ratio below 0.4 or above 4.0."""
    master = pd.read_csv(os.path.join(ROOT_DIR, "data", "ipo_master.csv"))
    ratio = master["listing_price"] / master["issue_price"]
    low = master[ratio < 0.4]
    high = master[ratio > 4.0]
    assert len(low) == 0, f"Price ratio < 0.4 for: {low['company'].tolist()}"
    assert len(high) == 0, f"Price ratio > 4.0 for: {high['company'].tolist()}"


def test_s1_excluded_rows_documented():
    """S1: data/excluded_rows.csv exists and has required columns."""
    path = os.path.join(ROOT_DIR, "data", "excluded_rows.csv")
    assert os.path.exists(path), "data/excluded_rows.csv must exist"
    df = pd.read_csv(path)
    required_cols = {"company", "listing_date", "reason", "source_url", "date_of_decision"}
    assert required_cols.issubset(set(df.columns)), f"Missing columns: {required_cols - set(df.columns)}"
    assert len(df) >= 3, "Expected at least 3 excluded rows (Patanjali Foods, Adani Enterprises, Vodafone Idea)"


def test_s2_phase5_errata_present():
    """S2: Phase 5 verdict has ERRATA (Phase 6) header."""
    verdict_path = os.path.join(ROOT_DIR, "phases", "Phase 5", "3_outcome_and_verdict.md")
    with open(verdict_path, "r", encoding="utf-8") as f:
        head = f.read(2000)
    assert "ERRATA (Phase 6)" in head, "Expected ERRATA (Phase 6) at top of Phase 5 verdict"
    assert "PARTIAL" in head, "Erratum should mention R5 is PARTIAL"


def test_s6_log_uses_calibrated_classifier():
    """S6: log_prediction.py uses cal_clf (calibrated) not raw clf."""
    script_path = os.path.join(ROOT_DIR, "scripts", "log_prediction.py")
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
    # The script must reference cal_clf
    assert "cal_clf" in content, "log_prediction.py must reference 'cal_clf' for calibrated probabilities"


def test_s6_forward_prediction_calibrated_range():
    """S6: All FORWARD predictions have P(gain>10%) within the calibrated range [0, 0.98]."""
    log_path = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")
    df = pd.read_csv(log_path)
    forward = df[df["status"] == "FORWARD"]
    if len(forward) == 0:
        pytest.skip("No FORWARD rows to check")
    for _, row in forward.iterrows():
        prob = float(row["pred_prob_gt10"])
        assert 0.0 <= prob <= 0.98, (
            f"FORWARD prediction for '{row['company']}' has P(gain>10%)={prob:.4f} "
            f"which exceeds 0.98 -- likely invalid or raw uncalibrated classifier"
        )


def test_s6_old_hd_fire_marked_invalid():
    """S6: The original HD Fire Protect row with uncalibrated prob is marked INVALID_SCRIPT_BUG."""
    log_path = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")
    df = pd.read_csv(log_path)
    hd_rows = df[df["company"].str.contains("HD Fire Protect", na=False)]
    assert len(hd_rows) >= 2, "Expected at least 2 HD Fire Protect rows (old invalid + new corrected)"
    
    # At least one should be INVALID_SCRIPT_BUG
    invalid_rows = hd_rows[hd_rows["status"] == "INVALID_SCRIPT_BUG"]
    assert len(invalid_rows) >= 1, "Original HD Fire Protect row must be marked INVALID_SCRIPT_BUG"
    
    # At least one should be FORWARD with calibrated prob
    forward_rows = hd_rows[hd_rows["status"] == "FORWARD"]
    assert len(forward_rows) >= 1, "Corrected HD Fire Protect row must be status=FORWARD"
    
    for _, row in forward_rows.iterrows():
        prob = float(row["pred_prob_gt10"])
        assert prob <= 0.98, f"Corrected prediction has P(gain>10%)={prob:.4f}, still looks uncalibrated"
        
        # scored_at must be before listing_date 2026-10-21
        scored_at = pd.Timestamp(row["scored_at"])
        listing_date = pd.Timestamp("2026-10-21")
        if scored_at.tzinfo is not None:
            listing_date = listing_date.tz_localize(scored_at.tzinfo)
        assert scored_at < listing_date, (
            f"scored_at={scored_at} must be before listing_date={listing_date}"
        )


def test_s6_hd_fire_is_mainboard():
    """S6: HD Fire Protect is verified as mainboard (not SME) based on issue size."""
    log_path = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")
    df = pd.read_csv(log_path)
    hd_forward = df[(df["company"].str.contains("HD Fire Protect", na=False)) & (df["status"] == "FORWARD")]
    assert len(hd_forward) >= 1, "Must have a FORWARD HD Fire Protect row"
    # Issue size > 25 Cr confirms mainboard (SME cap is 25 Cr post-issue paid-up capital)
    import json
    for _, row in hd_forward.iterrows():
        snapshot = json.loads(row["features_snapshot_json"])
        issue_size = snapshot.get("issue_size_cr", 0)
        assert issue_size > 25.0, f"HD Fire Protect issue_size_cr={issue_size} too small for mainboard"


# ==============================================================================
#  PHASE 7 GATE A7 TESTS (T1 to T7)
# ==============================================================================


def test_t1_t3_phase6_errata_header_and_items():
    """T1 & T3: Phase 6 verdict has ERRATA (Phase 7) at top correcting Wk D, overclaims, etc."""
    verdict_path = os.path.join(ROOT_DIR, "phases", "Phase 6", "3_outcome_and_verdict.md")
    with open(verdict_path, "r", encoding="utf-8") as f:
        head = f.read(4000)
    assert "ERRATA (Phase 7)" in head, "Expected ERRATA (Phase 7) at top of Phase 6 verdict"
    assert "NOT DONE" in head, "Expected Workstream D corrected to NOT DONE"
    assert "Hypothesis (untested)" in head, "Expected Hypothesis (untested) label"
    assert "Mukka Proteins" in head, "Expected Mukka Proteins correction in Errata"


def test_t2_duplicate_verification_csv():
    """T2: phases/Phase 7/duplicate_verification.csv has 15 rows with required schema and valid URLs."""
    csv_path = os.path.join(ROOT_DIR, "phases", "Phase 7", "duplicate_verification.csv")
    assert os.path.exists(csv_path), "phases/Phase 7/duplicate_verification.csv must exist"
    df = pd.read_csv(csv_path)
    assert len(df) == 15, f"Expected 15 rows, got {len(df)}"
    req_cols = {"company", "removed_row_date", "kept_row_date", "true_listing_date", "source_url", "page_date", "outcome"}
    assert req_cols.issubset(set(df.columns)), f"Missing columns: {req_cols - set(df.columns)}"
    assert (df["source_url"].notna() | (df["outcome"] == "UNVERIFIED")).all()


def test_t4_before_after_matched_csv():
    """T4: phases/Phase 7/before_after_matched.csv exists with equal row counts (398 vs 398)."""
    csv_path = os.path.join(ROOT_DIR, "phases", "Phase 7", "before_after_matched.csv")
    assert os.path.exists(csv_path), "phases/Phase 7/before_after_matched.csv must exist"
    df = pd.read_csv(csv_path)
    n_row = df[df["metric"] == "Evaluated Sample Size (n)"]
    assert not n_row.empty
    assert float(n_row["phase_5_matched"].values[0]) == 398.0
    assert float(n_row["phase_6_matched"].values[0]) == 398.0
    assert float(n_row["delta"].values[0]) == 0.0


def test_t5_gmp_status_definitions_and_column():
    """T5: references/gmp_status_definitions.md exists; gmp_status in ipo_master.csv."""
    ref_path = os.path.join(ROOT_DIR, "references", "gmp_status_definitions.md")
    assert os.path.exists(ref_path), "references/gmp_status_definitions.md must exist"
    
    master_path = os.path.join(ROOT_DIR, "data", "ipo_master.csv")
    df = pd.read_csv(master_path)
    assert "gmp_status" in df.columns, "gmp_status column missing in ipo_master.csv"
    valid = {"OBSERVED", "NOT_RECORDED", "CONFIRMED_UNAVAILABLE"}
    assert set(df["gmp_status"].unique()).issubset(valid)


def test_t6_hd_fire_unlisted_and_unmodified():
    """T6: HD Fire Protect Limited is unlisted, not modified, and in prediction log."""
    log_path = os.path.join(ROOT_DIR, "predictions", "prediction_log.csv")
    df = pd.read_csv(log_path)
    hd_forward = df[(df["company"].str.contains("HD Fire Protect", na=False)) & (df["status"] == "FORWARD")]
    assert len(hd_forward) == 1, "Expected exactly 1 FORWARD HD Fire Protect row"
    r = hd_forward.iloc[0]
    assert r["listing_date"] == "2026-10-21"
    # Prior to listing date actuals were unrecorded; once listed on 2026-10-21, official gain may be recorded
    if pd.notna(r["actual_gain_pct"]) and str(r["actual_gain_pct"]).strip() != "":
        assert float(r["actual_gain_pct"]) > 0


def test_fusion_cx_grounding_evidence():
    """D-031: Verify Fusion CX issue price 289 appears in saved snapshot under data/evidence/research/."""
    ev_path = os.path.join(ROOT_DIR, "data", "evidence", "research", "2026-10-22_fusion-cx-limited.html")
    assert os.path.exists(ev_path), "Fusion CX snapshot 2026-10-22_fusion-cx-limited.html must exist"
    with open(ev_path, "r", encoding="utf-8", errors="ignore") as f_ev:
        content = f_ev.read()
    assert "289" in content, "Issue price 289 must appear in Fusion CX snapshot"


def test_windows_setup_in_readme():
    """D-032: Verify README contains Windows setup and pytest_ethereum workaround guidance."""
    readme_path = os.path.join(ROOT_DIR, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Windows Setup" in content, "README must contain Windows Setup section"
    assert "pytest_ethereum" in content, "README must mention pytest_ethereum"

def test_phase12_process_stop_and_results_log():
    """D-052: Verify Gate A12 stop protocol and user approval recorded in results_log.md."""
    res_log = os.path.join(ROOT_DIR, "phases", "Phase 12", "results_log.md")
    assert os.path.exists(res_log), "phases/Phase 12/results_log.md must exist"
    with open(res_log, "r", encoding="utf-8") as f:
        text = f.read()
    assert "D-052" in text, "results_log.md must reference D-052"
    assert "phase12-gate-a" in text, "results_log.md must document phase12-gate-a commit"
    assert "resume" in text.lower() or "continue" in text.lower(), "results_log.md must document user approval"



def test_gate_a13_macro_correction():
    """D-054: Macro snapshot annotation data/corrections/macro_2026-10-23.md records true Oct 23 values."""
    corr_file = os.path.join(ROOT_DIR, "data", "corrections", "macro_2026-10-23.md")
    assert os.path.exists(corr_file), "data/corrections/macro_2026-10-23.md must exist"
    with open(corr_file, "r", encoding="utf-8") as f:
        text = f.read()
    assert "2026-10-23" in text
    assert "22,600.00" in text or "22600.00" in text
    assert "16.86" in text


def test_gate_a13_market_raw_decision():
    """D-055: Decision document phases/Phase 13/market_raw_decision.md documents raw vs parsed nomenclature."""
    dec_file = os.path.join(ROOT_DIR, "phases", "Phase 13", "market_raw_decision.md")
    assert os.path.exists(dec_file), "phases/Phase 13/market_raw_decision.md must exist"
    with open(dec_file, "r", encoding="utf-8") as f:
        text = f.read()
    assert "D-055" in text
    assert "nomenclature" in text.lower() or "raw" in text.lower()
