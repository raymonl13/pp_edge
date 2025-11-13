# Payout Ladders & odds_type (v1)

- PrizePicks provides different payout classes via `odds_type` (e.g. standard, goblin, demon).
- In PP-EDGE, `odds_type` does **not** change probabilities; it selects the payout ladder used for EV.
- Ladders are configured in `config_pp_edge_v6.8.yaml` (or a dedicated config) under a `payout_ladders` section keyed by odds_type and leg count.
- Some classes (e.g. demon/goblin) may be More-only in the book; the builder must enforce these book constraints when assembling slips.
