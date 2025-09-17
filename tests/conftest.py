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
    SKIP_FILES = {
        "demo_slipbuilder_test.py",
        "test_bankroll.py",
        "test_bankroll_pipeline.py",
        "test_alerting.py",
    }
    for item in items:
        if pathlib.Path(item.fspath).name in SKIP_FILES:
            item.add_marker(skip)
