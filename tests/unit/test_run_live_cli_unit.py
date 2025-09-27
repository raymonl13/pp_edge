import json, sys, subprocess, pytest
pytestmark = pytest.mark.unit
def test_run_live_cli_with_fake_source(tmp_path, monkeypatch):
    data = [
        {"player":"A","game_id":"g1","p_hit":0.61,"edge_pp":0.12,"correlation_group":"T1"},
        {"player":"B","game_id":"g2","p_hit":0.58,"edge_pp":0.09,"correlation_group":"T2"},
        {"player":"C","game_id":"g3","p_hit":0.63,"edge_pp":0.13,"correlation_group":"T3"},
    ]
    fake = tmp_path/"fake.json"
    fake.write_text(json.dumps(data))
    monkeypatch.setenv("LIVE_FAKE_PATH", str(fake))
    monkeypatch.setenv("PP_EDGE_TEST_MODE","1")
    out = tmp_path/"slips.json"
    args = [
        sys.executable, "cli/run_live.py",
        "--date","2025-09-27","--sport","MLB","--source","fake",
        "--out", str(out),
        "--bankroll","100","--slip-cap","2","--slate-cap-frac","0.1","--kelly","0.5","--min-stake","0.25"
    ]
    r = subprocess.run(args, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    slips = json.loads(out.read_text())["slips"]
    assert len(slips) >= 1
    assert all(0 <= s["stake_total"] <= 2.0 for s in slips)
