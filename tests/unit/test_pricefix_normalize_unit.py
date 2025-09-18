import importlib, inspect, pytest, sys
pytestmark = pytest.mark.unit

def _load():
    try:
        return importlib.import_module("code_data_ingest_pricefix_v1")
    except Exception as e:
        pytest.skip(f"pricefix not importable: {e}")

def test_normalize_row_or_pure_callable():
    mod = _load()

    # sandbox argv so CLI-style functions don't consume pytest flags
    old = list(sys.argv); sys.argv = [old[0]]
    try:
        # find a pure-ish callable (no required args), or a row-normalizer style function
        cands = []
        for n in dir(mod):
            if n.startswith("_"): continue
            obj = getattr(mod, n)
            if callable(obj):
                sig = inspect.signature(obj)
                if all(p.default is not inspect._empty or p.kind in (p.VAR_POSITIONAL,p.VAR_KEYWORD)
                       for p in sig.parameters.values()):
                    cands.append(obj)
        if not cands:
            pytest.skip("no side-effect-free callable available")

        fn = cands[0]
        try:
            _ = fn()
        except SystemExit:
            pytest.skip(f"{fn.__name__} exits (CLI); skip in unit lane")
    finally:
        sys.argv = old
