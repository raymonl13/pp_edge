import os, socket, pytest, pathlib, sys

print("CONFTEXT: loaded; PP_EDGE_TEST_MODE=", os.getenv("PP_EDGE_TEST_MODE"), file=sys.stderr)

# Block network unless explicitly allowed
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
    "bankroll", "alert", "demo_slipbuilder",
    "rolling_woba", "feature_rolling_woba", "tiers",
)

def pytest_ignore_collect(path, config):
    # Pre-ignore heavy patterns BEFORE import in PR unit lane
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        return False
    name = pathlib.Path(str(path)).name.lower()
    return any(p in name for p in HEAVY_PATTERNS)

def pytest_collection_modifyitems(config, items):
    # In PR lane, ONLY run tests explicitly marked @pytest.mark.unit
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        return
    skip = pytest.mark.skip(reason="PR CI runs unit-tier only (PP_EDGE_TEST_MODE=1)")
    for item in items:
        marks = {m.name for m in item.iter_markers()}
        if "unit" not in marks or {"integration","e2e"} & marks:
            item.add_marker(skip)
