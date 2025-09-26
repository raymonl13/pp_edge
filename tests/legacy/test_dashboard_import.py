def test_streamlit_import():
    import importlib
    assert importlib.import_module("dashboard.app")
