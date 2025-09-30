#!/usr/bin/env bash
set -euo pipefail
WF="${1:?workflow file}"
BR="${2:-main}"
DAY="${3:-}"
PREV="$(gh run list --workflow "$WF" --branch "$BR" -L 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || true)"
if [ -n "$DAY" ]; then gh workflow run "$WF" -r "$BR" -f day="$DAY"; else gh workflow run "$WF" -r "$BR"; fi
RID=""
for i in {1..90}; do
  RID="$(gh run list --workflow "$WF" --branch "$BR" -L 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || true)"
  if [ -n "$RID" ] && [ "$RID" != "$PREV" ]; then break; fi
  sleep 2
done
gh run watch "$RID" --exit-status 1>&2 || true
OUTDIR="$(mktemp -d)"
gh run download "$RID" -D "$OUTDIR" 1>&2 || true
printf '%s\n' "$OUTDIR"
