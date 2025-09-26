# PP-EDGE — Unit Seam Contracts (Hermetic Lane)

## Model utils — predict_hit_prob(df, model_path=None)
- Input: DataFrame; missing values OK
- Behavior: loads model via joblib; in unit lane we shim joblib
- Output: 1D probs of length len(df)

## Monte Carlo — simulate(edges, runs, seed, **kwargs)
- Deterministic for a fixed seed
- Accepts kwargs/columns for unit/payout/win_prob depending on signature
- Output: numeric vector/summary consistent across runs

## Bankroll stake — size_bet(..., bankroll_state=..., **kwargs)
- Signature may require bankroll_state
- Zero/negative edge → near-zero stake; positive edge → non-negative

## Unit-lane harness
- Feature functions are stubbed in conftest before product imports
- tests/unit/_fixtures.py provides contract-complete tiny frames
