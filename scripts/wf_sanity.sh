#!/usr/bin/env bash
set -euo pipefail
if command -v actionlint >/dev/null 2>&1; then
  if ! actionlint -oneliner -color never .github/workflows/manual_edge_sheet_e2e.yml; then
    git fetch origin main
    git checkout origin/main -- .github/workflows/manual_edge_sheet_e2e.yml
    echo RESET_WORKFLOW_FROM_ORIGIN
  else
    echo WORKFLOW_OK
  fi
else
  echo ACTIONLINT_NOT_FOUND
fi
