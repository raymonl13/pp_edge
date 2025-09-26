import importlib, inspect, types, numpy as np, pandas as pd, pytest
pytestmark = pytest.mark.unit
class _DummyModel:
    def predict(self, X): return np.full(len(X), 0.42)
def test_predict_hit_prob_joblib_shim(monkeypatch):
    try:
        mu = importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")
    predict = getattr(mu, "predict_hit_prob", None)
    if not callable(predict):
        pytest.skip("predict_hit_prob seam not available")
    def _loader(_p):
        return _DummyModel()
    monkeypatch.setattr(mu, "joblib", types.SimpleNamespace(load=_loader))
    df = pd.DataFrame({"f1":[1,2,3], "f2":[0,0,0]})
    sig = inspect.signature(predict)
    if "model_path" in sig.parameters:
        out = predict(df, model_path="dummy.pkl")
    else:
        out = predict(df)
    out = np.asarray(out, dtype=float)
    assert out.shape == (3,)
    assert np.all((out >= 0.0) & (out <= 1.0))
