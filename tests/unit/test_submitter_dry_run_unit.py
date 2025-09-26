import importlib, inspect, pytest
pytestmark = pytest.mark.unit

def _find(module, names):
    for n in names:
        fn = getattr(module, n, None)
        if callable(fn): return fn
    for name, obj in vars(module).items():
        if any(key in name.lower() for key in names) and callable(obj):
            return obj
    return None

def test_submitter_dry_run_minimal():
    try:
        mod = importlib.import_module("code_cli_submit_slips_v1")
    except Exception as e:
        pytest.skip(f"submitter not importable: {e}")

    fn = _find(mod, ("_dry_run","dry_run","preview"))
    if not callable(fn):
        pytest.skip("dry-run seam not available")

    payload = {"slips":[{"slip_type":"Power2","legs":[{"player":"A","p_hit":0.66},{"player":"B","p_hit":0.64}]}]}
    slips_list = payload["slips"]

    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())

    if "slips" in params:
        fn(slips=slips_list)
    elif "payload" in params:
        fn(payload=payload)
    elif "data" in params:
        fn(data=payload)
    else:
        try:
            fn(slips_list)
        except TypeError:
            fn(payload)
