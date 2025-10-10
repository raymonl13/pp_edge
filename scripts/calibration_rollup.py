#!/usr/bin/env python3
import argparse, glob, json, os, sys, datetime, csv
def _rows_from_file(path):
    try: d=json.loads(open(path).read())
    except Exception: return []
    if isinstance(d,dict): d=[d]
    out=[]; 
    for r in d:
        dt=r.get("date")
        if not dt:
            b=os.path.basename(path); dt=b.split("_")[-1].split(".")[0] if "_" in b else None
        out.append({"date":dt,"brier":r.get("brier"),"logloss":r.get("logloss"),"join_rows":r.get("join_rows")})
    return out
def _dt(s):
    try: return datetime.datetime.strptime(s,"%Y-%m-%d")
    except Exception: return None
def main():
    p=argparse.ArgumentParser(); p.add_argument("--glob",default="ci_cache/calibration/**/*.json"); p.add_argument("--outdir",default="calibration_trend"); a=p.parse_args()
    files=sorted(glob.glob(a.glob,recursive=True)); recs=[]
    for f in files: recs.extend(_rows_from_file(f))
    os.makedirs(a.outdir,exist_ok=True)
    if not recs:
        open(os.path.join(a.outdir,"calibration_trend.json"),"w").write("[]")
        open(os.path.join(a.outdir,"calibration_trend.csv"),"w").write("date,brier,logloss,join_rows\n")
        print("[cal] brier=nan join=0"); sys.exit(0)
    recs=[r for r in recs if r.get("date")]; recs.sort(key=lambda r:_dt(r["date"]) or datetime.datetime.min)
    tr=[r for r in recs if r.get("brier") is not None and r.get("logloss") is not None]
    open(os.path.join(a.outdir,"calibration_trend.json"),"w").write(json.dumps(tr))
    w=open(os.path.join(a.outdir,"calibration_trend.csv"),"w"); w.write("date,brier,logloss,join_rows\n")
    for r in tr: w.write("%s,%s,%s,%s\n"%(r["date"],r["brier"],r["logloss"],r.get("join_rows"))); w.close()
    if not tr: print("[cal] brier=nan join=0"); sys.exit(0)
    last_join=int(tr[-1].get("join_rows") or 0); last7=tr[-7:]; vals=[x["brier"] for x in last7 if x.get("brier") is not None]
    b7=sum(vals)/len(vals) if vals else None
    print("[cal] brier=%s join=%s"%("{:.5f}".format(b7) if b7 is not None else "nan", last_join))
if __name__=="__main__": main()
