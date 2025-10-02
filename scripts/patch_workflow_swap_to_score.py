#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
wf=Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt=wf.read_text(); L=txt.splitlines()
idx=[i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*',l)]
def bounds(k): s=idx[k]; e=idx[k+1] if k+1<len(idx) else len(L); return s,e
score_cmd='python3 scripts/score_board.py "$DAY" --cfg config_pp_edge_v6.8.yaml'
done=False
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Emit CSV from board\s*$', L[idx[k]]):
        s,e=bounds(k); ind=re.match(r'^(\s*)',L[idx[k]]).group(1); L[idx[k]]=f"{ind}- name: Score board"
        # replace or inject run:
        inserted=False
        for j in range(s+1,e):
            m=re.match(r'^(\s*)run:\s*(\|.*|>.*|.*)$', L[j])
            if m:
                # remove multiline run body if present
                ind2=m.group(1); j2=j+1
                while j2<e and (L[j2].startswith(ind2+"  ") or L[j2].strip()==""):
                    j2+=1
                del L[j:j2]
                L.insert(j, f"{ind2}run: {score_cmd}")
                inserted=True
                break
        if not inserted:
            L.insert(s+1, f"{ind}  run: {score_cmd}")
        done=True
        break
if not done:
    # Insert Score board before QA+Alloc
    qa=None
    for k in range(len(idx)):
        if re.search(r'^\s*-\s*name:\s*QA\+Alloc\s*$', L[idx[k]]):
            qa=idx[k]; break
    if qa is None:
        print("ERR: QA+Alloc step not found"); exit(1)
    ind=re.match(r'^(\s*)',L[qa]).group(1)
    ins=qa
    L[ins:ins]=[f"{ind}- name: Score board", f"{ind}  run: {score_cmd}"]
wf.write_text("\n".join(L))
print("OK")
