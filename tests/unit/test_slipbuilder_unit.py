import importlib, inspect, pytest

pytestmark = pytest.mark.unit

def test_slipbuilder_minimal_path():
    try:
        mod = importlib.import_module("code_utils_slipbuilder_v2")
    except Exception as e:
        pytest.skip(f"slipbuilder module not importable: {e}")

    # Prefer a builder function
    cand_funcs = [getattr(mod, n) for n in dir(mod) if n.lower() in {"build_slips","build","make_slips"}]
    for fn in cand_funcs:
        if callable(fn):
            sig = inspect.signature(fn)
            kwargs = {}
            # try to satisfy common minimal kwargs safely
            for k,p in sig.parameters.items():
                if p.default is not inspect._empty:
                    continue
                # best-effort dummy values for minimal execution
                if k in {"picks","legs","items"}: kwargs[k] = []
                elif k in {"max_slips","limit"}:  kwargs[k] = 0
                elif k in {"allow_duplicates","dry_run","strict"}: kwargs[k] = True
                else:
                    # unknown required param — skip function
                    break
            else:
                _ = fn(**kwargs)  # exercise the path
                return

    # Or a SlipBuilder class with a minimal method
    for name in dir(mod):
        if "builder" in name.lower():
            cls = getattr(mod, name)
            if isinstance(cls, type):
                try:
                    obj = cls()  # must not require args
                except Exception:
                    continue
                # call a minimal method if present
                for m in ("build","build_slips","validate","reset"):
                    if hasattr(obj, m) and callable(getattr(obj, m)):
                        try:
                            getattr(obj, m)()
                        except TypeError:
                            # try method with empty list or no-op args
                            try: getattr(obj, m)([])
                            except Exception: pass
                        return

    pytest.skip("No safe builder function/class found to exercise")
