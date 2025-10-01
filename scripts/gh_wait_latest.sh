#!/usr/bin/env bash
set -euo pipefail
WF="${1:?workflow file or name}"
BR="${2:-main}"
PREV="$(gh run list --workflow "$WF" --branch "$BR" -L 1 --json databaseId -q '.[0].databaseId' || true)"
for i in {1..120}; do
  RID="$(gh run list --workflow "$WF" --branch "$BR" -L 1 --json databaseId -q '.[0].databaseId' || true)"
  if [ -n "$RID" ] && [ "$RID" != "$PREV" ]; then break; fi
  sleep 2
done
gh run watch "$RID" --exit-status 1>&2 || true
OUTDIR="$(mktemp -d)"
gh run download "$RID" -D "$OUTDIR" 1>&2 || true
printf '%s\n' "$OUTDIR"
