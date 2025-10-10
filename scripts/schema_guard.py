#!/usr/bin/env python3
import argparse,glob,json,os,sys
def load_schema(p):
    s=json.loads(open(p).read()); cols=s.get("columns",{}); req=set(s.get("required",list(cols.keys()))); return cols,req
def latest(base,pat):
    f=sorted(glob.glob(os.path.join(base,pat))); return f[-1] if f else None
def jcols(p):
    try:
        d=json.loads(open(p).read())
        if isinstance(d,list) and d and isinstance(d[0],dict): return list(d[0].keys())
        if isinstance(d,dict): return list(d.keys())
        return []
    except Exception: return []
def main():
    p=argparse.ArgumentParser(); p.add_argument("--schemas-dir",default="schema"); p.add_argument("--data-dir",default="."); a=p.parse_args()
    pat="odds_sanity_*.json"; sch=os.path.join(a.schemas_dir,"odds_sanity.json"); f=latest(a.data_dir,pat)
    if not f: print("[schema] missing pattern=%s"%pat); print("[schema] diff_total=1"); sys.exit(0)
    _,req=load_schema(sch); got=jcols(f); miss=[c for c in req if c not in got]; extra=[c for c in got if c not in req]
    if not miss and not extra: print("[schema] ok pattern=%s file=%s"%(pat,os.path.basename(f))); print("[schema] ok")
    else: print("[schema] diff=%d missing=%s unexpected=%s file=%s"%(len(miss)+len(extra),",".join(miss),",".join(extra),os.path.basename(f)))
if __name__=="__main__": main()
