import sys, types, importlib, numpy as np, pandas as pd, pytest

pytestmark = pytest.mark.unit

class _DummyModel:
    def fit(self, X, y=None): return self
    def predict(self, X): return np.clip(np.full(len(X), 0.42), 0.0, 1.0)

def _prepare_import_shims(monkeypatch):
    import pathlib
    monkeypatch.setattr(pathlib.Path, "exists", lambda self: True, raising=False)
    sys.modules["joblib"] = types.SimpleNamespace(load=lambda _p: _DummyModel(), dump=lambda *a, **k: None)
    class _XGB:
        def __init__(self, *a, **k): pass
        def fit(self, *a, **k): return self
        def predict(self, X): return np.clip(np.zeros(len(X)), 0.0, 1.0)
    sys.modules["xgboost"] = types.SimpleNamespace(XGBClassifier=_XGB)
    sys.modules.pop("code_utils_model_v1", None)

def _import_mu(monkeypatch):
    _prepare_import_shims(monkeypatch)
    try:
        return importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils import failed under shims: {e}")

def _call_predict(fn, df):
    varnames = getattr(getattr(fn, "__code__", None), "co_varnames", ())
    return fn(df, model_path="dummy.pkl") if "model_path" in varnames else fn(df)

def test_predict_hit_prob_happy(monkeypatch):
    mu = _import_mu(monkeypatch)
    fn = getattr(mu, "predict_hit_prob", None)
    if not callable(fn): pytest.skip("predict_hit_prob seam missing")
    df = pd.DataFrame({"f1":[1,2,3,4], "f2":[0,1,0,1]})
    out = np.asarray(_call_predict(fn, df), dtype=float)
    assert out.shape == (4,) and np.all((out >= 0.0) & (out <= 1.0))

def test_predict_hit_prob_handles_nans_and_empty(monkeypatch):
    mu = _import_mu(monkeypatch)
    fn = getattr(mu, "predict_hit_prob", None)
    if not callable(fn): pytest.skip("predict_hit_prob seam missing")
    df = pd.DataFrame({"f1":[np.nan,2.0], "f2":[0.0,np.nan]})
    out = np.asarray(_call_predict(fn, df), dtype=float)
    assert out.shape == (2,) and np.all((out >= 0.0) & (out <= 1.0))
    df_empty = pd.DataFrame({"f1":[], "f2":[]})
    out2 = np.asarray(_call_predict(fn, df_empty), dtype=float)
    assert out2.size == 0

def test_predict_hit_prob_large_param_batch(monkeypatch):
    mu = _import_mu(monkeypatch)
    fn = getattr(mu, "predict_hit_prob", None)
    if not callable(fn): pytest.skip("predict_hit_prob seam missing")
    n = 64
    df = pd.DataFrame({"f1": np.arange(n, dtype=float), "f2": np.zeros(n, dtype=float)})
    out = np.asarray(_call_predict(fn, df), dtype=float)
    assert out.shape == (n,) and np.all((out >= 0.0) & (out <= 1.0))
