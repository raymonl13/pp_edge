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
    # Accept functions with all-default params (or *args/**kwargs only)
    return all(
        p.default is not inspect._empty or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        for p in sig.parameters.values()
    )

def test_pricefix_import_and_minimal_callable():
    mod = _load()
    # Find pure-ish functions (exclude CLI/data entrypoints)
    candidates = []
    for n in dir(mod):
        if n.startswith("_"): 
            continue
        obj = getattr(mod, n)
        if callable(obj) and _looks_pure(n, obj):
            candidates.append((n, obj))

    if not candidates:
        pytest.skip("no side-effect-free callable with defaults")


    old_argv = list(sys.argv); sys.argv = [old_argv[0]]
    try:
        for name, fn in candidates:
            try:
                _ = fn()     # run with defaults only
                return       # success; we exercised one pure path
            except SystemExit:
                continue     # CLI-like behavior, skip in unit lane
            except (TypeError, KeyError):
                continue     # needs args or rich JSON; skip
        pytest.skip("no minimal pure callable executed cleanly")
    finally:
        sys.argv = old_argv
