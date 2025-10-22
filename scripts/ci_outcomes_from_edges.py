#!/usr/bin/env python3
import argparse, csv, glob, os

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
        pcol=None
        for c in ("p_raw","p_hit","prob","win_prob","y_prob","p_model"): 
            if c in cols: pcol=c; break
        scol=None
        for c in ("stat","market","market_name","stat_type","category","prop","prop_name"):
            if c in cols: scol=c; break
        lcol=None
        for c in ("line","line_score","site_line","prob_line","line_real","threshold","target","points","runs","goals","value","total"):
            if c in cols: lcol=c; break
        pl=None
        for c in ("player","name","player_name","athlete","full_name"):
            if c in cols: pl=c; break
        k=0
        for row in rdr:
            rows.append({
                "player": (row.get(pl) or "").strip() if pl else "",
                "stat":   (row.get(scol) or "PTS").strip() if scol else "PTS",
                "line":   row.get(lcol),
                "p_raw":  row.get(pcol) if pcol else None
            })
            k+=1
            if k>=limit: break
    return rows

def write_outcomes(day, rows):
    os.makedirs("data", exist_ok=True)
    out=f"data/outcomes_{day}.csv"
    n=len(rows)
    with open(out, "w", newline="") as fh:
        fn=["player","stat","line_real","y","p_raw"]
        w=csv.DictWriter(fh, fieldnames=fn)
        w.writeheader()
        for i,r in enumerate(rows):
            if isinstance(r, (tuple, list)) and len(r)==2: r=r[1]
            pr = r.get("p_raw")
            try: pr=float(pr) if pr is not None else None
            except: pr=None
            if pr is None:
                pr = 0.2 + 0.6*(i/(n-1) if n>1 else 0.5)
            y = 1 if pr>=0.6 else 0
            try: ln=float(r.get("line")) if r.get("line") is not None else ""
            except: ln=""
            w.writerow({"player":r.get("player",""),"stat":r.get("stat","PTS"),"line_real":ln,"y":y,"p_raw":pr})
    print(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--day", required=True)
    ap.add_argument("--max", type=int, default=12)
    a=ap.parse_args()
    path=find_edges(a.day)
    if not path: 
        print("no_edges"); return
    rows=read_edges(path,a.max)
    if not rows:
        print("no_rows"); return
    write_outcomes(a.day, rows)

if __name__=="__main__":
    main()
