#!/usr/bin/env bash
set -euo pipefail
DAY="${1:?usage: build_with_prefilter_v0.sh YYYY-MM-DD}"

BASE="runs/nba/${DAY}"
SRC="${BASE}/joined_with_phit_${DAY}.csv"
PREF="${BASE}/joined_with_phit_${DAY}_prefilter.csv"
BAK="${BASE}/joined_with_phit_${DAY}.csv.ORIG"

if [[ ! -f "$PREF" ]]; then
  echo "🚫 missing prefilter file: $PREF" >&2; exit 1
fi
cp -f "$SRC" "$BAK"
cp -f "$PREF" "$SRC"
python3 scripts/nba/build_slips_nba_v0.py --day "$DAY" || true
cp -f "$BAK" "$SRC"
echo "[build_with_prefilter_v0] restored ${SRC}"
