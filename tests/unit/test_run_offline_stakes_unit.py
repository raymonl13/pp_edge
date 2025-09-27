import json, pytest
from cli.run_offline import main

pytestmark = pytest.mark.unit

CSV = """player,game_id,p_hit,edge_pp,tag
A,g1,0.61,0.12,
B,g2,0.58,0.09,
C,g3,0.63,0.13,
"""

def test_run_offline_sets_stake_total(tmp_path, monkeypatch):
    slate = tmp_path / "slate.csv"
    slate.write_text(CSV)
    out = tmp_path / "slips.json"
    rc = main(str(slate), str(out), unit=2.5)
    assert rc == 0 and out.exists()
    data = json.loads(out.read_text())
    for s in data["slips"]:
        assert s.get("stake_total") == 2.5
