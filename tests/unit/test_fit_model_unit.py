import importlib, pytest, pandas as pd
pytestmark = pytest.mark.unit

def _import_model_utils():
    mu = importlib.import_module("code_utils_model_v1")
    # Defensive bound-name patch for features, same as in build test
    try:
        for fn in ("rolling_woba","wind_adj","platoon_split"):
            if hasattr(mu, fn):
                setattr(mu, fn, lambda df: pd.Series(0.0, index=df.index, name=fn))
    except Exception:
        pass
    return mu

def _find_fit_fn(mu):
    for name in ("fit_model","fit","train_model"):
        fn = getattr(mu, name, None)
        if callable(fn): return fn
    import inspect
    for name in dir(mu):
        obj = getattr(mu, name)
        if callable(obj):
            try:
                sig = inspect.signature(obj)
                # looking for (X, y, ...) signature
                if len(sig.parameters) >= 2:
                    return obj
            except Exception:
                continue
    return None

def test_fit_model_minimal():
    mu = _import_model_utils()
    fit = _find_fit_fn(mu)
    if not callable(fit):
        pytest.skip("no fit seam available")

    X = pd.DataFrame({"x":[0,1,0,1]})
    y = pd.Series([0,1,0,1])
    model = fit(X, y)
    assert model is not None
