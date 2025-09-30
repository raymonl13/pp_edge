#!/usr/bin/env bash
set -euo pipefail
RUN_ID="${1:?}"
OUT="artifacts/run_$RUN_ID"
mkdir -p "$OUT"
gh run download "$RUN_ID" --dir "$OUT"
echo "$OUT"
