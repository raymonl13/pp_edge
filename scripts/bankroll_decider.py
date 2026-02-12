#!/usr/bin/env python3
import argparse,json,os,sys,datetime,math
def as_list(x): return [] if x is None else ([str(i) for i in x] if isinstance(x,list) else [str(x)])
def f(x):
    try: return float(x)
    except Exception:
        if isinstance(x,bool): return float(int(x))
        return None
def floor_step(x,s):
    try: s=float(s); return x if s<=0 else (int(x//s))*s
    except: return x
p=argparse.ArgumentParser()
p.add_argument("--inputs",default="slips_manual.json"); p.add_argument("--out",default="bankroll_decision.json")
p.add_argument("--day",default=None); p.add_argument("--currency",default="USD")
p.add_argument("--bankroll",type=float,required=True); p.add_argument("--kelly_fraction",type=float,default=0.25)
p.add_argument("--daily_max_risk_pct",type=float,default=0.03); p.add_argument("--per_slip_max_pct",type=float,default=0.01)
p.add_argument("--per_team_cap_pct",type=float,default=0.02); p.add_argument("--per_game_cap_pct",type=float,default=0.02)
p.add_argument("--min_stake",type=float,default=1.0); p.add_argument("--round_step",type=float,default=0.5)
p.add_argument("--field_slip_id",default="slip_id"); p.add_argument("--field_ev",default="ev_penalized"); p.add_argument("--field_pwin",default="p_win"); p.add_argument("--field_odds",default="odds"); p.add_argument("--field_team",default="team_id"); p.add_argument("--field_game",default="game_id")
a=p.parse_args()
day=a.day or os.environ.get("DAY") or str(datetime.date.today())
try: slips=json.load(open(a.inputs))
except: slips=[]
if not isinstance(slips,list): slips=[]
if not slips:
    dc=int(a.daily_max_risk_pct*a.bankroll); open(a.out,"w").write("[]\n"); print(f"bankroll_decider D={day} n=0 total_risk=0 daily_cap={dc} cool_off=false"); sys.exit(0)
tot=0.0; out=[]; team_used={}; game_used={}
for r in slips:
    sid=str(r.get(a.field_slip_id)); ev=f(r.get(a.field_ev)); pw=f(r.get(a.field_pwin)); od=f(r.get(a.field_odds))
    teams=as_list(r.get(a.field_team)); games=as_list(r.get(a.field_game))
    sk=None
    if ev is None or pw is None or od is None: sk="invalid_input"
    elif od<=1.0: sk="invalid_odds"
    elif ev<=0.0: sk="non_positive_ev"
    else:
        b=od-1.0; k=(pw*b-(1.0-pw))/b; x=max(0.0,a.kelly_fraction*k*a.bankroll)
        x=min(x,a.per_slip_max_pct*a.bankroll); x=min(x,max(a.daily_max_risk_pct*a.bankroll - tot,0.0))
        for t in teams: x=min(x,max(a.per_team_cap_pct*a.bankroll - team_used.get(t,0.0),0.0))
        for g in games: x=min(x,max(a.per_game_cap_pct*a.bankroll - game_used.get(g,0.0),0.0))
        x=floor_step(x,a.round_step)
        if x<a.min_stake or x<=0.0: sk="below_min_stake"
        else:
            tot+=x
            for t in teams: team_used[t]=team_used.get(t,0.0)+x
            for g in games: game_used[g]=game_used.get(g,0.0)+x
    out.append({"slip_id":sid,"stake":0.0 if sk else round(x,2),"currency":a.currency,"rationale":{"kelly_fraction":a.kelly_fraction,"p_effective":pw,"odds":od,"b":(od-1.0) if od else None,"ev_penalized":ev,"caps_applied":[] if sk is None else [sk],"team_id":teams or None,"game_id":games or None,"skip_reason":("None" if sk is None else sk)}})
open(a.out,"w").write(json.dumps(out,indent=2)+"\n")
dc=int(a.daily_max_risk_pct*a.bankroll); print(f"bankroll_decider D={day} n={len(out)} total_risk={round(tot,2)} daily_cap={dc} cool_off=false")
