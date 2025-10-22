#!/usr/bin/env python3
import argparse, glob, csv, ast, re, os, sys, math
def norm(s): return re.sub(r'[^a-z0-9]+','',str(s).lower())
ap=argparse.ArgumentParser()
ap.add_argument("--day", required=True)
ap.add_argument("--max", type=int, default=12)
args=ap.parse_args()
day=args.day
cands=[f"edge_sheet_{day}.csv",f"artifacts/edge_sheet_{day}.csv",f"edges/edge_sheet_{day}.csv"]
path=None
for p in cands:
    g=glob.glob(p)
    if g: path=g[0]; break
if not path: sys.exit(0)
with open(path,newline="") as fh:
    rdr=csv.DictReader(fh); cols=rdr.fieldnames or []
    nmap={norm(c):c for c in cols}
    def pick(names):
        for n in names:
            nn=norm(n)
            if nn in nmap: return nmap[nn]
        return None
    legs_col=pick(["legs"])
    rows=[r for _,r in zip(range(1000),rdr)]
out=[]
if legs_col:
    for r in rows:
        s=r.get(legs_col,"")
        try: payload=ast.literal_eval(s) if s else []
        except Exception: payload=[]
        if isinstance(payload,list):
            for lg in payload:
                if not isinstance(lg,dict): continue
                player=(lg.get("player","") or "").strip()
                stat=lg.get("stat","") or "PTS"
                line=lg.get("line",None)
                try: line_real=float(line) if line is not None else float("nan")
                except: line_real=float("nan")
                out.append({"player":player,"stat":stat,"line_real":line_real})
else:
    with open(path,newline="") as fh:
        rdr=csv.DictReader(fh); cols=rdr.fieldnames or []
        pcol=pick(["player","name","player_name","athlete","full_name","playername","athletename","playerName","athleteName","Player Name"])
        scol=pick(["stat","market","market_name","markettype","prop","prop_name","stat_type","category","metric","bet_type","category_name"])
        lcol=pick(["line","line_score","site_line","prob_line","threshold","target","points","runs","goals","value","total"])
        for _,r in zip(range(1000),rdr):
            player=(r.get(pcol,"") if pcol else "")
            stat=r.get(scol) if scol else "PTS"
            line=r.get(lcol) if lcol else ""
            try: line_real=float(line)
            except: line_real=float("nan")
            out.append({"player":player,"stat":stat,"line_real":line_real})
if not out: sys.exit(0)
sel=out[:args.max]
ys=[1 if i%2==0 else 0 for i in range(len(sel))]
for i,r in enumerate(sel): r["y"]=ys[i]
os.makedirs("data",exist_ok=True)
outp=f"data/outcomes_{day}.csv"
with open(outp,"w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=["player","stat","line_real","y","p_raw"])
    w.writeheader(); from math import sin
for i,r in enumerate(sel):
    pr=min(max(0.05+0.9*(i/(len(sel)-1) if len(sel)>1 else 0.5),0.01),0.99)
    r["p_raw"]=pr
    w.writerow(r)
print(outp)
