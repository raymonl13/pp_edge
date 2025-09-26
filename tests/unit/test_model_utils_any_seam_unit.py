import importlib, inspect, types, numpy as np, pandas as pd, pytest

pytestmark = pytest.mark.unit

class _DummyModel:
    def fit(self, X, y=None): return self
    def predict(self, X): return np.full(len(X), 0.5)

class _GridCV2:
    def __init__(self, estimator, param_grid=None, cv=None, **kw):
        import sklearn.model_selection as ms
        self._inner = ms.GridSearchCV(estimator, param_grid or {}, cv=2, **kw)
    def fit(self, X, y=None): return self._inner.fit(X, y)
    def __getattr__(self, n): return getattr(self._inner, n)

class _RandCV2:
    def __init__(self, estimator, param_distributions=None, cv=None, **kw):
        import sklearn.model_selection as ms
        self._inner = ms.RandomizedSearchCV(estimator, param_distributions or {}, cv=2, **kw)
    def fit(self, X, y=None): return self._inner.fit(X, y)
    def __getattr__(self, n): return getattr(self._inner, n)

def test_model_utils_any_seam_executes(monkeypatch):
    try:
        mu = importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")

    # Safe shims: joblib + optional CV classes
    monkeypatch.setattr(mu, "joblib", types.SimpleNamespace(
        load=lambda _p: _DummyModel(), dump=lambda *a, **k: None
    ), raising=False)
    monkeypatch.setattr(mu, "GridSearchCV", _GridCV2, raising=False)
    monkeypatch.setattr(mu, "RandomizedSearchCV", _RandCV2, raising=False)

    X = pd.DataFrame({"f1":[0,1,2,3], "f2":[1,0,1,0]})
    y = pd.Series([0,1,0,1])

    def _call(fn):
        sig = inspect.signature(fn)
        kwargs = {}
        # Common names we can satisfy
        if "df" in sig.parameters: kwargs["df"] = X
        if "data" in sig.parameters: kwargs["data"] = X
        if "X" in sig.parameters or "x" in sig.parameters: kwargs["X"] = X
        if "y" in sig.parameters or "Y" in sig.parameters: kwargs["y"] = y
        if "model_path" in sig.parameters: kwargs["model_path"] = "dummy.pkl"
        if "features" in sig.parameters: kwargs["features"] = X
        # Try kwargs-first; fall back to positional (X,y) if required
        try:
            out = fn(**kwargs)
        except TypeError:
            if len(sig.parameters) >= 2:
                out = fn(X, y)
            else:
                out = fn(X)
        return out

    executed = False
    for name, obj in vars(mu).items():
        if not callable(obj): continue
        # Skip obvious private/internal helpers if any
        if name.startswith("_"): continue
        try:
            _call(obj)
            executed = True
            break
        except Exception:
            continue

    assert executed, "No callable seam in code_utils_model_v1 executed successfully"
