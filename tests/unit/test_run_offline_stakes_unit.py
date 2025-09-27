import json, os, sys, pytest
from pathlib import Path
pytestmark = pytest.mark.unit

def test_run_offline_sets_stake_total(tmp_path, monkeypatch):
    from cli.run_offline import main
    out = tmp_path/"slips.json"
    rc = main("fixtures/slate_small.csv", str(out), unit=2.5)
    assert rc == 0 and out.exists()
    data = json.loads(out.read_text())
    for s in data["slips"]:
        assert s.get("stake_total") == 2.5
