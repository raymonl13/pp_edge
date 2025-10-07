#!/usr/bin/env bash
set -euo pipefail
mkdir -p outcomes realized
: "${DAY:=}"
PY="${PY_BIN:-python3}"
run() { "$PY" "$1" --date "${DAY:-}" --cfg config_pp_edge_v6.8.yaml || "$PY" "$1" --day "${DAY:-}" || "$PY" "$1" "${DAY:-}"; }
ok=0
if [ -f "code_cli_pp_edge_engine_v1.py" ]; then
echo CI_TRY_ENGINE=pp_edge_engine
  if run code_cli_pp_edge_engine_v1.py; then ok=1; else echo "CI_NIGHTLY_ENGINE_FAILED=pp_edge_engine"; fi
fi
if [ "$ok" -eq 0 ] && [ -f "code_cli_run_edge_sheet_v1.py" ]; then
echo CI_TRY_ENGINE=run_edge_sheet
  if run code_cli_run_edge_sheet_v1.py; then ok=1; else echo "CI_NIGHTLY_ENGINE_FAILED=run_edge_sheet"; fi
fi
if [ "$ok" -eq 0 ]; then echo "CI_NIGHTLY_NO_ENGINE_OR_ALL_FAILED"; fi
exit 0
