import json, os, sys
day = sys.argv[1] if len(sys.argv)>1 else os.environ.get("DAY","")
pricefix = f"data/pricefix_{day}.json"
csv = f"edge_sheet_{day}.csv"
# ingest count
cnt = 0
try:
    with open(pricefix, "r", encoding="utf-8") as f:
        j = json.load(f)
        if isinstance(j, dict):
            items = j.get("projections",{}).get("data",[]) or j.get("data") or j.get("results") or j.get("items") or []
        elif isinstance(j, list):
            items = j
        else:
            items = []
        cnt = len(items)
except Exception:
    cnt = 0
ingest_state = "OK" if cnt > 0 else "FALLBACK"
# csv rows
rows = 0
try:
    with open(csv, "r", encoding="utf-8") as f:
        rows = sum(1 for _ in f)
        rows = max(rows-1, 0)
except Exception:
    rows = 0
csv_state = "REAL" if rows > 0 else "PLACEHOLDER"
with open("run_meta.txt","w",encoding="utf-8") as f:
    f.write(f"DAY={day}\nINGEST_STATE={ingest_state}\nCSV_STATE={csv_state}\nCSV_ROWS={rows}\n")
print("Wrote run_meta.txt")
