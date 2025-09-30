import sys, json, csv
inp = sys.argv[1]
outp = sys.argv[2]
try:
    j = json.load(open(inp, "r", encoding="utf-8"))
except Exception:
    j = []
if isinstance(j, dict):
    items = j.get("projections",{}).get("data",[]) or j.get("data") or j.get("results") or j.get("items") or []
elif isinstance(j, list):
    items = j
else:
    items = []
rows = []
for o in items:
    a = (o.get("attributes") or {})
    tier_raw = (a.get("odds_type") or "").strip().lower()
    tier = "Demon" if tier_raw=="demon" else "Goblin" if tier_raw=="goblin" else "Standard"
    rows.append({
        "player": a.get("description") or "",
        "game_id": a.get("game_id") or "",
        "p_hit": "",
        "edge_pp": "",
        "tier": tier,
        "slip_type": "2-leg",
    })
with open(outp, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["player","game_id","p_hit","edge_pp","tier","slip_type"])
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(len(rows))
