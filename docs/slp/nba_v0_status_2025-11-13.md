# NBA v0.1 Status — 2025-11-13

## Artifacts
- Raw PP: data/pp_board/sport=nba/day=2025-11-13/pp_raw.json
- Board (normalized): runs/nba/2025-11-13/board_2025-11-13.json
- Joined: runs/nba/2025-11-13/joined_2025-11-13.csv
- Joined+p_hit: runs/nba/2025-11-13/joined_with_phit_2025-11-13.csv
- Ranked: runs/nba/2025-11-13/ranked_edges_2025-11-13.csv
- Slips: runs/nba/2025-11-13/slips_nba_v0.{csv,json}
- Sizing: runs/nba/2025-11-13/slips_nba_v0_sized.csv

## Rules (v0.1)
- No duplicate players per slip (hard).
- Demon quotas relaxed for NBA (6 per slip / 999 per day in wrapper).
- Per-game cap OFF.
- Candidate pool: top-K by edge_pp (K=25 default; consider 40 for NBA).
- Markets allowed: points, rebounds, assists, PRA/PR/PA/RA variants, 3pt made, fantasy score.

## Next
- NB-M1: finalize runner v1 + flat-stake sizing merged.
- NB-M2: points-only p_hit_v1 (logistic) with small historical set; compare to stub.
- NB-M3: mapping/alias coverage + gates.
