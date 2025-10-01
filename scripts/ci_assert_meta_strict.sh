#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?}"
META="$(find "$ROOT" -type f -name run_meta.txt | head -n1)"
[ -n "${META:-}" ] || { echo "NO_META=1"; exit 1; }
grep -Eq 'INGEST_STATE=(OK|WARN|FAIL)' "$META"
grep -Eq 'CSV_STATE=(REAL|PLACEHOLDER|MISSING)' "$META"
grep -Eq 'QA_STATE=(OK|WARN|FAIL)' "$META"
grep -Eq 'ALLOC_STATE=(OK|WARN|FAIL)' "$META"
echo "OK"
