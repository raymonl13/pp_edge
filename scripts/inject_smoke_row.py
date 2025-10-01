#!/usr/bin/env python3
import sys, csv, os

def is_header_only(path):
    try:
        with open(path, newline="") as f:
            return sum(1 for _ in f) <= 1
    except Exception:
        return True

def main():
    if len(sys.argv) < 2:
        print("usage: inject_smoke_row.py <edge_csv>"); sys.exit(0)
    path = sys.argv[1]
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(["player","game_id","p_hit","edge_pp","tier","slip_type"])
    if not is_header_only(path):
        print("csv_has_rows"); return
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or ["player","game_id","p_hit","edge_pp","tier","slip_type"]
    row = {
        "player": "Smoke Test",
        "game_id": "SMK-000",
        "p_hit": "0.55",
        "edge_pp": "0.05",
        "tier": "Standard",
        "slip_type": "Flex"
    }
    # Preserve field order, fill missing keys if needed
    out = {k: row.get(k, "") for k in fields}
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if f.tell() == 0:
            w.writeheader()
        w.writerow(out)
    print("smoke_row_appended")

if __name__ == "__main__":
    main()
