#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
META="$(find "$ROOT" -type f -name run_meta.txt | head -n1)"
if [ -z "$META" ]; then echo "NO_META=1"; exit 1; fi
grep -q 'INGEST_STATE=' "$META"
grep -q 'CSV_STATE=' "$META"
grep -q 'QA_STATE=' "$META"
grep -q 'ALLOC_STATE=' "$META"
echo "OK"
