"""Offline regression tests for opi/actuals.py and opi/log.update_actual_outcome (no network)."""
import json
from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest

import opi.actuals as actuals
import opi.log as oplog

COLS = ["scored_at", "company", "open_date", "close_date", "listing_date", "features_snapshot_json",
        "pred_gain_pct", "pred_prob_gt10", "gmp_pct_at_scoring", "actual_gain_pct", "status", "notes"]
URL = "https://www.nseindia.com/market-data/listing/test-co"


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(actuals, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(oplog, "ROOT_DIR", tmp_path)
    listing = datetime.now(actuals.IST).date() - timedelta(days=1)
    log = tmp_path / "predictions" / "prediction_log.csv"
    log.parent.mkdir(parents=True)
    row = {c: "" for c in COLS}
    row.update(scored_at="2026-10-10T20:00:00+05:30", company="Test Co", listing_date=listing.isoformat(),
               features_snapshot_json=json.dumps({"issue_price": 100.0}), pred_gain_pct="10", status="FORWARD", notes="scored with final data")
    pd.DataFrame([row], columns=COLS).to_csv(log, index=False)
    html = (f"<html><body><p>Test Co Ltd</p><p>Open Price 125.50</p>"
            f"<p>Date {listing.strftime('%d-%b-%Y')}</p></body></html>").encode()
    monkeypatch.setattr(actuals, "_fetch_exchange_page", lambda url, **k: (url, html, "text/html"))
    return dict(root=tmp_path, log=log, listing=listing)


def call(env, **over):
    kw = dict(company="Test Co", source_url=URL, listing_price=125.5, page_date=env["listing"].isoformat(),
              company_quote="Test Co Ltd", price_quote="Open Price 125.50", log_path=env["log"])
    kw.update(over)
    return actuals.record_actual_from_exchange(**kw)


def evidence_files(env):
    d = env["root"] / "data" / "evidence" / "actuals"
    return list(d.glob("*")) if d.exists() else []


def test_success_records_gain_snapshot_and_manifest(env):
    out = call(env)
    assert out["computed_listing_gain_pct"] == 25.5
    df = pd.read_csv(env["log"])
    assert float(df.actual_gain_pct.iloc[0]) == 25.5
    assert URL in str(df.notes.iloc[0])
    assert len(evidence_files(env)) == 2  # html + json manifest


def test_rejects_non_official_url(env):
    with pytest.raises(actuals.ActualsEvidenceError):
        call(env, source_url="https://example.com/x")
    assert evidence_files(env) == []


@pytest.mark.parametrize("bad", ["http://www.nseindia.com/x", "https://nseindia.com.evil.com/x",
                                 "https://user:pw@www.nseindia.com/x", "https://www.nseindia.com:8443/x"])
def test_url_lookalikes_rejected(bad):
    assert not actuals.is_official_exchange_url(bad)


def test_future_listing_rejected(env):
    df = pd.read_csv(env["log"], dtype=str, keep_default_na=False)
    df["listing_date"] = (datetime.now(actuals.IST).date() + timedelta(days=3)).isoformat()
    df.to_csv(env["log"], index=False)
    with pytest.raises(actuals.ActualsEvidenceError):
        call(env, page_date=df.listing_date.iloc[0])


def test_wrong_page_date_rejected(env):
    with pytest.raises(actuals.ActualsEvidenceError):
        call(env, page_date=(env["listing"] - timedelta(days=1)).isoformat())


def test_price_not_on_page_rejected(env):
    with pytest.raises(actuals.ActualsEvidenceError):
        call(env, listing_price=130.0, price_quote="Open Price 130.00")
    assert evidence_files(env) == []  # nothing saved on failure


def test_quote_without_opening_label_rejected(env):
    with pytest.raises(actuals.ActualsEvidenceError):
        call(env, price_quote="Price 125.50")


def test_company_quote_missing_rejected(env):
    with pytest.raises(actuals.ActualsEvidenceError):
        call(env, company_quote="Other Co Ltd")


def test_no_overwrite_second_call(env):
    call(env)
    with pytest.raises(actuals.ActualsEvidenceError):
        call(env)


def test_tampered_snapshot_blocks_log_update(env):
    out = call(env)
    snap = env["root"] / out["snapshot_path"]
    df = pd.read_csv(env["log"]); df["actual_gain_pct"] = float("nan"); df.to_csv(env["log"], index=False)
    snap.write_bytes(snap.read_bytes() + b"<!-- tampered -->")
    ok, msg = oplog.update_actual_outcome(company="Test Co", listing_date=env["listing"].isoformat(),
                                          actual_listing_price=125.5, issue_price=100.0, source_url=URL,
                                          source_snapshot_path=out["snapshot_path"], log_path=env["log"])
    assert not ok


def test_direct_gain_entry_disabled(env):
    ok, _ = oplog.update_actual_outcome(company="Test Co", listing_date=env["listing"].isoformat(), actual_gain_pct=50.0,
                                        log_path=env["log"])
    assert not ok


def test_redirect_to_non_official_host_rejected(monkeypatch):
    class R:
        is_redirect = True; is_permanent_redirect = False; status_code = 302
        headers = {"Location": "https://evil.example.com/x"}
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(actuals.requests, "get", lambda *a, **k: R())
    with pytest.raises(actuals.ActualsEvidenceError):
        actuals._fetch_exchange_page(URL)


def test_price_token_parsing():
    assert Decimal("1250.50") in actuals._decimal_price_tokens("Open Price Rs 1,250.50")
    assert Decimal("125.5") in actuals._decimal_price_tokens("Open Price 125.5")


def test_label_open_only_is_rejected_documented_limitation(env):
    """NSE/BSE quote pages usually say just 'Open'. The current rule demands 'Open Price'/'Listing Price'. Documented limitation."""
    with pytest.raises(actuals.ActualsEvidenceError):
        call(env, price_quote="Open 125.50")


def test_all_empty_notes_column_does_not_crash(env):
    """Robustness: a log whose notes column is entirely empty is read as float64 and string assignment can raise."""
    df = pd.read_csv(env["log"], dtype=str, keep_default_na=False)
    df["notes"] = ""
    df.to_csv(env["log"], index=False)
    call(env)  # must not raise TypeError
