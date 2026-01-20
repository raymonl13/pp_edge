#!/usr/bin/env bash
set -euo pipefail

DAY="${1:-$(date +%F)}"

echo "[run_golden_v1] DAY=${DAY}"

# 1) Ingest PrizePicks NBA board (raw JSON should already be at this path)
python3 scripts/nba/ingest_nba_board.py \
  --day "${DAY}" \
  --raw-path "data/pp_board/sport=nba/day=${DAY}/pp_raw.json"

# 2) Join with season features
python3 scripts/nba/join_nba_season_v0.py --day "${DAY}"

# 3) Add p_hit stub from season stats
python3 scripts/nba/add_p_hit_v0.py --day "${DAY}"

# 4) Rank legs by edge_over = p_hit - 0.5
python3 scripts/nba/rank_nba_edges_v0.py --day "${DAY}"

# 5) Build slips via SlipBuilder v2 (Power6/Power4)
python3 scripts/nba/build_slips_nba_v0.py --day "${DAY}"

# 6) (NB-M1) Bankroll skeleton: flat stakes + caps
python3 scripts/nba/size_nba_bankroll_v0.py --day "${DAY}"

echo "[run_golden_v1] done. Artifacts under runs/nba/${DAY}:"
ls -1 "runs/nba/${DAY}"
