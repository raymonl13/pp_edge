import pytest
from ingest.live_slate_v1 import fetch_slate
pytestmark = pytest.mark.unit
def test_fetch_slate_http_contract(monkeypatch):
    monkeypatch.setenv("PP_EDGE_TEST_MODE","1")
    class Resp:
        def __init__(self, payload): self._p = payload
        def raise_for_status(self): pass
        def json(self): return self._p
    class Sess:
        def get(self, url, headers=None, params=None, timeout=15):
            payload = [
                {"player":"X","game_id":"G1","prob":0.62,"edge":0.11,"team_id":"T1"},
                {"player":"Y","game_id":"G2","prob":0.55,"edge":0.05,"team_id":"T2"},
            ]
            return Resp(payload)
    slate = fetch_slate("2025-09-27", "MLB", source="http", session=Sess())
    assert isinstance(slate, list) and len(slate) >= 2
    for k in ("player","game_id","p_hit","edge_pp"):
        assert k in slate[0]
    assert 0.0 <= slate[0]["p_hit"] <= 1.0
