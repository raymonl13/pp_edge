import yaml
p=".github/workflows/nightly_edge_sheet.yml"
doc=yaml.safe_load(open(p))
jobs=doc.get("jobs") or {}; jid=next(iter(jobs))
steps=list(jobs[jid].get("steps") or [])
drop={"Derive slips for bankroll","Bankroll decider","Upload bankroll artifacts","Bankroll derive→decide→upload"}
steps=[s for s in steps if not (isinstance(s,dict) and s.get("name") in drop)]
idx=None
for i,s in enumerate(steps):
    nm=str(s.get("name") or ""); rn=str(s.get("run") or "")
    if "Assert joined exists" in nm or "ci_ensure_joined_day.py" in rn or "Inspect rescued day (pre)" in nm:
        idx=i+1; break
if idx is None: idx=len(steps)
derive_run="\n".join([
"set -e",
'PY=${PY:-python3}',
'DAY="${DAY:-${{ env.DAY }}}"',
'JP=""',
'for C in "outcomes/day=$DAY/joined.csv" "outcomes_data_download/day=$DAY/joined.csv" "outcomes_data_pre_download/day=$DAY/joined.csv" "outcomes_data_post_download/day=$DAY/joined.csv"; do [ -s "$C" ] && JP="$C" && break; done',
'if [ -n "$JP" ]; then $PY scripts/derive_slips_from_joined.py --day "$DAY" --joined "$JP" --out slips_manual.json --odds_default 2.18 || true; else echo "[]" > slips_manual.json; fi'
])
decide_run="\n".join([
"set -e",
'PY=${PY:-python3}',
'DAY="${DAY:-${{ env.DAY }}}"',
'$PY scripts/bankroll_decider.py --inputs slips_manual.json --out bankroll_decision.json --day "$DAY" --currency USD --bankroll 10000 --kelly_fraction 0.25 --daily_max_risk_pct 0.03 --per_slip_max_pct 0.01 --per_team_cap_pct 0.02 --per_game_cap_pct 0.02 --min_stake 1.0 --round_step 0.5 || true',
'python - <<\'PY\'',
'import json,os',
'day=os.environ.get("DAY","")',
'try: arr=json.load(open("bankroll_decision.json"))',
'except: arr=[]',
'tot=sum(float(x.get("stake",0)) for x in arr) if isinstance(arr,list) else 0.0',
'dc=int(10000*0.03)',
'open("bankroll_summary.txt","w").write(f"bankroll_decider D={day} n={(len(arr) if isinstance(arr,list) else 0)} total_risk={round(tot,2)} daily_cap={dc} cool_off=false\\n")',
'PY'
])
bundle=[{"name":"Derive slips for bankroll","run":derive_run,"shell":"bash"},
        {"name":"Bankroll decider","run":decide_run,"shell":"bash"},
        {"name":"Upload bankroll artifacts","uses":"actions/upload-artifact@v4","with":{"name":"bankroll_${{ env.DAY }}","path":"bankroll_decision.json\nbankroll_summary.txt"}}]
for j,b in enumerate(bundle): steps.insert(idx+j,b)
jobs[jid]["steps"]=steps; doc["jobs"][jid]=jobs[jid]
yaml.safe_dump(doc,open(p,"w"),sort_keys=False)
print("patched_after_index",idx)
