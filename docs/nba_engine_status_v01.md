# NBA Engine Status — v0.1 (STATUS SNAPSHOT)

_Last updated: 2025-11-27_

This document is the **current snapshot** of the NBA PrizePicks engine.
It describes what is in **Production (Lane A)** and what is **Experimental (Lane B)**.

It does **not** try to record history; only “what is true today.”

---

## 1. Lanes

- **Lane A (“Production”)**
  - Used by the Daily SLP flow.
  - Conservative, documented, and trusted.

- **Lane B (“Experimental”)**
  - Used for side-by-side experiments (new models, thresholds, EV logic, etc.).
  - Nothing in Lane B is assumed to be correct until promoted.

---

## 2. Data & Mapping (Lane A)

- Board ingest:
  - `scripts/nba/ingest_nba_board.py` ingests PP JSON from:
    - `data/pp_board/sport=nba/day=YYYY-MM-DD/pp_raw.json`
  - Writes normalized board to:
    - `runs/nba/<DAY>/board_<DAY>.json`

- Join with season features:
  - `scripts/nba/join_nba_season_v0.py`
  - Uses `data/nba/features/season_2025_features.csv`
  - Output:
    - `runs/nba/<DAY>/joined_<DAY>.csv`

- Add stub/model probabilities:
  - `scripts/nba/add_p_hit_v1.py`
  - Input:
    - `runs/nba/<DAY>/joined_<DAY>.csv`
  - Output:
    - `runs/nba/<DAY>/joined_with_phit_<DAY>.csv`
  - Adds:
    - `p_hit` (per-leg P(actual_points > line))
    - `edge_pp = p_hit - 0.5`

- ESPN labeler:
  - `scripts/nba/build_points_train_from_espn_v0.py`
  - Inputs:
    - `runs/nba/<DAY>/joined_with_phit_<DAY>.csv`
  - Outputs:
    - Labeled rows: `data/nba/modeling/daily/points_train_<DAY>.csv`
    - Unmatched rows: `data/nba/modeling/unmatched/unmatched_points_<DAY>.csv`

- Coverage reporting:
  - `scripts/nba/report_training_days_v0.py`
  - Output:
    - `data/nba/modeling/training_days_report_v0.csv`
  - Current coverage snapshot (approx):
    - GOOD: 2025-11-13, 2025-11-19, 2025-11-21, 2025-11-24
    - MEDIUM: 2025-11-25
    - BAD (quarantined from training): 2025-11-16, 2025-11-18

---

## 3. p_hit Model (Lane A)

- Model file:
  - `model_assets/model_v1.pkl`
- Training script:
  - `scripts/nba/train_hit_prob_points_v1.py`
- Training data:
  - `data/nba/modeling/points_train_v1.csv`
  - ~1,661 labeled Points props across days:
    - 2025-11-13, 2025-11-19, 2025-11-21, 2025-11-24, 2025-11-25
  - **Excluded from training:** 2025-11-16, 2025-11-18 (moved to `data/nba/modeling/daily_low_coverage/`)

- Model type:
  - Custom logistic regression implemented in `code_utils_model_v1.py`
  - **Features (v1):** `line` only

- Outputs (added by `add_p_hit_v1.py`):
  - `p_hit`: estimated P(actual_points > line)
  - `edge_pp = p_hit - 0.5` (crude edge proxy)

---

## 4. Slip Builder & Filter (Lane A)

- Candidate preparation:
  - `scripts/nba/prepare_candidates_nba_v0.py`
  - Output:
    - `runs/nba/<DAY>/joined_with_phit_<DAY>_prefilter.csv`
  - Typically top K candidates per day (e.g., K=60).

- Slip builder:
  - `scripts/nba/build_slips_nba_v0.py`
  - Inputs:
    - Prefiltered candidates (Points-only for NBA v0.1)
  - Outputs:
    - `runs/nba/<DAY>/slips_nba_v0.json`
    - `runs/nba/<DAY>/slips_nba_v0.csv`
  - Semantics:
    - `slip_type` (e.g., Power4)
    - `odds_type` (standard/goblin/demon)
    - Same-game allowed
    - No duplicate players per slip

- Sizing (Lane A is flat stake):
  - `scripts/nba/size_bankroll_v0.py`
  - Flat stake per slip (e.g., $10), full budget spend (e.g., $100 per day)

- **Filter (Lane A — A-set definition):**
  - `scripts/nba/filter_slips_nba_v0.py`
  - For each slip:
    - Expand legs
    - Join to `joined_with_phit_<DAY>.csv`
    - Require **for every leg**:
      - `p_hit ≥ 0.52`
      - `edge_pp ≥ 0.02`
  - Outputs:
    - `runs/nba/<DAY>/slips_nba_v0_filtered.csv`
    - `runs/nba/<DAY>/slips_nba_v0_sized_filtered.csv`
  - A-set = filtered slips; unfiltered = full slip set.

---

## 5. Evaluation & Reporting (Lane A)

- Slip-level eval:
  - `scripts/nba/eval_slips_nba_v0.py`
  - Inputs:
    - `joined_with_phit_<DAY>.csv`
    - `points_train_<DAY>.csv`
    - Slips CSV (unfiltered by default, or `--slips-file` for filtered slips)
  - Behavior:
    - Expands slip legs
    - Joins in p_hit / edge_pp and labels
    - Prints:
      - Leg-level table: player, team, market, line, p_hit, edge_pp, actual_points, hit
      - Slip-level outcomes (`slip_all_hit`: 1/0/None)
      - Calibration by p_hit bin (on labeled legs)

- Slip filter metrics:
  - `scripts/nba/report_slip_filter_metrics_v0.py`
  - For each labeled day:
    - `n_slips_orig`, `n_slips_filt`
    - `n_legs_orig_labeled`, `hit_rate_orig`
    - `n_legs_filt_labeled`, `hit_rate_filt`
  - Output:
    - `data/nba/modeling/slip_filter_report_v0.csv`

---

## 6. Known Limitations (v0.1)

- p_hit model v1:
  - Uses only `line` (no minutes, usage, opponent, pace, etc.).
  - No separate models for other markets (3PM, PRA, Fantasy Score, etc.).

- EV:
  - No explicit slip-level EV yet.
  - `edge_pp = p_hit - 0.5` is only a crude proxy.

- odds_type (standard/goblin/demon):
  - Carried through as a column.
  - Not yet used for odds_type-aware EV or exposure caps.

- Bankroll:
  - Flat stake per slip.
  - No Kelly / fractional Kelly or bankroll-aware stake sizing for NBA yet.

- Correlation:
  - Legs are treated as independent in selection/filtering.
  - No explicit same-game correlation modeling.

---

## 7. Next Planned Phase (Lane B / Design)

- **NB-F1 – Full-board calibration & coverage gating**
  - Implement `scripts/nba/eval_board_nba_v0.py` to:
    - Merge the full board (Points) with labels.
    - Bin by p_hit.
    - Compare `avg_p_hit` vs `actual_hit_rate` and compute Brier score.
  - Use F1 results to:
    - Validate or adjust the `p_hit ≥ 0.52` band used in the filter.
    - Identify trustworthy p_hit ranges and days for tuning.
