import os, sys, json, argparse
from pathlib import Path
os.environ.setdefault("PP_EDGE_TEST_MODE", "1")
CFG = {"diversification":{"demon_quota_per_slip":1,"demon_quota_per_day":2},"payouts":{"Power2":3.0,"Power3":5.0}}
def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True)
    p.add_argument("--sport", required=True, choices=["MLB", "NFL"])
    p.add_argument("--source", default="http", choices=["http", "fake"])
    p.add_argument("--out", default="out/slips.json")
    p.add_argument("--bankroll", type=float, default=100.0)
    p.add_argument("--slip-cap", type=float, default=2.0)
    p.add_argument("--slate-cap-frac", type=float, default=0.10)
    p.add_argument("--kelly", type=float, default=0.5)
    p.add_argument("--min-stake", type=float, default=0.25)
    p.add_argument("--allow-neg-ev", action="store_true")
    return p
def main(date, sport, source, out_path, bankroll, slip_cap, slate_cap_frac, kelly, min_stake, allow_neg_ev):
    if os.getenv("PP_EDGE_TEST_MODE") != "1" and os.getenv("PP_EDGE_LIVE") != "1":
        print("Refusing live run: set PP_EDGE_LIVE=1", file=sys.stderr); return 3
    try:
        from ingest.live_slate_v1 import fetch_slate
        from code_utils_slipbuilder_v2 import SlipBuilder
        from code_utils_slipqa_v1 import qa_slip, HARD_FLAGS
        from code_utils_bankroll_alloc_v1 import allocate_slips
    except Exception as e:
        print(f"missing seam: {e}", file=sys.stderr); return 2
    legs = fetch_slate(date, sport, source=source)
    from cli.run_offline import maybe_apply_model
    legs = maybe_apply_model(legs)
    sb = SlipBuilder(CFG)
    slips = sb.build_slips(legs)
    for s in slips: s["_qa_flags"] = qa_slip(s, CFG)
    approved = [s for s in slips if not any(s["_qa_flags"].get(k, False) for k in HARD_FLAGS)]
    staked = allocate_slips(approved, bankroll=bankroll, slip_cap=slip_cap, slate_cap_frac=slate_cap_frac, kelly=kelly, min_stake=min_stake, allow_neg_ev=allow_neg_ev)
    outdir = os.path.dirname(out_path); os.makedirs(outdir, exist_ok=True)
    with open(out_path, "w") as f: json.dump({"slips": staked}, f, indent=2)
    review_path = os.path.join(outdir, "slips_review.json")
    with open(review_path, "w") as f: json.dump({"slips": slips}, f, indent=2)
    print(f"wrote {out_path} with {len(staked)} approved slips; review at {review_path}")
    return 0
if __name__ == "__main__":
    a = build_parser().parse_args()
    sys.exit(main(a.date, a.sport, a.source, a.out, a.bankroll, a.slip_cap, a.slate_cap_frac, a.kelly, a.min_stake, a.allow_neg_ev))
