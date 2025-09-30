#!/usr/bin/env bash
set -euo pipefail
WF="${1:-manual_edge_sheet_e2e.yml}"
BR="${2:-main}"
RUN_ID="$(gh run list --workflow "$WF" --branch "$BR" --limit 1 --json databaseId --jq '.[0].databaseId')"
if [ -z "${RUN_ID:-}" ] || [ "${RUN_ID}" = "null" ]; then echo "RUN_ID="; exit 1; fi
while :; do
  S="$(gh run view "$RUN_ID" --json status --jq .status)"
  C="$(gh run view "$RUN_ID" --json conclusion --jq .conclusion)"
  U="$(gh run view "$RUN_ID" --json url --jq .url)"
  echo "STATUS=$S"
  if [ "$S" = "completed" ]; then
    echo "RUN_ID=$RUN_ID"
    echo "RUN_URL=$U"
    echo "CONCLUSION=${C:-}"
    echo "ARTIFACT_NAMES=$(gh run view "$RUN_ID" --json artifacts --jq '[.artifacts[].name]|join(",")')"
    exit 0
  fi
  sleep 6
done
