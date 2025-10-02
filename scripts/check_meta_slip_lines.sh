#!/usr/bin/env bash
set -euo pipefail
d="${1:-.}"
m="$(find "$d" -type f -name run_meta.txt -print | head -n 1)"
test -f "$m"
need=(SLIPS_BUILT SLIP_KEYS_METHOD SLIP_KEYS_OBSERVED SLIP_EV_METHOD)
missing=0
for k in "${need[@]}"; do
  if ! grep -q "^$k=" "$m"; then
    echo "MISSING:$k"
    missing=1
  fi
done
if [ "$missing" -eq 0 ]; then
  echo "META_OK"
  grep -E '^(SLIPS_BUILT|SLIP_KEYS_METHOD|SLIP_KEYS_OBSERVED|SLIP_EV_METHOD)=' "$m"
else
  exit 1
fi
