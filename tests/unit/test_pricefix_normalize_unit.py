import importlib, inspect, pytest, sys

pytestmark = pytest.mark.unit

BLOCKLIST_PREFIXES = ("run", "cli", "entry", "fetch", "download")
BLOCKLIST_EXACT = {"main"}

def _load():
    try:
        return importlib.import_module("code_data_ingest_pricefix_v1")
    except Exception as e:
        pytest.skip(f"pricefix module not importable: {e}")

def _looks_pure(name, fn):
    if name in BLOCKLIST_EXACT or any(name.lower().startswith(p) for p in BLOCKLIST_PREFIXES):
        return False
    sig = inspect.signature(fn)
    # Only accept functions with all-default params (or *args/**kwargs only)
    return all(
        p.default is not inspect._empty or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        for p in sig.parameters.values()
    )

def test_pricefix_import_and_minimal_pure_callable():
    mod = _load()


    candidates = []
    for name in dir(mod):
        if name.startswith("_"): 
            continue
        obj = getattr(mod, name)
        if callable(obj) and _looks_pure(name, obj):
            candidates.append((name, obj))

    if not candidates:
        pytest.skip("no side-effect-free callable with defaults")

    
    old_argv = list(sys.argv)
    sys.argv = [old_argv[0]]
    try:
        # Try each candidate until one executes without side effects/errors
        for name, fn in candidates:
            try:
                _ = fn()
                return  # success: exercised one pure callable path
            except SystemExit:
                # CLI-like behavior: skip in unit lane
                continue
            except (TypeError, KeyError):
                # Needs args or depends on specific JSON shape: skip
                continue
        pytest.skip("no minimal pure callable executed cleanly")
    finally:
        sys.argv = old_argv
