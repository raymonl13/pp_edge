#!/usr/bin/env bash
set -euo pipefail
d="${1:-.}"
meta="$(find "$d" -type f -name run_meta.txt | head -n1)"
test -f "$meta"
grep -q '^MODEL_STATE=' "$meta"
grep -q '^CAL_STATE=' "$meta"
csv="$(find "$d" -type f -name 'edge_sheet_*.csv' | head -n1)"
test -f "$csv"
head -n1 "$csv" | grep -q 'player,game_id,p_hit,edge_pp,tier,slip_type'
rows=$(wc -l < "$csv" | tr -d ' ')
if [ "$rows" -lt 2 ]; then echo "ERR: empty edge_sheet"; exit 1; fi
echo OK
