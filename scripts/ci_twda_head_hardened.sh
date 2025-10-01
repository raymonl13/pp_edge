#!/usr/bin/env bash
set -euo pipefail
wf="${1:-.github/workflows/manual_edge_sheet_e2e.yml}"
br="${2:-main}"
headsha="$(git rev-parse HEAD)"
command -v gh >/dev/null 2>&1
rid=""
for i in $(seq 1 120); do
  rid="$(gh run list --workflow "$wf" --branch "$br" --json databaseId,headSha,status,createdAt --limit 40 \
    --jq 'map(select(.headSha=="'"$headsha"'"))|.[0].databaseId' || true)"
  [ -n "$rid" ] && break
  sleep 2
done
[ -z "$rid" ] && { echo "run for HEAD not found"; exit 1; }
gh run watch "$rid" >&2 || true
out="artifacts/$rid"
rm -rf "$out"; mkdir -p "$out"
if gh run download "$rid" -D "$out" >&2; then
  printf "%s\n" "$out"
  exit 0
fi
jobids="$(gh run view "$rid" --json jobs --jq '.jobs[].id' || true)"
mkdir -p "$out/logs"
if [ -n "$jobids" ]; then
  while read -r jid; do
    gh run view "$rid" --job "$jid" --log > "$out/logs/$jid.log" || true
  done <<<"$jobids"
fi
printf "%s\n" "$out"
