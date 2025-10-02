#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
t=wf.read_text(); L=t.splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
up=None
for i in idx:
    if re.search(r'^\s*-\s*name:\s*Upload\s*$',L[i]): up=i
if up is None: raise SystemExit(0)
for j in range(up):
    if re.search(r'^\s*-\s*name:\s*Ensure pre-upload placeholders\s*$',L[j]): raise SystemExit(0)
ind=re.match(r'^(\s*)',L[up]).group(1); runind=ind+"  "
body="set -euo pipefail\nif [ -z \"${DAY:-}\" ]; then DAY=\"$(date -u +%F)\"; fi\nf=\"edge_sheet_${DAY}.csv\"; test -f \"$f\" || printf \"player,game_id,p_hit,edge_pp,tier,slip_type\\n\" > \"$f\"\nmeta=\"run_meta.txt\"; test -f \"$meta\" || printf \"CSV_ROWS=0\\n\" > \"$meta\"\ntest -f qa_report.json || printf '{}' > qa_report.json\ntest -f qa_report.csv || printf 'severity,msg\\n' > qa_report.csv\ntest -f alloc_summary.csv || printf 'player,game_id,tier,slip_type,stake\\n' > alloc_summary.csv\n"
L.insert(up, runind+"- name: Ensure pre-upload placeholders")
L.insert(up+1, runind+"  if: always()")
L.insert(up+2, runind+"  run: |")
for line in body.splitlines():
    L.insert(up+3, runind+"    "+line)
wf.write_text("\n".join(L)); print("OK")
