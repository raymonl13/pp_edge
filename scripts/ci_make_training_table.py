#!/usr/bin/env python3
import argparse, csv, json, os, sys, glob, unicodedata, datetime
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
def pick_first(df, names):
    for n in names:
        if n in df.columns: return n
    return None
def find_file(candidates):
    for pattern in candidates:
        m=sorted(glob.glob(pattern))
        if m: return m[0]
    return None
def load_edges(day):
    path=find_file([f"edge_sheet_{day}.csv",f"artifacts/edge_sheet_{day}.csv",f"edges/edge_sheet_{day}.csv"])
    if not path: return None
    df=pd.read_csv(path)
    df["day"]=day
    df["player_key"]=df.get("player").fillna("").map(canon_player) if "player" in df.columns else ""
    stat_col=pick_first(df,["stat","market","stat_type","category"])
    df["stat_key"]=df[stat_col].map(canon_stat) if stat_col else ""
    line_col=pick_first(df,["line","line_score","site_line","prob_line"])
    df["line_edge"]=pd.to_numeric(df[line_col],errors="coerce") if line_col else np.nan
    p_col=pick_first(df,["p_hit","win_prob","y_prob","prob","p_model"])
    df["p_raw"]=pd.to_numeric(df[p_col],errors="coerce") if p_col else np.nan
    payout_col=pick_first(df,["payout","payout_mult","payout_multiplier"])
    df["payout"]=pd.to_numeric(df[payout_col],errors="coerce") if payout_col else 2.0
    df["tier"]=df.get("tier") if "tier" in df.columns else ""
    df["game_id"]=df.get("game_id") if "game_id" in df.columns else ""
    return df
def coerce_outcomes(df):
    cols={c.lower():c for c in df.columns}
    def get(*names):
        for n in names:
            if n in cols: return cols[n]
        return None
    player=get("player","name","player_name")
    stat=get("stat","market","stat_type","category")
    line=get("line","line_score","site_line","prob_line")
    ycol=get("y","won","hit","is_win","label")
    rescol=get("result","status","outcome")
    df=df.copy()
    if player: df["player"]=df[player]
    else: df["player"]=""
    if stat: df["stat"]=df[stat]
    else: df["stat"]=""
    if line: df["line_real"]=pd.to_numeric(df[line],errors="coerce")
    else: df["line_real"]=np.nan
    if ycol:
        y=df[ycol]
        if y.dtype==bool: df["y"]=y.astype(int)
        else: df["y"]=pd.to_numeric(y,errors="coerce")
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
        xs,idx=np.unique(xs,return_index=True)
        ys=ys[idx]
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
def load_calibration(day):
    for pth in [f"calibration_{day}.json",f"calibration/{day}.json","calibration_global.json","calibration/latest.json"]:
        if os.path.exists(pth):
            try: return json.load(open(pth))
            except Exception: continue
    return None
def nearest_match(group,line_edge):
    if group.empty: return pd.Series(dtype=object),False
    if "line_real" in group.columns and pd.notna(line_edge):
        g=group.copy(); g["line_diff"]=(g["line_real"]-line_edge).abs()
        mn=g["line_diff"].min()
        winners=g[g["line_diff"]==mn]
        collision=len(winners)>1
        return winners.iloc[0],collision
    if len(group)>1: return group.iloc[0],True
    return group.iloc[0],False
def join_one_day(day,outdir):
    os.makedirs(f"{outdir}/day={day}",exist_ok=True)
    edges=load_edges(day)
    if edges is None or edges.empty:
        pd.DataFrame().to_csv(f"{outdir}/day={day}/joined.csv",index=False)
        json.dump({"day":day,"n_total":0,"n_joined":0,"n_pending":0,"n_collisions":0},open(f"{outdir}/day={day}/join_qc.json","w"))
        return {"n_total":0,"n_joined":0,"n_pending":0,"n_collisions":0}
    realized=discover_realized(day)
    calib=load_calibration(day)
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
        rows.append({"day":day,"player":r.get("player",""),"stat":r.get("stat",r.get("market","")),"line_edge":r.get("line_edge",np.nan),"line_real":line_real,"p_raw":r.get("p_raw",np.nan),"p_cal":np.nan,"payout":r.get("payout",np.nan),"y":y,"status":status,"collision":bool(collision),"player_key":pk,"stat_key":sk})
    df=pd.DataFrame(rows)
    df["p_cal"]=apply_calibration(df["p_raw"],calib)
    df["profit_units"]=np.where(df["y"].isin([0,1]),df["y"]*df["payout"]-1.0,np.nan)
    df.to_csv(f"{outdir}/day={day}/joined.csv",index=False)
    qc={"day":day,"n_total":int(len(df)),"n_joined":int(df["y"].isin([0,1]).sum()),"n_pending":int(df["y"].isna().sum()),"n_collisions":int(df["collision"].sum())}
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
