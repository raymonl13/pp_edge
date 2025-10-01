#!/usr/bin/env bash
set -euo pipefail

WF="${1:-manual_edge_sheet_e2e.yml}"
BR="${2:-main}"

bash scripts/ci_trigger_and_watch.sh "$WF" "$BR" >/dev/null 2>&1 || true

RID="$(awk -F= '/^RUN_ID=/{print $2}' .ci_watch.log | tail -1)"
ART="$(awk -F= '/^ARTIFACT_NAMES=/{print $2}' .ci_watch.log | tail -1)"
DIR="$(bash scripts/ci_download_artifacts.sh "$RID" "${ART:-}")"

META="$(bash scripts/ci_locate_meta.sh "$DIR" || true)"
NOW="$(date -u +%Y%m%d_%H%MZ)"
OUT="docs/report_session4_${NOW}.md"
mkdir -p docs

{
  echo "# Session 4 CI Report ($NOW)"
  echo
  echo "- Run ID: $RID"
  echo "- Artifact: ${ART:-<none>}"
  echo "- Artifact dir: $DIR"
  echo
  if [ -n "${META:-}" ] && [ -f "$META" ]; then
    echo "## run_meta.txt"
    echo '```'
    sed -n '1,160p' "$META"
    echo '```'
  else
    echo "## run_meta.txt"
    echo "_not found in artifact_"
  fi
  if ls "$DIR"/edge_sheet_*.csv >/dev/null 2>&1; then
    echo
    echo "## CSV line count"
    echo '```'
    wc -l "$DIR"/edge_sheet_*.csv
    echo '```'
  fi
  if ls "$DIR"/data/pricefix_*.json >/dev/null 2>&1; then
    echo
    echo "## Board JSON size"
    echo '```'
    du -h "$DIR"/data/pricefix_*.json
    echo '```'
  fi
} > "$OUT"

echo "Wrote $OUT"
