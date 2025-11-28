#!/usr/bin/env python3
import argparse, csv
from pathlib import Path

CORE = {"points","rebounds","assists","fantasy score"}
def is_core_market(m: str) -> bool:
    if not m: return False
    m = m.lower()
    bad = ["1st","first ","2nd","3rd","4th","quarter","qtr","half","minutes","minute","min ","1h","2h","overtime",
           "fg made","field goals","free throw","ft made","ft attempted"]
    if any(t in m for t in bad): return False
    if m in CORE: return True
    if "pts+rebs+asts" in m or m == "pra": return True
    if "pts+rebs" in m or "pts+asts" in m or "rebs+asts" in m: return True
    if any(s in m for s in ["3-pt","3 pt","3pt","threes","3pt made","3p made"]): return True
    return False

def ffloat(x, d=0.0):
    try: return d if x in (None,"") else float(x)
    except Exception: return d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", required=True)
    ap.add_argument("--top-k", type=int, default=60)
    args = ap.parse_args()

    day = args.day
    base = Path("runs")/"nba"/day
    src  = base/f"joined_with_phit_{day}.csv"
    dst  = base/f"joined_with_phit_{day}_prefilter.csv"
    if not src.exists():
        raise SystemExit(f"missing: {src}")

    rows = list(csv.DictReader(src.open()))
    # filter to usable rows
    filt = []
    for r in rows:
        if str(r.get("features_found","")).strip().lower() != "true": continue
        if ffloat(r.get("games"),0.0) < 10: continue
        if not is_core_market(r.get("market") or ""): continue
        r["edge_pp"] = ffloat(r.get("p_hit"),0.5) - 0.5
        filt.append(r)
    # keep best per player (player_name, team)
    best = {}
    for r in filt:
        key = (r.get("player_name",""), r.get("team",""))
        if key not in best or r["edge_pp"] > best[key]["edge_pp"]:
            best[key] = r
    dedup = list(best.values())
    dedup.sort(key=lambda r: r["edge_pp"], reverse=True)
    top = dedup[:args.top_k]

    # always write a valid CSV (header only if empty)
    fieldnames = top[0].keys() if top else (rows[0].keys() if rows else ["player_name","team","market","line","p_hit","edge_pp"])
    with dst.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        if top: w.writerows(top)

    print(f"[prepare_candidates_nba_v0] wrote {dst} rows={len(top)}")
if __name__ == "__main__":
    main()
