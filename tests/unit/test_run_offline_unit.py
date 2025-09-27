import json, os, subprocess, sys, pytest
pytestmark = pytest.mark.unit
def test_run_offline_emits_slips_json(tmp_path):
    out = tmp_path/"slips.json"
    r = subprocess.run([sys.executable, "cli/run_offline.py", "fixtures/slate_small.csv", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert "slips" in data and isinstance(data["slips"], list)
    for s in data["slips"]:
        assert 2 <= len(s.get("legs",[])) <= 6
