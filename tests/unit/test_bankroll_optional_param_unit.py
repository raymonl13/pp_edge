import importlib, inspect, pytest
pytestmark = pytest.mark.unit
def _find():
    for modname in ("code_utils_bankroll_v1","bankroll","bankroll_primitives","stake"):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        for name in dir(mod):
            obj = getattr(mod, name)
            if callable(obj) and any(k in name.lower() for k in ("size","stake","kelly","bet")):
                return obj
    return None
def test_bankroll_all_kwargs_path():
    fn = _find()
    if not callable(fn):
        pytest.skip("no bankroll stake function found")
    sig = inspect.signature(fn)
    kw = {}
    if "bankroll_state" in sig.parameters: kw["bankroll_state"] = {"bankroll": 100.0}
    if "bankroll" in sig.parameters: kw["bankroll"] = 100.0
    if "bankroll_cfg" in sig.parameters: kw["bankroll_cfg"] = {"starting": 100.0}
    if "tag" in sig.parameters: kw["tag"] = "Demon"
    fn(0.03, **kw)
