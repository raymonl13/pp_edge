#!/usr/bin/env python3
import argparse,csv,json,os,datetime
ap=argparse.ArgumentParser()
ap.add_argument("--joined",default=None)
ap.add_argument("--out",default="slips_manual.json")
ap.add_argument("--day",default=None)
ap.add_argument("--p_cols",default="p_cal,p_win,p_raw")
ap.add_argument("--odds_col",default="odds")
ap.add_argument("--odds_default",type=float,default=2.0)
ap.add_argument("--team_cols",default="team_id,team,team_abbr,player_team,home,home_team,home_abbr")
ap.add_argument("--game_cols",default="game_id,matchup,event_id,game_key,schedule_key,game_code")
ap.add_argument("--fallback_game_mode",choices=["same","unique"],default="same")
args=ap.parse_args()
day=args.day or os.environ.get("DAY") or str(datetime.date.today())
jp=args.joined or f"outcomes/day={day}/joined.csv"
if not os.path.exists(jp): raise SystemExit("missing joined.csv")
rows=list(csv.DictReader(open(jp,newline="")))
def pick(row,names):
    for k in names:
        v=row.get(k)
        if v not in (None,""): return v
    return None
p_names=[s.strip() for s in args.p_cols.split(",") if s.strip()]
t_names=[s.strip() for s in args.team_cols.split(",") if s.strip()]
g_names=[s.strip() for s in args.game_cols.split(",") if s.strip()]
slips=[]
for i,row in enumerate(rows):
    pv=pick(row,p_names)
    try: p=float(pv)
    except: p=0.5
    if p<=0.0: p=1e-6
    if p>=1.0: p=1-1e-6
    try: od=float(row.get(args.odds_col))
    except: od=args.odds_default
    if od<=1.0: od=2.0
    evp=p*od-1.0
    tid=pick(row,t_names)
    gid=pick(row,g_names)
    if gid is None:
        if args.fallback_game_mode=="same":
            gid="A@H-"+day
        else:
            gid=f"U{i+1}@U{i+1}-{day}"
    sid=row.get("slip_id") or row.get("edge_id") or row.get("id") or f"s{i+1}"
    slips.append({"slip_id":str(sid),"ev_penalized":float(evp),"p_win":float(p),"odds":float(od),"team_id":None if tid in ("",None) else str(tid),"game_id":str(gid)})
json.dump(slips,open(args.out,"w"),indent=2)
print(len(slips))
