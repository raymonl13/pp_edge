import os, csv, json, sys
os.environ.setdefault("PP_EDGE_TEST_MODE","1")
CFG={"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":2},"payouts":{"Power2":3.0,"Power3":5.0}}
def _row_to_leg(r):
    d={"player":r["player"],"game_id":r["game_id"],"p_hit":float(r["p_hit"]), "edge_pp":float(r["edge_pp"])}
    if r.get("tag"): d["tag"]=r["tag"]
    return d
def load_legs(path):
    with open(path,newline="") as f:
        return [_row_to_leg(r) for r in csv.DictReader(f)]
def main(fixtures="fixtures/slate_small.csv", out_path="out/slips.json"):
    try:
        from code_utils_slipbuilder_v2 import SlipBuilder
    except Exception:
        print("SlipBuilder seam not available", file=sys.stderr); return 2
    legs=load_legs(fixtures)
    sb=SlipBuilder(CFG)
    slips=sb.build_slips(legs)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path,"w") as f:
        json.dump({"slips":slips}, f, indent=2)
    print(f"wrote {out_path} with {len(slips)} slips")
    return 0
if __name__=="__main__":
    sys.exit(main(*(sys.argv[1:])))
