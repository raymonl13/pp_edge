#!/usr/bin/env python3
import os, json, glob, csv
from pathlib import Path
def first(p): 
    g=glob.glob(p, recursive=True)
    return Path(g[0]) if g else None
def read_json(p): 
    try: return json.loads(Path(p).read_text())
    except: return {}
def read_lines(p):
    try: return Path(p).read_text().splitlines()
    except: return []
def kv_meta(lines):
    out={}
    for ln in lines:
        if "=" in ln: k,v=ln.split("=",1); out[k.strip()]=v.strip()
        elif ":" in ln: k,v=ln.split(":",1); out[k.strip()]=v.strip()
    return out
def csv_rows(p):
    try:
        with open(p,newline="") as fh:
            r=csv.DictReader(fh)
            return [row for row in r]
    except: return []
def infer_day():
    m=read_json("metrics_run.json")
    d=(m.get("run") or {}).get("day")
    if d: return d
    g=glob.glob("edge_sheet_*.csv")
    if not g: return ""
    from re import match
    g=sorted(g)[-1]
    m=match(r"edge_sheet_(\d{4}-\d{2}-\d{2})\.csv", Path(g).name)
    return m.group(1) if m else ""
def build():
    day=os.environ.get("DAY") or infer_day()
    run_number=os.environ.get("GITHUB_RUN_NUMBER")
    commit=os.environ.get("GITHUB_SHA")
    rd=first("qa_alloc_*")
    meta=first("run_meta.txt") or (rd/ "run_meta.txt" if rd and (rd/ "run_meta.txt").exists() else None)
    meta_kv=kv_meta(read_lines(meta)) if meta else {}
    slips=[]
    alloc=first("alloc_slips_with_stakes.csv") or (rd/ "alloc_slips_with_stakes.csv" if rd else None)
    if alloc and Path(alloc).exists():
        rows=csv_rows(str(alloc))
        by_key={}
        for r in rows:
            k=r.get("slip_key") or r.get("slip_id") or "slip_0"
            by_key.setdefault(k,[]).append(r)
        for k,legs in by_key.items():
            stake=None
            for r in legs:
                v=r.get("stake") or r.get("wager") or r.get("stake_amount")
                if v:
                    try: stake=float(v); break
                    except: pass
            slip_type=legs[0].get("slip_type") or legs[0].get("type") or None
            legs_out=[]
            for r in legs:
                legs_out.append({
                    "player": r.get("player") or r.get("name"),
                    "market": r.get("market") or r.get("prop"),
                    "line": (float(r.get("line")) if r.get("line") not in (None,"") else None),
                    "price": (float(r.get("price")) if r.get("price") not in (None,"") else None)
                })
            slips.append({"slip_id":k,"type":slip_type,"stake":stake,"legs":legs_out})
    else:
        base=first("slips.csv") or (rd/ "slips.csv" if rd else None)
        rows=csv_rows(str(base)) if base and Path(base).exists() else []
        for i,r in enumerate(rows):
            slips.append({"slip_id":r.get("slip_key") or f"slip_{i}","type":r.get("slip_type"),"stake":None,"legs":[]})
    errors=[]; warns=[]
    if not slips: warns.append("no_slips_found")
    for s in slips:
        if not s.get("slip_id"): errors.append("slip_missing_id")
        if not isinstance(s.get("legs"), list): errors.append("slip_legs_not_list")
    out={
        "payload_version":"1.0",
        "run":{"day":day,"commit_sha":commit,"run_number":(int(run_number) if (run_number or "").isdigit() else None)},
        "slips":slips,
        "validation":{"errors":errors,"warnings":warns}
    }
    Path("submit_payload.json").write_text(json.dumps(out,indent=2))
    print("submit_payload.json written")
if __name__=="__main__":
    build()
