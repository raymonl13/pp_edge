# NB‑F2 Evidence Pack Template — Points Model v2

_Last updated: 2025-12-25_

Goal: compare v1 vs v2 on held-out days using eval_board and produce reproducible artifacts.

Required inputs:
- runs/nba/<DAY>/joined_with_phit_<DAY>.csv
- data/nba/modeling/daily/points_train_<DAY>.csv (labels)
- model assets:
  - model_assets/model_v1.pkl (baseline)
  - model_assets/model_points_v2_logit.pkl (new)

Required eval days:
- Training days (GOOD/MEDIUM): list explicitly
- Holdout day(s): list explicitly (never used in training)

Artifacts:
1) Per-day eval_board output for v1 (p_hit)
2) Per-day eval_board output for v2 (p_hit_v2_logit)
3) A single summary table aggregating across days:
   - Brier(v1) vs Brier(v2)
   - calibration error in bands 0.50–0.60 and 0.60–0.70
   - by odds_type (standard/goblin/demon)
4) A written conclusion:
   - Does v2 improve calibration for standard+goblin?
   - Are demon slices still unstable and flagged for NB‑F4?

Promotion rule:
No Lane A changes until the evidence pack shows clear improvement and we tag + document the promotion.

