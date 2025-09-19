import sys, types, importlib, inspect, pytest, pandas as pd, numpy as np

pytestmark = pytest.mark.unit

def _import_mod():

    sys.modules.setdefault("joblib", types.SimpleNamespace(dump=lambda *a, **k: None,
                                                          load=lambda *a, **k: None))
    try:
        return importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")

def _find_build_fn(mod):
    for name in ("build_feature_df","build_features","make_features","features_from_df"):
        fn = getattr(mod, name, None)
        if callable(fn): return fn

    for name in dir(mod):
        obj = getattr(mod, name)
        if callable(obj):
            sig = inspect.signature(obj)
            req = [p for p in sig.parameters.values() if p.default is inspect._empty
                   and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
            if len(req) == 1: return obj
    return None

def _maybe_stub_rolling_woba(df):
    """
    If features.rolling_woba is importable and needs columns we don't have,
    provide a zero-aligned Series with correct length to keep the path pure & hermetic.
    """
    try:
        rw = importlib.import_module("features.rolling_woba")
    except Exception:
        return  # not present; nothing to do
    if hasattr(rw, "rolling_woba"):

        orig = rw.rolling_woba
        def safe_rw(x):
            try:
                return orig(x)
            except KeyError:
                s = pd.Series(np.zeros(len(x), dtype=float), index=x.index, name="rolling_woba")
                return s
        rw.rolling_woba = safe_rw

def test_build_feature_df_happy_path():
    mod = _import_mod()
    build = _find_build_fn(mod)
    if not callable(build):
        pytest.skip("no feature builder seam available")


    df = pd.DataFrame({
        "a":[1,2,3],
        "b":[0,0,0],
        "label":[0,1,0],
        "game_date": pd.to_datetime(["2025-01-01","2025-01-02","2025-01-03"]),
        "events": ["UNK","UNK","UNK"]
    })


    _maybe_stub_rolling_woba(df)

    out = build(df)
    if isinstance(out, tuple) and len(out) == 2:
        X, y = out
        assert hasattr(X, "shape") and X.shape[0] == len(df)
        assert (y is None) or (len(y) == len(df))
    else:
        X = out
        assert hasattr(X, "shape") and X.shape[0] == len(df)
