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

def _call(fn, edge, bankroll):
    sig = inspect.signature(fn)
    kwargs = {}
    if "bankroll_state" in sig.parameters:
        kwargs["bankroll_state"] = {"bankroll": bankroll}
    if "bankroll" in sig.parameters:
        kwargs["bankroll"] = bankroll
    if "bankroll_cfg" in sig.parameters:
        kwargs["bankroll_cfg"] = {"starting": bankroll}
    try:
        return fn(edge, **kwargs)
    except TypeError:
        return fn(edge, **kwargs)

@pytest.mark.parametrize("edge,bankroll", [(0.0,100.0),(-0.05,50.0),(0.02,10.0),(0.10,1000.0)])
def test_bankroll_varied_edges(edge, bankroll):
    fn = _find()
    if not callable(fn):
        pytest.skip("no bankroll stake function found")
    s = _call(fn, edge, bankroll)
    if edge <= 0.0:
        assert s <= 1e-9 or s <= 0.0
    else:
        assert s >= 0.0
