#!/usr/bin/env bash
set -euo pipefail
WF="${1:-manual_edge_sheet_e2e.yml}"
BR="${2:-main}"
RID="$(gh run list --workflow "$WF" --branch "$BR" --limit 1 --json databaseId --jq '.[0].databaseId')"
if [ -z "${RID:-}" ] || [ "$RID" = "null" ]; then echo "RUN_ID="; exit 1; fi
REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
while :; do
  S="$(gh run view "$RID" --json status --jq .status)"
  C="$(gh run view "$RID" --json conclusion --jq .conclusion)"
  U="$(gh run view "$RID" --json url --jq .url)"
  echo "STATUS=$S"
  if [ "$S" = "completed" ]; then
    NAMES="$(gh api repos/$REPO/actions/runs/$RID/artifacts --jq '.artifacts|map(.name)|join(",")')"
    echo "RUN_ID=$RID"
    echo "RUN_URL=$U"
    echo "CONCLUSION=${C:-}"
    echo "ARTIFACT_NAMES=${NAMES:-}"
    exit 0
  fi
  sleep 6
done
