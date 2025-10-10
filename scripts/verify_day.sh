#!/usr/bin/env bash
set -euo pipefail
WF="nightly_edge_sheet.yml"
DAY="${1:-}"
RID="$(gh run list --workflow "$WF" --branch main -L 1 --json databaseId | jq -r ".[0].databaseId")"
rm -rf "ci_${RID}" && mkdir -p "ci_${RID}"
for NAME in edgesheet calibration drift outcomes_rollup rollup_probe; do
  gh run download "$RID" -n "$NAME" -D "ci_${RID}/$NAME" >/dev/null 2>&1 || true
done
CSV="$(find "ci_${RID}/edgesheet" -type f -name "edge_sheet_*.csv" | head -n 1 || true)"
if [ -z "${CSV:-}" ]; then echo "NO_EDGESHEET"; exit 2; fi
DAY_RUN="$(basename "$CSV" | sed -E "s/edge_sheet_([0-9-]+)\\.csv/\\1/")"
if [ -n "${DAY:-}" ] && [ "$DAY" != "$DAY_RUN" ]; then echo "DAY_MISMATCH: edgesheet=$DAY_RUN expected=$DAY"; fi
CAL="ci_${RID}/calibration/calibration_${DAY_RUN}.json"
DRF="ci_${RID}/drift/drift_${DAY_RUN}.json"
PRO="ci_${RID}/rollup_probe/rollup_probe.json"
ROL="ci_${RID}/outcomes_rollup/outcomes_rollup.json"
[ -f "$CAL" ] && printf "CAL=" && jq -c "." "$CAL" | sed -n "1p" || echo "CAL_MISSING"
[ -f "$DRF" ] && printf "DRIFT=" && jq -c "." "$DRF" | sed -n "1p" || echo "DRIFT_MISSING"
[ -f "$PRO" ] && printf "PROBE=" && jq -c "." "$PRO" | sed -n "1p" || echo "PROBE_MISSING"
[ -f "$ROL" ] && printf "ROLLOP=" && jq -c "." "$ROL" | sed -n "1p" || echo "ROLLOP_JSON_MISSING"
