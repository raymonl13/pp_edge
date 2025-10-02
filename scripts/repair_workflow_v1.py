#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path

wf = Path(".github/workflows/manual_edge_sheet_e2e.yml")
txt = wf.read_text()
L = txt.splitlines()

# locate all top-level step headers
idx = [i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
if not idx:
    print("NO_STEPS_FOUND"); exit(1)

def block(k):
    s = idx[k]; e = idx[k+1] if k+1 < len(idx) else len(L); return s,e

# helper: discover a good step indent
step_indent = re.match(r'^(\s*)', L[idx[0]]).group(1)

# 1) swap "Emit CSV from board" -> "Score board"
cmd_score = 'python3 scripts/score_board.py "$DAY" --cfg config_pp_edge_v6.8.yaml'
emit_found = False
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Emit CSV from board\s*$', L[idx[k]]):
        s,e = block(k)
        ind = re.match(r'^(\s*)', L[idx[k]]).group(1)
        L[idx[k]] = f"{ind}- name: Score board"
        # find run: and replace fully (handle multiline)
        replaced = False
        for j in range(s+1, e):
            m = re.match(r'^(\s*)run:\s*(\|.*|>.*|.*)$', L[j])
            if m:
                ind2 = m.group(1); j2 = j+1
                while j2 < e and (L[j2].startswith(ind2+"  ") or L[j2].strip()==""):
                    j2 += 1
                del L[j:j2]
                L.insert(j, f"{ind2}run: {cmd_score}")
                replaced = True
                break
        if not replaced:
            L.insert(s+1, f"{ind}  run: {cmd_score}")
        emit_found = True
        break
# if swap not found, do nothing; a separate score step may already exist

# refresh step indices after possible edits
idx = [i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]

# discover Upload and QA gate
upload_k = None
qagate_k = None
for k in range(len(idx)):
    name = L[idx[k]].strip()
    if re.search(r'^- name:\s*Upload\s*$', name): upload_k = k
    if re.search(r'^- name:\s*QA gate\s*$', name): qagate_k = k

# 2) insert Build slips before Upload (or QA gate if Upload missing; else before end)
need_build = True
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Build slips\s*$', L[idx[k]]): need_build = False; break

if need_build:
    insert_at = None
    if upload_k is not None: insert_at = idx[upload_k]
    elif qagate_k is not None: insert_at = idx[qagate_k]
    else: insert_at = len(L)  # append at end
    ind = step_indent
    L[insert_at:insert_at] = [
        f"{ind}- name: Build slips",
        f'{ind}  run: python3 scripts/build_slips.py "$DAY" --cfg config_pp_edge_v6.8.yaml'
    ]

# refresh step indices again
idx = [i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]

# 3) ensure Upload exists; if not, create before QA gate/end and include slip artifacts
upload_k = None
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Upload\s*$', L[idx[k]]): upload_k = k; break

if upload_k is None:
    # create Upload block
    insert_at = idx[qagate_k] if qagate_k is not None else len(L)
    ind = step_indent
    up = [
        f"{ind}- name: Upload",
        f"{ind}  uses: actions/upload-artifact@v4",
        f"{ind}  with:",
        f"{ind}    name: qa_alloc_auto",
        f"{ind}    path: |",
        f"{ind}      edge_sheet_*.csv",
        f"{ind}      qa_report.json",
        f"{ind}      qa_report.csv",
        f"{ind}      alloc_summary.csv",
        f"{ind}      run_meta.txt",
        f"{ind}      .artifact_marker",
        f"{ind}      slips.json",
        f"{ind}      alloc_slips.csv",
        f"{ind}    if-no-files-found: warn",
        f"{ind}    compression-level: 6",
        f"{ind}    overwrite: false",
    ]
    L[insert_at:insert_at] = up
else:
    # ensure slip files are included in Upload paths
    s,e = block(upload_k)
    # find "path: |"
    path_line = None
    for j in range(s+1, e):
        if re.match(r'^\s*path:\s*\|', L[j]): path_line = j; break
    if path_line is not None:
        ind = re.match(r'^(\s*)', L[path_line]).group(1) + "  "
        present = set()
        j = path_line+1
        while j < e and (L[j].startswith(ind) or L[j].strip()==""):
            present.add(L[j].strip()); j += 1
        for want in ["slips.json","alloc_slips.csv"]:
            if want not in present:
                L.insert(j, ind+want)

# 4) relax fallback placeholders (continue-on-error: true)
idx = [i for i,l in enumerate(L) if re.match(r'^\s*-\s*name:\s*', l)]
for k in range(len(idx)):
    if re.search(r'^\s*-\s*name:\s*Fallback meta and CSV \(force placeholders\)\s*$', L[idx[k]]):
        s,e = block(k); found=False
        for j in range(s+1, e):
            m = re.match(r'^(\s*)continue-on-error:\s*', L[j])
            if m:
                L[j] = f"{m.group(1)}continue-on-error: true"
                found=True; break
        if not found:
            ind = re.match(r'^(\s*)', L[idx[k]]).group(1) + "  "
            L.insert(s+1, f"{ind}continue-on-error: true")
        break

wf.write_text("\n".join(L))
print("OK")
