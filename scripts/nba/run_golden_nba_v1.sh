#!/usr/bin/env bash
set -euo pipefail

DAY="${1:-$(date +%F)}"

echo "[run_golden_nba_v1] DAY=${DAY}"

python3 scripts/nba/ingest_nba_board.py \
  --day "${DAY}" \
  --raw-path "data/pp_board/sport=nba/day=${DAY}/pp_raw.json"

python3 scripts/nba/join_nba_season_v0.py --day "${DAY}"

python3 scripts/nba/add_p_hit_v0.py --day "${DAY}"

python3 scripts/nba/rank_nba_edges_v0.py --day "${DAY}"

python3 scripts/nba/build_slips_nba_v0.py --day "${DAY}"

echo "[run_golden_nba_v1] done. Artifacts under runs/nba/${DAY}:"
ls -1 "runs/nba/${DAY}"
