#!/usr/bin/env python3
"""Independent verification of the OPI repo (v2). Does NOT trust the phase reports.

Usage:  python scripts/verify_all.py            # run all checks
        python scripts/verify_all.py --no-tests # skip pytest (faster)
Exit code 1 if any check FAILS. WARN means "look at this", not "broken".
Run it at the START of every phase (to see what the previous phase left behind)
and at the END (to prove nothing is broken). Paste the full output in 2_building_and_execution.md.
"""
import argparse, re, subprocess, sys
from datetime import datetime, date
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = []  # (status, check, detail)

def add(status, name, detail=""):
    R.append((status, name, detail))

def read(path, **kw):
    p = ROOT / path
    return pd.read_csv(p, **kw) if p.exists() else None

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")

# ---------- 1. hygiene ----------
def check_hygiene():
    pats = [re.compile(r"file:///"), re.compile(r"/Users/")]
    skip_line = re.compile(r"grep|Relative links only|No `file", re.I)
    hits = []
    files = list((ROOT / "phases").rglob("*.md")) + [ROOT / "README.md", ROOT / "RULES.md"]
    for d in ("scripts", "model", "tests"):
        files += list((ROOT / d).rglob("*.py"))
    for f in files:
        if not f.exists() or f.name == "verify_all.py":
            continue
        for i, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
            if any(p.search(line) for p in pats) and not skip_line.search(line):
                hits.append(f"{f.relative_to(ROOT)}:{i}")
    add("FAIL" if hits else "PASS", "no absolute/local paths in docs or code", ", ".join(hits[:5]))

# ---------- 2. tests ----------
def check_tests():
    if not (ROOT / "tests").exists():
        add("FAIL", "pytest suite exists", "tests/ missing"); return
    r = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True, timeout=900)
    tail = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
    add("PASS" if r.returncode == 0 else "FAIL", "pytest suite passes", tail)

# ---------- 3. master integrity ----------
def check_master():
    m = read("data/ipo_master.csv", parse_dates=["open_date", "close_date", "listing_date"])
    if m is None:
        add("FAIL", "master dataset exists"); return None
    d = m.duplicated(["company", "listing_date"]).sum()
    add("FAIL" if d else "PASS", "no duplicate (company, listing_date)", f"{d} duplicates")
    calc = (m.listing_price - m.issue_price) / m.issue_price * 100
    bad = (((calc - m.listing_gain_pct).abs() > 0.5) & calc.notna() & m.listing_gain_pct.notna()).sum()
    add("FAIL" if bad else "PASS", "listing_gain_pct matches prices", f"{bad} mismatches")
    lab = (m.listing_gain_pct > 10).astype(int)
    bad = ((lab != m.label_good) & m.listing_gain_pct.notna()).sum()
    add("FAIL" if bad else "PASS", "label_good matches gain", f"{bad} mismatches")
    bad = ((m.open_date > m.close_date) | (m.close_date > m.listing_date)).sum()
    add("FAIL" if bad else "PASS", "date order open<=close<=listing", f"{bad} rows")
    ratio = m.listing_price / m.issue_price
    out = m[(ratio < 0.4) | (ratio > 4)]
    add("FAIL" if len(out) else "PASS", "no extreme listing/issue price ratios (FPO-type errors)",
        ", ".join(out.company.head(5)) if len(out) else "")
    g = m.gmp_pct.dropna()
    bad = ((g < -50) | (g > 300)).sum()
    add("FAIL" if bad else "PASS", "gmp_pct in plausible range", f"{bad} rows")
    ex = read("data/excluded_rows.csv")
    if ex is not None and len(ex):
        nourl = ex.source_url.isna().sum() if "source_url" in ex else len(ex)
        add("WARN" if nourl else "PASS", "every excluded row has a source URL", f"{nourl} without URL")
    return m

# ---------- 4. GMP evidence ----------
def check_gmp(m):
    g = read("data/gmp_sourced.csv", parse_dates=["listing_date", "as_of_date", "page_date", "accessed_on"])
    if g is None:
        add("WARN", "gmp_sourced.csv present", "not found"); return
    need = ["company", "listing_date", "gmp_pct", "as_of_date", "source_url", "page_date", "accessed_on"]
    miss = [c for c in need if c not in g.columns]
    if miss:
        add("FAIL", "gmp_sourced.csv has required columns", f"missing {miss}"); return
    bad = g[["source_url", "page_date", "accessed_on"]].isna().any(axis=1).sum()
    add("FAIL" if bad else "PASS", "every GMP value has URL, page date, access date", f"{bad} rows incomplete")
    if m is not None:
        j = g.merge(m[["company", "listing_date", "close_date", "listing_gain_pct"]], on=["company", "listing_date"], how="left")
        nj = j.close_date.isna().sum()
        add("FAIL" if nj else "PASS", "every sourced GMP row exists in master", f"{nj} unmatched")
        leak = ((j.as_of_date > j.close_date) | (j.as_of_date >= j.listing_date)).sum()
        add("FAIL" if leak else "PASS", "GMP as_of_date not after last bidding day (no leakage)", f"{leak} rows")
        late = (j.page_date >= j.listing_date).sum()
        add("WARN" if late else "PASS", "source page dated before listing", f"{late} rows dated on/after listing")
        old = m[(m.gmp_status == "OBSERVED") & ~m.set_index(["company", "listing_date"]).index.isin(g.set_index(["company", "listing_date"]).index)]
        e_new = (j.gmp_pct - j.listing_gain_pct).abs().mean()
        e_old = (old.gmp_pct - old.listing_gain_pct).abs().mean()
        if pd.notna(e_new) and pd.notna(e_old):
            add("WARN" if e_old - e_new > 1.5 else "PASS", "backfilled GMP not suspiciously closer to outcomes than older GMP",
                f"MAE backfilled {e_new:.2f} vs older {e_old:.2f}")
    if len(g) > 10 and g.accessed_on.nunique() == 1:
        add("WARN", "access dates vary", f"all {len(g)} rows share {g.accessed_on.iloc[0].date()}")
    if "confidence" in g and g.confidence.nunique() == 1 and len(g) > 10:
        add("WARN", "confidence levels vary", f"all rows '{g.confidence.iloc[0]}'")
    for f in sorted((ROOT / "phases").glob("*/gmp_second_source_check.csv")):
        s = pd.read_csv(f)
        dcol = "diff_pct_points"
        if dcol in s and len(s) >= 10 and (s[dcol].abs() < 1e-9).all():
            add("FAIL", f"second-source check credible ({f.parent.name})",
                f"all {len(s)} differences exactly 0.00: independent trackers do not agree to the hundredth")
        else:
            add("PASS", f"second-source check credible ({f.parent.name})")
    ev = ROOT / "data" / "evidence" / "gmp"
    if not ev.exists():
        add("FAIL", "saved page snapshots exist for GMP values", "data/evidence/gmp/ missing")
    else:
        have = {p.stem for p in ev.iterdir() if p.is_file()}
        miss = [r for r in g.itertuples() if f"{r.listing_date.date()}_{slug(r.company)}" not in have]
        add("FAIL" if miss else "PASS", "snapshot file for every sourced GMP row (<listing_date>_<company-slug>.*)", f"{len(miss)} of {len(g)} missing")

# ---------- 5. forward log ----------
def check_forward():
    l = read("predictions/prediction_log.csv", parse_dates=["scored_at"])
    if l is None:
        add("FAIL", "prediction_log.csv exists"); return
    ok = l.status.astype(str).str.match(r"^(FORWARD|TEST_.*|INVALID.*)$")
    add("FAIL" if (~ok).any() else "PASS", "log statuses valid", f"{(~ok).sum()} invalid")
    f = l[l.status == "FORWARD"].copy()
    add("PASS", "FORWARD rows logged", f"{len(f)} rows")
    if f.empty:
        return
    f["listing_date"] = pd.to_datetime(f.listing_date); f["close_date"] = pd.to_datetime(f.close_date)
    # scored_at: tz-naive values are assumed IST (+05:30); tz-aware values are converted to IST. New rows SHOULD carry an offset.
    sc = pd.to_datetime(f.scored_at, utc=False, errors="coerce", format="mixed")
    f["scored_utc"] = sc.apply(lambda t: t.tz_localize("Asia/Kolkata").tz_convert("UTC") if t.tzinfo is None else t.tz_convert("UTC"))
    f["scored_at"] = f.scored_utc.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
    late = (f.scored_at >= f.listing_date).sum()
    add("FAIL" if late else "PASS", "FORWARD rows scored before listing", f"{late} rows")
    # final-day rule: scored after bidding closed (assume 18:00 on close date, local time)
    close_cut = f.close_date + pd.Timedelta(hours=18)
    early = f[f.scored_at < close_cut]
    add("FAIL" if len(early) else "PASS", "FORWARD rows scored after bidding closed (final subscription)",
        ", ".join(early.company) + " scored before close" if len(early) else "")
    nonfinal = f[f.notes.astype(str).str.contains(r"day\s*[12]\b|live", case=False, regex=True)]
    add("FAIL" if len(nonfinal) else "PASS", "FORWARD rows use final (not day-1/live) subscription",
        ", ".join(nonfinal.company) if len(nonfinal) else "")
    p = f.pred_prob_gt10
    add("FAIL" if ((p < 0) | (p > 1)).any() else "PASS", "probabilities within [0,1]")
    dup = f.duplicated(["company", "listing_date"]).sum()
    add("FAIL" if dup else "PASS", "no duplicate FORWARD rows", f"{dup}")
    # backdating: a row's scored_at must match the real time the row was first committed (git is the clock)
    bad = []
    lraw = read("predictions/prediction_log.csv", dtype=str)
    for _, row in lraw[lraw.status == "FORWARD"].iterrows():
        raw = str(row.scored_at)
        r = subprocess.run(["git", "log", f"-S{raw}", "--format=%aI", "--", "predictions/prediction_log.csv"],
                           cwd=ROOT, capture_output=True, text=True)
        times = [pd.Timestamp(x).tz_convert("UTC") for x in r.stdout.split()]
        if not times:
            continue  # not yet committed
        first = min(times)
        t = pd.Timestamp(raw)
        t = t.tz_localize("Asia/Kolkata").tz_convert("UTC") if t.tzinfo is None else t.tz_convert("UTC")
        if t < first - pd.Timedelta(hours=2) or t > first + pd.Timedelta(minutes=10):
            bad.append(f"{row.company}: scored_at {raw} vs first commit {first.tz_convert('Asia/Kolkata'):%Y-%m-%d %H:%M} IST")
    add("FAIL" if bad else "PASS", "FORWARD scored_at matches first commit time (no backdating)", "; ".join(bad))
    early_act = f[(f.actual_gain_pct.notna()) & (f.listing_date.dt.date > date.today())]
    add("FAIL" if len(early_act) else "PASS", "no actuals for unlisted IPOs")
    nourl = (~f.features_snapshot_json.astype(str).str.contains("http")).sum()
    add("WARN" if nourl else "PASS", "FORWARD feature snapshots carry source URLs", f"{nourl} rows with only site names")
    t = read("data/ipo_phase5_final_test.csv")
    if t is not None:
        n_act = f.actual_gain_pct.notna().sum()
        add("FAIL" if len(t) > n_act else "PASS", "final test rows <= FORWARD rows with actuals", f"{len(t)} rows vs {n_act}")

# ---------- 6. phases structure + defects register ----------
def parse_defects():
    p = ROOT / "DEFECTS.md"
    if not p.exists():
        add("FAIL", "DEFECTS.md exists"); return None
    rows = []
    for line in p.read_text().splitlines():
        if re.match(r"^\|\s*D-\d+", line):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) >= 7:
                rows.append(dict(id=c[0], phase=c[1], desc=c[2], sev=c[3], status=c[4].upper(), due=c[5], test=c[6]))
    return rows

def check_phases_and_defects():
    phases = sorted((ROOT / "phases").glob("Phase *"), key=lambda p: int(p.name.split()[1]))
    for ph in phases:
        miss = [f for f in ("1_planning_and_goals.md", "2_building_and_execution.md", "3_outcome_and_verdict.md") if not (ph / f).exists()]
        add("FAIL" if miss else "PASS", f"{ph.name}: three required files", ", ".join(miss))
    rows = parse_defects()
    if rows is None:
        return
    openish = [r for r in rows if r["status"] in ("OPEN", "PARTIAL")]
    add("PASS", "defect register parsed", f"{len(rows)} defects, {len(openish)} open/partial")
    bad = []
    for r in rows:
        if r["status"] == "FIXED":
            m = re.search(r"(tests/[\w./-]+\.py)::(\w+)", r["test"])
            if not m:
                bad.append(f'{r["id"]} (no test ref)'); continue
            f = ROOT / m.group(1)
            if not f.exists() or m.group(2) not in f.read_text():
                bad.append(f'{r["id"]} (test not found)')
    add("FAIL" if bad else "PASS", "every FIXED defect has an existing regression test", ", ".join(bad[:6]))
    if phases:
        v = (phases[-1] / "3_outcome_and_verdict.md")
        if v.exists():
            head = v.read_text(errors="ignore")[:4000]
            claims_none = re.search(r"unfixed items[^\n]{0,40}\bNone\b", head, re.I) and "is **not true**" not in head
            add("FAIL" if (claims_none and openish) else "PASS", f"{phases[-1].name} verdict 'None unfixed' consistent with defect register",
                f"{len(openish)} defects still open/partial" if claims_none and openish else "")

# ---------- 7. git order ----------
def check_git():
    r = subprocess.run(["git", "log", "--reverse", "--format=%s"], cwd=ROOT, capture_output=True, text=True)
    subj = r.stdout.splitlines()
    for ph in sorted((ROOT / "phases").glob("Phase *"), key=lambda p: int(p.name.split()[1])):
        n = int(ph.name.split()[1])
        if n < 6:
            continue
        try:
            ga, pr = subj.index(f"phase{n}-gate-a"), subj.index(f"phase{n}-preregistration")
        except ValueError:
            add("FAIL", f"Phase {n}: gate and preregistration commits exist"); continue
        others = [i for i, s in enumerate(subj) if f"(phase{n})" in s]
        ok = (not others) or min(others) > max(ga, pr)
        add("PASS" if ok else "FAIL", f"Phase {n}: gate + preregistration committed before other work")

# ---------- 8. recompute headline numbers ----------
def ece_eqfreq(p, y, k=10):
    o = np.argsort(p); chunks = np.array_split(o, k); t = 0
    for c in chunks:
        t += len(c) / len(p) * abs(p[c].mean() - y[c].mean())
    return t

def check_recompute():
    phases = sorted((ROOT / "phases").glob("Phase *"), key=lambda p: int(p.name.split()[1]))
    for ph in reversed(phases):
        pr, ba = ph / "rolling_origin_predictions.csv", ph / "before_after_comparison.csv"
        if pr.exists() and ba.exists():
            break
    else:
        add("WARN", "recompute headline metrics", "no rolling_origin_predictions.csv + before_after_comparison.csv found"); return
    r, b = pd.read_csv(pr), pd.read_csv(ba)
    col = "phase_" + ph.name.split()[1]
    if col not in b:
        add("WARN", "recompute headline metrics", f"{col} column not found"); return
    got = {"MAE: Historical Mean Baseline": (r.pred_mean_baseline - r.actual_gain).abs().mean(),
           "MAE: Model Without Fundamentals": (r.pred_no_fundamentals - r.actual_gain).abs().mean(),
           "MAE: Model With Fundamentals": (r.pred_with_fundamentals - r.actual_gain).abs().mean(),
           "Equal-Frequency ECE": ece_eqfreq(r.pred_prob_calibrated.values, r.actual_class.values)}
    h = r[r.has_gmp == True]
    got["MAE: Raw GMP"] = (h.gmp_pct - h.actual_gain).abs().mean()
    got["MAE: Blend"] = (h.pred_blend - h.actual_gain).abs().mean()
    bad = []
    for k, v in got.items():
        row = b[b.metric == k]
        if row.empty:
            continue
        rep = float(row[col].iloc[0]); tol = 0.005 if "ECE" in k else 0.06
        if abs(rep - v) > tol:
            bad.append(f"{k}: reported {rep:.4f}, recomputed {v:.4f}")
    add("FAIL" if bad else "PASS", f"{ph.name} headline metrics recompute from raw predictions", "; ".join(bad))


# ---------- 9. new in v2 ----------
def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout

def check_fresh_clone():
    """Tests must pass on a CLEAN clone of the committed repo (no ignored/untracked files)."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        c = subprocess.run(["git", "clone", "-q", str(ROOT), td], capture_output=True, text=True)
        if c.returncode:
            add("FAIL", "fresh clone of repo", c.stderr[:200]); return
        r = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=td, capture_output=True, text=True, timeout=900)
        tail = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        add("PASS" if r.returncode == 0 else "FAIL", "pytest passes on a fresh clone (no untracked/ignored files)", tail)

def check_ci_model():
    wf = ROOT / ".github" / "workflows"
    if not wf.exists():
        add("WARN", "CI workflow present", "no .github/workflows"); return
    tracked = [x for x in git("ls-files", "model").splitlines() if x.endswith((".joblib", ".pkl"))]
    trains = any(re.search(r"train|retrain|build_model", p.read_text(errors="ignore")) for p in wf.glob("*.yml"))
    ok = bool(tracked) or trains
    add("PASS" if ok else "FAIL", "CI can obtain the model (tracked artifact or training step)",
        "" if ok else "model binary is untracked and workflows never train it")

def check_immutable_history():
    """Files of earlier phases must not be altered after the current phase's gate commit (errata may only ADD lines to .md)."""
    phases = sorted((ROOT / "phases").glob("Phase *"), key=lambda p: int(p.name.split()[1]))
    if len(phases) < 2:
        return
    n = int(phases[-1].name.split()[1])
    log = git("log", "--format=%H%x09%s").splitlines()
    gate = [x.split("\t")[0] for x in log if x.split("\t")[-1] == f"phase{n}-gate-a"]
    if not gate:
        add("WARN", "earlier-phase files unchanged", f"phase{n}-gate-a commit not found"); return
    base = git("rev-parse", gate[0] + "^").strip()
    bad = []
    for line in git("diff", "--numstat", base, "HEAD", "--", "phases").splitlines():
        a, d, path = line.split("\t", 2)
        m = re.match(r"phases/Phase (\d+)/", path)
        if not m or int(m.group(1)) >= n:
            continue
        if not path.endswith(".md") or (d.isdigit() and int(d) > 0):
            bad.append(path)
    add("FAIL" if bad else "PASS", f"earlier-phase artifacts unchanged since phase{n}-gate-a (errata may only add lines)",
        f"{len(bad)} changed: " + ", ".join(sorted(bad)[:4]) if bad else "")

def check_gmp_outliers_evidence(m):
    if m is None:
        return
    ev = ROOT / "data" / "evidence" / "gmp"
    have = {p.stem for p in ev.iterdir()} if ev.exists() else set()
    o = m[(m.gmp_status == "OBSERVED") & ((m.gmp_pct > 100) | (m.gmp_pct < -30))]
    miss = [r.company for r in o.itertuples() if f"{r.listing_date.date()}_{slug(r.company)}" not in have]
    add("FAIL" if miss else "PASS", "extreme GMP values (>100% or <-30%) have a snapshot or are NOT_RECORDED",
        f"{len(miss)} of {len(o)} without snapshot: " + ", ".join(miss[:4]) if miss else "")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--no-tests", action="store_true"); a = ap.parse_args()
    check_hygiene()
    if not a.no_tests:
        check_tests()
    m = check_master()
    fns = [lambda: check_gmp(m), check_forward, check_phases_and_defects, check_git, check_recompute,
           check_ci_model, check_immutable_history, lambda: check_gmp_outliers_evidence(m)]
    if not a.no_tests:
        fns.append(check_fresh_clone)
    for fn in fns:
        try:
            fn()
        except Exception as e:
            add("FAIL", f"check crashed: {getattr(fn, '__name__', 'check')}", repr(e)[:200])
    w = max(len(n) for _, n, _ in R)
    for s, n, d in R:
        print(f"[{s}] {n.ljust(w)}  {d}")
    c = {k: sum(1 for s, _, _ in R if s == k) for k in ("PASS", "WARN", "FAIL")}
    print(f"\nSUMMARY: {c['PASS']} pass, {c['WARN']} warn, {c['FAIL']} fail")
    sys.exit(1 if c["FAIL"] else 0)

if __name__ == "__main__":
    main()
