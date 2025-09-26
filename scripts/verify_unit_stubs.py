import os, sys, importlib
os.environ["PP_EDGE_TEST_MODE"]="1"
sys.path.insert(0, ".")
import tests.conftest
mu = importlib.import_module("code_utils_model_v1")
def _is_zero(fn): return callable(fn) and getattr(fn, "__name__", "") == "_zero_series"
need = ("rolling_woba","wind_adj","platoon_split","barrel_pct","pitcher_swstr")
ok = all(_is_zero(getattr(mu, n, None)) for n in need)
print("OK" if ok else "MISS")
sys.exit(0 if ok else 1)
