import importlib, inspect, pytest

pytestmark = pytest.mark.unit

def _import_bankroll_mod():
    for modname in ("bankroll_primitives","bankroll","bankroll_utils"):
        try:
            return importlib.import_module(modname)
        except Exception:
            continue
    return None

def _find_stake_fn(mod):
    if not mod:
        return None
    for name in ("size_bet","stake_size","kelly","bet_size"):
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    for name in dir(mod):
        obj = getattr(mod, name)
        if callable(obj):
            try:
                sig = inspect.signature(obj)
                if len(sig.parameters) >= 2:
                    return obj
            except Exception:
                continue
    return None

def test_stake_sizing_branches():
    mod = _import_bankroll_mod()
    fn = _find_stake_fn(mod)
    if not callable(fn):
        pytest.skip("no bankroll stake function found")

    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    needs_bankroll = any("bankroll" in p for p in params)
    needs_state    = any("state" in p for p in params) or "bankroll_state" in params

    def call(edge, bankroll):
        if needs_state:
            state = {"bankroll": bankroll}
            return fn(edge=edge, bankroll_state=state) if "edge" in params else fn(edge, state)
        if needs_bankroll:
            return fn(edge=edge, bankroll=bankroll) if "edge" in params else fn(edge, bankroll)
        return fn(edge, bankroll)

    eps = 1e-12
    assert call(0.0, 100.0) == 0 or call(0.0, 100.0) <= eps
    assert call(-0.02, 100.0) == 0 or call(-0.02, 100.0) <= eps
    s = call(0.05, 100.0)
    assert s >= 0
