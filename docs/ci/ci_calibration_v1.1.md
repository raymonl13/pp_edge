# CI & Calibration (v1.1)

This document wraps **CI & Calibration (v1.0)** and adds expectations from the Session-8 audit.

## Upload→Gate
- CI must upload key artifacts (edgesheet CSV, rollup summary, calibration JSON, drift JSON, run_meta) before any gating.
- Gating should not hide evidence; failed runs still have artifacts.

## Metrics & SLO (scaffolding)
- `metrics_run.json` is derived from artifacts only (e.g. number of rows, model/QA/alloc states, runtime).
- A simple SLO guard (via `ci/slo.yaml` and a `guard_slo.py` script) fails only on hard breaches (e.g. router min rows, QA_STATE=FAIL).
- Calibration and drift probes remain non-gating until enough realized data is present; later they may be promoted to gating conditions.

Full details of calibration strategy and CI matrix remain in the original **CI & Calibration (v1.0)** doc.
