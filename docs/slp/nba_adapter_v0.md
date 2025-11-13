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
