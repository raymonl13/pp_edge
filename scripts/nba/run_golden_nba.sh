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
