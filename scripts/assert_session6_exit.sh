#!/usr/bin/env bash
set -euo pipefail
d="$1"
edge="$(find "$d" -type f -name 'edge_sheet_*.csv' -print | head -n 1)"
slip="$(find "$d" -type f -name 'alloc_slips.csv' -print | head -n 1)"
meta="$(find "$d" -type f -name 'run_meta.txt' -print | head -n 1)"
test -f "$edge"
test -f "$slip"
test -f "$meta"
erows=$(wc -l < "$edge" | tr -d ' ')
srows=$(wc -l < "$slip" | tr -d ' ')
head -n1 "$edge" | grep -q 'player,game_id,p_hit,edge_pp,tier,slip_type'
head -n1 "$slip" | grep -q 'slip_id,slip_type,size,ev,ev_method,players,games'
grep -q '^SLIPS_BUILT=' "$meta"
grep -q '^SLIP_KEYS_METHOD=' "$meta"
grep -q '^SLIP_KEYS_OBSERVED=' "$meta"
grep -q '^SLIP_EV_METHOD=' "$meta"
if [ "$erows" -lt 2 ]; then echo "FAIL: edge_sheet is header-only"; exit 1; fi
if [ "$srows" -lt 2 ]; then echo "FAIL: alloc_slips.csv is header-only"; exit 1; fi
echo "PASS: Session 6 exit criteria met"
echo "--- edge_sheet header ---"; head -n1 "$edge"
echo "--- alloc_slips sample ---"; head -n5 "$slip"
echo "--- meta slip lines ---"; grep -E '^(SLIPS_BUILT|SLIP_KEYS_METHOD|SLIP_KEYS_OBSERVED|SLIP_EV_METHOD)=' "$meta"
