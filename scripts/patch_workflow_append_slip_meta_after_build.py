#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt=wf.read_text(); L=txt.splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def bounds(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
build=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Build slips\s*$', L[idx[k]]): build=k; break
if build is None: print("BUILD_SLIPS_NOT_FOUND"); exit(1)
s,e=bounds(build); ins=e
ind=re.match(r'^(\s*)',L[idx[build]]).group(1)
step=[
f"{ind}- name: Append slip meta lines",
f"{ind}  if: always()",
f"{ind}  run: |",
f"{ind}    set -euo pipefail",
f'{ind}    m="run_meta.txt"',
f'{ind}    sfile="alloc_slips.csv"; sb=0; if [ -f "$sfile" ]; then sb=$(($(wc -l < "$sfile")-1)); [ "$sb" -lt 0 ] && sb=0; fi',
f'{ind}    grep -q "^SLIPS_BUILT=" "$m" 2>/dev/null || printf "SLIPS_BUILT=%s\\n" "$sb" >> "$m"',
f'{ind}    evm="none"; if [ -f "$sfile" ] && [ "$(wc -l < "$sfile")" -ge 2 ]; then evm="$(awk -F, "NR==2{print \\$5}" "$sfile")"; fi',
f'{ind}    grep -q "^SLIP_EV_METHOD=" "$m" 2>/dev/null || printf "SLIP_EV_METHOD=%s\\n" "$evm" >> "$m"',
f'{ind}    efile="$(ls edge_sheet_*.csv 2>/dev/null | head -n 1 || true)"; obs="NONE";',
f'{ind}    if [ -n "$efile" ] && [ -f "$efile" ]; then obs="$(awk -F, "NR>1 && NF>=6{print \\$6}" "$efile" | sort -u | paste -sd, -)"; [ -z "$obs" ] && obs="NONE"; fi',
f'{ind}    grep -q "^SLIP_KEYS_OBSERVED=" "$m" 2>/dev/null || printf "SLIP_KEYS_OBSERVED=%s\\n" "$obs" >> "$m"',
f'{ind}    pref="$(python3 - <<\'PPY\' 2>/dev/null || true)',
f'{ind}    import yaml',
f'{ind}    try:',
f'{ind}        d=yaml.safe_load(open("config_pp_edge_v6.8.yaml")) or {}',
f'{ind}        t=(d.get("slips") or {}).get("slip_types") or []',
f'{ind}        print(",".join(t))',
f'{ind}    except Exception:',
f'{ind}        pass',
f'{ind}    PPY',
f'{ind}    )"',
f'{ind}    method="observed"',
f'{ind}    if [ -n "$pref" ] && [ "$obs" != "NONE" ]; then',
f'{ind}      IFS=, read -r -a A <<< "$obs"; IFS=, read -r -a B <<< "$pref"; sub=1;',
f'{ind}      for a in "${{A[@]}}"; do found=0; for b in "${{B[@]}}"; do [ "$a" = "$b" ] && found=1 && break; done; [ "$found" -eq 0 ] && sub=0; done;',
f'{ind}      [ "$sub" -eq 1 ] && method="prefer";',
f'{ind}    fi',
f'{ind}    grep -q "^SLIP_KEYS_METHOD=" "$m" 2>/dev/null || printf "SLIP_KEYS_METHOD=%s\\n" "$method" >> "$m"',
]
L[ins:ins]=step
wf.write_text("\n".join(L)); print("OK")
