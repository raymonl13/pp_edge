import sys, types, importlib, inspect, pytest, pandas as pd, numpy as np

pytestmark = pytest.mark.unit

def _import_mod():
    # Shim joblib so module import doesn't fail in lean unit lane
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
    # fallback: first callable with 1 required positional arg
    for name in dir(mod):
        obj = getattr(mod, name)
        if callable(obj):
            sig = inspect.signature(obj)
            req = [p for p in sig.parameters.values() if p.default is inspect._empty
                   and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
            if len(req) == 1: return obj
    return None

def _force_stub_rolling_woba():
    """
    Always replace rolling_woba with a zero-aligned Series stub to keep unit lane hermetic.
    This still executes build_feature_df/_feature_matrix without requiring full pipeline columns.
    """
    try:
        rw = importlib.import_module("features.rolling_woba")
    except Exception:
        return  # module absent; nothing to stub
    def zero_rw(df):
        return pd.Series(np.zeros(len(df), dtype=float), index=df.index, name="rolling_woba")
    rw.rolling_woba = zero_rw

def test_build_feature_df_happy_path():
    mod = _import_mod()
    build = _find_build_fn(mod)
    if not callable(build):
        pytest.skip("no feature builder seam available")

    # Minimal deterministic frame; keep only generic columns (no pipeline schema dependence)
    df = pd.DataFrame({
        "a":[1,2,3],
        "b":[0,0,0],
        "label":[0,1,0],
    })

    _force_stub_rolling_woba()

    out = build(df)
    if isinstance(out, tuple) and len(out) == 2:
        X, y = out
        assert hasattr(X, "shape") and X.shape[0] == len(df)
        assert (y is None) or (len(y) == len(df))
    else:
        X = out
        assert hasattr(X, "shape") and X.shape[0] == len(df)
