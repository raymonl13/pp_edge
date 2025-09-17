import os, socket, pytest, pathlib


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


def _looks_heavy_test(path: pathlib.Path) -> bool:
    name = path.name.lower()
    return any(p in name for p in (
        "test_bankroll", "bankroll_", "alert", "demo_slipbuilder",
        "test_feature_rolling_woba", "rolling_woba",
    ))

def pytest_collection_modifyitems(config, items):
    if os.getenv("PP_EDGE_TEST_MODE") != "1":
        return
    skip_non_unit = pytest.mark.skip(reason="skipped: PR CI runs unit-tier only (PP_EDGE_TEST_MODE=1)")
    for item in items:
        # Prefer explicit markers
        marks = {m.name for m in item.iter_markers()}
        is_unit = "unit" in marks and not ({"integration","e2e"} & marks)
        looks_heavy = _looks_heavy_test(pathlib.Path(item.fspath))
        if not is_unit or looks_heavy:
            item.add_marker(skip_non_unit)
