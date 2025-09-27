import json, subprocess, sys, pytest, os, re
pytestmark = pytest.mark.unit

CSV = """player,game_id,p_hit,edge_pp,tag
A,g1,0.61,0.12,
B,g2,0.58,0.09,
C,g3,0.63,0.13,
"""

def test_cli_allocator_applies_caps_and_budget(tmp_path):
    slate = tmp_path / "slate.csv"
    slate.write_text(CSV)
    out = tmp_path / "slips.json"
    args = [
        sys.executable, "cli/run_offline.py", str(slate), str(out),
        "--bankroll","100","--slip-cap","2","--slate-cap-frac","0.05","--kelly","0.5"
    ]
    r = subprocess.run(args, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    data = json.loads(out.read_text())
    slips = data["slips"]
    assert len(slips) >= 1
    total = sum(s.get("stake_total",0) for s in slips)
    assert total <= 5.0 + 1e-9
    assert all(0 <= s.get("stake_total",0) <= 2.0 + 1e-9 for s in slips)
