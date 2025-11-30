#!/usr/bin/env bash
set -euo pipefail

DAY="${1:-$(date +%F)}"

echo "[run_golden_nba_v0] DAY=${DAY}"

# 1) Ingest PrizePicks board (raw JSON assumed present under data/pp_board)
python3 scripts/nba/ingest_nba_board.py \
  --day "${DAY}" \
  --raw-path "data/pp_board/sport=nba/day=${DAY}/pp_raw.json"

# 2) Join with season features
python3 scripts/nba/join_nba_season_v0.py --day "${DAY}"

# 3) Add p_hit stub
python3 scripts/nba/add_p_hit_v0.py --day "${DAY}"

# 4) Rank edges
python3 scripts/nba/rank_nba_edges_v0.py --day "${DAY}"

echo "[run_golden_nba_v0] done. Artifacts under runs/nba/${DAY}:"
ls -1 "runs/nba/${DAY}"
