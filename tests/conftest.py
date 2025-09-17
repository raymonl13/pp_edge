import os, socket, pytest, pathlib

@pytest.fixture(autouse=True, scope="session")
def _block_network_session():
    if os.getenv("ALLOW_NETWORK_TESTS") == "1":
        return
    original_create = socket.create_connection
    def guard(*args, **kwargs):
        raise RuntimeError("Network calls are disabled in unit tests (set ALLOW_NETWORK_TESTS=1 to override)")
    socket.create_connection = guard
    try:
        yield
    finally:
        socket.create_connection = original_create

def pytest_ignore_collect(path, config):
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        return False
    name = pathlib.Path(str(path)).name.lower()
    patterns = (
        "test_bankroll", "bankroll_", "alert", "demo_slipbuilder",
        "test_feature_rolling_woba", "rolling_woba",
    )
    return any(p in name for p in patterns)

def pytest_collection_modifyitems(config, items):
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        return
    skip = pytest.mark.skip(reason="skipped in CI test mode (PP_EDGE_TEST_MODE=1)")
    for item in items:
        n = pathlib.Path(item.fspath).name.lower()
        if any(p in n for p in ("test_bankroll", "bankroll_", "alert", "demo_slipbuilder", "rolling_woba")):
            item.add_marker(skip)
