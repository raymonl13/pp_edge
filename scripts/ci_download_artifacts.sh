#!/usr/bin/env bash
set -euo pipefail
RID="${1:?}"
REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
OUT="artifacts/run_${RID}"
mkdir -p "$OUT"
NAME="$(gh api repos/$REPO/actions/runs/$RID/artifacts --jq '.artifacts[0].name')"
gh run download "$RID" --name "$NAME" --dir "$OUT"
DIR="$OUT/$NAME"
echo "$DIR"
