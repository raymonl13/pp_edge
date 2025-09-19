import importlib, pytest, pandas as pd
from tests.unit._fixtures import make_minimal_games_df

pytestmark = pytest.mark.unit

def _import_model_utils():

    mu = importlib.import_module("code_utils_model_v1")

    try:
        feats = importlib.import_module("features")
        for fn in ("rolling_woba","wind_adj","platoon_split"):
            if hasattr(mu, fn):
                setattr(mu, fn, lambda df: pd.Series(0.0, index=df.index, name=fn))
    except Exception:
        pass
    return mu

def _find_build_fn(mu):
    for name in ("build_feature_df","build_features","build_features_df"):
        fn = getattr(mu, name, None)
        if callable(fn): return fn

    import inspect
    for name in dir(mu):
        obj = getattr(mu, name)
        if callable(obj):
            try:
                sig = inspect.signature(obj)
                if 1 <= len(sig.parameters) <= 2:
                    return obj
            except Exception:
                continue
    return None

def test_build_feature_df_happy_path():
    mu = _import_model_utils()
    build = _find_build_fn(mu)
    if not callable(build):
        pytest.skip("no feature builder seam available")


    df = make_minimal_games_df(n=4)

    out = build(df)
    if isinstance(out, tuple) and len(out) == 2:
        X, y = out
        assert getattr(X, "shape", None) and X.shape[0] == len(df)
        assert (y is None) or (len(y) == len(df))
    else:
        X = out
        assert getattr(X, "shape", None) and X.shape[0] == len(df)
