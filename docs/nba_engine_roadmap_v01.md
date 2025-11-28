# NBA Engine Roadmap — v0.1 (FAST-LANE)

_Last updated: 2025-11-27_

This roadmap outlines the **fast-lane** build-out of the NBA PrizePicks engine.
It assumes:

- Daily SLP flow handles **ops** (Lane A).
- Engine design & QA live in this design thread + the repo (Lane B).
- The repo (code + docs) is the source of truth, not chat history.

We split the engine into layers and phases.

---

## 1. Engine Layers

1. **Data & Mapping**
   - Board ingest, features, ESPN mapping, label coverage.
2. **Probability Modeling (p_hit)**
   - Models that map features → P(prop hits).
3. **Pricing & EV**
   - Slip-level EV using p_hit + payout ladders (odds_type, slip_type).
4. **Selection & Slips**
   - Slip-building and filtering logic.
5. **Bankroll & Risk**
   - Stake sizing, exposure caps, portfolio behavior.

We maintain two lanes:

- **Lane A (Production)**: what Daily SLP uses by default.
- **Lane B (Experimental)**: new models/logic tested side-by-side before promotion.

---

## 2. Phases (NB-F0 → NB-F7)

### NB-F0 – Baseline v1 Lock-in (DONE)

**Goal:** Have a live, honest v1 engine we can use now for NBA Points.

- v1 p_hit model:
  - Logistic regression on `line` only.
  - Trained on ~1,661 labeled Points props from 5 days with acceptable coverage:
    - 2025-11-13, 11-19, 11-21, 11-24, 11-25
  - Low-coverage days (2025-11-16, 11-18) are quarantined from training.

- edge_pp:
  - `edge_pp = p_hit - 0.5` (crude per-leg edge measure).

- Slip filter (Lane A):
  - `filter_slips_nba_v0.py`
  - Keeps only slips where every leg satisfies:
    - `p_hit ≥ 0.52`
    - `edge_pp ≥ 0.02`
  - Filtered slips = A-set; unfiltered slips remain available for analysis.

- Coverage & slip metrics:
  - `report_training_days_v0.py` → per-day label coverage.
  - `report_slip_filter_metrics_v0.py` → original vs filtered slips per day.

Daily SLP uses this v1 + filter as the baseline engine today.

---

### NB-F1 – Full-board Calibration & Coverage Gating (NEXT)

**Goal:** Understand how well v1 p_hit aligns with reality across the entire Points board, not just slip legs.

**Tasks:**

- Implement `scripts/nba/eval_board_nba_v0.py`:
  - For a given day:
    - Load `joined_with_phit_<DAY>.csv` and `points_train_<DAY>.csv`.
    - Filter to Points market.
    - Merge on (player, team, line).
    - Bin props by p_hit (e.g., [0.45,0.5], [0.5,0.55], [0.55,0.6], [0.6,0.65], [0.65,0.7], (0.7,1.0]).
    - For each bin:
      - `n`, `avg_p_hit`, `actual_hit_rate`, `avg_edge_pp`.
      - Also compute a Brier score for the day.

- Run on several high-coverage days (e.g., 2025-11-19, 11-21, 11-24).

**Decisions to derive from F1:**

- Which p_hit bands are “trustworthy” (roughly calibrated).
- Whether the current `p_hit ≥ 0.52` per-leg filter band is appropriate.
- Whether to introduce a per-day “calibration trust” flag:
  - Days with low coverage and poor calibration are low-trust for tuning (but may still be playable).

Lane impact:

- Lane A remains v1 + current filter for now.
- F1 runs in Lane B and feeds into future threshold and model decisions.

---

### NB-F2 – Points Model v2 (Feature-rich Logistic + Tree-based Experiment)

**Goal:** Move from “line-only” p_hit to “context-aware” p_hit without sacrificing calibration.

**Tasks:**

1. Define a v2 feature set for Points:
   - `line`
   - `minutesPg` or a minutes projection
   - `points_per_game` (stat_ppg)
   - `usage_pct`
   - `pace_proj` or game total proxy
   - optional: home/away, role flags

2. Extend training and inference:
   - Add `train_hit_prob_points_v2.py` (or a v2 mode in the v1 script).
   - Add `add_p_hit_v2.py` (or extend v1) to compute `p_hit_v2` for Points props.

3. (Experimental) Train a tree-based model (e.g., GBM/XGBoost/LightGBM) on the same features:
   - Evaluate via full-board calibration.
   - Do not promote tree-only model to Lane A until we see clear, consistent value.

**QA:**

- Use `eval_board_nba_v0.py` to compare v1 vs v2 (and optionally GBM) across several days:
  - p_hit calibration across bins.
  - Brier scores.

**Lane behavior:**

- During F2:
  - Lane A: v1 p_hit + current filter.
  - Lane B: v2 (and tree model) run in shadow, used for eval and optional experimental slip sets.

**Exit criteria:**

- Documented decision on whether Points v2 logistic becomes the A-lane p_hit model.
- Updated engine status doc specifying which model and features are in use.

---

### NB-F3 – EV Core for Standard Slips

**Goal:** Replace `edge_pp` as the main slip decision metric with true, payout-aware EV for **standard odds_type**.

**Tasks:**

1. Configure NBA payout ladders (standard odds_type):
   - For each slip_type (Power3, Power4, Flex5, Flex6, etc.):
     - Define payout multipliers for each hit-count scenario.

2. Implement slip EV calculator:
   - `ev_slip_nba_v0.py` (or integrated into builder).
   - For a slip:
     - Use per-leg p_hit and independence assumption to compute P(k hits).
     - EV = Σ P(k) * payout_k - stake.

3. Integrate EV into slip selection:
   - Keep per-leg p_hit/edge thresholds as a coarse guard.
   - Add slip-level EV requirement (e.g., EV ≥ 1.05 for standard slips).

**QA:**

- For multiple days, compare:
  - Slip sets chosen by edge_pp-only rules vs EV rules.
  - Realized returns / hit behavior (even with small stakes).

**Lane behavior:**

- Initially:
  - Lane A: edge_pp-based filter.
  - Lane B: EV-based filter.
- After sufficient evidence, promote EV gating to Lane A.

---

### NB-F4 – Demon/Goblin Integration & Tier Caps

**Goal:** Make demon/goblin (odds_type) first-class in EV and risk.

**Tasks:**

1. Extend payout config to account for:
   - `(slip_type, odds_type)` ladders for standard, goblin, demon.

2. Extend EV calculation:
   - EV now uses correct payout ladder based on odds_type.

3. Tier caps and policies:
   - Configurable limits for:
     - Number of demon legs per slip.
     - Demon/goblin share of daily EV / stakes.
     - Possibly higher EV thresholds for demon slips.

4. Integrate into filter and selection:
   - Adjust thresholds and EV cuts per odds_type.
   - Consider separate A/B lanes for demon vs standard until performance is understood.

---

### NB-F5 – Bankroll v1 (Kelly-lite + Risk Controls)

**Goal:** Move from flat stakes to risk-aware staking and portfolio management.

**Tasks:**

1. Bankroll module for NBA:
   - Use EV and “win” probability to compute fractional Kelly stakes.
   - Define personas (conservative, standard, aggressive) via Kelly fractions and stake caps.

2. Monte Carlo bankroll simulations:
   - Stress-test bankroll trajectories given slip EV distribution and planned volume.

3. Risk and exposure caps:
   - Max % bankroll staked per day.
   - Max stake per slip.
   - Limits by slip_type and odds_type (e.g., demon exposure).

**Lane behavior:**

- Initially B-lane:
  - Bankroll recommendations are logged and evaluated; A-lane may still use fixed stakes.
- After confidence, adopt Bankroll v1 policies into A-lane.

---

### NB-F6 – Prop-type Expansion (Beyond Points)

**Goal:** Expand to additional NBA markets while keeping quality and calibration.

**Tasks:**

1. Prioritize new markets:
   - Likely: 3PM (threes made), PRA or Fantasy Score.

2. For each market:
   - Build a v1 p_hit model with appropriate features.
   - Run coverage and full-board calibration.
   - Integrate into EV calculations and slip builder.

3. Slip composition rules:
   - Limit number of high-variance legs (e.g., 3PM) per slip.
   - Use robust markets (Points, PRA) as anchors in slips.

---

### NB-F7 – Advanced Modeling (Tree-based, GLMM, Correlation)

**Goal:** Apply more advanced statistical machinery where it clearly adds value.

**Tasks:**

1. Tree-based models:
   - Train GBM/XGBoost/LightGBM on feature-rich data.
   - Calibrate and compare vs logistic.
   - Potential hybrid approaches (logistic + tree corrections).

2. Hierarchical/GLMM models:
   - Incorporate player/team random effects for better handling of low-sample players and new roles.

3. Correlation modeling:
   - Heuristics for same-game correlation and exposure.
   - More formal correlation structures if needed (later).

**Note:** F7 is a later-phase optimization, not a blocker for F1–F6.

---

This roadmap is intentionally ambitious but layered so that:

- We **keep betting with v1** while we improve the brain.
- We introduce EV, demon/goblin logic, and bankroll policies in a measured order.
- We avoid “re-skeletonizing” by documenting engine state and promoting changes only when evidence supports them.
