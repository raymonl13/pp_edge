#!/usr/bin/env bash
set -euo pipefail
if command -v actionlint >/dev/null 2>&1; then
  actionlint -oneline -no-color .github/workflows/manual_edge_sheet_e2e.yml
  echo WORKFLOW_OK
else
  echo ACTIONLINT_NOT_FOUND
fi
