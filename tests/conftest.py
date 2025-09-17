import os, socket, pytest, pathlib, sys

print("CONFTEXT: loaded; PP_EDGE_TEST_MODE=", os.getenv("PP_EDGE_TEST_MODE"), file=sys.stderr)

@pytest.fixture(autouse=True, scope="session")
def _block_network_session():
    if os.getenv("ALLOW_NETWORK_TESTS") == "1":
        return
    original = socket.create_connection
    def guard(*a, **k):
        raise RuntimeError("Network calls are disabled in unit tests (ALLOW_NETWORK_TESTS=1 to override)")
    socket.create_connection = guard
    try:
        yield
    finally:
        socket.create_connection = original

HEAVY_PATTERNS = (
    "test_bankroll", "bankroll_", "alert", "demo_slipbuilder",
    "test_feature_rolling_woba", "rolling_woba", "tiers",
)

def pytest_ignore_collect(path, config):
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        return False
    name = pathlib.Path(str(path)).name.lower()
    return any(p in name for p in HEAVY_PATTERNS)

def pytest_collection_modifyitems(config, items):
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        return
    skip = pytest.mark.skip(reason="PR CI runs unit-tier only (PP_EDGE_TEST_MODE=1)")
    for item in items:
        name = pathlib.Path(item.fspath).name.lower()
        marks = {m.name for m in item.iter_markers()}
        is_unit = "unit" in marks and not ({"integration","e2e"} & marks)
        looks_heavy = any(p in name for p in HEAVY_PATTERNS)
        if not is_unit or looks_heavy:
            item.add_marker(skip)
