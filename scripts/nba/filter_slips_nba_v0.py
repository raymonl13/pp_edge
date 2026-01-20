#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict

import pandas as pd


def _log(msg: str) -> None:
    print(f"[filter_slips_nba_v0] {msg}")


def _expand_slip_legs(slips: pd.DataFrame) -> pd.DataFrame:
    rows: List[dict] = []
    for _, row in slips.iterrows():
        slip_id = row["slip_id"]
        slip_type = row.get("slip_type")
        legs_str = str(row.get("legs", ""))
        for leg in legs_str.split("; "):
            if not leg.strip():
                continue
            try:
                player, market, line = leg.split("|")
                rows.append(
                    {
                        "slip_id": slip_id,
                        "slip_type": slip_type,
                        "player": player.strip(),
                        "market": market.strip(),
                        "line": float(line),
                    }
                )
            except ValueError:
                _log(f"WARNING: could not parse leg '{leg}' for slip_id={slip_id}")
    return pd.DataFrame(rows)


def filter_slips_for_day(
    day: str,
    runs_root: Path,
    p_hit_min: float,
    edge_min: float,
) -> None:
    runs_dir = runs_root / day

    slips_path = runs_dir / "slips_nba_v0.csv"
    preds_path = runs_dir / f"joined_with_phit_{day}.csv"
    sized_path = runs_dir / "slips_nba_v0_sized.csv"

    if not slips_path.exists():
        raise SystemExit(f"Slips file not found: {slips_path}")
    if not preds_path.exists():
        raise SystemExit(f"Predictions file not found: {preds_path}")

    _log(f"DAY={day}")
    _log(f"slips={slips_path}")
    _log(f"preds={preds_path}")

    slips = pd.read_csv(slips_path)
    preds = pd.read_csv(preds_path)

    legs = _expand_slip_legs(slips)
    _log(f"expanded legs rows={len(legs)}")

    # Normalize player name in preds if needed
    if "player_name" in preds.columns and "player" not in preds.columns:
        preds = preds.rename(columns={"player_name": "player"})

    # Determine market column
    if "market" in preds.columns:
        mcol = "market"
    elif "market_norm" in preds.columns:
        mcol = "market_norm"
    else:
        raise SystemExit("Predictions file has no 'market' or 'market_norm' column")

    preds_sub = preds[["player", mcol, "line", "p_hit", "edge_pp"]].rename(columns={mcol: "market"})

    legs = legs.merge(
        preds_sub,
        on=["player", "market", "line"],
        how="left",
    )
    _log(
        f"after merge with preds, legs rows={len(legs)}, "
        f"with p_hit non-null={legs['p_hit'].notna().sum()}"
    )

    if legs["p_hit"].isna().any():
        _log("WARNING: some legs had no predictions; these slips will be dropped.")

    # Decide which slips to keep: all legs must meet thresholds and have non-null p_hit/edge_pp
    def slip_passes(df: pd.DataFrame) -> bool:
        df = df.dropna(subset=["p_hit", "edge_pp"])
        if df.empty:
            return False
        cond = (df["p_hit"] >= p_hit_min) & (df["edge_pp"] >= edge_min)
        return bool(cond.all())

    keep_map: Dict[str, bool] = {}
    for slip_id, group in legs.groupby("slip_id"):
        keep_map[slip_id] = slip_passes(group)

    keep_ids = {sid for sid, keep in keep_map.items() if keep}
    _log(f"original slips={len(slips)}, kept after filter={len(keep_ids)}")

    filtered_slips = slips[slips["slip_id"].isin(keep_ids)].copy()
    out_slips = runs_dir / "slips_nba_v0_filtered.csv"
    filtered_slips.to_csv(out_slips, index=False)
    _log(f"wrote filtered slips to {out_slips}")

    if sized_path.exists():
        sized = pd.read_csv(sized_path)
        filtered_sized = sized[sized["slip_id"].isin(keep_ids)].copy()
        out_sized = runs_dir / "slips_nba_v0_sized_filtered.csv"
        filtered_sized.to_csv(out_sized, index=False)
        _log(f"wrote filtered sized slips to {out_sized}")
    else:
        _log("no slips_nba_v0_sized.csv found; skipping sized filter output")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Filter NBA v0 slips by per-leg p_hit and edge_pp thresholds."
    )
    ap.add_argument("--day", required=True, help="Day in YYYY-MM-DD format, e.g. 2025-11-21")
    ap.add_argument(
        "--runs-root",
        default="runs/nba",
        help="Root directory for run artifacts (default: runs/nba)",
    )
    ap.add_argument(
        "--p-hit-min",
        type=float,
        default=0.52,
        help="Minimum per-leg p_hit threshold (default: 0.52)",
    )
    ap.add_argument(
        "--edge-min",
        type=float,
        default=0.02,
        help="Minimum per-leg edge_pp threshold (default: 0.02)",
    )
    args = ap.parse_args()

    day = args.day
    runs_root = Path(args.runs_root)
    filter_slips_for_day(day, runs_root, args.p_hit_min, args.edge_min)


if __name__ == "__main__":
    main()
