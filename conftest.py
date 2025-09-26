def pytest_ignore_collect(path):
    return "tests/legacy/" in str(path)
