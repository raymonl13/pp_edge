# CI Preflight (Guardrails)

This checklist must be followed for any CI/workflow change:

## 0) Isolation
- Quarantine unrelated/broken workflows when iterating (move to `.github/workflows_disabled/`).
- Use a minimal skeleton first to prove jobs actually schedule.

## 1) Parse-proof
- No YAML heredocs. If you must generate YAML, use printf or separate files.
- Keep logic in `scripts/`, not embedded in YAML steps.

## 2) Shell-proof (zsh-safe)
- Assume zsh locally: use `NULL_GLOB`, `noglob` for jq, and correct here-doc closures.
- No brittle globs in commands; prefer `find`/`awk`.

## 3) Observability-first
- Capture stdout/stderr to artifacts for critical steps.
- Force placeholders (run_meta.txt, qa_report.*, alloc_summary.csv, CSV header) so Upload always has files.
- Upload a `.artifact_marker` to guarantee an artifact exists.

## 4) Env symmetry
- Set `PYTHONPATH=.:$PYTHONPATH` if importing repo modules.
- Print `PWD` and `ls -al scripts/` in preflight steps.

## 5) Smoke controls
- Support env overrides (e.g., `QA_MIN_ROWS`) and optional row injection via `SMOKE_INJECT=1`.
- Default to real-data behavior; use smoke only when asked.

## 6) Asserts & local tooling
- zsh-safe watcher: `awk` for extracting RUN_ID/ART, recursive `find` for meta and files.
- Idempotent downloader that writes to `artifacts/run_<id>/dl_<epoch>`.

## 7) Gate last (and only when it matters)
- Place QA gate **after Upload**.
- Gate only on **non-empty slates**: fail iff `CSV_ROWS>0 && QA_STATE=FAIL`.

## 8) Reporting
- Always keep `run_meta.txt` as the truth for INGEST_STATE/CSV_STATE/QA_STATE/ALLOC_STATE (+ versions).
- Upload the board JSON and CSV so you can diagnose data issues without CI churn.
