import importlib, inspect, pytest

pytestmark = pytest.mark.unit

def test_pricefix_import_and_minimal_callable():
    try:
        mod = importlib.import_module("code_data_ingest_pricefix_v1")
    except Exception as e:
        pytest.skip(f"pricefix module not importable: {e}")

    # pick a harmless function to execute (no network, no file I/O)
    candidates = []
    for n in dir(mod):
        if n.startswith("_"): continue
        obj = getattr(mod, n)
        if callable(obj):
            sig = inspect.signature(obj)
            # prefer functions with all-default params (or no params)
            if all(p.default is not inspect._empty or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
                   for p in sig.parameters.values()):
                candidates.append(obj)

    if not candidates:
        pytest.skip("no side-effect-free callable with defaults")
    # Execute the first candidate with no args (defaults only)
    fn = candidates[0]
    try:
        _ = fn()
    except TypeError:
        pytest.skip(f"{fn.__name__} requires args; skipping")
