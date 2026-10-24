#!/usr/bin/env python3
"""verify_extra.py - Phase 12 independent checks (read-only). Do NOT edit to make a check pass.
Usage: python scripts/verify_extra.py [repo_root]
Catches: report numbers that contradict the prediction log, wrong evidence notes,
hard-coded dated numeric constants in code, missing market evidence for cited market moves."""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
res = []
def rec(status, name, detail=""):
    res.append((status, name, detail)); print(f"[{status}] {name:<88} {detail}")

# ---- load log
log = list(csv.DictReader(open(ROOT / "predictions/prediction_log.csv", encoding="utf-8")))
fwd = {}
for r in log:
    if r["status"] == "FORWARD":
        f = json.loads(r["features_snapshot_json"]); f["_row"] = r; fwd[r["company"]] = f
def who(line):
    """company a line is about: table row -> first cell; heading -> heading text; else None (keep context)"""
    t = line.strip()
    if t.startswith("|"):
        cell = t.strip("|").split("|")[0].lower()
    elif t.startswith("#"):
        cell = t.lower()
    else:
        return None
    for k, n in keys.items():
        if re.search(r"\b" + re.escape(k) + r"\b", cell): return n
    return None
def key(name): return name.lower().split()[0]
keys = {key(n): n for n in fwd}

# ---- docs in scope: Phase 11 onward
docs = [p for p in (ROOT / "phases").glob("Phase *") if p.name.split()[-1].isdigit() and int(p.name.split()[-1]) >= 11]
md_files = [m for d in docs for m in d.glob("*.md") if not m.name.startswith("1_planning")]
FIELD = {"qib": "sub_qib", "nii": "sub_nii", "retail": "sub_retail", "total": "sub_total"}
pat = re.compile(r"\b(QIB|NII|Retail|Total)\b[^0-9\n]{0,25}?(\d+(?:\.\d+)?)\s*x", re.I)

# 1. subscription multiples in prose/tables must equal the log for the company in context
bad = []
for m in md_files:
    cur = None
    for i, line in enumerate(m.read_text(encoding="utf-8").splitlines(), 1):
        cur = who(line) or cur
        if cur is None: continue
        for fld, val in pat.findall(line):
            truth = fwd[cur].get(FIELD[fld.lower()])
            if truth is None: continue
            if abs(float(val) - float(truth)) > 0.06 and not re.search(r"(100|>|≥|over|above|\+)", line[max(0,line.find(val)-6):line.find(val)]):
                bad.append(f"{m.relative_to(ROOT)}:{i} {cur} {fld} {val}x != log {truth}x")
rec("FAIL" if bad else "PASS", "subscription figures in Phase 11+ reports equal prediction_log values", f"{len(bad)} mismatches")
for b in bad[:20]: print("      ", b)

# 2. exchange/evidence notes: HD Fire's BSE code must not be reused for other companies
bad = []
for m in md_files:
    for i, line in enumerate(m.read_text(encoding="utf-8").splitlines(), 1):
        if "544994" in line and who(line) not in (None, "HD Fire Protect Limited"):
            bad.append(f"{m.relative_to(ROOT)}:{i}")
rec("FAIL" if bad else "PASS", "no company other than HD Fire cites BSE code 544994", f"{len(bad)} lines")
for b in bad[:10]: print("      ", b)

# 3. hard-coded dated numeric constants in code (data must be computed from evidence files)
rx = re.compile(r"""["']20\d\d-\d\d-\d\d["']\s*:\s*-?\d+\.\d+""")
bad = []
for p in list((ROOT / "scripts").glob("*.py")) + list((ROOT / "opi").glob("*.py")):
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if rx.search(line): bad.append(f"{p.relative_to(ROOT)}:{i}")
rec("FAIL" if bad else "PASS", "no hard-coded dated numeric constants in scripts/ or opi/", f"{len(bad)} lines")
for b in bad[:10]: print("      ", b)

# 4. any market move cited for a listing date needs a parsed market evidence file for that date
need = sorted({r["listing_date"] for r in (v["_row"] for v in fwd.values()) if r["actual_gain_pct"]})
missing = []
for d in need:
    ok = False
    for p in (ROOT / "data/evidence/market").glob(f"{d}*.json"):
        try:
            j = json.loads(p.read_text()); ok = ok or ("nifty_close" in j and any(k in j for k in ("nifty_prev_close", "nifty_day_return_pct")))
        except Exception: pass
    if not ok: missing.append(d)
rec("FAIL" if missing else "PASS", "each listed date has a parsed Nifty evidence file (close + prev close or day return)", f"missing: {', '.join(missing) or 'none'}")

# 5. explicit contradictions: a report line saying an IPO had "only"/"low" demand while log shows >50x in same file
bad = []
for m in md_files:
    cur = None
    for i, line in enumerate(m.read_text(encoding="utf-8").splitlines(), 1):
        cur = who(line) or cur
        if cur and re.search(r"\b(only|tepid|subdued|weak)\b[^.\n]{0,40}(subscription|demand)", line, re.I):
            q = fwd[cur].get("sub_qib") or 0
            if q > 50: bad.append(f"{m.relative_to(ROOT)}:{i} {cur} described weak but QIB={q}x")
rec("FAIL" if bad else "PASS", "no 'weak/only/subdued demand' text for IPOs with QIB > 50x", f"{len(bad)} lines")
for b in bad[:10]: print("      ", b)

# 6. README coverage numbers reconcile (two different champion coverage figures must be explained)
rd = (ROOT / "README.md").read_text(encoding="utf-8")
both = "91.2%" in rd and "87.94%" in rd
explained = bool(re.search(r"(differ|reconcil|different (protocol|sample|window))", rd, re.I))
rec("WARN" if both and not explained else "PASS", "README's two champion coverage figures (91.2% vs 87.94%) are reconciled in text", "")

# 7. secrets
import subprocess
g = subprocess.run(["git", "grep", "-nE", r"sk-or-v1-[A-Za-z0-9]{20,}"], cwd=ROOT, capture_output=True, text=True)
rec("FAIL" if g.stdout.strip() else "PASS", "no OpenRouter key material in tracked files", "")

n = lambda s: sum(1 for r in res if r[0] == s)
print(f"\nSUMMARY: {n('PASS')} pass, {n('WARN')} warn, {n('FAIL')} fail")
sys.exit(1 if n("FAIL") else 0)
