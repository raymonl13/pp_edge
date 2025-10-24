#!/usr/bin/env python3
import argparse,json,math,os,sys,datetime
def as_list(x):
    if x is None:
        return []
    if isinstance(x,list):
        return [str(i) for i in x if i is not None]
    return [str(x)]
def to_float(x):
    if x is None:
        return None
    try:
        if isinstance(x,bool):
            return float(int(x))
        return float(x)
    except Exception:
        return None
def floor_step(x,step):
    if step is None or step<=0:
        return x
    return math.floor(x/step)*step
def load_slips(path):
    with open(path,"r") as f:
        data=json.load(f)
    if isinstance(data,dict) and isinstance(data.get("slips"),list):
        return data["slips"]
    if isinstance(data,list):
        return data
    raise SystemExit("schema error: invalid top-level shape")
def schema_check(slips,fields):
    if not slips:
        raise SystemExit("schema error: empty slips")
    errs=[]
    reqs=[fields["id"],fields["ev"],fields["pwin"],fields["odds"],fields["team"],fields["game"]]
    for i,s in enumerate(slips):
        for k in reqs:
            if k not in s:
                errs.append({"row":i,"key":k,"issue":"missing"})
    for i,s in enumerate(slips):
        ev=to_float(s.get(fields["ev"]))
        pw=to_float(s.get(fields["pwin"]))
        od=to_float(s.get(fields["odds"]))
        if ev is None:
            errs.append({"row":i,"key":fields["ev"],"issue":"non_numeric"})
        if pw is None:
            errs.append({"row":i,"key":fields["pwin"],"issue":"non_numeric"})
        if od is None:
            errs.append({"row":i,"key":fields["odds"],"issue":"non_numeric"})
    if errs:
        raise SystemExit("schema error: "+json.dumps(errs,ensure_ascii=False))
def cool_off(psifile,psi_threshold,need):
    if not psifile or not os.path.exists(psifile):
        return False
    try:
        obj=json.load(open(psifile,"r"))
    except Exception:
        return False
    if isinstance(obj,dict) and "consecutive_fail_count" in obj:
        try:
            return int(obj["consecutive_fail_count"])>=int(need)
        except Exception:
            return False
    if isinstance(obj,dict) and "history" in obj and isinstance(obj["history"],list):
        c=0
        for rec in reversed(obj["history"]):
            st=rec.get("status")
            if st and str(st).lower()=="fail":
                c+=1
            elif "psi" in rec:
                try:
                    c=c+1 if float(rec["psi"])>=psi_threshold else 0
                except Exception:
                    c=0
            else:
                c=0
            if c>=need:
                return True
        return False
    if isinstance(obj,dict) and "status" in obj:
        return str(obj["status"]).lower()=="fail" and need<=1
    if isinstance(obj,dict) and "psi" in obj:
        try:
            return float(obj["psi"])>=psi_threshold and need<=1
        except Exception:
            return False
    return False
def kelly_amount(bankroll,p,b,kfrac):
    if b<=0 or p is None:
        return 0.0
    q=1.0-p
    k=(b*p-q)/b
    if k<=0:
        return 0.0
    return bankroll*kfrac*k
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--inputs",default="slips_manual.json")
    ap.add_argument("--out",default="bankroll_decision.json")
    ap.add_argument("--day",default=None)
    ap.add_argument("--currency",default="USD")
    ap.add_argument("--bankroll",type=float,required=True)
    ap.add_argument("--kelly_fraction",type=float,default=0.25)
    ap.add_argument("--daily_max_risk_pct",type=float,default=0.03)
    ap.add_argument("--per_slip_max_pct",type=float,default=0.01)
    ap.add_argument("--per_team_cap_pct",type=float,default=0.02)
    ap.add_argument("--per_game_cap_pct",type=float,default=0.02)
    ap.add_argument("--min_stake",type=float,default=1.0)
    ap.add_argument("--round_step",type=float,default=0.5)
    ap.add_argument("--cool_off_psifile",default=None)
    ap.add_argument("--psi_threshold",type=float,default=0.20)
    ap.add_argument("--cool_off_consecutive",type=int,default=2)
    ap.add_argument("--field_slip_id",default="slip_id")
    ap.add_argument("--field_ev",default="ev_penalized")
    ap.add_argument("--field_pwin",default="p_win")
    ap.add_argument("--field_odds",default="odds")
    ap.add_argument("--field_team",default="team_id")
    ap.add_argument("--field_game",default="game_id")
    args=ap.parse_args()
    slips=load_slips(args.inputs)
    fields={"id":args.field_slip_id,"ev":args.field_ev,"pwin":args.field_pwin,"odds":args.field_odds,"team":args.field_team,"game":args.field_game}
    schema_check(slips,fields)
    day=args.day or datetime.date.today().isoformat()
    bankroll=float(args.bankroll)
    daily_cap=bankroll*float(args.daily_max_risk_pct)
    slip_cap=bankroll*float(args.per_slip_max_pct)
    team_cap=bankroll*float(args.per_team_cap_pct)
    game_cap=bankroll*float(args.per_game_cap_pct)
    is_cool=cool_off(args.cool_off_psifile,float(args.psi_threshold),int(args.cool_off_consecutive))
    prep=[]
    for s in slips:
        sid=str(s.get(fields["id"]))
        evp=to_float(s.get(fields["ev"]))
        pw=to_float(s.get(fields["pwin"]))
        od=to_float(s.get(fields["odds"]))
        teams=as_list(s.get(fields["team"]))
        games=as_list(s.get(fields["game"]))
        prep.append({"sid":sid,"evp":evp,"pw":pw,"od":od,"teams":teams,"games":games})
    prep.sort(key=lambda r:((r["evp"] if r["evp"] is not None else -1e18),(r["pw"] if r["pw"] is not None else -1e18),r["sid"]),reverse=True)
    team_used={}
    game_used={}
    total_used=0.0
    out=[]
    for r in prep:
        sid=r["sid"]
        evp=r["evp"]
        pw=r["pw"]
        od=r["od"]
        teams=r["teams"]
        games=r["games"]
        caps=[]
        skip=None
        stake=0.0
        p_eff=None
        b=None
        if is_cool:
            skip="cool_off"
        elif evp is None or pw is None or od is None:
            skip="invalid_input"
        elif od<=1.0:
            skip="invalid_odds"
        elif evp<=0.0:
            skip="non_positive_ev"
        else:
            b=od-1.0
            if pw is not None and 0.0<pw<1.0:
                p_eff=pw
            else:
                try:
                    p_eff=(evp+1.0)/od
                except Exception:
                    p_eff=None
            raw_amt=kelly_amount(bankroll,p_eff,b,args.kelly_fraction)
            if raw_amt<=0.0:
                skip="kelly_non_positive"
            else:
                x=raw_amt
                x0=min(x,slip_cap)
                if x0<x:
                    caps.append("per_slip_max_pct")
                remain_daily=max(daily_cap-total_used,0.0)
                x1=min(x0,remain_daily)
                if x1<x0:
                    caps.append("daily_max_risk_pct")
                x2=x1
                if teams:
                    for t in teams:
                        remain=max(team_cap-team_used.get(t,0.0),0.0)
                        x2=min(x2,remain)
                if x2<x1:
                    caps.append("per_team_cap_pct")
                x3=x2
                if games:
                    for g in games:
                        remain=max(game_cap-game_used.get(g,0.0),0.0)
                        x3=min(x3,remain)
                if x3<x2:
                    caps.append("per_game_cap_pct")
                xr=floor_step(x3,args.round_step)
                if xr<args.min_stake or xr<=0.0:
                    if remain_daily<=0.0:
                        skip="daily_cap"
                    else:
                        team_zero=any(max(team_cap-team_used.get(t,0.0),0.0)<=0.0 for t in teams) if teams else False
                        game_zero=any(max(game_cap-game_used.get(g,0.0),0.0)<=0.0 for g in games) if games else False
                        if team_zero:
                            skip="per_team_cap_pct"
                        elif game_zero:
                            skip="per_game_cap_pct"
                        elif slip_cap<=0.0:
                            skip="per_slip_max_pct"
                        else:
                            skip="below_min_stake"
                else:
                    stake=round(xr,2)
                    total_used+=stake
                    for t in teams:
                        team_used[t]=team_used.get(t,0.0)+stake
                    for g in games:
                        game_used[g]=game_used.get(g,0.0)+stake
        out.append({"slip_id":sid,"stake":float(stake),"currency":args.currency,"rationale":{"kelly_fraction":float(args.kelly_fraction),"p_effective":None if p_eff is None else float(p_eff),"odds":None if od is None else float(od),"b":None if b is None else float(b),"ev_penalized":None if evp is None else float(evp),"caps_applied":caps,"team_id":teams if teams else None,"game_id":games if games else None,"skip_reason":skip}})
    with open(args.out,"w") as f:
        json.dump(out,f,indent=2)
    print("bankroll_decider D="+str(day)+" n="+str(len(out))+" total_risk="+str(round(total_used,2))+" daily_cap="+str(round(daily_cap,2))+" cool_off="+str(is_cool).lower())
if __name__=="__main__":
    main()
