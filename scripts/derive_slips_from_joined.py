#!/usr/bin/env python3
import argparse,csv,json,os,sys,datetime
p=argparse.ArgumentParser()
p.add_argument("--joined",default=None); p.add_argument("--out",default="slips_manual.json")
p.add_argument("--day",default=None)
p.add_argument("--p_cols",default="p_cal,p_win,p_raw"); p.add_argument("--odds_col",default="odds"); p.add_argument("--odds_default",type=float,default=2.18)
p.add_argument("--team_cols",default="team_id,team,team_abbr,player_team,home,home_team,home_abbr")
p.add_argument("--game_cols",default="game_id,matchup,event_id,game_key,schedule_key,game_code")
a=p.parse_args()
d=a.day or os.environ.get("DAY") or str(datetime.date.today())
j=a.joined or f"outcomes/day={d}/joined.csv"
used=j
try:
    if not (os.path.exists(j) and os.path.getsize(j)>0):
        cands=[f"outcomes_data_download/day={d}/joined.csv",f"outcomes_data_pre_download/day={d}/joined.csv",f"outcomes_data_post_download/day={d}/joined.csv"]
        j=None
        for c in cands:
            if os.path.exists(c) and os.path.getsize(c)>0: j=c; used=c; break
    if not j:
        open(a.out,"w").write("[]\n"); print("joined_used=NO_JOINED rows=0"); sys.exit(0)
    rows=list(csv.DictReader(open(j,newline="")))
    pk=[s.strip() for s in (a.p_cols or "").split(",") if s.strip()]
    tk=[s.strip() for s in (a.team_cols or "").split(",") if s.strip()]
    gk=[s.strip() for s in (a.game_cols or "").split(",") if s.strip()]
    def pick(m,keys):
        for k in keys:
            v=m.get(k)
            if v not in ("",None): return v
        return None
    out=[]
    for i,r in enumerate(rows):
        pv=pick(r,pk) or "0.5"
        try: pval=float(pv)
        except: pval=0.5
        pval=max(1e-6,min(1-1e-6,pval))
        try: od=float(r.get(a.odds_col))
        except: od=a.odds_default
        if od<=1.0: od=2.0
        ev=pval*od-1.0
        tid=pick(r,tk)
        gid=pick(r,gk) or f"{r.get('away') or 'A'}@{r.get('home') or 'H'}-{d}"
        sid=r.get("slip_id") or r.get("edge_id") or r.get("id") or f"s{i+1}"
        out.append({"slip_id":str(sid),"p_win":pval,"odds":od,"ev_penalized":ev,"team_id":(None if tid in (None,"") else str(tid)),"game_id":str(gid)})
    open(a.out,"w").write(json.dumps(out,indent=2)+"\n")
    print(f"joined_used={used} rows={len(out)}"); sys.exit(0)
except Exception as e:
    try: open(a.out,"w").write("[]\n")
    except: pass
    print("joined_used=DERIVE_ERROR rows=0"); sys.exit(0)
