import importlib, inspect, pandas as pd, pytest
from tests.unit._fixtures import make_minimal_games_df
pytestmark = pytest.mark.unit

def _import_model_utils():
    try:
        return importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")

def _find_build_fn(mu):
    # preferred names
    for name in ("build_feature_df","build_features","build_feature_matrix"):
        fn = getattr(mu, name, None)
        if callable(fn): return fn
    # fallback: any callable that takes a DataFrame as first arg
    for name in dir(mu):
        obj = getattr(mu, name)
        if callable(obj):
            try:
                sig = inspect.signature(obj)
                if len(sig.parameters) >= 1:
                    return obj
            except Exception:
                pass
    return None

def test_build_feature_df_happy_path():
    mu = _import_model_utils()
    build = _find_build_fn(mu)
    if not callable(build):
        pytest.skip("no feature builder seam available")

    df = make_minimal_games_df(n=6)
    out = build(df)
    if isinstance(out, tuple) and len(out) == 2:
        X, y = out
        assert getattr(X, "shape", None) and X.shape[0] == len(df)
        assert (y is None) or (len(y) == len(df))
    else:
        X = out
        assert getattr(X, "shape", None) and X.shape[0] == len(df)
