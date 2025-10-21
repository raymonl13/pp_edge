#!/usr/bin/env python3
import argparse, csv, json, os, sys, glob, unicodedata, datetime, re, ast
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
STAT_ALIASES={"PTS":"PTS","POINTS":"PTS","REB":"REB","REBOUNDS":"REB","AST":"AST","ASSISTS":"AST","3PM":"3PM","THREES":"3PM","3PTM":"3PM","3PMADE":"3PM","3P_MADE":"3PM","HR":"HR","HRS":"HR","HOMERUNS":"HR","HOME_RUNS":"HR","SO":"SO","K":"SO","STRIKEOUTS":"SO","H":"H","HITS":"H","R":"R","RUNS":"R","RBI":"RBI","SB":"SB","STEALS":"SB","BB":"BB","WALKS":"BB","SOG":"SOG","SHOTS_ON_GOAL":"SOG"}
def _strip_accents(s): return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
def canon_player(s):
    s=_strip_accents((s or "")).lower()
    s=''.join(ch for ch in s if ch.isalnum() or ch.isspace())
    return ' '.join(s.split())
def canon_stat(s):
    k=''.join(ch for ch in (s or "") if ch.isalnum()).upper()
    return STAT_ALIASES.get(k, k)
def norm(s): return re.sub(r'[^a-z0-9]+','',str(s).lower())
def pick_ci(df, names):
    nmap={norm(c):c for c in df.columns}
    for n in names:
        nn=norm(n)
        if nn in nmap: return nmap[nn]
    return None
def find_file(candidates):
    for pattern in candidates:
        m=sorted(glob.glob(pattern))
        if m: return m[0]
    return None
def explode_legs(df, day):
    out=[]
    for _,row in df.iterrows():
        legs=row.get("legs","")
        if isinstance(legs,str) and legs.strip():
            try:
                payload=ast.literal_eval(legs)
            except Exception:
                payload=[]
            if isinstance(payload,list):
                for lg in payload:
                    player=(lg.get("player","") if isinstance(lg,dict) else "")
                    stat=(lg.get("stat","") if isinstance(lg,dict) else "")
                    line=lg.get("line",None) if isinstance(lg,dict) else None
                    p_raw=lg.get("p_hit",lg.get("prob",np.nan)) if isinstance(lg,dict) else np.nan
                    payout=2.0
                    out.append({"day":day,"player":player,"stat":stat,"line_edge":line,"p_raw":p_raw,"payout":payout,"tier":lg.get("tier","") if isinstance(lg,dict) else ""})
    if not out:
        return None
    ed=pd.DataFrame(out)
    ed["player_key"]=ed["player"].fillna("").map(canon_player)
    ed["stat_key"]=ed["stat"].fillna("").map(canon_stat)
    ed["line_edge"]=pd.to_numeric(ed["line_edge"],errors="coerce")
    return ed
def heuristic_player_col(df):
    cand=[c for c in df.columns if df[c].dtype==object]
    cand_sorted=sorted(cand,key=lambda c: -df[c].astype(str).str.len().fillna(0).mean())
    return cand_sorted[0] if cand_sorted else None
def heuristic_stat_col(df):
    cand=[c for c in df.columns if df[c].dtype==object]
    for c in cand:
        u=df[c].astype(str).str.upper().str.replace(r'[^A-Z0-9]+','',regex=True)
        if u.isin(list(STAT_ALIASES.keys())).mean()>0.2: return c
    return cand[0] if cand else None
def heuristic_line_col(df):
    cand=[c for c in df.columns if np.issubdtype(df[c].dtype, np.number)]
    return cand[0] if cand else None
def load_edges(day):
    path=find_file([f"edge_sheet_{day}.csv",f"artifacts/edge_sheet_{day}.csv",f"edges/edge_sheet_{day}.csv"])
    if not path: return None, {}
    df=pd.read_csv(path)
    meta={"path":path}
    if "legs" in df.columns:
        ed=explode_legs(df, day)
        meta.update({"mode":"legs_exploded","player_src":"legs","stat_src":"legs","line_src":"legs"})
        if ed is not None and not ed.empty:
            return ed, meta
    pcol=pick_ci(df,["player","name","player_name","athlete","full_name","playername","athletename","playerName","athleteName","Player Name"])
    scol=pick_ci(df,["stat","market","market_name","markettype","prop","prop_name","stat_type","category","metric","bet_type","category_name"])
    lcol=pick_ci(df,["line","line_score","site_line","prob_line","threshold","target","points","runs","goals","value","total"])
    if not pcol: pcol=heuristic_player_col(df)
    if not scol: scol=heuristic_stat_col(df)
    if not lcol: lcol=heuristic_line_col(df)
    meta.update({"mode":"rowwise","player_src":pcol,"stat_src":scol,"line_src":lcol})
    df=df.copy()
    if pcol:
        df["player"]=df[pcol]
        df["player_key"]=df[pcol].fillna("").map(canon_player)
    else:
        df["player"]=""; df["player_key"]=""
    if scol:
        df["stat"]=df[scol]
        df["stat_key"]=df[scol].fillna("").map(canon_stat)
    else:
        df["stat"]=""; df["stat_key"]=""
    if lcol:
        df["line_edge"]=pd.to_numeric(df[lcol],errors="coerce")
    else:
        df["line_edge"]=np.nan
    p_col=pick_ci(df,["p_hit","win_prob","y_prob","prob","p_model"])
    df["p_raw"]=pd.to_numeric(df[p_col],errors="coerce") if p_col else np.nan
    payout_col=pick_ci(df,["payout","payout_mult","payout_multiplier"])
    df["payout"]=pd.to_numeric(df[payout_col],errors="coerce") if payout_col else 2.0
    df["day"]=day
    return df, meta
def coerce_outcomes(df):
    cols={c.lower():c for c in df.columns}
    def get(*names):
        for n in names:
            if n in cols: return cols[n]
        return None
    player=get("player","name","player_name","athlete","full_name")
    stat=get("stat","market","market_name","prop","prop_name","stat_type","category","metric","bet_type")
    line=get("line","line_score","site_line","prob_line","line_real","threshold","target","value","total")
    ycol=get("y","won","hit","is_win","label")
    rescol=get("result","status","outcome")
    df=df.copy()
    df["player"]=df[player] if player else ""
    df["stat"]=df[stat] if stat else ""
    df["line_real"]=pd.to_numeric(df[line],errors="coerce") if line else np.nan
    if ycol:
        y=df[ycol]
        df["y"]=y.astype(int) if y.dtype==bool else pd.to_numeric(y,errors="coerce")
    elif rescol:
        res=df[rescol].astype(str).str.lower()
        df["y"]=np.where(res.isin(["win","won","w","hit","over"]),1,np.where(res.isin(["loss","lost","l","miss","under"]),0,np.nan))
    else:
        df["y"]=np.nan
    df["player_key"]=df["player"].fillna("").map(canon_player)
    df["stat_key"]=df["stat"].fillna("").map(canon_stat)
    return df[["player","stat","player_key","stat_key","line_real","y"]]
def discover_realized(day):
    path=find_file([f"data/outcomes_{day}.csv",f"outcomes_{day}.csv",f"data/realized_{day}.csv",f"realized_{day}.csv",f"data/statlines_{day}.csv"])
    if not path: return None
    try: df=pd.read_csv(path)
    except Exception:
        try: df=pd.read_json(path)
        except Exception: return None
    return coerce_outcomes(df)
def apply_calibration(p, calib):
    if calib is None: return p
    method=calib.get("method")
    if method=="platt":
        a=float(calib.get("a",1.0)); b=float(calib.get("b",0.0))
        z=a*p+b
        return 1.0/(1.0+np.exp(-z))
    if method=="isotonic":
        pts=calib.get("pairs",[])
        if not pts: return p
        xs=np.array([float(t[0]) for t in pts],dtype=float)
        ys=np.array([float(t[1]) for t in pts],dtype=float)
        xs,idx=np.unique(xs,return_index=True); ys=ys[idx]
        def interp(x):
            i=np.searchsorted(xs,x,side="left")
            if i==0: return ys[0]
            if i>=len(xs): return ys[-1]
            x0,x1=xs[i-1],xs[i]; y0,y1=ys[i-1],ys[i]
            if x1==x0: return y0
            t=(x-x0)/(x1-x0)
            return float(y0+t*(y1-y0))
        return p.map(interp)
    return p
def nearest_match(group,line_edge):
    if group.empty: return pd.Series(dtype=object),False
    if "line_real" in group.columns and pd.notna(line_edge):
        g=group.copy()
        g["line_diff"]=(g["line_real"]-line_edge).abs()
        if g["line_diff"].notna().any():
            mn=g["line_diff"].min()
            winners=g[g["line_diff"]==mn]
            return winners.iloc[0],len(winners)>1
        return g.iloc[0],len(g)>1
    if len(group)>1: return group.iloc[0],True
    return group.iloc[0],False
def join_one_day(day,outdir):
    os.makedirs(f"{outdir}/day={day}",exist_ok=True)
    edges,meta=load_edges(day)
    if edges is None or edges.empty:
        pd.DataFrame().to_csv(f"{outdir}/day={day}/joined.csv",index=False)
        json.dump({"day":day,"n_total":0,"n_joined":0,"n_pending":0,"n_collisions":0,**meta},open(f"{outdir}/day={day}/join_qc.json","w"))
        return {"day":day,"n_total":0,"n_joined":0,"n_pending":0,"n_collisions":0,**meta}
    realized=discover_realized(day)
    calib=None
    idx={}
    if realized is not None and not realized.empty:
        for (pk,sk),g in realized.groupby(["player_key","stat_key"]):
            idx[(pk,sk)]=g
    rows=[]; collisions=0
    for _,r in edges.iterrows():
        pk,sk=r.get("player_key",""),r.get("stat_key","")
        group=idx.get((pk,sk),pd.DataFrame(columns=["player","stat","player_key","stat_key","line_real","y"]))
        match,collision=nearest_match(group,r.get("line_edge",np.nan))
        collisions+=int(bool(collision))
        y=match.get("y",np.nan) if not match.empty else np.nan
        status="won" if y==1 else ("lost" if y==0 else "pending")
        line_real=match.get("line_real",np.nan) if not match.empty else np.nan
        rows.append({"day":day,"player":r.get("player",""),"stat":r.get("stat",""),"line_edge":r.get("line_edge",np.nan),"line_real":line_real,"p_raw":r.get("p_raw",np.nan),"p_cal":np.nan,"payout":r.get("payout",np.nan),"y":y,"status":status,"collision":bool(collision),"player_key":pk,"stat_key":sk})
    df=pd.DataFrame(rows)
    df["p_cal"]=apply_calibration(df["p_raw"],calib)
    df["profit_units"]=np.where(df["y"].isin([0,1]),df["y"]*df["payout"]-1.0,np.nan)
    df.to_csv(f"{outdir}/day={day}/joined.csv",index=False)
    qc={"day":day,"n_total":int(len(df)),"n_joined":int(df["y"].isin([0,1]).sum()),"n_pending":int(df["y"].isna().sum()),"n_collisions":int(df["collision"].sum()),**meta}
    json.dump(qc,open(f"{outdir}/day={day}/join_qc.json","w"))
    return qc
def main():
    p=argparse.ArgumentParser(description="Join edges → realized outcomes")
    p.add_argument("--date",action="append"); p.add_argument("--dates-file"); p.add_argument("--outdir",default="outcomes")
    args=p.parse_args()
    dates=[]
    if args.date: dates.extend(args.date)
    if args.dates_file and os.path.exists(args.dates_file):
        for s in open(args.dates_file):
            s=s.strip()
            if s and not s.startswith("#"): dates.append(s)
    if not dates: dates=[(datetime.date.today()-datetime.timedelta(days=1)).isoformat()]
    totals=[]
    for d in dates:
        try: qc=join_one_day(d,args.outdir)
        except Exception as e: qc={"day":d,"n_total":0,"n_joined":0,"n_pending":0,"n_collisions":0,"error":str(e)}
        totals.append(qc)
        print(f"ci_make_training_table day={d} n_total={qc['n_total']} n_joined={qc['n_joined']} n_pending={qc['n_pending']} n_collisions={qc['n_collisions']}")
    pd.DataFrame(totals).to_csv(f"{args.outdir}/join_counts.csv",index=False)
if __name__=="__main__": main()
