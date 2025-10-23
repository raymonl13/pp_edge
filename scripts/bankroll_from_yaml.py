import os,sys,subprocess,glob,re,shutil,datetime,json,yaml
def find_joined(day):
    p=f"outcomes/day={day}/joined.csv"
    if os.path.exists(p): return day,p
    c=glob.glob("outcomes/day=*/joined.csv")+glob.glob("outcomes_data_download/day=*/joined.csv")+glob.glob("outcomes_data_pre_download/day=*/joined.csv")+glob.glob("outcomes_data_post_download/day=*/joined.csv")
    m=[]
    for q in c:
        g=re.search(r"day=([0-9\-]+)",q)
        if g: m.append((g.group(1),q))
    if not m: return None,None
    pref=[(d,q) for d,q in m if d==day]
    d,q=(pref[0] if pref else sorted(m,key=lambda x:x[0])[-1])
    dst=f"outcomes/day={d}"
    os.makedirs(dst,exist_ok=True)
    shutil.copy(q,os.path.join(dst,"joined.csv"))
    return d,os.path.join(dst,"joined.csv")
def main():
    day=os.environ.get("DAY") or sys.argv[1] if len(sys.argv)>1 else str(datetime.date.today())
    cfg=yaml.safe_load(open("config/bankroll_v1.yml"))
    b=cfg["bankroll"]; r=cfg["rails"]; c=cfg["cool_off"]; f=cfg["fields"]; d=cfg["derive"]
    day,joined=find_joined(day)
    if not joined: raise SystemExit("missing joined.csv")
    p_cols=",".join(d.get("p_cols",[]))
    team_cols=",".join(d.get("team_cols",[]))
    game_cols=",".join(d.get("game_cols",[]))
    der=[sys.executable,"scripts/derive_slips_from_joined.py","--day",day,"--joined",joined,"--out","slips_manual.json","--p_cols",p_cols,"--odds_col",d.get("odds_col","odds"),"--odds_default",str(2.18),"--team_cols",team_cols,"--game_cols",game_cols,"--fallback_game_mode","same"]
    subprocess.check_call(der)
    args=[sys.executable,"scripts/bankroll_decider.py","--inputs","slips_manual.json","--out","bankroll_decision.json","--day",day,"--currency",b["currency"],"--bankroll",str(b["amount"]),"--kelly_fraction",str(b["kelly_fraction"]),"--daily_max_risk_pct",str(r["daily_max_risk_pct"]),"--per_slip_max_pct",str(r["per_slip_max_pct"]),"--per_team_cap_pct",str(r["per_team_cap_pct"]),"--per_game_cap_pct",str(r["per_game_cap_pct"]),"--min_stake",str(b["min_stake"]),"--round_step",str(b["round_step"]),"--psi_threshold",str(c["psi_threshold"]),"--cool_off_consecutive",str(c["consecutive_fail_count"]),"--field_slip_id",f["slip_id"],"--field_ev",f["ev"],"--field_pwin",f["pwin"],"--field_odds",f["odds"],"--field_team",f["team_id"],"--field_game",f["game_id"]]
    pp=(c.get("probe_path") or "").strip()
    if pp: args+=["--cool_off_psifile",pp]
    subprocess.check_call(args)
    data=json.load(open("bankroll_decision.json"))
    tot=sum(float(x.get("stake") or 0.0) for x in data)
    daily_cap=b["amount"]*r["daily_max_risk_pct"]
    line=f"bankroll_decider D={day} n={len(data)} total_risk={round(tot,2)} daily_cap={round(daily_cap,2)} cool_off={str(bool(pp)).lower()}"
    open("bankroll_summary.txt","w").write(line+"\n")
    print(line)
if __name__=="__main__":
    main()
