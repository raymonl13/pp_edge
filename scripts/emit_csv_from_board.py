#!/usr/bin/env python3
import sys, json, csv, pathlib
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("data/pricefix.json")
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("edge_sheet.csv")
rows = []
if src.exists():
    with src.open() as f:
        for i,line in enumerate(f):
            try:
                d = json.loads(line)
            except Exception:
                continue
            leg_id = d.get("leg_id")
            if not leg_id:
                leg_id = chr(ord('A') + i)
            p = d.get("p")
            if p is None:
                p = d.get("p_hit", 0.55)
            rows.append({
                "leg_id": leg_id,
                "player": d.get("player") or "Sample",
                "game_id": d.get("game_id") or "SMK-0",
                "p": float(p),
                "p_hit": float(d.get("p_hit") or p),
                "edge_pp": float(d.get("edge_pp") or 0.05),
                "tier": d.get("tier") or "Standard",
                "slip_type": d.get("slip_type") or "P4",
            })
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["leg_id","player","game_id","p","p_hit","edge_pp","tier","slip_type"])
    w.writeheader()
    for r in rows or [{"leg_id":"A","player":"Sample","game_id":"SMK-0","p":0.55,"p_hit":0.55,"edge_pp":0.05,"tier":"Standard","slip_type":"P4"}]:
        w.writerow(r)
print(str(out))
