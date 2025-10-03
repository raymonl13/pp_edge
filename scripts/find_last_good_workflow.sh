#!/usr/bin/env bash
set -euo pipefail
file=".github/workflows/manual_edge_sheet_e2e.yml"
base="origin/main"
git fetch origin main >/dev/null 2>&1 || true
commits=$(git rev-list --max-count=200 "$base" -- "$file")
good=""
if command -v actionlint >/dev/null 2>&1; then
  for c in $commits; do
    if git show "${c}:${file}" | actionlint -oneline -no-color - >/dev/null 2>&1; then
      good="$c"; break
    fi
  done
else
  for c in $commits; do
    if git show "${c}:${file}" >/tmp/wf.yml 2>/dev/null && python3 - <<'PY' >/dev/null 2>&1
import yaml,sys
yaml.safe_load(open("/tmp/wf.yml"))
PY
    then
      good="$c"; break
    fi
  done
fi
if [ -z "$good" ]; then
  echo "GOOD_COMMIT=NOT_FOUND"; exit 1
fi
echo "GOOD_COMMIT=$good"
git checkout "$good" -- "$file"
