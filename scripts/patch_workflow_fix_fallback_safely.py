#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt=wf.read_text(); L=txt.splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def bounds(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
body = [
  "set -euo pipefail",
  'if [ -z "${DAY:-}" ]; then DAY="$(date -u +%F)"; fi',
  'f="edge_sheet_${DAY}.csv"; [ -s "$f" ] || printf "player,game_id,p_hit,edge_pp,tier,slip_type\\n" > "$f"',
  'meta="run_meta.txt"; [ -f "$meta" ] || printf "CSV_ROWS=0\\n" > "$meta"',
  'grep -q "^CSV_ROWS=" "$meta" || printf "CSV_ROWS=0\\n" >> "$meta"',
  "[ -f qa_report.json ] || printf '{}' > qa_report.json",
  "[ -f qa_report.csv ] || printf 'severity,msg\\n' > qa_report.csv",
  "[ -f alloc_summary.csv ] || printf 'player,game_id,tier,slip_type,stake\\n' > alloc_summary.csv",
]
def patch_fallback():
  for k,i in enumerate(idx):
    if re.search(r'^\s*-\s*name:\s*Fallback meta and CSV \(force placeholders\)\s*$', L[i]):
      s,e=bounds(k)
      ind=re.match(r'^(\s*)',L[i]).group(1)+"  "
      # ensure continue-on-error
      inserted=False
      for j in range(s+1,e):
        m=re.match(r'^(\s*)continue-on-error:\s*',L[j])
        if m: L[j]=f"{m.group(1)}continue-on-error: true"; inserted=True; break
      if not inserted:
        L.insert(s+1, f"{ind}continue-on-error: true"); e+=1
      # replace run block with non-destructive shell
      run_line=None
      for j in range(s+1,e):
        if re.match(r'^\s*run:\s*(\|.*|>.*|.*)$', L[j]): run_line=j; break
      if run_line is None:
        L.insert(e, f"{ind}run: |"); run_line=e; e+=1
      else:
        # remove any existing multiline body
        m=re.match(r'^(\s*)',L[run_line])
        j=run_line+1
        while j<e and (L[j].startswith(m.group(1)+"  ") or L[j].strip()==""): j+=1
        del L[run_line+1:j]; e=run_line+1
        if not re.search(r'^\s*run:\s*\|',L[run_line]):
          L[run_line]=f"{ind}run: |"
      for n,line in enumerate(body):
        L.insert(run_line+1+n, f"{ind}  {line}")
      return True
  return False
if patch_fallback():
  wf.write_text("\n".join(L)); print("OK")
else:
  print("FALLBACK_STEP_NOT_FOUND")
