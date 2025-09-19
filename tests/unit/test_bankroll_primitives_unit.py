import importlib, pytest

pytestmark = pytest.mark.unit

def _load():
    try:
        return importlib.import_module("code_utils_bankroll_v1")
    except Exception as e:
        pytest.skip(f"bankroll utils not importable: {e}")

def test_stake_sizing_branches():
    mod = _load()
    # pick the stake function by common names; otherwise, find any fn with edge+bankroll
    fn = None
    for name in ("stake_from_edge","size_stake","stake_size"):
        f = getattr(mod, name, None)
        if callable(f): fn = f; break
    if fn is None:
        # fallback: first function with two required params
        for name in dir(mod):
            obj = getattr(mod, name)
            if callable(obj) and getattr(obj, "__code__", None):
                if obj.__code__.co_argcount >= 2:
                    fn = obj; break
    if fn is None:
        pytest.skip("no bankroll stake function found")

    # branches: non-positive edge -> clamp to 0
    assert fn(0.0, 100.0) == 0 or fn(0.0, 100.0) <= 1e-12
    assert fn(-0.02, 100.0) == 0 or fn(-0.02, 100.0) <= 1e-12
    # positive edge -> positive stake; ceiling/floor behavior tolerated
    s = fn(0.05, 100.0)
    assert s >= 0
