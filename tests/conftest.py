import os, socket, pytest

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
