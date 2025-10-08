#!/usr/bin/env bash
set -euo pipefail

WF="${1:-nightly_edge_sheet.yml}"
DAY="${2:-$(date -u +%F)}"

gh workflow run "$WF" --ref main -f day="$DAY" >/dev/null 2>&1
RID_MAIN="$(gh run list --workflow "$WF" --branch main -L 1 --json databaseId | jq -r '.[0].databaseId')"
echo "RID_MAIN=$RID_MAIN"
gh run watch "$RID_MAIN" --interval 5

gh run view "$RID_MAIN" --json jobs \
  --jq '.jobs[]|select(.name=="nightly")|.steps[]|{n:.number,name,conclusion}'

rm -rf "ci_artifacts_${RID_MAIN}" && mkdir -p "ci_artifacts_${RID_MAIN}"
for NAME in engine_logs edgesheet rollup_probe outcomes_rollup outcomes; do
  gh run download "$RID_MAIN" -n "$NAME" -D "ci_artifacts_${RID_MAIN}/$NAME" || true
done

echo "ARTIFACTS:"
gh api "repos/$(git config --get remote.origin.url | sed -E 's#.*github.com[:/](.*)\.git#\1#')/actions/runs/$RID_MAIN/artifacts" \
  -q '.artifacts[].name' || true

CSV="$(find "ci_artifacts_${RID_MAIN}/edgesheet" -type f -name 'edge_sheet_*.csv' | head -n 1 || true)"
if [ -n "${CSV:-}" ]; then
  echo "EDGESHEET_FILE=$CSV"
  echo "EDGESHEET_ROWS=$(( $(wc -l < "$CSV") - 1 ))"
else
  echo "EDGESHEET_MISSING"
fi

if [ -f "ci_artifacts_${RID_MAIN}/rollup_probe/rollup_probe.json" ]; then
  printf "PROBE="; jq -c '.' "ci_artifacts_${RID_MAIN}/rollup_probe/rollup_probe.json" | sed -n '1p'
else
  echo "PROBE_MISSING"
fi

if [ -f "ci_artifacts_${RID_MAIN}/outcomes_rollup/outcomes_rollup.json" ]; then
  printf "ROLLOP="; jq -c '.' "ci_artifacts_${RID_MAIN}/outcomes_rollup/outcomes_rollup.json" | sed -n '1p'
else
  echo "ROLLOP_JSON_MISSING"
fi
