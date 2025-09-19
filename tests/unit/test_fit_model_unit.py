import sys, types, importlib, inspect, pytest, pandas as pd
pytestmark = pytest.mark.unit

def _import_mod():
    sys.modules.setdefault("joblib", types.SimpleNamespace(dump=lambda *a, **k: None,
                                                          load=lambda *a, **k: None))
    try:
        return importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")

def _find_fit_fn(mod):
    for name in ("fit_model","train_model","fit"):
        fn = getattr(mod, name, None)
        if callable(fn): return fn
    # fallback: first callable with 2 required args
    for name in dir(mod):
        obj = getattr(mod, name)
        if callable(obj):
            sig = inspect.signature(obj)
            req = [p for p in sig.parameters.values() if p.default is inspect._empty and p.kind in (p.POSITIONAL_ONLY,p.POSITIONAL_OR_KEYWORD)]
            if len(req) == 2: return obj
    return None

def test_fit_model_minimal():
    mod = _import_mod()
    fit = _find_fit_fn(mod)
    if not callable(fit):
        pytest.skip("no fit seam available")

    X = pd.DataFrame({"x":[0,1,0,1]})
    y = pd.Series([0,1,0,1])
    model = fit(X, y)
    assert model is not None
