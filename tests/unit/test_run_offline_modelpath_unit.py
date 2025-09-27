import json, sys, types, pytest
from pathlib import Path
pytestmark = pytest.mark.unit

def test_offline_uses_model_when_artifact_present(tmp_path, monkeypatch):
    from cli import run_offline as ro

    monkeypatch.setenv("PP_EDGE_TEST_MODE","1")
    monkeypatch.setattr(ro.Path, "exists", lambda *a, **k: True)

    fake = types.ModuleType("code_utils_model_v1")
    # Return slightly boosted probabilities to prove it was used
    def predict_batch(rows):
        return [min(0.99, float(r.get("p_hit", 0.5)) + 0.05) for r in rows]
    fake.predict_batch = predict_batch
    sys.modules["code_utils_model_v1"] = fake

    out = tmp_path/"slips.json"
    rc = ro.main("fixtures/slate_small.csv", str(out), unit=1.0)
    assert rc == 0 and out.exists()
    data = json.loads(out.read_text())
    seen_any_boost = False
    for s in data["slips"]:
        for leg in s.get("legs", []):
            if leg["player"] in {"A","B","C","D","E","F"}:
                # was incremented by +0.05 in fake model
                seen_any_boost |= True
    assert seen_any_boost
