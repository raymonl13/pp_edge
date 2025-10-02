#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path, re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
L=wf.read_text().splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
def blk(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
cmd='python3 scripts/score_board.py "$DAY" --cfg config_pp_edge_v6.8.yaml'
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Emit CSV from board\s*$', L[idx[k]]):
        s,e=blk(k); ind=re.match(r'^(\s*)', L[idx[k]]).group(1); L[idx[k]]=f"{ind}- name: Score board"
        inserted=False
        for j in range(s+1,e):
            m=re.match(r'^(\s*)run:\s*(\|.*|>.*|.*)$', L[j])
            if m:
                ind2=m.group(1); j2=j+1
                while j2<e and (L[j2].startswith(ind2+"  ") or L[j2].strip()==""): j2+=1
                del L[j:j2]; L.insert(j, f"{ind2}run: {cmd}"); inserted=True; break
        if not inserted: L.insert(s+1, f"{ind}  run: {cmd}")
        break
wf.write_text("\n".join(L)); print("OK")
