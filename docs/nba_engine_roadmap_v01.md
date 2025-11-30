# NBA Engine Roadmap — v0.1 (FAST-LANE)

_Last updated: 2025-11-27_

This roadmap outlines the **fast-lane** build-out of the NBA PrizePicks engine.
It assumes:

- The **Daily SLP** chat handles **ops (Lane A)** and only runs **Production** scripts.
- This “NBA Engine” lane (design thread + repo) handles **Lane B (Experimental)**: models, EV logic, filters, bankroll, roadmap evolution.
- The repo (code + docs + tags) is the source of truth; ChatGPT is a stateless brain that reads the repo.

We split the engine into layers and phases.

---

## 1. Engine Layers & Lanes

### Layers

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

### Lanes

- **Lane A (Production / Daily SLP)**
  - Used by Daily SLP chats to run today’s slate.
  - Only uses scripts and behaviors explicitly marked as Production.
  - Never calls Experimental (Lane B) scripts unless explicitly promoted.

- **Lane B (Experimental / Engine)**
  - Used in NBA Engine design threads.
  - Hosts new models, EV logic, filters, bankroll experiments.
  - Changes are only promoted to Lane A after:
    - Code is implemented and QA’d on real slates.
    - Docs updated.
    - A git tag is created.

---

## 2. Phases (NB-F0 → NB-F7)

### NB-F0 – Baseline v1 Lock-in (DONE)

**Goal:** Have a live, honest v1 engine we can use now for NBA Points.

- v1 p_hit model:
  - Logistic regression on `line` only.
  - Trained on ~1,661 labeled Points props from 5 days with acceptable coverage:
    - 2025-11-13, 2025-11-19, 2025-11-21, 2025-11-24, 2025-11-25
  - Low-coverage days (2025-11-16, 2025-11-18) are quarantined from training
    into `data/nba/modeling/daily_low_coverage/`.

- edge_pp:
  - `edge_pp = p_hit - 0.5` (crude per-leg edge measure; not payout-aware).

- Slip filter (Lane A):
  - `scripts/nba/filter_slips_nba_v0.py`
  - Keeps only slips where **every leg** satisfies:
    - `p_hit ≥ 0.52`
    - `edge_pp ≥ 0.02`
  - Filtered slips = A-set; unfiltered slips remain available for analysis.

- Coverage & slip metrics:
  - `scripts/nba/report_training_days_v0.py` → per-day label coverage.
  - `scripts/nba/report_slip_filter_metrics_v0.py` → original vs filtered slips per day.

Daily SLP uses this v1 + filter as the baseline engine today.

---

### NB-F1 – Full-board Calibration & Coverage Gating (IN PROGRESS)

**Goal:** Understand how well v1 p_hit aligns with reality across the entire **Points** board, not just slip legs, and use that to inform thresholds and future models.

**Tasks:**

- Implement `scripts/nba/eval_board_nba_v0.py` (DONE):
  - For a given day:
    - Load `runs/nba/<DAY>/joined_with_phit_<DAY>.csv` and `data/nba/modeling/daily/points_train_<DAY>.csv`.
    - Filter to Points market.
    - Merge on (player, team, line).
    - Bin props by p_hit (e.g., [0.45,0.5], [0.5,0.55], [0.55,0.6], [0.6,0.65], [0.65,0.7], (0.7,1.0]).
    - For each bin:
      - `n`, `avg_p_hit`, `actual_hit_rate`, `avg_edge_pp`.
      - Compute Brier score for the day (lower is better).

- Run on multiple high-coverage days (e.g., 2025-11-19, 11-21, 11-24, 11-26).

**Sample size discipline:**

- Per-bin tuning:
  - Do **not** tune thresholds based on a p_bin with very small sample size.
  - As a rule of thumb:
    - A bin with <50 total props across all evaluated days is considered low-power.
    - Use those bins as qualitative hints only, not for numeric gates.

**Key early observations (from initial F1 runs):**

- In the 0.5–0.6 band for **standard/goblin Points**, v1 is often underconfident:
  - `avg_p_hit` ≈ 0.52–0.57, `actual_hit_rate` often higher (e.g., 0.57–0.69 on some days).
- For **demon Points** in similar bands, v1 can be badly miscalibrated on certain days:
  - Sometimes `avg_p_hit` ≈ 0.52 but `actual_hit_rate` ≈ 0.20–0.33.

**Decisions informed by F1:**

- The current per-leg band (`p_hit ≥ 0.52`) for standard/goblin Points is conservative and acceptable for v0.1.
- Demon props are flagged as a **special risk group**:
  - They may need stricter thresholds or separate handling, which will be addressed explicitly in NB-F4.

**Lane impact:**

- Lane A remains v1 + current per-leg filter for now.
- Lane B uses F1 results for analysis and to design Points v2 (NB-F2) and demon/goblin logic (NB-F4).

---

### NB-F2 – Points Model v2 (Feature-rich Logistic + Tree-based Experiment)

**Goal:** Move from “line-only” p_hit to “context-aware” p_hit without sacrificing calibration.

**Tasks:**

1. Define a v2 feature set for Points (subject to what exists in features/joined CSVs):
   - `line`
   - `minutesPg` or a minutes projection
   - `points_per_game` (stat_ppg)
   - `usage_pct`
   - `pace_proj` or game total proxy
   - optional: home/away, role flags

2. Extend training & inference:
   - Add `train_hit_prob_points_v2.py` (or a v2 mode in the v1 script).
   - Add `add_p_hit_v2.py` (or extend v1) to compute `p_hit_v2` for Points props.
   - Keep v1 p_hit available for comparison.

3. Experimental: tree-based model (e.g., GBM/XGBoost/LightGBM):
   - Same feature set.
   - Evaluate via full-board calibration and Brier scores.
   - Treat as experimental until clearly better.

**QA:**

- Use `eval_board_nba_v0.py` to compare v1 vs v2 (and tree model) across several days:
  - p_hit calibration across bins.
  - Brier scores.
- Only promote v2 logistic (or GBM) to Lane A if:
  - Calibration is at least as good in key bands.
  - Behavior is stable across days.

**Lane behavior:**

- During F2:
  - Lane A: v1 p_hit + current filter.
  - Lane B: v2 (and tree model) run in shadow, used for eval and optional experimental slip sets.

**Exit criteria:**

- Documented decision on whether Points v2 logistic becomes the A-lane p_hit model.
- `nba_engine_status` updated to reflect the chosen model and feature set.
- New git tag created (e.g., `nba-engine-v0.2`).

---

### NB-F3 – EV Core for Standard Slips

**Goal:** Replace `edge_pp` as the main slip decision metric with true, payout-aware EV for **standard odds_type**.

**Tasks:**

1. Configure NBA payout ladders (standard odds_type):
   - In config (e.g., `config_pp_edge_v6.8.yaml` or `config/odds_tables_nba.yaml`):
     - For each slip_type (Power3, Power4, Flex5, Flex6, etc.):
       - Define payout multipliers for each hit-count scenario.

2. Implement slip EV calculator:
   - `ev_slip_nba_v0.py` (or integrated into builder).
   - For a slip:
     - Use per-leg p_hit and independence assumption to compute P(k hits).
     - EV = Σ P(k hits) * payout_k - stake.

3. Integrate EV into slip selection:
   - Keep per-leg p_hit/edge thresholds as a coarse guard.
   - Add slip-level EV requirement (e.g., EV ≥ 1.05) for standard odds_type.

**QA:**

- For multiple days, compare:
  - Slip sets chosen by edge_pp-only rules vs EV-based rules.
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

1. Extend payout config:
   - Ladders for `(slip_type, odds_type)` including standard, goblin, demon.

2. Extend EV calculation:
   - EV now uses the correct payout ladder based on odds_type.

3. Tier caps and policies:
   - Configurable limits for:
     - Number of demon legs per slip.
     - Demon/goblin share of daily EV / stakes.
     - Possibly higher EV thresholds for demon slips vs standard/goblin.

4. Integrate into filter and selection:
   - Adjust thresholds and EV cuts per odds_type.
   - Consider keeping demon-heavy slips in Lane B until their behavior is well understood.

**QA:**

- Track performance and volatility of demon/goblin vs standard slips.
- Use F1 calibration insights to guide demon-specific rules.

---

### NB-F5 – Bankroll v1 (Kelly-lite + Risk Controls)

**Goal:** Move from flat stakes to risk-aware staking and portfolio management.

**Tasks:**

1. Implement bankroll module for NBA:
   - Use EV and slip “win” probabilities to compute fractional Kelly stakes.
   - Define personas (conservative, standard, aggressive) via Kelly fractions and stake caps.

2. Monte Carlo bankroll simulations:
   - Stress-test bankroll trajectories given slip EV distribution and planned volume.

3. Risk and exposure caps:
   - Max % bankroll staked per day.
   - Max stake per slip.
   - Limits by slip_type and odds_type (e.g., demon exposure).

**Lane behavior:**

- Initially B-lane:
  - Bankroll recommendations are logged and evaluated; Lane A may still use fixed stakes.
- After confidence, adopt Bankroll v1 policies into Lane A.

---

### NB-F6 – Prop-type Expansion (Beyond Points)

**Goal:** Expand to additional NBA markets while keeping quality and calibration.

**Tasks:**

1. Prioritize new markets:
   - Likely: 3PM (threes made), and then PRA or Fantasy Score.

2. For each market:
   - Build its own v1 p_hit model with appropriate features.
   - Run coverage and full-board calibration (using `eval_board_nba_v0.py` extended to that market).
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
   - Calibrate and compare vs logistic using full-board eval.
   - Potential hybrid: logistic as baseline, tree model as residual corrector.

2. Hierarchical/GLMM models:
   - Incorporate player/team random effects.
   - Improve modeling for low-sample players and new roles.

3. Correlation modeling:
   - Heuristics for same-game correlation and exposure caps.
   - More formal correlation structures if needed (later).

**Note:** NB-F7 is a later-phase optimization, not a blocker for F1–F6.

---

This roadmap is intentionally ambitious but layered so that:

- We **keep betting with v1** while we improve the brain.
- We introduce calibration (F1), better models (F2), EV (F3), demon/goblin logic (F4), bankroll policies (F5), and new markets (F6) in an ordered, testable way.
- We avoid “re-skeletonizing” by documenting engine state and promoting changes only when evidence supports them.
