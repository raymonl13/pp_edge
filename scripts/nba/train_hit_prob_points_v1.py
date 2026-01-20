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

from code_utils_model_v1 import train_logistic_model, save_model


def _load_cfg(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Train NBA Points hit-probability model (v1) using logistic regression."
    )
    p.add_argument(
        "--train-csv",
        required=True,
        help="Path to training CSV with features + binary target.",
    )
    p.add_argument(
        "--features",
        required=True,
        help="Comma-separated list of feature column names, e.g. "
             "'line,season_pts_per_game'.",
    )
    p.add_argument(
        "--target",
        default="hit",
        help="Name of binary target column (1 = went over line, 0 = did not). Default: hit.",
    )
    p.add_argument(
        "--config",
        default="config_pp_edge_v6.8.yaml",
        help="YAML config; used to resolve model_assets.hit_prob_v1 if --model-path is omitted.",
    )
    p.add_argument(
        "--model-path",
        default=None,
        help="Optional explicit output path for the trained model .pkl. "
             "If omitted, uses model_assets.hit_prob_v1 from config.",
    )
    p.add_argument(
        "--iters",
        type=int,
        default=2000,
        help="Gradient descent iterations (default: 2000).",
    )
    p.add_argument(
        "--lr",
        type=float,
        default=0.01,
        help="Learning rate (default: 0.01).",
    )
    p.add_argument(
        "--l2",
        type=float,
        default=0.0,
        help="L2 regularization strength (default: 0.0).",
    )
    args = p.parse_args()

    train_path = Path(args.train_csv)
    if not train_path.exists():
        raise SystemExit(f"[train_hit_prob_points_v1] training CSV not found: {train_path}")

    df = pd.read_csv(train_path)

    feature_names = [c.strip() for c in args.features.split(",") if c.strip()]
    if not feature_names:
        raise SystemExit("[train_hit_prob_points_v1] --features must list at least one column.")

    target_col = args.target
    if target_col not in df.columns:
        raise SystemExit(
            f"[train_hit_prob_points_v1] target column '{target_col}' not found in {train_path}"
        )

    # Determine model output path
    if args.model_path:
        model_path = Path(args.model_path)
    else:
        cfg = _load_cfg(Path(args.config))
        try:
            mp_str = cfg["model_assets"]["hit_prob_v1"]
        except Exception as e:
            raise SystemExit(
                f"[train_hit_prob_points_v1] Could not resolve model_assets.hit_prob_v1 "
                f"from {args.config}: {e}"
            )
        model_path = Path(mp_str)

    print(
        f"[train_hit_prob_points_v1] training on {len(df)} rows "
        f"features={feature_names} target={target_col}"
    )
    model = train_logistic_model(
        df,
        feature_names=feature_names,
        target_col=target_col,
        num_iter=args.iters,
        learning_rate=args.lr,
        l2_reg=args.l2,
    )

    save_model(model, model_path)
    print(f"[train_hit_prob_points_v1] saved model to {model_path}")


if __name__ == "__main__":
    main()
