import os, socket, pytest, pathlib, sys

print("CONFTEXT: loaded; PP_EDGE_TEST_MODE=", os.getenv("PP_EDGE_TEST_MODE"), file=sys.stderr)

# Block network unless explicitly allowed


import sys, types, os
if os.getenv("PP_EDGE_TEST_MODE") == "1":
    sys.modules.setdefault("joblib", types.SimpleNamespace(dump=lambda *a, **k: None,
                                                           load=lambda *a, **k: None))
    sys.modules.setdefault("xgboost", types.SimpleNamespace(DMatrix=object, XGBClassifier=object))
    sys.modules.setdefault("lightgbm", types.SimpleNamespace(Dataset=object, LGBMClassifier=object))
    sys.modules.setdefault("sklearn", types.SimpleNamespace())

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

# --- Extended shims for heavy sklearn submodules in unit lane ---
import sys, types, os
if os.getenv("PP_EDGE_TEST_MODE") == "1":
    # ensure sklearn is a ModuleType with submodules
    if "sklearn" not in sys.modules or not hasattr(sys.modules.get("sklearn"), "__spec__"):
        import types as _t
        sys.modules["sklearn"] = _t.ModuleType("sklearn")
    # model_selection shim (e.g., train_test_split / KFold)
    if "sklearn.model_selection" not in sys.modules:
        ms = types.SimpleNamespace(
            train_test_split=lambda *a, **k: (a[0], a[0], a[0], a[0]),
            KFold=object
        )
        sys.modules["sklearn.model_selection"] = ms
        setattr(sys.modules["sklearn"], "model_selection", ms)
    # metrics shim (e.g., roc_auc_score)
    if "sklearn.metrics" not in sys.modules:
        met = types.SimpleNamespace(roc_auc_score=lambda *a, **k: 0.5)
        sys.modules["sklearn.metrics"] = met
        setattr(sys.modules["sklearn"], "metrics", met)


# --- Extended shims for sklearn search CV in unit lane ---
import sys, types, os
if os.getenv("PP_EDGE_TEST_MODE") == "1":
    # ensure sklearn root exists
    if "sklearn" not in sys.modules:
        sys.modules["sklearn"] = types.ModuleType("sklearn")
    # ensure model_selection module exists
    if "sklearn.model_selection" not in sys.modules:
        ms = types.ModuleType("sklearn.model_selection")
        sys.modules["sklearn.model_selection"] = ms
        setattr(sys.modules["sklearn"], "model_selection", ms)
    ms = sys.modules["sklearn.model_selection"]
    # light stubs that won't run searches but keep imports happy
    class _DummySearch:
        def __init__(self, *a, **k): pass
        def fit(self, *a, **k): return self
        def predict(self, *a, **k): return [0]*len(a[0]) if a else []
    if not hasattr(ms, "RandomizedSearchCV"):
        ms.RandomizedSearchCV = _DummySearch
    if not hasattr(ms, "GridSearchCV"):
        ms.GridSearchCV = _DummySearch
    # keep handy split helpers too
    if not hasattr(ms, "train_test_split"):
        ms.train_test_split = lambda X, y=None, *a, **k: (X, X, y, y) if y is not None else (X, X, X, X)
    if not hasattr(ms, "KFold"):
        ms.KFold = object

    # ensure metrics exists (roc_auc_score etc.)
    if "sklearn.metrics" not in sys.modules:
        met = types.ModuleType("sklearn.metrics")
        met.roc_auc_score = lambda *a, **k: 0.5
        sys.modules["sklearn.metrics"] = met
        setattr(sys.modules["sklearn"], "metrics", met)


# --- Unified feature stubs for unit lane (PP_EDGE_TEST_MODE=1) ---
# Goal: keep unit tests hermetic; any features.* used by code_utils_model_v1 returns aligned zeros.
import os, sys, types, importlib
if os.getenv("PP_EDGE_TEST_MODE") == "1":
    def _zero_series(df):
        import pandas as _pd, numpy as _np
        return _pd.Series(_np.zeros(len(df), dtype=float), index=df.index, name="stubbed_feature")

    # List of feature module:function pairs we know about (expandable)
    _FEATURE_FUNCS = [
        ("features.rolling_woba", "rolling_woba"),
        ("features.wind_adj", "wind_adj"),
        # add future feature funcs here without touching tests
    ]

    # Patch source modules if present
    for mod_name, func_name in _FEATURE_FUNCS:
        try:
            m = importlib.import_module(mod_name)
            setattr(m, func_name, _zero_series)
        except Exception:
            pass

    # Patch bound names inside code_utils_model_v1 (handles "from … import func")
    try:
        mu = importlib.import_module("code_utils_model_v1")
        for _, func_name in _FEATURE_FUNCS:
            setattr(mu, func_name, _zero_series)
    except Exception:
        pass
