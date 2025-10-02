#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
fk=None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Fallback meta and CSV \(force placeholders\)\s*$', L[idx[k]]):
        fk=k; break
if fk is None:
    print("FALLBACK_STEP_NOT_FOUND"); exit(0)
s,e=blk(fk)
# ensure continue-on-error: true
found=False
for j in range(s+1,e):
    m=re.match(r'^(\s*)continue-on-error:\s*(.+)$', L[j])
    if m:
        L[j]=f"{m.group(1)}continue-on-error: true"; found=True; break
if not found:
    ind=re.match(r'^(\s*)', L[idx[fk]]).group(1)+"  "
    L.insert(s+1, f"{ind}continue-on-error: true"); e+=1
# replace run: with non-destructive seeding only-if-missing
run=None
for j in range(s+1,e):
    if re.match(r'^\s*run:\s*(\|.*|>.*|.*)$', L[j]): run=j; break
ind2=re.match(r'^(\s*)', L[idx[fk]]).group(1)+"  "
body=[
    f"{ind2}run: |",
    f"{ind2}  set -euo pipefail",
    f'{ind2}  if [ -z "${{DAY:-}}" ]; then DAY="$(date -u +%F)"; fi',
    f'{ind2}  es="edge_sheet_${{DAY}}.csv"; [ -f "$es" ] || printf "player,game_id,p_hit,edge_pp,tier,slip_type\\n" > "$es"',
    f'{ind2}  [ -f run_meta.txt ] || printf "CSV_ROWS=0\\n" > run_meta.txt',
    f"{ind2}  [ -f qa_report.json ] || printf '{{}}' > qa_report.json",
    f"{ind2}  [ -f qa_report.csv ] || printf 'severity,msg\\n' > qa_report.csv",
    f"{ind2}  [ -f alloc_summary.csv ] || printf 'player,game_id,tier,slip_type,stake\\n' > alloc_summary.csv",
    f"{ind2}  [ -f slips.json ] || printf '{{\"day\":\"%s\",\"slips\":[]}}\\n' \"$(date -u +%F)\" > slips.json",
    f"{ind2}  [ -f alloc_slips.csv ] || printf 'slip_id,slip_type,size,ev,ev_method,players,games\\n' > alloc_slips.csv",
]
if run is None:
    L.insert(e, body[0]); L[e+1:e+1]=body[1:]
else:
    # delete old run block body and replace
    m=re.match(r'^(\s*)', L[run])
    j=run+1
    while j<e and (L[j].startswith(m.group(1)+"  ") or L[j].strip()==""):
        j+=1
    del L[run:j]
    L[run:run]=body
wf.write_text("\n".join(L)); print("OK")
