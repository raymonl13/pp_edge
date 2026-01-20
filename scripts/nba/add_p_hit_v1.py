#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

# Ensure repo root is on sys.path so `code_utils_model_v1` imports cleanly
THIS_FILE = Path(__file__).resolve()
ROOT = THIS_FILE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from code_utils_model_v1 import predict_hit_prob


def _load_cfg(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main() -> None:
    p = argparse.ArgumentParser(
        description="NBA v1 hit-probability step: overwrite p_hit for Points using model_assets.hit_prob_v1."
    )
    p.add_argument("--day", required=True, help="Slate day, e.g. 2025-11-14.")
    p.add_argument(
        "--config",
        default="config_pp_edge_v6.8.yaml",
        help="Config file with model_assets.hit_prob_v1.",
    )
    p.add_argument(
        "--model-path",
        default=None,
        help="Optional explicit model path; if omitted, uses model_assets.hit_prob_v1.",
    )
    p.add_argument(
        "--features",
        required=True,
        help="Comma-separated feature columns to feed the model, "
             "e.g. 'line,season_pts_per_game'. Must exist in joined_<DAY>.csv.",
    )
    args = p.parse_args()

    day = args.day
    runs_dir = Path("runs") / "nba" / day
    in_path = runs_dir / f"joined_{day}.csv"
    out_path = runs_dir / f"joined_with_phit_{day}.csv"

    if not in_path.exists():
        raise SystemExit(f"[add_p_hit_v1] input not found: {in_path}")

    df = pd.read_csv(in_path)

    # Ensure markets column
    if "market" in df.columns:
        market_col = "market"
    elif "market_norm" in df.columns:
        market_col = "market_norm"
    else:
        raise SystemExit("[add_p_hit_v1] required column 'market' or 'market_norm' not found")

    # Initialize stub: everyone at 0.5
    df["p_hit"] = 0.5
    df["edge_pp"] = 0.0

    mask_points = df[market_col].astype(str).str.lower().eq("points")
    n_points = int(mask_points.sum())
    print(f"[add_p_hit_v1] day={day} total_rows={len(df)} points_rows={n_points}")

    if n_points == 0:
        print("[add_p_hit_v1] no Points rows found; writing stubbed output.")
        df.to_csv(out_path, index=False)
        return

    # Resolve model path
    if args.model_path:
        model_path = Path(args.model_path)
    else:
        cfg = _load_cfg(Path(args.config))
        try:
            mp_str = cfg["model_assets"]["hit_prob_v1"]
        except Exception as e:
            raise SystemExit(
                f"[add_p_hit_v1] Could not resolve model_assets.hit_prob_v1 "
                f"from {args.config}: {e}"
            )
        model_path = Path(mp_str)

    if not model_path.exists():
        print(
            f"[add_p_hit_v1] WARNING: model not found at {model_path}; "
            "leaving p_hit=0.5 for all rows (NB-M1 behavior)."
        )
        df.to_csv(out_path, index=False)
        return

    feature_names = [c.strip() for c in args.features.split(",") if c.strip()]
    if not feature_names:
        raise SystemExit("[add_p_hit_v1] --features must specify at least one column.")

    missing = [c for c in feature_names if c not in df.columns]
    if missing:
        raise SystemExit(
            f"[add_p_hit_v1] feature columns missing from joined CSV: {missing}"
        )

    points_df = df.loc[mask_points, feature_names].copy()
    probs = predict_hit_prob(points_df, model_path=model_path)

    # Clamp for safety
    probs = pd.Series(probs, index=df.index[mask_points]).clip(0.01, 0.99)

    df.loc[mask_points, "p_hit"] = probs
    df["edge_pp"] = df["p_hit"] - 0.5

    df.to_csv(out_path, index=False)
    print(f"[add_p_hit_v1] wrote {out_path}")


if __name__ == "__main__":
    main()
