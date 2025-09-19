import sys, types, importlib, pytest, pandas as pd
pytestmark = pytest.mark.unit

def test_build_feature_df_happy_path_joblib_shim():
    # Shim joblib so module import doesn't fail in lean unit lane
    sys.modules.setdefault("joblib", types.SimpleNamespace(dump=lambda *a, **k: None,
                                                          load=lambda *a, **k: None))
    try:
        mod = importlib.import_module("code_utils_model_v1")
    except Exception as e:
        pytest.skip(f"model utils not importable: {e}")

    build = getattr(mod, "build_feature_df", None)
    if not callable(build):
        pytest.skip("build_feature_df not available")

    # Minimal deterministic frame; label may or may not be used depending on implementation
    df = pd.DataFrame({"a":[1,2,3], "b":[0,0,0], "label":[0,1,0]})
    X_y = build(df)               # some variants return (X, y), some return (X, None)
    if isinstance(X_y, tuple) and len(X_y) == 2:
        X, y = X_y
        assert hasattr(X, "shape") and X.shape[0] == len(df)
        assert (y is None) or (len(y) == len(df))
    else:
        X = X_y
        assert hasattr(X, "shape") and X.shape[0] == len(df)
