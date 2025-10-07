#!/usr/bin/env python3
import os, json, glob, csv, subprocess
from pathlib import Path

def first_any(patterns, roots=(".", "ci_all")):
    for root in roots:
        for pat in patterns:
            ps = str(Path(root) / pat)
            for p in glob.glob(ps, recursive=True):
                return Path(p)
    return None

def load_metrics():
    for pat in ["ci_all/**/metrics_run.json", "**/metrics_run.json", "metrics_run.json"]:
        for p in glob.glob(pat, recursive=True):
            try:
                return json.loads(Path(p).read_text())
            except Exception:
                pass
    return {}

def git_head():
    try:
        s = subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
        return s or None
    except Exception:
        return None

def read_json_file(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return None

def read_lines(p):
    try:
        return Path(p).read_text().splitlines()
    except Exception:
        return []

def kv_meta(lines):
    out={}
    for ln in lines:
        if "=" in ln:
            k,v=ln.split("=",1); out[k.strip()]=v.strip()
        elif ":" in ln:
            k,v=ln.split(":",1); out[k.strip()]=v.strip()
    return out

def csv_rows(path):
    try:
        with open(path, newline="") as fh:
            r=csv.DictReader(fh)
            return [row for row in r]
    except Exception:
        return []

def infer_day():
    m=load_metrics()
    d=(m.get("run") or {}).get("day")
    if d: return d
    g=sorted(glob.glob("edge_sheet_*.csv"))
    if not g: return ""
    from re import match
    m0=match(r"edge_sheet_(\d{4}-\d{2}-\d{2})\.csv", Path(g[-1]).name)
    return m0.group(1) if m0 else ""

def _to_float(x):
    try: return float(x)
    except Exception: return None

def _norm_leg(d):
    return {
        "player": d.get("player") or d.get("name"),
        "market": d.get("market") or d.get("prop"),
        "line": _to_float(d.get("line")),
        "price": _to_float(d.get("price")),
    }

def build_from_alloc_csv(p):
    rows=csv_rows(str(p))
    by={}
    for r in rows:
        k=r.get("slip_key") or r.get("slip_id") or "slip_0"
        by.setdefault(k,[]).append(r)
    slips=[]
    for k,legs in by.items():
        stake=None
        for r in legs:
            v=r.get("stake") or r.get("wager") or r.get("stake_amount")
            fv=_to_float(v) if v is not None else None
            if fv is not None: stake=fv; break
        typ=legs[0].get("slip_type") or legs[0].get("type") or None
        legs_out=[_norm_leg(r) for r in legs]
        legs_out.sort(key=lambda t: ((t.get("player") or ""), (t.get("market") or "")))
        slips.append({"slip_id":k,"type":typ,"stake":stake,"legs":legs_out})
    return slips

def build_from_slips_csv(p):
    rows=csv_rows(str(p))
    slips=[]
    for i,r in enumerate(rows):
        slips.append({"slip_id":r.get("slip_key") or f"slip_{i}","type":r.get("slip_type"),"stake":None,"legs":[]})
    return slips

def build_from_slips_json(p):
    raw=read_json_file(str(p))
    if raw is None: return []
    it=list(raw.values()) if isinstance(raw,dict) else (raw if isinstance(raw,list) else [])
    slips=[]
    for i,e in enumerate(it):
        if not isinstance(e,dict): continue
        sid=e.get("slip_id") or e.get("slip_key") or e.get("id") or f"slip_{i}"
        st=_to_float(e.get("stake") or e.get("stake_amount"))
        typ=e.get("type") or e.get("slip_type")
        legs_src=e.get("legs") if isinstance(e.get("legs"),list) else []
        legs_out=[_norm_leg(d) for d in legs_src if isinstance(d,dict)]
        legs_out.sort(key=lambda t: ((t.get("player") or ""), (t.get("market") or "")))
        slips.append({"slip_id":sid,"type":typ,"stake":st if st is not None else None,"legs":legs_out})
    return slips

def build():
    m=load_metrics()
    day=os.environ.get("DAY") or (m.get("run") or {}).get("day") or infer_day()
    run_number_env=os.environ.get("GITHUB_RUN_NUMBER")
    run_number=(int(run_number_env) if run_number_env and run_number_env.isdigit() else (m.get("run") or {}).get("run_number"))
    commit=os.environ.get("GITHUB_SHA") or (m.get("run") or {}).get("commit_sha") or git_head()

    rd = first_any(["qa_alloc_*"])
    meta = first_any(["run_meta.txt","**/run_meta.txt"]) or (rd/"run_meta.txt" if rd and (rd/"run_meta.txt").exists() else None)
    meta_kv = kv_meta(read_lines(meta)) if meta else {}

    source="none"
    slips=[]

    alloc = first_any(["alloc_slips_with_stakes.csv","**/alloc_slips_with_stakes.csv"]) or (rd/"alloc_slips_with_stakes.csv" if rd else None)
    if alloc and Path(alloc).exists():
        slips=build_from_alloc_csv(alloc); source="alloc"
        if len(slips)==0:
            csv_p = first_any(["slips.csv","**/slips.csv"]) or (rd/"slips.csv" if rd else None)
            if csv_p and Path(csv_p).exists():
                slips=build_from_slips_csv(csv_p); source="csv"
            if len(slips)==0:
                json_p= first_any(["slips.json","**/slips.json"]) or (rd/"slips.json" if rd else None)
                if json_p and Path(json_p).exists():
                    slips=build_from_slips_json(json_p); source="json"
    else:
        csv_p = first_any(["slips.csv","**/slips.csv"]) or (rd/"slips.csv" if rd else None)
        json_p= first_any(["slips.json","**/slips.json"]) or (rd/"slips.json" if rd else None)
        if csv_p and Path(csv_p).exists():
            slips=build_from_slips_csv(csv_p); source="csv"
        elif json_p and Path(json_p).exists():
            slips=build_from_slips_json(json_p); source="json"

    slips.sort(key=lambda s: s.get("slip_id") or "")

    errors, warns = [], []
    if not slips: warns.append("no_slips_found")
    for s in slips:
        if not s.get("slip_id"): errors.append("slip_missing_id")
        if not isinstance(s.get("legs"), list): errors.append("slip_legs_not_list")

    preview={"total_slips":len(slips),"top_slip_id":(slips[0]["slip_id"] if slips else None),"top_slip_legs":(len(slips[0]["legs"]) if slips else 0)}

    out={
        "payload_version":"1.0",
        "run":{"day":day,"commit_sha":commit,"run_number":run_number},
        "preview":preview,
        "slips":slips,
        "validation":{"errors":errors,"warnings":warns},
    }

    Path("submit_payload.json").write_text(json.dumps(out,indent=2))
    print(f"submit_payload: slips={len(slips)} top={(slips[0]['slip_id'] if slips else 'None')} source={source}")
    print("submit_payload.json written")

if __name__=="__main__":
    build()
