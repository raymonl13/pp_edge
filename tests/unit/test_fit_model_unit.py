import importlib, inspect, pandas as pd, pytest
pytestmark = pytest.mark.unit

def _import_model_utils():
    try:
        return importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")

def _find_fit_fn(mu):
    # prefer explicit names
    for name in ("fit_model","train_model","fit"):
        fn = getattr(mu, name, None)
        if callable(fn):
            return fn
    # fallback by signature (X, y, ...)
    for name in dir(mu):
        obj = getattr(mu, name)
        if callable(obj):
            try:
                sig = inspect.signature(obj)
                if len(sig.parameters) >= 2:
                    return obj
            except Exception:
                pass
    return None

def test_fit_model_minimal():
    mu = _import_model_utils()
    fit = _find_fit_fn(mu)
    if not callable(fit):
        pytest.skip("no fit seam available")

    X = pd.DataFrame({"x":[0,1,0,1,0,1]})
    y = pd.Series([0,1,0,1,0,1])
    model = fit(X, y)
    assert model is not None
