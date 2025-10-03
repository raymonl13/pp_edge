#!/usr/bin/env bash
set -euo pipefail
GOOD_COMMIT="${1:-000a7a1ff6368178e13081400a09e8816274081b}"
FILE=".github/workflows/manual_edge_sheet_e2e.yml"
git fetch origin main >/dev/null 2>&1 || true
git checkout "$GOOD_COMMIT" -- "$FILE"
if command -v actionlint >/dev/null 2>&1; then
  actionlint -oneline -no-color "$FILE"
else
  python3 - <<'PY'
import yaml; yaml.safe_load(open(".github/workflows/manual_edge_sheet_e2e.yml"))
PY
fi
git add "$FILE"
git commit -m "revert: restore manual_edge_sheet_e2e.yml to lint-clean commit $GOOD_COMMIT" || true
git push || true
echo OK
