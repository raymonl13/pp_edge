#!/usr/bin/env bash
set -euo pipefail
RUN_ID="${1:?}"
NAME="${2:-}"
OUT="artifacts/run_$RUN_ID"
mkdir -p "$OUT"
if [ -n "$NAME" ]; then
  gh run download "$RUN_ID" --name "$NAME" --dir "$OUT"
  echo "$OUT/$NAME"
else
  gh run download "$RUN_ID" --dir "$OUT"
  echo "$OUT"
fi
