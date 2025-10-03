#!/usr/bin/env python3
from __future__ import annotations
import sys, json, csv
from pathlib import Path

G = "\033[32m"
R = "\033[31m"
Y = "\033[33m"
B = "\033[36m"
X = "\033[0m"

def color(s: str, c: str, enable: bool) -> str:
    return f"{c}{s}{X}" if enable else s

def read_meta(meta_path: Path) -> dict:
    d={}
    if not meta_path.exists(): return d
    for ln in meta_path.read_text().splitlines():
        if "=" in ln:
            k,v=ln.split("=",1); d[k.strip()]=v.strip()
    return d

def head_lines(p: Path, n=2) -> int:
    if not p.exists(): return 0
    try:
        with p.open() as f:
            return sum(1 for _,_ in zip(f, range(n)))
    except Exception:
        return 0

def load_json(p: Path) -> dict:
    if not p.exists(): return {}
    try: return json.loads(p.read_text())
    except Exception: return {}

def count_csv_rows(p: Path) -> int:
    if not p.exists(): return 0
    try:
        with p.open() as f:
            r=csv.reader(f)
            return sum(1 for _ in r)-1
    except Exception:
        return 0

def main():
    args=sys.argv[1:]
    no_color="--no-color" in args
    strict="--strict" in args
    dirs=[a for a in args if not a.startswith("-")]
    root=Path(dirs[0]).resolve() if dirs else Path(".").resolve()

    meta_path=root/"run_meta.txt"
    diag_txt=root/"slip_diag.txt"
    debug_json=root/"slip_builder_debug.json"
    slips_csv=root/"alloc_slips.csv"
    stakes_csv=root/"alloc_slips_with_stakes.csv"
    edge_csv=None
    for p in root.glob("edge_sheet_*.csv"):
        edge_csv=p; break
    run_debug=root/"run_debug.json"

    meta=read_meta(meta_path)
    run_dbg=load_json(run_debug)

    ok=True
    def mark(name, cond, note=""):
        nonlocal ok
        tag = color("PASS", G, not no_color) if cond else color("FAIL", R, not no_color)
        print(f"{tag}  {name}{('  '+note) if note else ''}")
        ok = ok and cond

    print(color("=== PRE-FLIGHT TRIAGE ===", B, not no_color))
    mark("meta present", meta_path.exists())
    mark("diag present", diag_txt.exists())
    mark("edge_sheet present", edge_csv is not None)
    mark("builder debug present", debug_json.exists() or bool(run_dbg.get("debug_present", False)))
    mark("slips csv has data", count_csv_rows(slips_csv) > 0)
    if stakes_csv.exists():
        stakes_rows = count_csv_rows(stakes_csv)
        mark("stakes csv present", True, f"rows={stakes_rows}")
        if strict:
            mark("stakes rows > 0 (strict)", stakes_rows > 0)
    else:
        mark("stakes csv present", False)

    slips_built = None
    try: slips_built=int(meta.get("SLIPS_BUILT","0"))
    except: slips_built=None
    mark("SLIPS_BUILT in meta", slips_built is not None, f"value={slips_built}")
    mark("selected in meta", "SLIP_KEYS_SELECTED" in meta, meta.get("SLIP_KEYS_SELECTED",""))
    mark("builder SIG in meta", "BUILDER_SIG" in meta, meta.get("BUILDER_SIG",""))

    if edge_csv:
        lines = head_lines(edge_csv, n=2)
        mark("edge_sheet has header+row", lines>=2)

    # Hints
    print(color("\n--- HINTS ---", Y, not no_color))
    if not meta_path.exists():
        print("no run_meta.txt → confirm Ensure slip meta step is if: always()")
    if diag_txt.exists() and "built=1" in diag_txt.read_text() and count_csv_rows(slips_csv)==0:
        print("diag says feasible but slips are empty → check builder runtime (debug JSON, __main__ guard, selection)")
    if meta.get("BUILD_SLIPS_RC","0")!="0":
        print("builder rc != 0 → open builder_stderr.log for line-number traceback")

    # Exit code
    sys.exit(0 if ok else 2)

if __name__=="__main__":
    main()
