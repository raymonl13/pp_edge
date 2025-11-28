#!/usr/bin/env bash
# Run NBA Golden Day v0.1 pipeline for a given DAY (YYYY-MM-DD).
# v0.1 semantics:
# - Raw board: data/pp_board/sport=nba/day=$DAY/pp_raw.json
# - Ingest -> runs/nba/$DAY/board_$DAY.json
# - Join vs season features -> joined_$DAY.csv
# - Stub p_hit (v0) -> joined_with_phit_$DAY.csv
# - Prefilter (1 leg/player, K<=60) -> ..._prefilter.csv
# - Build slips (Points-only) -> slips_nba_v0.{json,csv}
# - Size bankroll (header-safe 0-slip) -> slips_nba_v0_sized.csv

set -euo pipefail

DAY="${1:-}"
if [[ -z "$DAY" ]]; then
  echo "Usage: $0 YYYY-MM-DD"
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

RUN_DIR="runs/nba/${DAY}"
RAW_BOARD="data/pp_board/sport=nba/day=${DAY}/pp_raw.json"

echo "[nba_golden_v0.1] DAY=${DAY}"
echo "[nba_golden_v0.1] ROOT=${ROOT}"
echo "[nba_golden_v0.1] RUN_DIR=${RUN_DIR}"
echo "[nba_golden_v0.1] RAW_BOARD=${RAW_BOARD}"

# 0) Sanity check: raw board exists
if [[ ! -f "${RAW_BOARD}" ]]; then
  echo "[nba_golden_v0.1] ERROR: raw board not found at ${RAW_BOARD}" >&2
  exit 2
fi

mkdir -p "${RUN_DIR}"

# 1) Ingest board (file-first; no network)
python3 scripts/nba/ingest_nba_board.py \
  --day "${DAY}" \
  --raw-path "${RAW_BOARD}"

# 2) Join vs season features (uses season_2025_features.csv per NBA adapter)
python3 scripts/nba/join_nba_season_v0.py \
  --day "${DAY}"

# 3) Stub p_hit (v0) + edge_pp
python3 scripts/nba/add_p_hit_v0.py \
  --day "${DAY}"

# 4) Candidate prefilter (1 leg/player, K<=60)
python3 scripts/nba/prepare_candidates_nba_v0.py \
  --day "${DAY}" \
  --top-k 60

# 5) Build slips (Points-only, method-adaptive SlipBuilder)
python3 scripts/nba/build_slips_nba_v0.py \
  --day "${DAY}" \
  --config "config_pp_edge_v6.8.yaml" \
  --markets points

# 6) Size bankroll (header-safe on 0-slip days)
python3 scripts/nba/size_bankroll_v0.py \
  --day "${DAY}" \
  --budget 100 \
  --stake 10

echo "[nba_golden_v0.1] Completed NBA v0.1 pipeline for ${DAY}."
