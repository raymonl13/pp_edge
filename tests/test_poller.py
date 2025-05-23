import pathlib, json, requests, os
from unittest import mock
import poll_slip_results as ps

def _sample():
    return {"results": [{"slip_id": "abc", "status": "WON", "payout": 150.0, "updated_at": "2025-05-23T10:00:00Z"}]}

def test_poll_append(tmp_path):
    csv_path = tmp_path / "slip_results.csv"
    with mock.patch.object(requests, "get") as mg:
        mg.return_value.status_code = 200
        mg.return_value.json.return_value = _sample()
        ps.poll(csv_path)
    assert csv_path.exists()
    assert "abc" in csv_path.read_text()

def test_poll_no_network_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PP_EDGE_TEST_MODE", "1")
    csv_path = tmp_path / "slip_results.csv"
    ps.poll(csv_path)
    assert not csv_path.exists()
