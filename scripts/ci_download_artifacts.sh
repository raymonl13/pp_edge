#!/usr/bin/env bash
set -euo pipefail
RUN_ID="${1:?}"
NAME="${2:-}"
BASE="artifacts/run_${RUN_ID}"
STAMP="$(date +%s)"
OUT="${BASE}/dl_${STAMP}"
mkdir -p "$OUT"

if [ -n "${NAME}" ]; then
  gh run download "$RUN_ID" --name "$NAME" --dir "$OUT" || true
else
  gh run download "$RUN_ID" --dir "$OUT" || true
fi

# If download failed due to existing files or produced nothing, fall back to latest non-empty subdir or BASE
if ! find "$OUT" -type f -mindepth 1 -print -quit | grep -q .; then
  LAST="$(ls -1dt "${BASE}/"dl_* 2>/dev/null | head -n1 || true)"
  if [ -n "$LAST" ] && find "$LAST" -type f -mindepth 1 -print -quit | grep -q .; then
    echo "$LAST"
    exit 0
  fi
  # As a final fallback, echo BASE so callers' recursive find still works if prior runs lived there
  echo "$BASE"
  exit 0
fi

echo "$OUT"
