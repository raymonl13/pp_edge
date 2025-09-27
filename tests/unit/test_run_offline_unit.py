import json, subprocess, sys, pytest

pytestmark = pytest.mark.unit

CSV = """player,game_id,p_hit,edge_pp,tag
A,g1,0.61,0.12,
B,g2,0.58,0.09,
C,g3,0.63,0.13,
D,g4,0.57,0.08,
E,g5,0.60,0.11,Demon
F,g6,0.55,0.07,
"""

def test_run_offline_emits_slips_json(tmp_path):
    slate = tmp_path / "slate.csv"
    slate.write_text(CSV)
    out = tmp_path / "slips.json"
    r = subprocess.run(
        [sys.executable, "cli/run_offline.py", str(slate), str(out)],
        capture_output=True, text=True
    )
    assert r.returncode == 0, r.stderr
    assert out.exists()
    data = json.loads(out.read_text())
    assert "slips" in data and isinstance(data["slips"], list)
    for s in data["slips"]:
        assert 2 <= len(s.get("legs", [])) <= 6
