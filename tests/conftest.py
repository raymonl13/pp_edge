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

def pytest_collection_modifyitems(config, items):
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        return
    skip = pytest.mark.skip(reason="skipped in CI test mode (PP_EDGE_TEST_MODE=1)")
    patterns = ("test_bankroll", "bankroll_", "alert", "demo_slipbuilder")
    for item in items:
        name = pathlib.Path(item.fspath).name.lower()
        if any(p in name for p in patterns):
            item.add_marker(skip)
