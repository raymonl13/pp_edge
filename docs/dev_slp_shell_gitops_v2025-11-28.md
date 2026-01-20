# PP-EDGE Shell & GitOps SLP (v2025-11-28)

## Shell & Scripts
- Scripts must declare a shebang (`#!/usr/bin/env bash` or `python3`).
- Use **RRHM** (Rip-and-Replace Heredoc Mode) for repo code and handoffs:
  - Paste-to-create files with **single-quoted** heredocs (`cat <<'TAG' > path/to/file`).
  - Then run the resulting script or command as a **separate step**.
  - Never use `<<TAG | cmd` (no heredocs into pipes).
- **No notebook / Colab magics in repo code:**
  - Do **not** emit `%%writefile`, `!pip`, `%run`, or other notebook magics into tracked files.
  - All code handoffs must be RRHM-compatible: a single heredoc that writes the file, plus separate run commands.
- Bash **bracketed paste mode** (shell ergonomics):
  - Purpose: when you paste a multi-line block into the terminal, it should appear as a single editable block and **not execute until you press Enter**.
  - RRHM remains the primary safety rail; bracketed paste is an ergonomics upgrade on top.
- Embedded Python:
  - Do not put `${VAR}` inside the Python heredoc.
  - Export variables in bash and read them in Python with `os.environ`.
- Hermetic subshells:
  - For reproducible steps, use `env -i bash --noprofile --norc` so dotfiles and login shell do not affect behavior.

## Git & Hooks
...
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

## Operator Workstation Config (shell ergonomics)
- Default shell for SLP runs:
  - Use `bash` for PP-EDGE SLP sessions. If your login shell is `zsh`, start a fresh session with `bash` before running SLP commands.
- Enable Bash bracketed paste mode:
  - Ensure you have a `$HOME/.inputrc` file (create it if necessary) with:
    - `set enable-bracketed-paste on`
  - After editing `~/.inputrc`, open a new terminal window/tab or, in an existing Bash session, run:
    - `bind 'set enable-bracketed-paste on'`
  - Expected behavior: pasting a multi-line block shows the entire block at the prompt; the block only runs after you press Enter.
- If a terminal does not respect bracketed paste:
  - Fall back on SLP guarantees:
    - Always use RRHM handoffs for code (heredocs that write files, then run the file).
    - Avoid pasting ad-hoc multi-line commands directly into a live prompt.

## Troubleshooting & Debugging
- For pipeline-level debugging and triage, follow:
  - **PP-EDGE — Troubleshooting & Ops Playbook (v1.1)** (canonical doc for debugging flows).
- General debugging pattern:
  - Check coverage with `scripts/nba/report_training_days_v0.py`.
  - Use `scripts/nba/eval_slips_nba_v0.py` to inspect slip legs (p_hit, edge_pp, hit).
  - Use `scripts/nba/eval_board_nba_v0.py` to inspect full-board calibration (p_hit vs actual).
