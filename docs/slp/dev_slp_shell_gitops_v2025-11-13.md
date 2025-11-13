# PP-EDGE Shell & GitOps SLP (v2025-11-13)

## Shell & Scripts
- Scripts must declare a shebang (`#!/usr/bin/env bash` or `python3`).
- Use **RRHM** (Rip-and-Replace Heredoc Mode):
  - Paste-to-create files with **single-quoted** heredocs (`<<'TAG'`).
  - Then run the script separately.
  - Never use `<<TAG | cmd` (no heredocs into pipes).
- Embedded Python:
  - Do not put `${VAR}` inside the Python heredoc.
  - Export variables in bash and read them in Python with `os.environ`.
- Hermetic subshells:
  - For reproducible steps, use `env -i bash --noprofile --norc` so dotfiles and login shell do not affect behavior.

## Git & Hooks
- Pre-push hook:
  - Install into the real hooks dir: `git rev-parse --git-path hooks`, not `.git/hooks`.
  - Hook must be fast and deterministic (e.g. quick unit tests + a light probe/smoke).
- Auth:
  - Use `gh auth login` + `gh auth setup-git` to wire Git to your GitHub token.
  - Never embed a PAT in `remote.origin.url`.
  - If GitHub Push Protection flags a secret, **do not** click "Allow secret":
    - Remove tracked secrets, scrub history with `git-filter-repo`, rotate token, push again.

## Semantic Rails
- Upload→Gate:
  - CI must upload artifacts (edgesheet, rollup, calibration/drift JSON, run_meta) **before** any gating.
  - QA gate only fails when `CSV_ROWS>0` **and** `QA_STATE=FAIL`. Empty slates and skip states are allowed.
- Demon/Goblin (PrizePicks odds types):
  - `odds_type ∈ {standard,goblin,demon}` are **payout classes**, not internal personas.
  - They select a payout ladder (per leg count) from config (see payouts README).
  - Some tiers may be More-only; builder must enforce that where applicable.
