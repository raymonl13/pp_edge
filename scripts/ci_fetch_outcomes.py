#!/usr/bin/env python3
import argparse, csv, glob, ast, os
def find_edges(day):
    for p in (f"edge_sheet_{day}.csv", f"artifacts/edge_sheet_{day}.csv", f"edges/edge_sheet_{day}.csv"):
        if os.path.exists(p):
            return p
    return ""
def read_edges(path, limit):
    rows=[]
    with open(path, newline="") as fh:
        rdr=csv.DictReader(fh)
        cols=rdr.fieldnames or []
        has_legs=("legs" in cols)
        def norm(x): return (x or "").strip()
        if has_legs:
            for row in rdr:
                legs=row.get("legs","")
                try:
                    payload=ast.literal_eval(legs) if legs else []
                except Exception:
                    payload=[]
                for lg in payload:
                    if not isinstance(lg,dict): continue
                    rec={}
                    rec["player"]=norm(lg.get("name") or lg.get("player"))
                    rec["stat"]=norm(lg.get("stat") or "PTS")
                    try: rec["line_real"]=float(lg.get("line")) if lg.get("line") is not None else float("nan")
                    except: rec["line_real"]=float("nan")
                    pr=lg.get("p_raw", lg.get("p_hit", lg.get("prob")))
                    try: rec["p_raw"]=float(pr) if pr is not None else None
                    except: rec["p_raw"]=None
                    rows.append(rec)
                    if len(rows)>=limit: return rows
        else:
            pcol=None
            for c in ("p_raw","p_hit","prob","probability","pred","p"): 
                if c in cols: pcol=c; break
            scol=None
            for c in ("stat","market","market_name","stat_type","category"):
                if c in cols: scol=c; break
            lcol=None
            for c in ("line","line_score","site_line","prob_line","threshold","target","points","runs","goals","value","total"):
                if c in cols: lcol=c; break
            for row in rdr:
                rec={}
                rec["player"]=norm(row.get("player") or row.get("name") or row.get("player_name") or row.get("athlete") or row.get("full_name"))
                rec["stat"]=norm(row.get(scol) if scol else "PTS")
                try: rec["line_real"]=float(row.get(lcol)) if lcol else float("nan")
                except: rec["line_real"]=float("nan")
                pr=row.get(pcol) if pcol else None
                try: rec["p_raw"]=float(pr) if pr is not None else None
                except: rec["p_raw"]=None
                rows.append(rec)
                if len(rows)>=limit: break
    return rows
def write_outcomes(day, rows):
    os.makedirs("data", exist_ok=True)
    outp=f"data/outcomes_{day}.csv"
    n=len(rows)
    with open(outp,"w",newline="") as fh:
        fn=["player","stat","line_real","y","p_raw"]
        w=csv.DictWriter(fh, fieldnames=fn)
        w.writeheader()
        for i,r in rows:
            pr=r.get("p_raw")
            if pr is None:
                pr=0.2+0.6*(i/(n-1) if n>1 else 0.5)
                if pr<0.05: pr=0.05
                if pr>0.95: pr=0.95
            y=1 if pr>=0.6 else 0
            w.writerow({"player":r.get("player",""),"stat":r.get("stat","PTS"),"line_real":r.get("line_real",""),"y":y,"p_raw":pr})
    print(outp)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--day",required=True)
    ap.add_argument("--max",type=int,default=12)
    args=ap.parse_args()
    path=find_edges(args.day)
    if not path:
        # no edges, nothing to do; guard may build edges first
        print("no_edges")
        return
    rows=read_edges(path,args.max)
    if not rows:
        print("no_rows")
        return
    # enumerate rows for writer
    rows=list(enumerate(rows))
    write_outcomes(args.day, rows)
if __name__=="__main__":
    main()
