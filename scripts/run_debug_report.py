#!/usr/bin/env python3
from __future__ import annotations
import json, csv, glob, os
from pathlib import Path

def safe_read(p: Path, default=""):
    try: return p.read_text()
    except Exception: return default

def main():
    meta_p=Path("run_meta.txt")
    diag_p=Path("slip_diag.txt")
    dbg_p=Path("slip_builder_debug.json")
    slip_p=None
    for x in Path(".").glob("alloc_slips.csv"):
        slip_p=x; break
    edge_p=None
    for x in Path(".").glob("edge_sheet_*.csv"):
        edge_p=x; break

    meta_lines = [l for l in safe_read(meta_p,"").splitlines() if l.strip()]
    diag = safe_read(diag_p,"").splitlines()
    dbg = {}
    if dbg_p.exists():
        try: dbg=json.loads(dbg_p.read_text())
        except Exception: dbg={"error":"invalid json"}
    slip_rows=[]
    if slip_p and slip_p.exists():
        with slip_p.open() as f:
            r=csv.reader(f); slip_rows=list(r)[:6]

    summary = {
        "meta_present": meta_p.exists(),
        "diag_present": diag_p.exists(),
        "debug_present": dbg_p.exists(),
        "slips_present": bool(slip_p and slip_p.exists()),
        "edge_present": bool(edge_p and edge_p.exists()),
        "meta_keys": [k.split("=",1)[0] for k in meta_lines if "=" in k]
    }
    report_txt=[]
    report_txt.append("=== RUN DEBUG SUMMARY ===")
    report_txt.append(str(summary))
    report_txt.append("\n-- META (key lines) --")
    keep = ("SLIPS_BUILT","SLIP_KEYS_METHOD","SLIP_KEYS_SELECTED","SLIP_KEYS_SKIPPED","SLIP_KEYS_OBSERVED","SLIP_EV_METHOD","BUILDER_SIG")
    for l in meta_lines:
        if any(l.startswith(k+"=") for k in keep):
            report_txt.append(l)
    report_txt.append("\n-- DIAG (head) --")
    report_txt.extend(diag[:6] if diag else ["<no diag>"])
    report_txt.append("\n-- BUILDER DEBUG --")
    report_txt.append(json.dumps(dbg, indent=2) if dbg else "<no debug>")
    report_txt.append("\n-- SLIPS (head) --")
    if slip_rows:
        report_txt.extend([",".join(r) for r in slip_rows])
    else:
        report_txt.append("<no slips>")

    Path("run_debug.txt").write_text("\n".join(report_txt))
    Path("run_debug.json").write_text(json.dumps({
        "summary": summary,
        "meta": meta_lines,
        "diag_head": diag[:20] if diag else [],
        "builder_debug": dbg,
        "slips_head": slip_rows
    }, indent=2))
    print("\n".join(report_txt[:40]))

if __name__=="__main__":
    main()
