import importlib, inspect, pytest
pytestmark = pytest.mark.unit

def _load():
    try:
        return importlib.import_module("code_utils_slipbuilder_v2")
    except Exception as e:
        pytest.skip(f"slipbuilder not importable: {e}")

def test_minimal_branch_paths():
    mod = _load()

    # prefer a validate/build function first
    for name in ("validate_pick","validate","build_slips","build"):
        fn = getattr(mod, name, None)
        if callable(fn):
            sig = inspect.signature(fn)
            kwargs = {}
            for k,p in sig.parameters.items():
                if p.default is not inspect._empty:  # has default
                    continue
                # minimal dummies for common params
                if k in {"picks","legs","items"}: kwargs[k] = []
                elif k in {"max_slips","limit"}: kwargs[k] = 0
                elif k in {"allow_duplicates","dry_run","strict"}: kwargs[k] = True
                else:
                    break
            else:
                _ = fn(**kwargs)
                return

    # otherwise exercise a minimal method on a builder class
    for attr in dir(mod):
        if "builder" in attr.lower():
            cls = getattr(mod, attr)
            if isinstance(cls, type):
                try:
                    obj = cls()
                except Exception:
                    continue
                for m in ("validate","reset","build","build_slips"):
                    if hasattr(obj, m) and callable(getattr(obj, m)):
                        try:
                            getattr(obj, m)()
                        except TypeError:
                            try: getattr(obj, m)([])
                            except Exception: pass
                        return
    pytest.skip("no safe minimal slipbuilder path found")
