#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob
f=(edge_sheet_*.csv)
if [ "${#f[@]}" -eq 0 ]; then echo "CI_EDGESHEET_ABSENT"; fi
