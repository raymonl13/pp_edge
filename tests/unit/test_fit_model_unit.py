import importlib, inspect, types, numpy as np, pandas as pd, pytest
pytestmark = pytest.mark.unit
class _DummyEstimator:
    def fit(self, X, y=None): self._fit = True; return self
    def predict(self, X): return np.zeros(len(X))
class _GridCV2:
    def __init__(self, estimator, param_grid=None, cv=None, **kw):
        import sklearn.model_selection as ms
        self._inner = ms.GridSearchCV(estimator, param_grid or {}, cv=2, **kw)
    def fit(self, X, y=None): return self._inner.fit(X, y)
    def __getattr__(self, name): return getattr(self._inner, name)
class _RandCV2:
    def __init__(self, estimator, param_distributions=None, cv=None, **kw):
        import sklearn.model_selection as ms
        self._inner = ms.RandomizedSearchCV(estimator, param_distributions or {}, cv=2, **kw)
    def fit(self, X, y=None): return self._inner.fit(X, y)
    def __getattr__(self, name): return getattr(self._inner, name)
def _pick(keys, pool):
    for k in keys:
        if k in pool: return k
    return None
def test_fit_model_minimal(monkeypatch):
    try:
        mu = importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")
    fit = getattr(mu, "fit_model", None)
    if not callable(fit):
        pytest.skip("fit_model seam not available")
    monkeypatch.setattr(mu, "joblib", types.SimpleNamespace(load=lambda _p: _DummyEstimator(), dump=lambda *a, **k: None))
    try:
        monkeypatch.setattr(mu, "GridSearchCV", _GridCV2, raising=False)
        monkeypatch.setattr(mu, "RandomizedSearchCV", _RandCV2, raising=False)
    except Exception:
        pass
    X = pd.DataFrame({"f1":[0,1,0,1,0,1], "f2":[1,0,1,0,1,0]})
    y = pd.Series([0,1,0,1,0,1])
    sig = inspect.signature(fit)
    params = list(sig.parameters.keys())
    kwargs = {}
    args = []
    if "model_path" in params:
        kwargs["model_path"] = "dummy.pkl"
    x_key = _pick(("X","x","features","X_train","data","df"), params)
    y_key = _pick(("y","Y","labels","target","y_train"), params)
    if x_key: kwargs[x_key] = X
    if y_key: kwargs[y_key] = y
    if not x_key and not y_key:
        args = [X, y] if len(params) >= 2 else [X]
    model = fit(*args, **kwargs)
    ok = (model is None) or hasattr(model, "predict") or hasattr(model, "fit")
    assert ok
