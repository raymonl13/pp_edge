#!/usr/bin/env python3
import argparse, csv, json, os, glob, unicodedata
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

STAT_ALIASES={"PTS":"PTS","POINTS":"PTS","REB":"REB","REBOUNDS":"REB","AST":"AST","ASSISTS":"AST",
              "3PM":"3PM","THREES":"3PM","3PTM":"3PM","3PMADE":"3PM","3P_MADE":"3PM",
              "HR":"HR","HRS":"HR","HOMERUNS":"HR","HOME_RUNS":"HR",
              "SO":"SO","K":"SO","STRIKEOUTS":"SO",
              "H":"H","HITS":"H",
              "R":"R","RUNS":"R",
              "RBI":"RBI",
              "SB":"SB","STEALS":"SB",
              "SOG":"SOG","SHOTS_ON_GOAL":"SOG"}

def _strip_accents(s): return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
def canon_player(s): 
    s=_strip_accents((s or "")).lower()
    s=''.join(ch for ch in s if ch.isalnum() or ch.isspace())
    return ' '.join(s.split())
def canon_stat(s):
    k=''.join(ch for ch in (s or "") if ch.isalnum()).upper()
    return STATING.get(k,k) if (STATING:={"3PTM":"3PM",**{k:v for k,v in STAT_ALIASES.items()}}) else k

def _csv_has(a): 
    try:
        import csv
        with open(a,'r') as fh:
            for row in csv.DictReader(fh):
                if any(str(v or "").strip() for v in row.values()): return True
    except Exception: pass
    return False

def find_file_nonempty(candidates: List[str]) -> Optional[str]:
    picks, empties = [], []
    for pattern in candidates:
        for m in sorted(glob.glob(pattern)):
            (picks if _csv_has(m) else empties).append(m)
    return picks[0] if picks else (empties[0] if empties else None)

def coerce_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    cols={c.lower():c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in cols: return cols[n]
        return None
    df=df.copy()
    pcol=pick("p_raw","p_hit","prob","y_prob","p_model")
    player=pick("player","name","player_name","athlete","full_name")
    stat=pick("stat","market","market_name","markettype","prop","prop_name","stat_type","category","metric","bet_type")
    lcol=pick("line","line_score","site_line","prob_line","line_real","threshold","target","points","runs","goals","value","total")
    df["player"]=df[player] if player else ""
    df["stat"]=df[stat] if stat else ""
    df["line_real"]=pd.to_numeric(df[lcol],errors="coerce") if lcol else np.nan
    if pc:=pcol:
        pv=pd.to_numeric(df[pc],errors="coerce")
    else:
        pv=pd.Series(np.nan,index=df.index)
    df["p_raw"]=pv
    if "y" in cols:
        yy=df[cols["y"]]
        df["y"]=yy.astype(int) if yy.dtype==bool else pd.to_numeric(yy,errors="coerce")
    elif "result" in cols:
        rr=df[cols["result"]].astype(str).str.lower()
        df["y"]=np.where(rr.isin(["win","won","w","hit","over"]),1,np.where(rr.isin(["loss","lost","l","miss","under"]),0,np.nan))
    else:
        df["y"]=np.nan
    df["player_key"]=df["player"].apply(canon_player)
    df["stat_key"]=df["stat"].apply(canon_stat)
    return df[["player","stat","player_key","stat_key","line_real","p_raw","y"]]

def synth_edges_from_realized(realized: pd.DataFrame, day: str) -> pd.DataFrame:
    # Build synthetic edges from realized labels when no real legs exist.
    rows=[]
    for _,r in realized.iterrows():
        rows.append({
            "day":day,
            "player":r.get("player",""),
            "stat":r.get("stat",""),
            "line_edge":r.get("line_real",np.nan),
            "p_raw": r.get("p_raw",np.nan),
            "payout": 2.0,
            "player_key": r.get("player_key",""),
            "stat_key": r.get("stat_key",""),
        })
    ed=pd.DataFrame(rows)
    if "line_edge" not in ed.columns: ed["line_edge"]=np.nan
    return ed

def apply_calibration(p: pd.Series, calib: Optional[Dict]) -> pd.Series:
    if calib is None: return p
    meth=calib.get("method")
    if meth=="pl":
        a=calib.get("a",1.0); b=calib.get("b",0.0)
        z=a*p+b; return 1.0/(1.0+np.exp(-z))
    if meth in ("isotonic",) and "pairs" in calib:
        pts=np.array(calib["pairs"],dtype=float)
        xs,ys=pts[:,0],pts[:,1]
        # clamp and interpolate
        idx=np.argsort(xs); xs=xs[idx]; ys=ys[idx]
        def interp(x):
            import numpy as np
            if np.isnan(x): return np.nan
            i=np.searchsorted(xs,x,side="left")
            if i<=0: return float(ys[0])
            if i>=len(xs): return float(ys[-1])
            x0,x1=xs[i-1],xs[i]; y0,y1=ys[i-1],ys[i]
            t=(x-x0)/(x1-x0) if x1!=x0 else 0.0
            return float(y0 + t*(y1-y0))
        return p.apply(interp)
    return p

def load_edges(day:str):
    path=find_file_nonempty([f"edge_sheet_{day}.csv",f"artifacts/edge_sheet_{day}.csv",f"edges/edge_sheet_{day}.csv"])
    if not path: return None,{}
    df=pd.read_csv(path)
    meta={"path":path,"mode":"edges"}
    # best-effort canonicalization for rowwise edges
    def pick(names):
        for n in names:
            if n in df.columns: return n
        return None
    df = df.copy()
    pcol=pick(["p_raw","p_hit","prob","y_prob","p_model"])
    scol=pick(["stat","market","market_name","markettype","prop","prop_name","stat_type","category","metric","bet_type"])
    pcol = pcol
    pseries = pd.to_numeric(df[pcol],errors="coerce") if pcol else np.nan
    df["player"]=df.get(pick(["player","name","player_name","athlete","full_name"])) if pick(["player","name","player_name","athlete","full_name"]) else ""
    df["player_key"]=df["player"].apply(lambda x: ''.join(ch for ch in unicodedata.normalize('NFKD', x).lower() if ch.isalnum() or ch.isspace()))
    if scol: 
        df["stat"]=df[scol].astype(str)
    else:
        df["stat"]=""
    df["stat_key"]=df["stat"].apply(lambda x: ''.join(ch for ch in x if x.isalnum()).upper())
    lcol=pick(["line","line_score","site_line","prob_line","threshold","target","points","runs","goals","value","total"])
    df["line_edge"]=pd.to_numeric(df[lcol],errors="coerce") if lcol else np.nan
    df["p_raw"]=pseries
    df["payout"]=pd.to_numeric(df.get("payout"),errors="coerce").fillna(2.0)
    return df,meta

def discover_realized(day:str)->Optional[pd.DataFrame]:
    for p in (f"data/outcomes_{day}.csv",f"outcomes_{day}.csv",f"data/realized_{day}.csv",f"realized_{day}.csv",f"data/statlines_{day}.csv"):
        if os.path.exists(p):
            try:
                df=pd.read_csv(p)
                return coiled(df:=df)
            except Exception:
                try:
                    return coiled(pd.read_json(p))
                except Exception:
                    pass
    return None

def coiled(df): # alias for readability
    return coerce_outcomes(df)

def nearest_match(group:pd.DataFrame,line_edge:float)->Tuple[pd.Series,bool]:
    if group is None or len(group)==0: return pd.Series(dtype=object),False
    if "line_real" in group.columns and pd.notna(line_edge):
        g=group.copy()
        g["diff"]=abs(g["line_real"]-line_edge)
        mn=g["diff"].min()
        w=g[g["diff"]==mn]
        return (w.iloc[0], len(w)>1)
    if len(group)>0:
        return (group.iloc[0], len(group)>1)
    return pd.Series(dtype=object),False

def main():
    ap=argparse.ArgumentParser(description="Join edges → realized outcomes")
    ap.add_argument("--date",action="append"); ap.add_argument("--dates-file")
    ap.add_argument("--outdir",default="outcomes")
    args=ap.parse_args()

    dates=[]
    if args.date: dates.extend(args.date)
    if args.dates_file and os.path.exists(args.dates_file):
        import sys
        for ln in open(args.dates_file):
            ln=ln.strip()
            if ln and not ln.startswith("#"): dates.append(ln)
    if not dates:
        from datetime import date,timedelta
        dates=[(date.today()-timedelta(days=1)).isoformat()]

    os.makedirs(args.outdir,exist_ok=True)
    totals=[]
    for day in dates:
        edges,meta=load_edges(day)
        realized=discover_realized(day)
        if edges is None or (edges is not None and len(edges)==0):
            if realized is not None and len(realized)>0:
                edges=synth_edges_from_realized(realized,day); meta={"path":f"synth:{day}","mode":"synth"}
            else:
                pd.DataFrame().to_csv(f"{args.outdir}/day={day}/joined.csv",index=False)
                with open(f"{args.outdir}/day={day}/join_qc.json","w") as fh:
                    json.dump({"day":day,"n_total":0,"n_joined":0,"n_pending":0,"n_collisions":0,**meta},fh)
                print(f"ci_make_training_table day={day} n_total=0 n_joined=0 n_pending=0 n_collisions=0")
                continue
        os.makedirs(f"{args.outdir}/day={day}",exist_ok=True)
        df_edges=edges.copy()
        df_edges["player_key"]=df_edges["player"].apply(canon_player)
        df_edges["stat_key"]=df_edges["stat"].apply(canon_stat)
        idx={}
        if realized is not None and len(realized)>0:
            for (pk,sk),g in realized.groupby(["player","stat"]):
                pass
        rows=[]
        collisions=0
        if realized is None: 
            for _,r in df_edges.iterrows():
                rows.append({"day":day,"player":r.get("player",""),"stat":r.get("stat",""),
                            "line_edge":r.get("line_edge",np.nan),
                            "line_real":np.nan,"p_raw":r.get("p_raw",np.nan),"p_cal":np.nan,
                            "payout":r.get("payout",2.0),"y":np.nan,"collision":False,
                            "player_key":r.get("player_key",""),"stat_key":r.get("stat_key","")})
        else:
            rco=coiled(realized)
            for _,r in df_edges.iterrows():
                pk=r.get("player_key",""); sk=r.get("stat_key","")
                grp=rco[(rco["player_key"]==pk)&(rco["stat_key"]==sk)]
                m, col = nearest_match(grp, r.get("line_edge",np.nan))
                collisions += int(col)
                y = m.get("y", np.nan) if not m.empty else np.nan
                lr = m.get("line_real", np.nan) if not m.empty else np.nan
                pr = r.get("p_raw", np.nan)
                if (pd.isna(pr)) and not m.empty:
                    pr = m.get("p_raw", np.nan)
                rows.append({"day":day,"player":r.get("player",""),"stat":r.get("stat",""),
                            "line_edge":r.get("line_edge",np.nan),
                            "line_real":lr,"p_raw":pr,"p_cal":np.nan,
                            "payout":r.get("payout",2.0),"y":y,
                            "collision":bool(col),"player_key":pk,"stat_key":sk})
        df=pd.DataFrame(rows)
        # calibration
        cal=None
        for cp in ("calibration/latest.json","calibration/%s.json"%day):
            if os.path.exists(cp):
                try:
                    cal=json.load(open(cp)); break
                except Exception: pass
        df["p_cal"]=apply_br=apply_calibration(df.get("p_raw",pd.Series([np.nan]*len(df))),cal) if cal else df.get("p_raw",pd.Series([np.nan]*len(br:=[])))
        df["profit_units"]=np.where(df["y"].isin([0,1]), df["y"]*df["payout"]-1.0, np.nan)
        df.to_csv(f"{args.outdir}/day={day}/joined.csv",index=False)
        qc={"day":day,"n_total":int(len(df)),"n_joined":int(df["y"].isin([0,1]).sum()),
            "n_pending":int(df["y"].isna().sum()),"n_collisions":int(collisions),**meta}
        with open(f"{args.outdir}/day={day}/join_qc.json","w") as fh: json.dump(qc,fh)
        print(f"ci_make_training_table day={day} n_total={qc['n_total']} n_joined={qc['n_joined']} n_pending={qc['n_pending']} n_collisions={qc['n_collisions']}")
    pd.DataFrame(totals).to_csv(f"{args.outdir}/join_counts.csv",index=False)
