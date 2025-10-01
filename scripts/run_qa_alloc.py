#!/usr/bin/env python3
import argparse,datetime,json,sys,os
from pathlib import Path
from code_utils_slipqa_v2 import load_edge_sheet,run_qa,_load_yaml,QA_RULES_VERSION
from code_utils_allocator_v2 import allocate,ALLOC_VERSION
def _write_csv(path:Path,rows,header):
    import csv
    with path.open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=header); w.writeheader()
        for r in rows: w.writerow({k:r.get(k) for k in header})
def _resolve_day(day, tz):
    if day: return day
    from zoneinfo import ZoneInfo
    now=datetime.datetime.now(ZoneInfo(tz))
    return (now.date()+datetime.timedelta(days=1)).isoformat()
def _append_meta(qa,alloc,extra=""):
    line=f"QA_STATE={qa} ALLOC_STATE={alloc} QA_RULES_VERSION={QA_RULES_VERSION} ALLOC_VERSION={ALLOC_VERSION}"
    if extra: line += f" {extra}"
    with open("run_meta.txt","a") as f: f.write(line+"\n")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("day",nargs="?"); ap.add_argument("--cfg",default="config_pp_edge_v6.8.yaml"); ap.add_argument("--tz",default="America/Los_Angeles")
    a=ap.parse_args()
    day=_resolve_day(a.day,a.tz)
    edge=Path(f"edge_sheet_{day}.csv")
    try:
        if not edge.exists():
            Path("qa_report.json").write_text(json.dumps({"state":"FAIL","rules_version":QA_RULES_VERSION,"issues":[{"severity":"FAIL","msg":"edge_csv_missing"}]},indent=2))
            Path("qa_report.csv").write_text("severity,msg\nFAIL,edge_csv_missing\n")
            Path("alloc_summary.csv").write_text("player,game_id,tier,slip_type,stake\n")
            _append_meta("FAIL","WARN","REASON=EDGE_CSV_MISSING")
            print("FAIL"); print("WARN"); return
        cfg=_load_yaml(Path(a.cfg))
        rows=load_edge_sheet(edge)
        qa=run_qa(rows,cfg)
        Path("qa_report.json").write_text(json.dumps(qa,indent=2,sort_keys=True))
        _write_csv(Path("qa_report.csv"),qa.get("issues",[]),["severity","msg"])
        qa_state=qa.get("state","UNKNOWN"); print(qa_state)
        out=allocate(rows,cfg)
        _write_csv(Path("alloc_summary.csv"),out,["player","game_id","tier","slip_type","stake"])
        alloc_state="OK" if any(float(r.get("stake") or 0)>0 for r in out) else "WARN"; print(alloc_state)
        _append_meta(qa_state,alloc_state,f"CSV_ROWS={len(rows)}")
    except Exception as e:
        Path("qa_report.json").write_text(json.dumps({"state":"FAIL","rules_version":QA_RULES_VERSION,"issues":[{"severity":"FAIL","msg":f"exception:{type(e).__name__}:{e}"}]},indent=2))
        Path("qa_report.csv").write_text("severity,msg\nFAIL,exception\n")
        _append_meta("FAIL","WARN",f"REASON=EXC:{type(e).__name__}")
        print("FAIL"); print("WARN")
    finally:
        sys.exit(0)
if __name__=="__main__": main()
