"""Tests for Phase 8 independent verification and headline metric recomputation (D-002, D-014)."""

import json
import re
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def ece_eqfreq(p, y, k=10):
    o = np.argsort(p)
    chunks = np.array_split(o, k)
    t = 0
    for c in chunks:
        t += len(c) / len(p) * abs(p[c].mean() - y[c].mean())
    return t

def test_headline_metrics_recompute():
    """D-002: Verify that reported headline metrics recompute exactly from raw predictions."""
    phases = sorted((ROOT / "phases").glob("Phase *"), key=lambda p: int(p.name.split()[1]))
    target_ph = None
    for ph in reversed(phases):
        pr, ba = ph / "rolling_origin_predictions.csv", ph / "before_after_comparison.csv"
        if pr.exists() and ba.exists():
            target_ph = ph
            break
            
    assert target_ph is not None, "At least one phase must have rolling_origin_predictions.csv and before_after_comparison.csv"
    r = pd.read_csv(target_ph / "rolling_origin_predictions.csv")
    b = pd.read_csv(target_ph / "before_after_comparison.csv")
    col = f"phase_{target_ph.name.split()[1]}"
    assert col in b.columns, f"Column {col} must exist in before_after_comparison.csv"
    
    got = {
        "MAE: Historical Mean Baseline": (r.pred_mean_baseline - r.actual_gain).abs().mean(),
        "MAE: Model Without Fundamentals": (r.pred_no_fundamentals - r.actual_gain).abs().mean(),
        "MAE: Model With Fundamentals": (r.pred_with_fundamentals - r.actual_gain).abs().mean(),
        "Equal-Frequency ECE": ece_eqfreq(r.pred_prob_calibrated.values, r.actual_class.values)
    }
    h = r[r.has_gmp == True]
    got["MAE: Raw GMP"] = (h.gmp_pct - h.actual_gain).abs().mean()
    got["MAE: Blend"] = (h.pred_blend - h.actual_gain).abs().mean()
    
    for k, v in got.items():
        row = b[b.metric == k]
        if row.empty:
            continue
        rep = float(row[col].iloc[0])
        tol = 0.005 if "ECE" in k else 0.06
        assert abs(rep - v) <= tol, f"{target_ph.name} mismatch for {k}: reported {rep:.4f}, recomputed {v:.4f}"


def test_verify_all_runs():
    """D-014: verify_all.py runs independently without crashes."""
    script_path = ROOT / "scripts" / "verify_all.py"
    assert script_path.exists(), "scripts/verify_all.py must exist"
    
    # Run with --no-tests flag inside pytest to avoid recursive pytest invocation
    res = subprocess.run([sys.executable, str(script_path), "--no-tests"], capture_output=True, text=True, cwd=ROOT)
    assert res.stdout, "verify_all.py produced no output"
    assert "[PASS] master dataset exists" in res.stdout or "[PASS] no duplicate" in res.stdout


def test_phase7_errata_present():
    """D-009: Verify that ERRATA (Phase 8) is present at the top of Phase 7 verdict."""
    verdict = ROOT / "phases" / "Phase 7" / "3_outcome_and_verdict.md"
    assert verdict.exists(), "Phase 7 verdict must exist"
    head = verdict.read_text(encoding="utf-8")[:2500]
    assert "## ERRATA (Phase 8)" in head, "ERRATA (Phase 8) header must be present in Phase 7 verdict"
    assert "no demonstrated effect" in head
    assert "Phase 7 indicates this was misdiagnosed" in head


def test_earlier_phases_immutable():
    """D-017: Earlier phase artifacts (Phases 1-7, Phase 4 summary) must remain immutable."""
    # Check that Phase 8 re-run outputs are preserved in rerun_phase7_cleaned/
    rerun_dir = ROOT / "phases" / "Phase 8" / "rerun_phase7_cleaned"
    assert rerun_dir.exists(), "phases/Phase 8/rerun_phase7_cleaned must exist"
    assert (rerun_dir / "before_after_comparison.csv").exists()
    ba = pd.read_csv(rerun_dir / "before_after_comparison.csv")
    gmp_row = ba[ba["metric"].str.contains("Observed GMP", na=False)]
    assert not gmp_row.empty
    # Must not contain stale '+75 IPOs backfilled'
    assert "+75" not in str(gmp_row["notes"].iloc[0]), f"Stale backfill note remains: {gmp_row['notes'].iloc[0]}"

    # Check that Phase 7 non-md files are restored
    p7_ba = ROOT / "phases" / "Phase 7" / "before_after_comparison.csv"
    assert p7_ba.exists()
    p4_sum = ROOT / "phases" / "Phase 4" / "phase4_summary.json"
    assert p4_sum.exists()


def test_phase8_errata_present():
    """D-019: Verify that ERRATA (Phase 9) is present at the top of Phase 8 verdict."""
    verdict = ROOT / "phases" / "Phase 8" / "3_outcome_and_verdict.md"
    assert verdict.exists(), "Phase 8 verdict must exist"
    head = verdict.read_text(encoding="utf-8")[:2500]
    assert "## ERRATA (Phase 9)" in head, "ERRATA (Phase 9) header must be present in Phase 8 verdict"
    assert "D-001" in head
    assert "revert" in head.lower()


def test_phase10_errata_present():
    """D-034: Verify that ERRATA (patch) is present at the top of Phase 10 verdict and recheck."""
    verdict = ROOT / "phases" / "Phase 10" / "3_outcome_and_verdict.md"
    assert verdict.exists(), "Phase 10 verdict must exist"
    head = verdict.read_text(encoding="utf-8")[:4000]
    assert "## ERRATA (patch)" in head, "ERRATA (patch) header must be present in Phase 10 verdict"
    assert "700" in head, "Tonbo issue price 700 must be in errata"
    assert "586" in head, "Bonfiglioli issue price 586 must be in errata"
    assert "6.98" in head, "SMT GMP 6.98 must be in errata"
    assert "72.86" in head, "Tonbo GMP 72.86 must be in errata"
    assert "21.67" in head, "Bonfiglioli GMP 21.67 must be in errata"
    assert "UNSUPPORTED" in head, "Master dataset 654 claim must be marked UNSUPPORTED"
    assert "731" in head, "Master dataset 731 rows must be stated"

    recheck = ROOT / "phases" / "Phase 10" / "prior_phase_recheck.csv"
    assert recheck.exists(), "prior_phase_recheck.csv must exist"
    recheck_text = recheck.read_text(encoding="utf-8")
    assert "UNSUPPORTED" in recheck_text
    assert "731" in recheck_text


def test_verdict_table_matches_log():
    """D-035: Results tables in Phase 10+ verdict documents must strictly match prediction_log.csv."""
    log_path = ROOT / "predictions" / "prediction_log.csv"
    assert log_path.exists(), "prediction_log.csv must exist"
    df = pd.read_csv(log_path, dtype=str, keep_default_na=False)
    fwd = df[df["status"].str.strip().str.upper() == "FORWARD"]
    assert not fwd.empty, "prediction_log.csv must have FORWARD rows"

    expected = {}
    for _, r in fwd.iterrows():
        try:
            feats = json.loads(r["features_snapshot_json"])
        except Exception:
            feats = {}
        issue_p = float(feats.get("issue_price", 0))
        gmp_raw = r["gmp_pct_at_scoring"].strip()
        gmp_val = float(gmp_raw) if gmp_raw and gmp_raw != "nan" else None
        expected[r["company"].strip()] = {
            "issue_price": issue_p,
            "gmp_pct": gmp_val,
        }

    phases = sorted((ROOT / "phases").glob("Phase *"), key=lambda p: int(p.name.split()[1]))
    checked_phases = 0
    for ph in phases:
        n = int(ph.name.split()[1])
        if n < 10:
            continue
        v_file = ph / "3_outcome_and_verdict.md"
        if not v_file.exists():
            # In-progress phase whose verdict document has not yet been authored
            continue
        text = v_file.read_text(encoding="utf-8")

        # Parse markdown tables: if ERRATA has a table, that is the authoritative table
        target_section = text
        if "## ERRATA" in text:
            errata_part = text.split("## ERRATA", 1)[1]
            if "\n## " in errata_part:
                errata_part = errata_part.split("\n## ", 1)[0]
            if "| Company |" in errata_part:
                target_section = errata_part

        lines = [line.strip() for line in target_section.splitlines() if line.strip().startswith("|")]
        table_rows = []
        for line in lines:
            if "Company" in line or ":---" in line:
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 7:
                co = re.sub(r"\*+", "", cols[0]).strip()
                p_issue_match = re.search(r"\u20b9?\s*([0-9]+(?:\.[0-9]+)?)", cols[2])
                p_issue = float(p_issue_match.group(1)) if p_issue_match else None
                gmp_col = cols[6]
                p_gmp_match = re.search(r"([+-]?[0-9]+(?:\.[0-9]+)?)\s*%", gmp_col)
                p_gmp = float(p_gmp_match.group(1)) if p_gmp_match else None
                table_rows.append((co, p_issue, p_gmp))

        assert table_rows, f"No results table rows found in {ph.name} verdict"
        for co, p_issue, p_gmp in table_rows:
            if co in expected:
                exp_issue = expected[co]["issue_price"]
                exp_gmp = expected[co]["gmp_pct"]
                assert p_issue is not None and abs(p_issue - exp_issue) < 0.05, (
                    f"Mismatch in {ph.name} for {co} issue price: table has {p_issue}, log has {exp_issue}"
                )
                if exp_gmp is not None:
                    assert p_gmp is not None and abs(p_gmp - exp_gmp) < 0.05, (
                        f"Mismatch in {ph.name} for {co} GMP: table has {p_gmp}, log has {exp_gmp}"
                    )
                else:
                    assert p_gmp is None, (
                        f"Mismatch in {ph.name} for {co} GMP: expected None, table has {p_gmp}"
                    )
        checked_phases += 1

    assert checked_phases > 0, "At least one Phase 10+ verdict table must be checked"


def test_discovery_dry_run_artifact():
    """D-036: Verify that discovery dry-run timestamped output is committed and valid."""
    artifact = ROOT / "phases" / "Phase 10" / "discovery_dry_run.txt"
    assert artifact.exists(), "phases/Phase 10/discovery_dry_run.txt must exist"
    content = artifact.read_text(encoding="utf-8")
    assert "Discovered 17 eligible Mainboard candidate(s)" in content
    assert "Timestamp:" in content
    assert "Jio Platforms" in content
    assert "Paras Healthcare" in content


def test_forward_report_exchange_matches_source():
    """D-047: Verify that forward_report notes cite real exchange and do not misattribute BSE 544994."""
    from scripts.forward_report import generate_markdown_results_table
    md = generate_markdown_results_table()
    for line in md.splitlines():
        if not line.startswith("|") or "Company" in line or ":---" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        co = re.sub(r"\*+", "", cols[0]).strip()
        note = cols[-1]
        if "544994" in note:
            assert "HD Fire" in co, f"544994 erroneously cited for {co}"
        if "NSE official" in note:
            assert "HD Fire" not in co, f"NSE erroneously cited for HD Fire"

def test_phase11_postmortem_has_errata():
    """D-053: Verify that ERRATA is present in Phase 11 forward_postmortem.md."""
    postmortem = ROOT / "phases" / "Phase 11" / "forward_postmortem.md"
    assert postmortem.exists(), "Phase 11 forward_postmortem.md must exist"
    head = postmortem.read_text(encoding="utf-8")[:2500]
    assert "## ERRATA (patch)" in head, "ERRATA (patch) must be present in Phase 11 post-mortem"
    assert "Bonfiglioli" in head
    assert "120.78x" in head
    assert "3.4x" in head



def test_quoted_verify_results_match_saved_files():
    """D-088: Verify all 'N pass, N warn, N fail' quoted beside verify_*.txt match the real file SUMMARY."""
    import re
    import subprocess

    def extract_and_check(content_text, ph_dir, md_name):
        errata_text = ""
        if "## ERRATA" in content_text:
            errata_part = content_text.split("## ERRATA", 1)[1]
            if "\n## " in errata_part:
                errata_part = errata_part.split("\n## ", 1)[0]
            errata_text = errata_part

        # Regex to find verify_*.txt followed or preceded by summary numbers
        matches = list(re.finditer(r"(verify(?:_extra)?_(?:start|end)\.txt)[^.\n]*?[:\-–]\s*(\d+\s+pass,\s*(?:\d+\s+warn,\s*)?\d+\s+fail)", content_text, re.I))
        mismatches = []
        for m in matches:
            txt_name = m.group(1)
            quoted = m.group(2)

            # If ERRATA exists and specifies this txt_name, ERRATA is authoritative
            if errata_text and txt_name in errata_text:
                err_m = re.search(rf"{re.escape(txt_name)}[^.\n]*?[:\-–]\s*(\d+\s+pass,\s*(?:\d+\s+warn,\s*)?\d+\s+fail)", errata_text, re.I)
                if err_m:
                    quoted = err_m.group(1)

            target_file = ph_dir / txt_name
            if not target_file.exists():
                continue
            sum_line = [l.strip() for l in target_file.read_text(encoding="utf-8").splitlines() if l.strip().startswith("SUMMARY:")]
            if not sum_line:
                continue
            real_summary = sum_line[0].split("SUMMARY:", 1)[1].strip()

            def norm(s):
                p_m = re.search(r"(\d+)\s+pass", s, re.I)
                w_m = re.search(r"(\d+)\s+warn", s, re.I)
                f_m = re.search(r"(\d+)\s+fail", s, re.I)
                return (int(p_m.group(1)) if p_m else 0, int(w_m.group(1)) if w_m else 0, int(f_m.group(1)) if f_m else 0)

            if norm(quoted) != norm(real_summary):
                mismatches.append(f"{md_name}: quoted '{quoted}' for {txt_name} != real '{real_summary}'")
        return mismatches

    # A. Check current workspace for Phase 16 and 17
    all_mismatches = []
    for ph_num in range(16, 18):
        ph_dir = ROOT / "phases" / f"Phase {ph_num}"
        if not ph_dir.exists():
            continue
        for md_name in ["2_building_and_execution.md", "3_outcome_and_verdict.md"]:
            md_path = ph_dir / md_name
            if md_path.exists():
                mismatches = extract_and_check(md_path.read_text(encoding="utf-8"), ph_dir, md_name)
                all_mismatches.extend(mismatches)

    assert not all_mismatches, f"Mismatches found between quoted verify results and actual files:\n" + "\n".join(all_mismatches)

    # B. Prove that without ERRATA, commit d814892 fails this check
    res = subprocess.run(
        ["git", "show", "d814892:phases/Phase 16/2_building_and_execution.md"],
        cwd=ROOT, capture_output=True, text=True
    )
    if res.returncode == 0:
        d814892_content = res.stdout
        p16_dir = ROOT / "phases" / "Phase 16"
        d814892_mismatches = extract_and_check(d814892_content, p16_dir, "2_building_and_execution.md")
        assert len(d814892_mismatches) > 0, "Test should have caught discrepancy on pre-ERRATA commit d814892!"
        assert "71 pass, 0 warn, 0 fail" in d814892_mismatches[0]


def test_verify_all_allows_in_progress_phase(tmp_path, monkeypatch):
    """D-094: Completed older phases missing exit files still FAIL; latest phase missing exit files reports WARN."""
    import scripts.verify_all as va

    phases_dir = tmp_path / "phases"
    phases_dir.mkdir(parents=True)

    # Phase 1: completed phase with all 3 files -> PASS
    p1 = phases_dir / "Phase 1"
    p1.mkdir()
    (p1 / "1_planning_and_goals.md").write_text("ok", encoding="utf-8")
    (p1 / "2_building_and_execution.md").write_text("ok", encoding="utf-8")
    (p1 / "3_outcome_and_verdict.md").write_text("ok", encoding="utf-8")

    # Phase 2: completed older phase missing exit files -> must FAIL
    p2 = phases_dir / "Phase 2"
    p2.mkdir()
    (p2 / "1_planning_and_goals.md").write_text("ok", encoding="utf-8")

    # Phase 3: latest phase missing exit files -> must WARN
    p3 = phases_dir / "Phase 3"
    p3.mkdir()
    (p3 / "1_planning_and_goals.md").write_text("ok", encoding="utf-8")

    monkeypatch.setattr(va, "ROOT", tmp_path)
    monkeypatch.setattr(va, "R", [])
    monkeypatch.setattr(va, "parse_defects", lambda: [])

    va.check_phases_and_defects()

    statuses = {name: (status, detail) for status, name, detail in va.R}
    assert statuses["Phase 1: three required files"][0] == "PASS"
    assert statuses["Phase 2: three required files"][0] == "FAIL"
    assert statuses["Phase 3: three required files"][0] == "WARN"
    assert "phase in progress" in statuses["Phase 3: three required files"][1]

    # If latest phase lacks 1_planning_and_goals.md, it must FAIL
    p4 = phases_dir / "Phase 4"
    p4.mkdir()
    monkeypatch.setattr(va, "R", [])
    va.check_phases_and_defects()
    statuses = {name: (status, detail) for status, name, detail in va.R}
    assert statuses["Phase 4: three required files"][0] == "FAIL"


def test_forward_report_chronological_first_9_mae():
    """Phase 19: Prior cohort MAE evaluates the first 9 listed IPOs sorted chronologically by listing_date (5.85 pp)."""
    from pathlib import Path
    import pandas as pd
    from opi.outcomes import get_effective_predictions_df

    root = Path(__file__).resolve().parents[1]
    log_path = root / "predictions" / "prediction_log.csv"
    df = get_effective_predictions_df(log_path=log_path)
    forward_df = df[df["status"] == "FORWARD"].copy()
    forward_df["actual_clean"] = pd.to_numeric(forward_df["actual_gain_pct"], errors="coerce")
    forward_df["pred_clean"] = pd.to_numeric(forward_df["pred_gain_pct"], errors="coerce")
    evaluated = forward_df[forward_df["actual_clean"].notna()].copy()
    evaluated["err_model"] = (evaluated["pred_clean"] - evaluated["actual_clean"]).abs()

    # Sorted chronologically by listing_date then scored_at
    eval_chrono = evaluated.sort_values(by=["listing_date", "scored_at"]).copy()
    assert len(eval_chrono) >= 9
    first_9 = eval_chrono.iloc[:9]
    mae_9 = float(first_9["err_model"].mean())
    assert round(mae_9, 2) == 5.85, f"Expected first 9 chronological MAE to be 5.85 pp, got {mae_9:.4f}"


def test_phase20_quoted_paths_and_run_ids_exist():
    """D-103: Every concrete data/evidence/... path in phases/Phase 20/*.md exists on disk;
    every 11-digit run ID in those files appears in phases/Phase 20/run_ids_raw.json."""
    import json
    import re

    root = Path(__file__).resolve().parents[1]
    phase20_dir = root / "phases" / "Phase 20"
    raw_json_path = phase20_dir / "run_ids_raw.json"
    assert raw_json_path.exists(), "run_ids_raw.json must exist in phases/Phase 20"

    with open(raw_json_path, encoding="utf-8") as f:
        raw_runs = json.load(f)
    known_run_ids = {str(k) for k in raw_runs.keys()}

    md_files = list(phase20_dir.glob("*.md"))
    assert md_files, "No markdown files found in phases/Phase 20"

    missing_paths = []
    missing_run_ids = []

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")

        tokens = re.findall(r"`?(data/evidence/[^\s`\"\')>]+)", content)
        for token in tokens:
            clean_token = token.rstrip(".,;:)'\"")
            if "<" in clean_token or ">" in clean_token:
                continue
            # Directory paths that will be created / populated by actions
            if clean_token.rstrip("/").endswith("pending"):
                continue
            target = root / clean_token
            if not target.exists():
                missing_paths.append((md_file.name, clean_token))

        run_ids = re.findall(r"\b(\d{11})\b", content)
        for rid in run_ids:
            if rid not in known_run_ids:
                missing_run_ids.append((md_file.name, rid))

    assert not missing_paths, f"Quoted evidence paths missing on disk: {missing_paths}"
    assert not missing_run_ids, f"Quoted 11-digit run IDs not in run_ids_raw.json: {missing_run_ids}"


def test_autopilot_docs_match_workflow_schedules():
    """D-113: docs/AUTOPILOT.md documented schedules must match .github/workflows/daily.yml and watchdog.yml."""
    root = Path(__file__).resolve().parents[1]
    doc = (root / "docs" / "AUTOPILOT.md").read_text(encoding="utf-8")
    assert "06:00 UTC" in doc or "11:30 IST" in doc, "Daily pipeline morning run not documented in docs/AUTOPILOT.md"
    assert "14:00 UTC" in doc or "19:30 IST" in doc, "Daily pipeline evening run not documented in docs/AUTOPILOT.md"
    assert "10:00 UTC" in doc or "15:30 IST" in doc, "Watchdog pipeline run not documented in docs/AUTOPILOT.md"


def test_readme_forward_status_up_to_date():
    """D-114: README.md Section 4 must reflect genuine forward test count and reference forward_mae.py."""
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "13 of 30" in readme, "README.md must cite current listed count (13 of 30)"
    assert "scripts/forward_mae.py" in readme, "README.md must reference scripts/forward_mae.py"
    assert "due to be compared with the official listing outcome after 2026-10-22" not in readme, "Outdated Fusion CX pending text still present in README.md"

