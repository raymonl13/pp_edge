from importlib import import_module

FEATURE_REGISTRY = {
    "rolling_woba":   "features.rolling_woba",
    "barrel_pct":     "features.barrel_pct",
    "pitcher_swstr":  "features.pitcher_swstr",
    "park_factor":    "features.park_factor",
    "wind_adj":       "features.wind_adj",
    "travel_miles":   "features.travel_miles",
    "platoon_split":  "features.platoon_split",
}

for name, module_path in FEATURE_REGISTRY.items():
    module = import_module(module_path)
    globals()[name] = getattr(module, name)

__all__ = list(FEATURE_REGISTRY.keys())
