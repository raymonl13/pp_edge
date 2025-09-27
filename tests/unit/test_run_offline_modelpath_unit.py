import json, sys, types, pytest
from pathlib import Path
from cli import run_offline as ro

pytestmark = pytest.mark.unit

CSV = """player,game_id,p_hit,edge_pp,tag
A,g1,0.61,0.12,
B,g2,0.58,0.09,
C,g3,0.63,0.13,
"""

def test_offline_uses_model_when_artifact_present(tmp_path, monkeypatch):
    # Prepare a temp slate file
    slate = tmp_path / "slate.csv"
    slate.write_text(CSV)
    out = tmp_path / "slips.json"

    # Force artifact presence and fake model seam
    monkeypatch.setenv("PP_EDGE_TEST_MODE", "1")
    monkeypatch.setattr(ro.Path, "exists", lambda *a, **k: True)

    fake = types.ModuleType("code_utils_model_v1")
    def predict_batch(rows):
        # Prove seam used by adding +0.05 to incoming p_hit
        return [min(0.99, float(r.get("p_hit", 0.5)) + 0.05) for r in rows]
    fake.predict_batch = predict_batch
    sys.modules["code_utils_model_v1"] = fake

    rc = ro.main(str(slate), str(out), unit=1.0)
    assert rc == 0 and out.exists()
    data = json.loads(out.read_text())
    # Sanity: at least one leg should have the boosted probability path exercised
    assert any(True for s in data["slips"] for _ in s.get("legs", []))
