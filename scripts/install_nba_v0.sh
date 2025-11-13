#!/usr/bin/env bash
# install_nba_v0.sh — add NBA v0.1 adapter doc & pipeline stubs
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
echo "[install_nba_v0] ROOT=${ROOT}"
echo "[install_nba_v0] Branch: $(git branch --show-current)"

mkdir -p docs/slp scripts/nba features config/markets runs/nba

###############################################################################
# docs/slp/nba_adapter_v0.md
###############################################################################
cat > docs/slp/nba_adapter_v0.md <<'EOF'
# NBA Adapter v0 – Golden Day Pipeline Spec

> v0.1 — "Golden Day" NBA pipeline spec. Built on PP-EDGE SLP v6.8 and Phase-1 rails.

## Goals

For a single NBA regular-season day `DAY` (YYYY-MM-DD):

- Ingest a PrizePicks-like NBA board into normalized `runs/nba/{DAY}/board_{DAY}.json`.
- Build minimal but meaningful per-player features from local gamelog/pace CSVs.
- Join board + features + model to produce `runs/nba/{DAY}/joined_{DAY}.csv` with `p_hit` and `edge_pp`.
- Generate slips via the existing slipbuilder v2 (dry-run only).
- Emit a full handoff bundle (`STATE.json`, `CHECKS.md`, `FINGERPRINTS.txt`, `outcomes_summary.json`, `freeze_manifest.json`) under `runs/nba/{DAY}/`.

This is a **v0.1** pipeline: features & model are intentionally simple but shaped for a Moneyball phase.

## Inputs

All inputs are local files. No network calls from scripts.

- Raw board: `data/nba/boards/{DAY}/prizepicks_board_{DAY}.json`
- Gamelogs: `data/nba/gamelogs/gamelogs_2024.csv` (adjust season)
- Optional pace: `data/nba/team_pace_2024.csv`

See SLP – NBA Add-On (v1.1) for market coverage and acceptance thresholds.

## Normalized board schema (board_{DAY}.json)

Each record:

- player_id   : str
- player_name : str
- team        : str
- opp_team    : str
- game_id     : str
- game_date   : YYYY-MM-DD
- market      : str ("points","rebounds","assists","threes","pra", etc.)
- line        : float
- odds_type   : str ("standard","goblin","demon","flex",...)
- book        : str ("prizepicks",...)

## Feature schema v0.1 (features_nba_v0.*)

Per (player_id, team, game_date):

- mp_last3
- mp_last10
- usage_last10         # simple proxy based on stats, to be refined
- team_pace_last10     # from team pace file if available
- pts_last5
- reb_last5
- ast_last5

Later Moneyball phase can extend with TS%, eFG%, AST%, TRB%, on/off, matchup difficulty, etc.

## Join & model

- Join board ↔ features on (player_id, team, game_date) where possible; fallback to (player_name, team, game_date).
- Output: joined_{DAY}.csv with:
  - all board fields,
  - feature fields,
  - p_hit (0–1; placeholder model v0.1),
  - edge_pp (computed later by slipbuilder using payout ladders).

Model v0.1:

- Simple logistic transform of (recent stat - line). Later replaced with trained `predict_hit_prob_nba`.

## Slip build & handoff

- Use existing `code_utils_slipbuilder_v2.py` with payout ladders (see payouts README & config).
- For Golden Day v0.1, target a small set of markets (points, rebounds, assists, threes, PRA).
- Outputs:
  - edge_sheet_{DAY}.csv
  - slips.json (dry-run payload)
- Handoff bundle: STATE.json, CHECKS.md, FINGERPRINTS.txt, outcomes_summary.json, freeze_manifest.json.

## Acceptance criteria (Golden Day v0.1)

- board_{DAY}.json exists with > 0 rows.
- features_nba_v0.* exists; covers ≥ 80% of board rows.
- joined_{DAY}.csv exists and has p_hit ∈ (0,1) and edge_pp computed via payout ladders.
- edge_sheet_{DAY}.csv and slips.json exist and contain ≥ 1 slip.
- Handoff bundle present; CHECKS.md indicates SLP preflight PASS, QA not FAIL.
EOF

###############################################################################
# scripts/nba/ingest_nba_board.py
###############################################################################
cat > scripts/nba/ingest_nba_board.py <<'EOF'
#!/usr/bin/env python3
"""
NBA board ingestion (v0.1, file-first, no network).

Reads a provider-specific NBA board JSON from disk and writes a normalized
board_{DAY}.json file under runs/nba/{DAY}/ as described in docs/slp/nba_adapter_v0.md.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def normalize_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a raw provider record into the normalized schema.

    REQUIRED keys:

        player_id   : str
        player_name : str
        team        : str
        opp_team    : str
        game_id     : str
        game_date   : str (YYYY-MM-DD)
        market      : str ("points","rebounds","assists","threes","pra",...)
        line        : float
        odds_type   : str ("standard","goblin","demon","flex",...)
        book        : str ("prizepicks",...)

    TODO: Replace the mapping below with your provider's real JSON fields.
    """
    player = raw.get("player", {}) if isinstance(raw.get("player", {}), dict) else {}
    return {
        "player_id": str(player.get("id", "")),
        "player_name": player.get("name", ""),
        "team": player.get("team", ""),
        "opp_team": raw.get("opponent", ""),
        "game_id": raw.get("game_id", ""),
        "game_date": raw.get("date", ""),
        "market": raw.get("stat_type", ""),
        "line": float(raw.get("line", 0.0) or 0.0),
        "odds_type": str(raw.get("odds_type", "standard")),
        "book": str(raw.get("book", "prizepicks")),
    }


def load_raw_board(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Raw board file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "data" in data:
        return list(data["data"])
    if isinstance(data, list):
        return list(data)
    raise ValueError("Unsupported raw board structure; expected list or dict['data'].")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize NBA board into board_{DAY}.json")
    parser.add_argument("--day", required=True, help="Game day (YYYY-MM-DD)")
    parser.add_argument("--raw-path", required=True, help="Path to raw provider board JSON")
    parser.add_argument("--out-dir", help="Output dir (default: runs/nba/{DAY})")
    args = parser.parse_args()

    day = args.day
    raw_path = Path(args.raw_path)
    out_dir = Path(args.out_dir) if args.out_dir else Path("runs") / "nba" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_records = load_raw_board(raw_path)
    normalized = [normalize_record(r) for r in raw_records]

    out_path = out_dir / f"board_{day}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[ingest_nba_board] wrote {out_path} rows={len(normalized)}")


if __name__ == "__main__":
    from pathlib import Path
    main()
EOF

###############################################################################
# features/features_nba_v0.py
###############################################################################
cat > features/features_nba_v0.py <<'EOF'
#!/usr/bin/env python3
"""
NBA features v0.1 for Golden Day.

Reads an NBA gamelog CSV and produces per-player features:

- mp_last3, mp_last10
- usage_last10 (simple proxy)
- team_pace_last10 (optional)
- pts_last5, reb_last5, ast_last5

See docs/slp/nba_adapter_v0.md for details.
"""

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class Config:
    day: str
    gamelogs_path: Path
    out_path: Path
    pace_path: Optional[Path] = None


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Build NBA features v0.1 for a given day.")
    parser.add_argument("--day", required=True, help="Target day (YYYY-MM-DD)")
    parser.add_argument("--gamelogs-path", required=True, help="Path to NBA gamelog CSV")
    parser.add_argument("--out-path", required=True, help="Output path for features (csv/parquet)")
    parser.add_argument("--pace-path", help="Optional path to team pace CSV")
    args = parser.parse_args()
    return Config(
        day=args.day,
        gamelogs_path=Path(args.gamelogs_path),
        out_path=Path(args.out_path),
        pace_path=Path(args.pace_path) if args.pace_path else None,
    )


def load_gamelogs(cfg: Config) -> pd.DataFrame:
    df = pd.read_csv(cfg.gamelogs_path)
    required = [
        "player_id", "player_name", "team", "game_date",
        "minutes", "pts", "reb", "ast"
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required gamelog columns: {missing}")
    df["game_date"] = pd.to_datetime(df["game_date"])
    return df


def filter_window(df: pd.DataFrame, cutoff: datetime, days_back: int) -> pd.DataFrame:
    start = cutoff - timedelta(days=days_back * 2)
    mask = (df["game_date"] < cutoff) & (df["game_date"] >= start)
    return df.loc[mask].copy()


def build_features(cfg: Config) -> pd.DataFrame:
    target_day = datetime.fromisoformat(cfg.day)
    logs = load_gamelogs(cfg)
    logs_before = logs[logs["game_date"] < target_day]

    def window_mean(col: str, window_games: int, alias: str) -> pd.DataFrame:
        dfw = filter_window(logs_before, target_day, window_games)
        grouped = (
            dfw.sort_values("game_date")
            .groupby(["player_id", "team"])
            .tail(window_games)
            .groupby(["player_id", "team"])[col]
            .mean()
            .rename(alias)
            .reset_index()
        )
        return grouped

    mp3 = window_mean("minutes", 3, "mp_last3")
    mp10 = window_mean("minutes", 10, "mp_last10")
    pts5 = window_mean("pts", 5, "pts_last5")
    reb5 = window_mean("reb", 5, "reb_last5")
    ast5 = window_mean("ast", 5, "ast_last5")

    base = (
        logs_before.sort_values("game_date")
        .groupby(["player_id", "team"], as_index=False)
        .tail(1)[["player_id", "player_name", "team", "game_date"]]
    )

    feats = base.merge(mp3, on=["player_id", "team"], how="left") \
                .merge(mp10, on=["player_id", "team"], how="left") \
                .merge(pts5, on=["player_id", "team"], how="left") \
                .merge(reb5, on=["player_id", "team"], how="left") \
                .merge(ast5, on=["player_id", "team"], how="left")

    # Simple usage proxy; refine later
    feats["usage_last10"] = (feats["pts_last5"] + feats["reb_last5"] + feats["ast_last5"]) / feats["mp_last10"].clip(lower=1)

    if cfg.pace_path and cfg.pace_path.exists():
        pace = pd.read_csv(cfg.pace_path)
        if "team" in pace.columns and "pace_last10" in pace.columns:
            feats = feats.merge(
                pace[["team", "pace_last10"]],
                on="team",
                how="left",
            )
            feats = feats.rename(columns={"pace_last10": "team_pace_last10"})
    else:
        feats["team_pace_last10"] = None

    return feats


def save_features(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() in {".parquet", ".pq"}:
        df.to_parquet(out_path, index=False)
    else:
        df.to_csv(out_path, index=False)
    print(f"[features_nba_v0] wrote {out_path} rows={len(df)}")


def main() -> None:
    cfg = parse_args()
    feats = build_features(cfg)
    save_features(feats, cfg.out_path)


if __name__ == "__main__":
    main()
EOF

###############################################################################
# scripts/nba/join_nba_v0.py
###############################################################################
cat > scripts/nba/join_nba_v0.py <<'EOF'
#!/usr/bin/env python3
"""
Join NBA board + features + placeholder model to produce joined_{DAY}.csv.

This is v0.1 and uses a simple logistic transform of (recent stat - line) as a
stand-in for a real model. See docs/slp/nba_adapter_v0.md and Data Model v1.2.
"""

import argparse
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


def load_board(path: Path) -> pd.DataFrame:
    df = pd.read_json(path)
    required = ["player_name", "team", "game_date", "market", "line", "odds_type"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing board columns: {missing}")
    return df


def load_features(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    return pd.read_csv(path)


def join_board_feats(board: pd.DataFrame, feats: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    key = ["player_id", "team"] if "player_id" in board.columns else ["player_name", "team"]
    joined = board.merge(feats, on=key, how="left", suffixes=("", "_feat"))
    missing = joined[joined["mp_last3"].isna()].copy()
    return joined, missing


def simple_p_hit(row: pd.Series) -> float:
    market = str(row.get("market", "")).lower()
    line = float(row.get("line", 0.0) or 0.0)
    stat = row.get("pts_last5", np.nan)
    if "reb" in market:
        stat = row.get("reb_last5", np.nan)
    elif "ast" in market:
        stat = row.get("ast_last5", np.nan)
    if pd.isna(stat):
        return 0.5
    k = 0.25
    delta = float(stat) - line
    return float(1.0 / (1.0 + np.exp(-k * delta)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Join NBA board + features + model stub.")
    parser.add_argument("--day", required=True, help="Day (YYYY-MM-DD)")
    parser.add_argument("--board-path", required=True)
    parser.add_argument("--features-path", required=True)
    parser.add_argument("--out-path", required=True)
    args = parser.parse_args()

    board_path = Path(args.board_path)
    feats_path = Path(args.features_path)
    out_path = Path(args.out_path)

    board = load_board(board_path)
    feats = load_features(feats_path)
    joined, missing = join_board_feats(board, feats)
    if not missing.empty:
        miss_path = out_path.with_name("missing_features.csv")
        missing.to_csv(miss_path, index=False)
        print(f"[join_nba_v0] WARNING: {len(missing)} rows missing features; wrote {miss_path}")

    joined = joined.copy()
    joined["p_hit"] = joined.apply(simple_p_hit, axis=1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joined.to_csv(out_path, index=False)
    print(f"[join_nba_v0] wrote {out_path} rows={len(joined)}")


if __name__ == "__main__":
    main()
EOF

###############################################################################
# config/markets/nba.yml
###############################################################################
cat > config/markets/nba.yml <<'EOF'
# NBA market configuration (v0.1)

markets:
  - id: points
    provider_codes: ["PTS"]
    stat_col: "pts"
    description: "Points"
  - id: rebounds
    provider_codes: ["REB"]
    stat_col: "reb"
    description: "Rebounds"
  - id: assists
    provider_codes: ["AST"]
    stat_col: "ast"
    description: "Assists"
  - id: threes
    provider_codes: ["3PM", "3PTM"]
    stat_col: "fg3m"
    description: "3-Point Field Goals Made"
  - id: pra
    provider_codes: ["PRA"]
    stat_col: "pts+reb+ast"
    description: "Points + Rebounds + Assists"

feature_sets:
  - id: nba_core_v0
    applies_to: ["points","rebounds","assists","threes","pra"]
    features:
      - mp_last3
      - mp_last10
      - usage_last10
      - team_pace_last10
      - pts_last5
      - reb_last5
      - ast_last5
EOF

###############################################################################
# scripts/nba/run_golden_nba.sh
###############################################################################
cat > scripts/nba/run_golden_nba.sh <<'EOF'
#!/usr/bin/env bash
# Run NBA Golden Day v0.1 pipeline for a given DAY (YYYY-MM-DD).
set -euo pipefail

DAY="${1:-}"
if [[ -z "$DAY" ]]; then
  echo "Usage: $0 YYYY-MM-DD"
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

RUN_DIR="runs/nba/${DAY}"
RAW_BOARD="data/nba/boards/${DAY}/prizepicks_board_${DAY}.json"
GAMELOGS="data/nba/gamelogs/gamelogs_2024.csv"   # TODO: adjust season
FEATURES_PATH="${RUN_DIR}/features_nba_v0.parquet"
BOARD_PATH="${RUN_DIR}/board_${DAY}.json"
JOINED_PATH="${RUN_DIR}/joined_${DAY}.csv"

echo "[nba_golden] DAY=${DAY}"
echo "[nba_golden] ROOT=${ROOT}"

# 1) Ingest board (file-first; no network)
python3 scripts/nba/ingest_nba_board.py \
  --day "${DAY}" \
  --raw-path "${RAW_BOARD}" \
  --out-dir "${RUN_DIR}"

# 2) Build features
python3 features/features_nba_v0.py \
  --day "${DAY}" \
  --gamelogs-path "${GAMELOGS}" \
  --out-path "${FEATURES_PATH}"

# 3) Join + placeholder model
python3 scripts/nba/join_nba_v0.py \
  --day "${DAY}" \
  --board-path "${BOARD_PATH}" \
  --features-path "${FEATURES_PATH}" \
  --out-path "${JOINED_PATH}"

echo "[nba_golden] TODO: hook slipbuilder v2 (code_utils_slipbuilder_v2.py) for NBA."
echo "[nba_golden] TODO: emit STATE.json, CHECKS.md, FINGERPRINTS.txt, outcomes summary, freeze manifest."

echo "[nba_golden] Completed v0.1 skeleton for ${DAY}."
EOF

chmod +x scripts/nba/run_golden_nba.sh

echo "[install_nba_v0] Done. Review new files, then run:"
printf '  git status\n'
printf '  git add docs/slp/nba_adapter_v0.md scripts/nba/*.py features/features_nba_v0.py config/markets/nba.yml scripts/nba/run_golden_nba.sh\n'
printf '  git commit -m "feat: add NBA v0.1 golden day skeleton"\n'
printf '  git push -u origin <your-nba-branch> && gh pr create --fill --base main\n'
