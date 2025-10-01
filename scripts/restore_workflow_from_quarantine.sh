#!/usr/bin/env bash
set -euo pipefail
FILE="${1:?usage: restore_workflow_from_quarantine.sh <filename.yml>}"
SRC=".github/workflows_disabled/$FILE"
DST=".github/workflows/$FILE"
[ -f "$SRC" ] || { echo "Not found: $SRC"; exit 1; }
git mv "$SRC" "$DST"
git add "$DST"
git commit -m "ci: restore workflow $FILE (pending actionlint)"
git push
echo "Restored $FILE. Create a PR to validate with actionlint + CI."
