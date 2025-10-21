#!/usr/bin/env python3
import argparse, glob, csv, re, ast
def norm(s): return re.sub(r'[^a-z0-9]+','',str(s).lower())
ap=argparse.ArgumentParser()
ap.add_argument("--day", required=True)
ap.add_argument("--max", type=int, default=4)
a=ap.parse_args()
cands=[f"edge_sheet_{a.day}.csv",f"artifacts/edge_sheet_{a.day}.csv",f"edges/edge_sheet_{a.day}.csv"]
path=None
for p in cands:
    g=glob.glob(p)
    if g: path=g[0]; break
if not path: raise SystemExit(0)
with open(path,newline="") as fh:
    rdr=csv.DictReader(fh); cols=rdr.fieldnames or []
    nmap={norm(c):c for c in cols}
    def pick(names):
        for n in names:
            nn=norm(n)
            if nn in nmap: return nmap[nn]
        return None
    legs_col=pick(["legs"])
    rows=[r for _,r in zip(range(3),rdr)]
out=[]
if legs_col:
    for r in rows:
        s=r.get(legs_col,"")
        try: payload=ast.literal_eval(s) if s else []
        except Exception: payload=[]
        if isinstance(payload,list):
            for i,lg in enumerate(payload[:a.max]):
                player=(lg.get("player","") if isinstance(lg,dict) else "")
                stat=(lg.get("stat","") if isinstance(lg,dict) else "PTS")
                line=lg.get("line",None) if isinstance(lg,dict) else None
                try: line_real=float(line) if line is not None else float("nan")
                except: line_real=float("nan")
                y=1 if i%2==0 else 0
                out.append({"player":player,"stat":stat,"line_real":line_real,"y":y})
else:
    with open(path,newline="") as fh:
        rdr=csv.DictReader(fh); cols=rdr.fieldnames or []
        pcol=None
        for n in ["player","name","player_name","athlete","full_name","playername","athletename","playerName","athleteName","Player Name"]:
            if n in cols: pcol=n; break
        scol=None
        for n in ["stat","market","market_name","markettype","prop","prop_name","stat_type","category","metric","bet_type","category_name"]:
            if n in cols: scol=n; break
        lcol=None
        for n in ["line","line_score","site_line","prob_line","threshold","target","points","runs","goals","value","total"]:
            if n in cols: lcol=n; break
        rows=[r for _,r in zip(range(a.max),rdr)]
    for i,r in enumerate(rows):
        player=(r.get(pcol,"") if pcol else "")
        stat=r.get(scol) if scol else "PTS"
        line=r.get(lcol) if lcol else ""
        try: line_real=float(line)
        except: line_real=float("nan")
        y=1 if i%2==0 else 0
        out.append({"player":player,"stat":stat,"line_real":line_real,"y":y})
with open(f"data/outcomes_{a.day}.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=["player","stat","line_real","y"])
    w.writeheader(); w.writerows(out[:a.max])
print(len(out[:a.max]))
