#!/usr/bin/env python3
import os, sys, json, csv, hashlib, glob, re
from pathlib import Path
from typing import Any, Dict, Optional, List
ROOT = Path(".").resolve()
METRICS_VERSION = "1.0"
def read_json(p: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(p.read_text())
    except Exception:
        return None
def read_lines(p: Path) -> List[str]:
    try:
        return p.read_text().splitlines()
    except Exception:
        return []
def ci_get(d: Dict[str, Any], *keys):
    for k in keys:
        if k in d: return d[k]
        if isinstance(k, str):
            for v in (k.lower(), k.upper(), k.title()):
                if v in d: return d[v]
    return None
def sha16_file(p: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with p.open("rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return None
def infer_day_from_csv() -> Optional[str]:
    files = sorted(ROOT.glob("edge_sheet_*.csv"))
    if not files:
        return None
    m = re.match(r"edge_sheet_(\d{4}-\d{2}-\d{2})\.csv", files[-1].name)
    return m.group(1) if m else None
def parse_kv(lines: List[str]) -> Dict[str, str]:
    out = {}
    for ln in lines:
        if "=" in ln:
            k, v = ln.split("=", 1)
        elif ":" in ln:
            k, v = ln.split(":", 1)
        else:
            continue
        out[k.strip()] = v.strip()
    return out
def count_csv_rows(p: Path) -> Optional[int]:
    try:
        with p.open(newline="") as fh:
            rdr = csv.reader(fh)
            next(rdr, None)
            return sum(1 for _ in rdr)
    except Exception:
        return None
def latest_run_dir() -> Optional[Path]:
    cands = [p for p in ROOT.glob("qa_alloc_*") if p.is_dir()]
    return max(cands, key=lambda x: x.stat().st_mtime) if cands else None
def presence_map(names: List[str], run_dir: Optional[Path]) -> Dict[str, bool]:
    res = {}
    for name in names:
        p_root = ROOT / name
        p_run = (run_dir / name) if run_dir else None
        found = (p_root.exists()) or (p_run.exists() if p_run else False)
        if not found:
            found = bool(list(ROOT.glob(f"**/{name}")))
        res[name] = bool(found)
    return res
def main() -> None:
    env_day = os.environ.get("DAY")
    gh_run = os.environ.get("GITHUB_RUN_NUMBER")
    gh_sha = os.environ.get("GITHUB_SHA")
    day = env_day or infer_day_from_csv()
    run_dir = latest_run_dir()
    router_debug = None
    for cand in [ROOT / "route_debug.json", ROOT / "logs" / "route_debug.json", (run_dir / "route_debug.json") if run_dir else None]:
        if cand and cand.exists():
            router_debug = cand
            break
    route = read_json(router_debug) if router_debug else None
    meta_path = None
    for cand in [ROOT / "run_meta.txt", (run_dir / "run_meta.txt") if run_dir else None]:
        if cand and cand.exists():
            meta_path = cand
            break
    meta_kv = parse_kv(read_lines(meta_path)) if meta_path else {}
    if not day:
        day = meta_kv.get("DAY") or infer_day_from_csv()
    board_sha16 = None
    if day:
        board_path = ROOT / f"data/pricefix_{day}.json"
        if board_path.exists():
            board_sha16 = sha16_file(board_path)
    router = {"row_count": None, "retry_count": None, "http_status": None, "route_state": None, "route_noop": None, "board_sha16": board_sha16}
    if route:
        attempts = ci_get(route, "attempts")
        retry = ci_get(route, "RETRY_COUNT")
        retry_count = retry if isinstance(retry, int) else (attempts - 1 if isinstance(attempts, int) and attempts > 0 else None)
        router.update({
            "row_count": ci_get(route, "row_count"),
            "retry_count": retry_count,
            "http_status": ci_get(route, "HTTP_STATUS", "http_status"),
            "route_state": ci_get(route, "ROUTE_STATE", "route_state"),
            "route_noop": ci_get(route, "ROUTE_NOOP", "route_noop"),
            "board_sha16": ci_get(route, "board_sha16") or board_sha16
        })
    csv_rows = None
    if day:
        csv_path = ROOT / f"edge_sheet_{day}.csv"
        if csv_path.exists():
            csv_rows = count_csv_rows(csv_path)
    scorer = {"csv_rows": csv_rows, "model_state": meta_kv.get("MODEL_STATE"), "cal_state": meta_kv.get("CAL_STATE")}
    slips_built = None
    try:
        slips_built = int(meta_kv.get("SLIPS_BUILT")) if ("SLIPS_BUILT" in meta_kv) else None
    except Exception:
        slips_built = None
    builder = {"slips_built": slips_built, "selected": meta_kv.get("SLIP_KEYS_SELECTED"), "builder_sig": meta_kv.get("BUILDER_SIG")}
    qa_keys = ["alloc_slips.csv","alloc_slips_with_stakes.csv","alloc_summary.csv","slips.csv","slips.json","slip_diag.txt","slip_diag.json","qa_report.json","qa_report.csv","qa_stdout.log","qa_stderr.log","builder_stdout.log","builder_stderr.log"]
    qa = presence_map(qa_keys, run_dir)
    out = {"metrics_version": METRICS_VERSION, "run": {"day": day, "run_number": int(gh_run) if (gh_run and gh_run.isdigit()) else None, "commit_sha": gh_sha, "commit_sha7": gh_sha[:7] if gh_sha else None}, "router": router, "scorer": scorer, "builder": builder, "qa": qa}
    Path("metrics_run.json").write_text(json.dumps(out, indent=2))
    print("metrics_run.json written")
if __name__ == "__main__":
    main()
