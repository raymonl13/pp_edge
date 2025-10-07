#!/usr/bin/env python3
import os, json, glob, csv, hashlib
from pathlib import Path
from typing import Optional
def first(pattern: str) -> Optional[Path]:
    xs = sorted(glob.glob(pattern, recursive=True))
    return Path(xs[0]) if xs else None
def load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}
def sha16_file(p: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with p.open("rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return None
def pct_delta(curr, prev):
    try:
        curr = int(curr); prev = int(prev)
        if prev == 0: return "n/a"
        d = 100.0 * (curr - prev) / prev
        return f"{d:+.1f}%"
    except Exception:
        return "n/a"
def main():
    day = os.environ.get("DAY","")
    print(f"[run] day={day}")
    rj = first("**/route_debug.json")
    board_sha = None
    if day:
        bp = Path(f"data/pricefix_{day}.json")
        if bp.exists():
            board_sha = sha16_file(bp)
    if rj:
        r = load_json(rj)
        attempts = r.get("attempts")
        retry = r.get("RETRY_COUNT")
        retry_count = retry if isinstance(retry,int) else (attempts-1 if isinstance(attempts,int) and attempts>0 else None)
        sha = r.get('board_sha16') or board_sha
        print(f"[router] state={r.get('ROUTE_STATE')} http={r.get('HTTP_STATUS')} rows={r.get('row_count')} retry={retry_count} sha16={sha}")
    else:
        print("[router] state=? http=? rows=? retry=? sha16=?")
    csv_rows = None
    if day:
        p = Path(f"edge_sheet_{day}.csv")
        if p.exists():
            with p.open(newline="") as fh:
                rdr = csv.reader(fh)
                next(rdr, None)
                csv_rows = sum(1 for _ in rdr)
    print(f"[csv] rows={csv_rows if csv_rows is not None else '?'}")
    meta = first("run_meta.txt") or first("**/run_meta.txt")
    if meta:
        kv = {}
        for ln in meta.read_text().splitlines():
            if "=" in ln:
                k,v = ln.split("=",1); kv[k.strip()] = v.strip()
            elif ":" in ln:
                k,v = ln.split(":",1); kv[k.strip()] = v.strip()
        s_built = kv.get("SLIPS_BUILT")
        s_sel = kv.get("SLIP_KEYS_SELECTED")
        model = kv.get("MODEL_STATE")
        cal = kv.get("CAL_STATE")
        print(f"[builder] slips_built={s_built} selected={s_sel}")
        if model or cal:
            print(f"[model] state={model} cal={cal}")
    curr = load_json(Path("metrics_run.json")) if Path("metrics_run.json").exists() else {}
    prev_path = Path("metrics_prev.json")
    if prev_path.exists():
        prev = load_json(prev_path)
        c_rr = ((curr.get("router") or {}).get("row_count"))
        p_rr = ((prev.get("router") or {}).get("row_count"))
        c_cr = ((curr.get("scorer") or {}).get("csv_rows"))
        p_cr = ((prev.get("scorer") or {}).get("csv_rows"))
        def warn(name, c, p):
            try:
                c = int(c); p = int(p)
            except Exception:
                return
            if p and abs(c - p) / max(1, p) >= 0.5:
                print(f"[WARN drift] {name}: prev={p} curr={c} delta={pct_delta(c,p)}")
        warn("router.row_count", c_rr, p_rr)
        warn("csv.rows", c_cr, p_cr)
if __name__ == "__main__":
    main()
