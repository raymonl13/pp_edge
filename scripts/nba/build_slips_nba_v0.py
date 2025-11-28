#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml


def _log(msg: str) -> None:
    print(f"[build_slips_nba_v0] {msg}", file=sys.stderr)


# Ensure repo root is on sys.path so we can import code_utils_slipbuilder_v1
THIS_FILE = Path(__file__).resolve()
ROOT = THIS_FILE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from code_utils_slipbuilder_v1 import SlipBuilder as SB  # type: ignore


class MethodAdaptiveSlipBuilder:
    def __init__(self, cfg: Dict[str, Any]) -> None:
        try:
            self.impl = SB(cfg, demons_used_today=0)
        except TypeError:
            self.impl = SB(cfg)

    def build(self, legs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if hasattr(self.impl, "build_slips"):
            return self.impl.build_slips(legs)  # type: ignore[attr-defined]
        if hasattr(self.impl, "build"):
            return self.impl.build(legs)  # type: ignore[attr-defined]
        raise AttributeError("Underlying SlipBuilder has neither build_slips nor build")


def _load_cfg(config_path: Path) -> Dict[str, Any]:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def _majority(values: List[str], default: str = "standard") -> str:
    if not values:
        return default
    counts: Dict[str, int] = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return max(counts, key=counts.get)


def _ladder_for_type(cfg: Dict[str, Any], odds_type: str) -> Dict[str, float]:
    payouts: Dict[str, float] = {}
    ladders = cfg.get("payout_ladders", {})
    ladder = ladders.get(odds_type)
    if isinstance(ladder, dict):
        for k, v in ladder.items():
            try:
                payouts[k] = float(v)
            except (TypeError, ValueError):
                continue
    if not payouts:
        for k, v in (cfg.get("payouts") or {}).items():
            try:
                payouts[k] = float(v)
            except (TypeError, ValueError):
                continue
    return payouts


def _compute_ev(legs: List[Dict[str, Any]], slip_type: str, ladder: Dict[str, float]) -> Dict[str, float]:
    p_all = 1.0
    for leg in legs:
        p_all *= float(leg.get("p_hit", 0.0))
    payout = float(ladder.get(slip_type, 1.0))
    ev = p_all * payout - 1.0
    return {"p_all": round(p_all, 6), "EV": round(ev, 6)}


def _pick_player_column(df: pd.DataFrame, source: Path) -> pd.DataFrame:
    """
    Normalize whatever column holds the player name to 'player'.
    """
    candidates = [
        "player",
        "player_name",
        "player_full_name",
        "athlete",
        "athlete_name",
        "name",
    ]
    for col in candidates:
        if col in df.columns:
            if col != "player":
                _log(f"{source} using '{col}' as player column")
                df = df.rename(columns={col: "player"})
            return df
    raise SystemExit(
        f"[build_slips_nba_v0] no player-name column found in {source}; "
        f"tried {candidates}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="NBA v0.1 slip builder (Points-only) using SlipBuilder v1."
    )
    ap.add_argument("--day", required=True, help="Slate day, e.g. 2025-11-16.")
    ap.add_argument(
        "--config",
        default="config_pp_edge_v6.8.yaml",
        help="YAML config (payouts, diversification).",
    )
    ap.add_argument(
        "--runs-root",
        default="runs/nba",
        help="Root for NBA run artifacts (default: runs/nba).",
    )
    ap.add_argument(
        "--markets",
        default="points",
        help="Comma-separated allowed markets (default: points).",
    )
    args = ap.parse_args()

    day = args.day
    runs_dir = Path(args.runs_root) / day
    runs_dir.mkdir(parents=True, exist_ok=True)

    pre = runs_dir / f"joined_with_phit_{day}_prefilter.csv"
    base = runs_dir / f"joined_with_phit_{day}.csv"
    in_path = pre if pre.exists() else base
    if not in_path.exists():
        raise SystemExit(f"[build_slips_nba_v0] input not found: {in_path}")

    df = pd.read_csv(in_path)
    df = _pick_player_column(df, in_path)

    _log(f"day={day}")
    _log(f"input={in_path}")
    _log(f"loaded {len(df)} candidate legs")

    allowed_markets = {m.strip().lower() for m in args.markets.split(",") if m.strip()}
    if "market" in df.columns:
        mcol = "market"
    elif "market_norm" in df.columns:
        mcol = "market_norm"
    else:
        raise SystemExit("[build_slips_nba_v0] required column 'market' or 'market_norm' not found")

    before = len(df)
    df = df[df[mcol].astype(str).str.lower().isin(allowed_markets)].copy()
    _log(f"markets guard: kept {len(df)}/{before} rows where {mcol} in {sorted(allowed_markets)}")

    if df.empty:
        (runs_dir / "slips_nba_v0.json").write_text("[]")
        pd.DataFrame(columns=["slip_id", "slip_type", "odds_type", "n_legs", "p_all", "EV", "legs"]).to_csv(
            runs_dir / "slips_nba_v0.csv", index=False
        )
        _log("no candidates after markets guard; wrote empty slips")
        return

    odds_type = "standard"
    if "odds_type" in df.columns:
        odds_type = _majority(df["odds_type"].fillna("standard").astype(str).tolist(), default="standard")
        df = df[df["odds_type"].fillna(odds_type).astype(str) == odds_type].copy()
    _log(f"odds_type_selected={odds_type}")

    legs: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        legs.append(
            {
                "player": row.get("player"),
                "p_hit": float(row.get("p_hit", 0.0)),
                "edge_pp": float(row.get("edge_pp", 0.0)),
                "market": row.get(mcol),
                "line": float(row.get("line", 0.0)),
                "game_id": row.get("game_id"),
            }
        )

    cfg = _load_cfg(Path(args.config))
    payouts = _ladder_for_type(cfg, odds_type)
    diversification = cfg.get("diversification", {})
    sb_cfg = {"payouts": payouts, "diversification": diversification}

    sb = MethodAdaptiveSlipBuilder(sb_cfg)
    raw_slips = sb.build(legs)

    unique_slips: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def _slip_signature(slip: Dict[str, Any]) -> str:
        legs_list = slip.get("legs", [])
        parts = [f"{l.get('player')}|{l.get('market')}|{l.get('line')}" for l in legs_list]
        return "||".join(sorted(parts))

    for slip in raw_slips:
        sig = _slip_signature(slip)
        if sig in seen:
            continue
        seen.add(sig)
        unique_slips.append(slip)

    slips = unique_slips

    out_json = runs_dir / "slips_nba_v0.json"
    out_csv = runs_dir / "slips_nba_v0.csv"

    json_slips: List[Dict[str, Any]] = []
    csv_rows: List[Dict[str, Any]] = []

    for s in slips:
        slip_type = s.get("slip_type")
        legs_list = s.get("legs", [])
        ev_meta = _compute_ev(legs_list, slip_type, payouts)
        slip_id = str(uuid.uuid4())
        json_slips.append(
            {
                "slip_id": slip_id,
                "slip_type": slip_type,
                "odds_type": odds_type,
                "p_all": ev_meta["p_all"],
                "EV": ev_meta["EV"],
                "n_legs": len(legs_list),
                "legs": [
                    {
                        "player": l.get("player"),
                        "market": l.get("market"),
                        "line": l.get("line"),
                        "p_hit": l.get("p_hit"),
                        "edge_pp": l.get("edge_pp"),
                    }
                    for l in legs_list
                ],
            }
        )
        legs_str = "; ".join(f"{l.get('player')}|{l.get('market')}|{l.get('line')}" for l in legs_list)
        csv_rows.append(
            {
                "slip_id": slip_id,
                "slip_type": slip_type,
                "odds_type": odds_type,
                "n_legs": len(legs_list),
                "p_all": ev_meta["p_all"],
                "EV": ev_meta["EV"],
                "legs": legs_str,
            }
        )

    out_json.write_text(json.dumps(json_slips, indent=2))
    pd.DataFrame(csv_rows, columns=["slip_id", "slip_type", "odds_type", "n_legs", "p_all", "EV", "legs"]).to_csv(
        out_csv, index=False
    )
    _log(f"wrote {len(csv_rows)} slips to {out_csv} and {out_json}")


if __name__ == "__main__":
    main()
