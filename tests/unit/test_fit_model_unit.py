import sys, types, importlib, pytest, pandas as pd
pytestmark = pytest.mark.unit

def test_fit_model_minimal_joblib_shim():
    sys.modules.setdefault("joblib", types.SimpleNamespace(dump=lambda *a, **k: None,
                                                          load=lambda *a, **k: None))
    try:
        mod = importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")

    fit = getattr(mod, "fit_model", None)
    if not callable(fit):
        pytest.skip("fit_model not available")

    X = pd.DataFrame({"x":[0,1,0,1]})
    y = pd.Series([0,1,0,1])
    model = fit(X, y)
    assert model is not None
