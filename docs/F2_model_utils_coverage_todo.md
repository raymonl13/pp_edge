# F2 TODO — Bring `code_utils_model_v1` under unit-lane coverage

Scope:
- Re-include `code_utils_model_v1.py` in pytest addopts and .coveragerc.
- Add explicit contract tests:
  - `predict_hit_prob`: joblib shim, NaN handling, empty-DF path, param batch.
  - Optional: fit/train seam with CV shims (GridSearchCV/RandomizedSearchCV cv=2).
- Harden stubs in tests/conftest.py to neutralize any artifact/network assumptions.
- Goal for F2: lift unit-lane coverage to ≥80% with model utils included.
