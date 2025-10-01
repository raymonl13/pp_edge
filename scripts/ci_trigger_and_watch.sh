#!/usr/bin/env bash
set -euo pipefail
WF="${1:-manual_edge_sheet_e2e.yml}"
BR="${2:-main}"
git commit --allow-empty -m "ci: trigger qa_alloc $(date -u +%FT%TZ)"
git push origin "$BR"
REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
while :; do
  ID="$(gh run list --workflow "$WF" --branch "$BR" --limit 1 --json databaseId --jq '.[0].databaseId')"
  [ -n "$ID" ] && [ "$ID" != "null" ] && break
  sleep 2
done
while :; do
  S="$(gh run view "$ID" --json status --jq .status)"
  C="$(gh run view "$ID" --json conclusion --jq .conclusion)"
  echo "STATUS=$S"
  if [ "$S" = "completed" ]; then
    if [ "$C" = "cancelled" ]; then
      ID="$(gh run list --workflow "$WF" --branch "$BR" --limit 1 --json databaseId,conclusion --jq '[.[]|select(.conclusion!="cancelled")][0].databaseId')"
      [ -n "$ID" ] && [ "$ID" != "null" ] || exit 1
      continue
    fi
    U="$(gh run view "$ID" --json url --jq .url)"
    NAMES="$(gh api repos/$REPO/actions/runs/$ID/artifacts --jq '.artifacts|map(.name)|join(",")')"
    echo "RUN_ID=$ID"
    echo "RUN_URL=$U"
    echo "CONCLUSION=${C:-}"
    echo "ARTIFACT_NAMES=${NAMES:-}"
    exit 0
  fi
  sleep 6
done
