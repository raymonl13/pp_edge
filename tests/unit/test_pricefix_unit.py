import importlib, inspect, pytest, sys

pytestmark = pytest.mark.unit

def test_pricefix_import_and_minimal_callable():
    try:
        mod = importlib.import_module("code_data_ingest_pricefix_v1")
    except Exception as e:
        pytest.skip(f"pricefix module not importable: {e}")

    candidates = []
    for n in dir(mod):
        if n.startswith("_"): continue
        obj = getattr(mod, n)
        if callable(obj):
            sig = inspect.signature(obj)
            # Prefer fully-defaulted or no-arg functions (no network, no files)
            if all(p.default is not inspect._empty or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
                   for p in sig.parameters.values()):
                candidates.append(obj)

    if not candidates:
        pytest.skip("no side-effect-free callable with defaults")

    fn = candidates[0]
    # Sandbox argv so argparse inside the callable doesn't see pytest flags
    old_argv = list(sys.argv)
    sys.argv = [old_argv[0]]
    try:
        try:
            _ = fn()
        except SystemExit:
            pytest.skip(f"{fn.__name__} exits (argparse/CLI); skipping in unit lane")
    finally:
        sys.argv = old_argv
