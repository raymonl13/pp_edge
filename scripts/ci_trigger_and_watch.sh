#!/usr/bin/env bash
set -euo pipefail
WF="${1:-manual_edge_sheet_e2e.yml}"
BR="${2:-main}"
git commit --allow-empty -m "ci: trigger qa_alloc $(date -u +%FT%TZ)"
git push origin "$BR"
bash scripts/ci_wait_latest.sh "$WF" "$BR"
