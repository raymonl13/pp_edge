#!/usr/bin/env bash
set -euo pipefail
mkdir -p outcomes realized
: "${DAY:=}"
PY="${PY_BIN:-python3}"
run() { "$PY" "$1" --date "${DAY:-}" --cfg config_pp_edge_v6.8.yaml || "$PY" "$1" --day "${DAY:-}" || "$PY" "$1" "${DAY:-}"; }
if [ -f "code_cli_pp_edge_engine_v1.py" ]; then run code_cli_pp_edge_engine_v1.py; fi
if [ -f "code_cli_run_edge_sheet_v1.py" ]; then run code_cli_run_edge_sheet_v1.py; fi
if [ ! -f "code_cli_pp_edge_engine_v1.py" ] && [ ! -f "code_cli_run_edge_sheet_v1.py" ]; then echo "CI_NIGHTLY_NO_ENGINE"; fi
