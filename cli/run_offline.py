import os, csv, json, sys, argparse
from pathlib import Path
os.environ.setdefault("PP_EDGE_TEST_MODE", "1")
CFG={"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":2},"payouts":{"Power2":3.0,"Power3":5.0}}
def _row_to_leg(r):
    d={"player":r["player"],"game_id":r["game_id"],"p_hit":float(r["p_hit"]),"edge_pp":float(r["edge_pp"])}
    if r.get("tag"): d["tag"]=r["tag"]
    for opt in ("correlation_group","team_id","market"):
        if opt in r and r[opt]!="": d[opt]=r[opt]
    return d
def load_legs(p):
    with open(p,newline="") as f: return [_row_to_leg(r) for r in csv.DictReader(f)]
def maybe_apply_model(legs):
    if not Path("model_v2.pkl").exists(): return legs
    try: from code_utils_model_v1 import predict_batch
    except Exception: return legs
    try:
        rows=[{"player":g.get("player"),"game_id":g.get("game_id"),"p_hit":g.get("p_hit"),"edge_pp":g.get("edge_pp"),"tag":g.get("tag")} for g in legs]
        new_p=list(predict_batch(rows))
        if len(new_p)==len(legs):
            for i,p in enumerate(new_p):
                try: legs[i]["p_hit"]=float(p)
                except Exception: pass
    except Exception: return legs
    return legs
def build_parser():
    p=argparse.ArgumentParser()
    p.add_argument("fixtures",nargs="?",default="fixtures/slate_small.csv")
    p.add_argument("out_path",nargs="?",default="out/slips.json")
    p.add_argument("--unit",type=float,default=1.0)
    p.add_argument("--bankroll",type=float,default=0.0)
    p.add_argument("--slip-cap",type=float,default=2.0)
    p.add_argument("--slate-cap-frac",type=float,default=0.10)
    p.add_argument("--kelly",type=float,default=0.5)
    p.add_argument("--min-stake",type=float,default=0.0)
    p.add_argument("--allow-neg-ev",action="store_true")
    return p
def main(fixtures="fixtures/slate_small.csv",out_path="out/slips.json",unit=1.0,bankroll=0.0,slip_cap=2.0,slate_cap_frac=0.10,kelly=0.5,min_stake=0.0,allow_neg_ev=False):
    try: from code_utils_slipbuilder_v2 import SlipBuilder
    except Exception: print("SlipBuilder seam not available",file=sys.stderr); return 2
    from code_utils_slipqa_v1 import qa_slip,HARD_FLAGS
    from code_utils_bankroll_alloc_v1 import allocate_slips
    legs=maybe_apply_model(load_legs(fixtures))
    sb=SlipBuilder(CFG)
    slips=sb.build_slips(legs)
    for s in slips: s["_qa_flags"]=qa_slip(s,CFG)
    approved=[s for s in slips if not any(s["_qa_flags"].get(k,False) for k in HARD_FLAGS)]
    if bankroll and bankroll>0:
        staked=allocate_slips(approved,bankroll=bankroll,slip_cap=slip_cap,slate_cap_frac=slate_cap_frac,kelly=kelly,min_stake=min_stake,allow_neg_ev=allow_neg_ev)
    else:
        staked=[{**s,"stake_total":unit} for s in approved]
    os.makedirs(os.path.dirname(out_path),exist_ok=True)
    with open(out_path,"w") as f: json.dump({"slips":staked},f,indent=2)
    review_path=os.path.join(os.path.dirname(out_path),"slips_review.json")
    with open(review_path,"w") as f: json.dump({"slips":slips},f,indent=2)
    print(f"wrote {out_path} with {len(staked)} approved slips; review at {review_path}")
    return 0
if __name__=="__main__":
    a=build_parser().parse_args()
    sys.exit(main(a.fixtures,a.out_path,a.unit,bankroll=a.bankroll,slip_cap=a.slip_cap,slate_cap_frac=a.slate_cap_frac,kelly=a.kelly,min_stake=a.min_stake,allow_neg_ev=a.allow_neg_ev))
