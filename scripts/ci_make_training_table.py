#!/usr/bin/env python3
import argparse, csv, json, os, glob, unicodedata
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

STAT_ALIASES={"PTS":"PTS","POINTS":"PTS","REB":"REB","REBOUNDS":"REB","AST":"AST","ASSISTS":"AST",
              "3PM":"3PM","THREES":"3PM","3PTM":"3PM","3P_MADE":"3PM","3PMADE":"3PM",
              "HR":"HR","HRS":"HR","HOMERUNS":"HR","HOME_RUNS":"HR",
              "SO":"SO","K":"SO","STRIKEOUTS":"SO",
              "H":"H","HITS":"H",
              "R":"R","RUNS":"R","RBI":"RBI",
              "SB":"SB","STEALS":"SB",
              "SOG":"SOG","SHOTS_ON_GOAL":"SOG"}

def _strip_accents(s): return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
def canon_player(s):
    s=_strip_accents((s or "")).lower()
    s=''.join(ch for ch in s if ch.isalnum() or ch.isspace())
    return ' '.join(s.split())
def canon_stat(s):
    k=''.join(ch for ch in (s or "") if ch.isalnum()).upper()
    return STAT_ALIASES.get(k,k)

def _csv_has_rows(path):
    try:
        with open(path,'r') as fh:
            dr=csv.DictReader(fh)
            for row in dr:
                if any(str(v or "").strip() for v in row.values()):
                    return True
        return False
    except Exception:
        return False

def find_file_nonempty(candidates: List[str]) -> Optional[str]:
    picks,empties=[],[]
    for pattern in candidates:
        for m in sorted(glob.glob(pattern)):
            (picks if _csv_has_rows(m) else empties).append(m)
    return picks[0] if picks else (empties[0] if empties else None)

def _pick(cols, names):
    for n in names:
        if n in cols: return cols[n]
    return None

def coerce_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    cols={c.lower():c for c in df.columns}
    player=_pick(cols,["player","name","player_name","athlete","full_name"])
    stat=_pick(cols,["stat","market","market_name","markettype","prop","prop_name","stat_type","category","metric","bet_type"])
    lcol=_pick(cols,["line","line_score","site_line","prob_line","line_real","threshold","target","points","runs","goals","value","total"])
    pcol=_pick(cols,["p_raw","p_hit","prob","y_prob","p_model"])
    ycol=_pick(cols,["y","won","hit","is_win","label"])
    rcol=_pick(cols,["result","status","outcome"])
    out=df.copy()
    out["player"]=out[player] if player else ""
    out["stat"]=out[stat] if stat else ""
    out["line_real"]=pd.to_numeric(out[lcol],errors="coerce") if lcol else np.nan
    out["p_raw"]=pd.to_numeric(out[pcol],errors="coerce") if pcol else np.nan
    if ycol:
        yy=out[ycol]; out["y"]=yy.astype(int) if yy.dtype==bool else pd.to_numeric(yy,errors="coerce")
    elif rcol:
        rr=out[rcol].astype(str).str.lower()
        out["y"]=np.where(rr.isin(["win","won","w","hit","over"]),1,np.where(rr.isin(["loss","lost","l","miss","under"]),0,np.nan))
    else:
        out["y"]=np.nan
    out["player_key"]=out["player"].apply(canon_player)
    out["stat_key"]=out["stat"].apply(canon_stat)
    return out[["player","stat","player_key","stat_key","line_real","p_raw","y"]]

def load_edges(day:str) -> Tuple[Optional[pd.DataFrame],Dict]:
    path=find_file_nonempty([f"edge_sheet_{day}.csv",f"artifacts/edge_sheet_{day}.csv",f"edges/edge_sheet_{day}.csv"])
    if not path: return None,{}
    df=pd.read_csv(path)
    meta={"path":path,"mode":"edges"}
    cols=list(df.columns)
    def pick(names):
        for n in names:
            if n in cols: return n
        return None
    ed=df.copy()
    pl=pick(["player","name","player_name","athlete","full_name"])
    st=pick(["stat","market","market_name","markettype","prop","prop_name","stat_type","category","metric","bet_type"])
    ln=pick(["line","line_score","site_line","prob_line","threshold","target","points","runs","goals","value","total"])
    pr=pick(["p_raw","p_hit","prob","y_prob","p_model"])
    ed["player"]=ed[pl] if pl else ""
    ed["stat"]=ed[st] if st else ""
    ed["line_edge"]=pd.to_numeric(ed[ln],errors="coerce") if ln else np.nan
    ed["p_raw"]=pd.to_numeric(ed[pr],errors="coerce") if pr else np.nan
    ed["payout"]=pd.to_numeric(ed.get("payout"),errors="coerce").fillna(2.0)
    ed["player_key"]=ed["player"].apply(canon_player)
    ed["stat_key"]=ed["stat"].apply(canon_stat)
    return ed,meta

def discover_realized(day:str)->Optional[pd.DataFrame]:
    for p in (f"data/outcomes_{day}.csv",f"outcomes_{day}.csv",f"data/realized_{day}.csv",f"realized_{day}.csv",f"data/statlines_{day}.csv"):
        if os.path.exists(p):
            try:
                return coerce_outcomes(pd.read_csv(p))
            except Exception:
                try:
                    return coerce_outcomes(pd.read_json(p))
                except Exception:
                    pass
    return None

def synth_edges_from_realized(realized: pd.DataFrame, day: str) -> pd.DataFrame:
    rows=[]
    for _,r in realized.iterrows():
        rows.append({
            "day":day,
            "player":r.get("player",""),
            "stat":r.get("stat","PTS"),
            "line_edge":r.get("line_real",np.nan),
            "p_raw":r.get("p_raw",np.nan),
            "payout":2.0,
            "player_key":r.get("player_key",""),
            "stat_key":r.get("stat_key","")
        })
    return pd.DataFrame(rows)

def nearest_match(group:pd.DataFrame,line_edge:float)->Tuple[pd.Series,bool]:
    if group is None or len(group)==0: return pd.Series(dtype=object),False
    if "line_real" in group.columns and pd.notna(line_edge):
        g=group.copy(); g["diff"]=abs(g["line_real"]-line_edge)
        mn=g["diff"].min(); w=g[g["diff"]==mn]
        return (w.iloc[0], len(w)>1)
    return (group.iloc[0], len(group)>1)

def main():
    ap=argparse.ArgumentParser(description="Join edges → realized outcomes")
    ap.add_argument("--date",action="append"); ap.add_argument("--dates-file")
    ap.add_argument("--outdir",default="outcomes")
    args=ap.parse_args()
    dates=[]
    if args.date: dates.extend(args.date)
    if args.dates_file and os.path.exists(args.dates_file):
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
        if edges is None or len(edges)==0:
            if realized is not None and len(realized)>0:
                edges=synth_edges_from_realized(realized,day); meta={"path":f"synth:{day}","mode":"synth"}
            else:
                pd.DataFrame().to_csv(f"{args.outdir}/day={day}/joined.csv",index=False)
                with open(f"{args.outdir}/day={day}/join_qc.json","w") as fh:
                    json.dump({"day":day,"n_total":0,"n_joined":0,"n_pending":0,"n_collisions":0,**meta},fh)
                print(f"ci_make_training_table day={day} n_total=0 n_joined=0 n_pending=0 n_collisions=0")
                continue

        os.makedirs(f"{args.outdir}/day={day}",exist_ok=True)
        rows=[]; collisions=0
        if realized is None or len(realized)==0:
            for _,r in edges.iterrows():
                rows.append({"day":day,"player":r["player"],"stat":r["stat"],
                             "line_edge":r["line_edge"],"line_real":np.nan,"p_raw":r.get("p_raw",np.nan),
                             "p_cal":np.nan,"payout":r.get("payout",2.0),"y":np.nan,"collision":False,
                             "player_key":r["player_key"],"stat_key":r["stat_key"]})
        else:
            rco=realized.copy()
            for _,r in edges.iterrows():
                pk=r["player_key"]; sk=r["stat_key"]
                grp=rco[(rco["player_key"]==pk)&(rco["stat_key"]==sk)]
                m,col=nearest_match(grp, r.get("line_edge",np.nan))
                collisions+=int(col)
                y = m.get("y",np.nan) if not m.empty else np.nan
                lr= m.get("line_real",np.nan) if not m.empty else np.nan
                pr= r.get("p_raw",np.nan)
                if (pd.isna(pr)) and not m.empty: pr=m.get("p_raw",np.nan)
                rows.append({"day":day,"player":r["player"],"stat":r["stat"],
                             "line_edge":r["line_edge"],"line_real":lr,"p_raw":pr,"p_cal":np.nan,
                             "payout":r.get("payout",2.0),"y":y,"collision":bool(col),
                             "player_key":pk,"stat_key":sk})

        df=pd.DataFrame(rows)
        df["profit_units"]=np.where(df["y"].isin([0,1]), df["y"]*df["payout"]-1.0, np.nan)
        df.to_csv(f"{args.outdir}/day={day}/joined.csv",index=False)
        qc={"day":day,"n_total":int(len(df)),"n_joined":int(df["y"].isin([0,1]).sum()),"n_pending":int(df["y"].isna().sum()),"n_collisions":int(collisions),**meta}
        with open(f"{args.outdir}/day={day}/join_qc.json","w") as fh: json.dump(qc,fh)
        print(f"ci_make_training_table day={day} n_total={qc['n_total']} n_joined={qc['n_joined']} n_pending={qc['n_pending']} n_collisions={qc['n_collisions']}")
    pd.DataFrame(totals).to_csv(f"{args.outdir}/join_counts.csv",index=False)
