#!/usr/bin/env python3
import argparse, glob, json, os, sys
def _parse_yaml_kv(path):
    out={}; 
    try:
        for line in open(path):
            t=line.strip()
            if not t or t.startswith("#") or ":" not in t: continue
            k,v=t.split(":",1); k=k.strip(); v=v.strip()
            try: out[k]=float(v)
            except: out[k]=v
    except Exception: pass
    return out
def _psi(o):
    if not isinstance(o,dict): return None
    if o.get("psi") is not None:
        try: return float(o["psi"])
        except: return None
    pf=o.get("psi_by_feature")
    if isinstance(pf,dict) and pf:
        vs=[v for v in pf.values() if v is not None]
        if vs:
            try: return float(sum(vs)/len(vs))
            except: return None
    return None
def main():
    p=argparse.ArgumentParser(); p.add_argument("--glob",default="ci_cache/drift/**/*.json"); p.add_argument("--slo",default="ci/slo.yaml"); p.add_argument("--outdir",default="drift_trend"); a=p.parse_args()
    slo={"psi_warn":0.10,"psi_fail":0.20,"window":14}
    if os.path.exists(a.slo):
        cfg=_parse_yaml_kv(a.slo)
        if "psi_warn" in cfg:
            try: slo["psi_warn"]=float(cfg["psi_warn"])
            except: pass
        if "psi_fail" in cfg:
            try: slo["psi_fail"]=float(cfg["psi_fail"])
            except: pass
        if "window" in cfg:
            try: slo["window"]=int(cfg["window"])
            except: pass
    files=sorted(glob.glob(a.glob,recursive=True)); recs=[]
    for f in files:
        try: d=json.loads(open(f).read())
        except Exception: d={}
        if isinstance(d,list): d=d[-1] if d else {}
        b=os.path.basename(f); dt=b.split("_")[-1].split(".")[0] if "_" in b else None
        recs.append({"date":dt,"psi":_psi(d)})
    os.makedirs(a.outdir,exist_ok=True)
    if not recs:
        open(os.path.join(a.outdir,"drift_trend.json"),"w").write("[]")
        open(os.path.join(a.outdir,"drift_trend.csv"),"w").write("date,psi\n")
        print("[drift] psi=nan state=OK window=%s base=missing"%slo["window"]); sys.exit(0)
    recs=[r for r in recs if r.get("date")]; recs.sort(key=lambda r:r["date"])
    open(os.path.join(a.outdir,"drift_trend.json"),"w").write(json.dumps(recs))
    w=open(os.path.join(a.outdir,"drift_trend.csv"),"w"); w.write("date,psi\n")
    for r in recs: w.write("%s,%s\n"%(r["date"], "" if r["psi"] is None else "{:.5f}".format(r["psi"]))); w.close()
    psi=recs[-1]["psi"]; state="OK"
    if psi is not None and psi>=slo.get("psi_fail",0.2): state="FAIL"
    elif psi is not None and psi>=slo.get("psi_warn",0.1): state="WARN"
    ps="nan" if psi is None else "{:.5f}".format(psi)
    print("[drift] psi=%s state=%s window=%s base=%s"%(ps,state,slo["window"],"present" if psi is not None else "missing"))
if __name__=="__main__": main()
