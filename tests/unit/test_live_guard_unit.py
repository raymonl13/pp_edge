import os, pytest
pytestmark = pytest.mark.unit
def test_live_guard_refuses_without_flag(monkeypatch):
    monkeypatch.delenv("PP_EDGE_LIVE", raising=False)
    monkeypatch.setenv("PP_EDGE_TEST_MODE","0")
    from ingest.live_slate_v1 import _require_live_guard
    with pytest.raises(RuntimeError):
        _require_live_guard("http")
def test_live_guard_allows_in_test_mode(monkeypatch):
    monkeypatch.setenv("PP_EDGE_TEST_MODE","1")
    from ingest.live_slate_v1 import _require_live_guard
    _require_live_guard("http")
