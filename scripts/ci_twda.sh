#!/usr/bin/env bash
set -euo pipefail
wf="${1:-.github/workflows/manual_edge_sheet_e2e.yml}"
br="${2:-main}"
command -v gh >/dev/null 2>&1
rid=$(gh run list --workflow "$wf" --branch "$br" --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$rid"
out="artifacts/$rid"
mkdir -p "$out"
gh run download "$rid" -D "$out"
echo "$out"
