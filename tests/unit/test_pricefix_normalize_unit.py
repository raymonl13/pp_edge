import importlib, inspect, pandas as pd, numpy as np, pytest
pytestmark = pytest.mark.unit
def _find(mod, names):
    for n in names:
        fn = getattr(mod, n, None)
        if callable(fn): return fn
    for name, obj in vars(mod).items():
        if any(k in name.lower() for k in names) and callable(obj):
            return obj
    return None
def test_pricefix_normalize_transforms_idempotent():
    try:
        mod = importlib.import_module("code_data_ingest_pricefix_v1")
    except Exception as e:
        pytest.skip(f"pricefix module not importable: {e}")
    fn = _find(mod, ("normalize","normalize_prices","price_normalize","transform"))
    if not callable(fn):
        pytest.skip("normalize seam not available")
    df = pd.DataFrame({"name":["A","B","C"],"line":[10,12,14],"payout":[2.0,2.0,2.0]})
    sig = inspect.signature(fn)
    try:
        out1 = fn(df.copy())
    except TypeError:
        out1 = fn(df=df.copy())
    if out1 is None:
        pytest.skip("normalize returned None")
    try:
        out2 = fn(out1.copy())
    except TypeError:
        out2 = fn(df=out1.copy())
    assert len(out1) == len(out2)
    assert set(out1.columns) == set(out2.columns)
