import pathlib, csv, os, sys
import tier_analytics as ta

def _make_csv(tmp, rows):
    p = tmp / "slip_results.csv"
    with p.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["slip_id","status","payout","stake","tier"])
        w.writeheader()
        w.writerows(rows)
    return p

def test_aggregate_basic(tmp_path):
    rows = [
        {"slip_id":"a","status":"WON","payout":"200","stake":"100","tier":"Demon"},
        {"slip_id":"b","status":"LOST","payout":"0","stake":"50","tier":"Demon"},
        {"slip_id":"c","status":"WON","payout":"90","stake":"45","tier":"Goblin"}
    ]
    csv_in = _make_csv(tmp_path, rows)
    agg = ta._aggregate(ta._read_slips(csv_in))
    tiers = {r[1]: r for r in agg}
    assert tiers["Demon"][2] == 2
    assert tiers["Demon"][3] == 1
    assert tiers["Demon"][6] == 50.0
    assert tiers["Goblin"][4] == 0

def test_write_and_path(tmp_path):
    out_rows = [["2025-05-23","Demon",1,1,0,1.0,100.0,0]]
    out_path = ta._write(out_rows, tmp_path)
    assert out_path.exists()
    with out_path.open() as fh:
        assert "Demon" in fh.read()

def test_env_skip(tmp_path, monkeypatch):
    monkeypatch.setenv("PP_EDGE_TEST_MODE","1")
    rows = [{"slip_id":"x","status":"WON","payout":"10","stake":"5","tier":"Goblin"}]
    _make_csv(tmp_path, rows)
    monkeypatch.setattr(sys, "argv", ["tier_analytics"])   # wipe pytest args
    ta.main()
