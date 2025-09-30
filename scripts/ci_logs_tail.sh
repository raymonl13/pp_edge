#!/usr/bin/env bash
set -euo pipefail
RUN_ID="${1:?}"
LINES="${2:-300}"
gh run view "$RUN_ID" --log | tail -n "$LINES"
