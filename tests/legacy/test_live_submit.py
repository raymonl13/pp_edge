import importlib, json, os, sys, types, pathlib

def test_live_submit(monkeypatch, tmp_path):
    ls = importlib.import_module("scripts.live_submit")
    sent = {}
    class DummyResp:
        text = "ok"
        def raise_for_status(self): pass
    def fake_post(url, json=None, headers=None, timeout=None):
        sent["url"], sent["json"], sent["headers"] = url, json, headers
        return DummyResp()
    monkeypatch.setattr(ls, "requests", types.SimpleNamespace(post=fake_post))
    monkeypatch.setenv("PPEDGE_MODE", "live")
    monkeypatch.setenv("PPEDGE_SUBMIT_URL", "https://api.example.com")
    monkeypatch.setenv("PPEDGE_LIVE_TOKEN", "tok")
    slip = tmp_path / "s.json"
    slip.write_text(json.dumps({"legs":[1]}))
    sys.argv = ["live_submit.py", str(slip)]
    assert ls.main() == 0
    assert sent["url"] == "https://api.example.com"
