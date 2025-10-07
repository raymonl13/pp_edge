#!/usr/bin/env bash
set -euo pipefail
mkdir -p outcomes realized
if [ -f "code_cli_pp_edge_engine_v1.py" ]; then python3 code_cli_pp_edge_engine_v1.py --date "${DAY:-}"; fi
if [ -f "scripts/ci_entrypoint.py" ]; then python3 scripts/ci_entrypoint.py --day "${DAY:-}"; fi
