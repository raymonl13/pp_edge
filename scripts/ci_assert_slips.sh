#!/usr/bin/env bash
set -euo pipefail
d="${1:-.}"
sj="$(find "$d" -type f -name slips.json -print -quit)"
sc="$(find "$d" -type f -name alloc_slips.csv -print -quit)"
test -f "$sj"
test -f "$sc"
head -n1 "$sc" | grep -q 'slip_id,slip_type,size,ev,ev_method,players,games'
echo OK
