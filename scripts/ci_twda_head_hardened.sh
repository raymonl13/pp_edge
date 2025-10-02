#!/usr/bin/env bash
set -euo pipefail
wf="${1:-.github/workflows/manual_edge_sheet_e2e.yml}"
br="${2:-main}"
headsha="$(git rev-parse HEAD)"
command -v gh >/dev/null 2>&1
rid=""
for i in $(seq 1 120); do
  rid="$(gh run list --workflow "$wf" --branch "$br" --json databaseId,headSha,status --limit 40 \
    --jq 'map(select(.headSha=="'"$headsha"'"))|.[0].databaseId' || true)"
  [ -n "$rid" ] && break
  sleep 2
done
[ -z "$rid" ] && { echo "run for HEAD not found"; exit 1; }
gh run watch "$rid" >&2 || true
out="artifacts/$rid"
rm -rf "$out"; mkdir -p "$out"
if gh run download "$rid" -D "$out" >&2; then
  printf "%s\n" "$out"; exit 0
fi
mkdir -p "$out/logs"
if gh run view "$rid" --log > "$out/logs/run.log" 2>/dev/null; then
  printf "%s\n" "$out"; exit 0
fi
jobs="$(gh run view "$rid" --json jobs --jq '.jobs[].name' || true)"
if [ -n "${jobs:-}" ]; then
  echo "$jobs" | while read -r jn; do
    [ -n "$jn" ] && gh run view "$rid" --job "$jn" --log > "$out/logs/${jn// /_}.log" 2>/dev/null || true
  done
fi
printf "%s\n" "$out"
