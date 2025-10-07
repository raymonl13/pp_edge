#!/usr/bin/env python3
import os, csv, json, re
from pathlib import Path

def load_metrics():
    for pat in ["metrics_run.json","ci_all/**/metrics_run.json","**/metrics_run.json"]:
        for p in Path(".").glob(pat):
            try: return json.loads(p.read_text())
            except Exception: pass
    return {}

def infer_day():
    m = load_metrics()
    d = (m.get("run") or {}).get("day")
    if d: return d
    g = sorted(Path(".").glob("edge_sheet_*.csv"))
    if not g: return ""
    m = re.match(r"edge_sheet_(\d{4}-\d{2}-\d{2})\.csv", g[-1].name)
    return m.group(1) if m else ""

def load_schema():
    p = Path("ci/model_schema.json")
    if not p.exists(): return None
    try:
        s = json.loads(p.read_text())
        feats = s.get("features") or {}
        return {"version": s.get("version") or "1.0", "features": feats}
    except Exception:
        return None

def read_csv_head(path, limit=200):
    rows=[]
    try:
        with open(path, newline="") as fh:
            r=csv.DictReader(fh)
            for i,row in enumerate(r):
                rows.append(row)
                if i+1>=limit: break
    except Exception:
        pass
    return rows

def bucket_of(values):
    vals=[v for v in values if v not in (None,"")]
    if not vals: return "unknown"
    boolset={"0","1","true","false","True","False","yes","no","YES","NO"}
    def is_int(x):
        try: xi=float(str(x)); return xi.is_integer()
        except: return False
    def is_float(x):
        try: float(str(x)); return True
        except: return False
    def is_bool(x): return str(x).strip() in boolset
    def is_dt(x):
        s=str(x).strip()
        if re.match(r"\d{4}-\d{2}-\d{2}$", s): return True
        if re.match(r"\d{4}-\d{2}-\d{2}T", s): return True
        return False
    if all(is_bool(v) for v in vals): return "boolean"
    if all(is_int(v) for v in vals): return "integer"
    if all(is_float(v) for v in vals): return "numeric"
    if all(is_dt(v) for v in vals): return "datetime"
    return "categorical"

def detect_types(rows):
    cols={}
    if not rows: return cols
    for k in rows[0].keys():
        cols[k]=bucket_of([row.get(k) for row in rows])
    return cols

def write_meta(updates):
    p=Path("run_meta.txt")
    existing={}
    if p.exists():
        for ln in p.read_text().splitlines():
            if "=" in ln:
                k,v=ln.split("=",1); existing[k.strip()]=v.strip()
    existing.update(updates)
    p.write_text("\n".join(f"{k}={existing[k]}" for k in sorted(existing))+"\n")

def main():
    day=os.environ.get("DAY") or infer_day()
    csv_path=Path(f"edge_sheet_{day}.csv") if day else None

    # SKIP (not ERROR) when the CSV isn't built yet
    if (not csv_path) or (not csv_path.exists()):
        out={"parity":"SKIP","reason":"EDGE_SHEET_NOT_BUILT","missing":[],"extra":[],"type_mismatch":[],"schema_version":None}
        Path("model_parity.json").write_text(json.dumps(out,indent=2))
        # Do not set MODEL_STATE to ERROR; allow scorer to run
        print("[parity] state=SKIP missing=0 extra=0 mismatched=0")
        return

    schema=load_schema()
    if schema is None or not isinstance(schema.get("features"),dict) or not schema["features"]:
        out={"parity":"ERROR","reason":"SCHEMA_MISSING_OR_EMPTY","missing":[],"extra":[],"type_mismatch":[],"schema_version": (schema or {}).get("version")}
        Path("model_parity.json").write_text(json.dumps(out,indent=2))
        write_meta({"MODEL_STATE":"ERROR","MODEL_REASON":"SCHEMA_MISSING_OR_EMPTY"})
        print("[parity] state=ERROR missing=0 extra=0 mismatched=0")
        return

    rows=read_csv_head(csv_path, limit=200)
    found_types=detect_types(rows)
    expected=schema["features"]

    missing=sorted([f for f in expected if f not in found_types])
    extra=sorted([c for c in found_types if c not in expected])
    mismatched=[]
    for f,exp_t in expected.items():
        if f in found_types:
            got_t=found_types[f]
            if exp_t!=got_t:
                mismatched.append({"feature":f,"expected":exp_t,"found":got_t})

    state="PASS" if (not missing and not mismatched) else "ERROR"
    out={"parity":state,"reason":None if state=="PASS" else "SCHEMA_MISMATCH","missing":missing,"extra":extra,"type_mismatch":mismatched,"schema_version":schema["version"]}
    Path("model_parity.json").write_text(json.dumps(out,indent=2))
    if state=="ERROR":
        reason=f"missing={len(missing)} mismatched={len(mismatched)}"
        write_meta({"MODEL_STATE":"ERROR","MODEL_REASON":reason})
    else:
        write_meta({"MODEL_STATE":"OK","MODEL_REASON":"PARITY_OK"})
    print(f"[parity] state={state} missing={len(missing)} extra={len(extra)} mismatched={len(mismatched)}")

if __name__=="__main__":
    main()
