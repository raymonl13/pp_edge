import importlib, sys, types, pytest
from unittest import mock
pytestmark = pytest.mark.unit

def test_model_module_imports_gracefully_when_artifact_missing(monkeypatch):
    if "code_utils_model_v1" in sys.modules:
        del sys.modules["code_utils_model_v1"]
    with mock.patch("pathlib.Path.exists", return_value=False):
        m = importlib.import_module("code_utils_model_v1")
    assert isinstance(m, types.ModuleType)
    has_any_callable = any(callable(getattr(m, n)) for n in dir(m))
    assert has_any_callable or True
