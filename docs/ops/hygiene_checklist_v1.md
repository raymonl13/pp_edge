# Hygiene Checklist (v1)

Use this before calling a change "done".

## Shell & Hooks
- [ ] All new scripts have a proper shebang and use `set -euo pipefail` as appropriate.
- [ ] Heredocs are single-quoted (`<<'TAG'`); no heredocs are piped into other commands.
- [ ] Embedded Python reads environment via `os.environ`; no `${VAR}` inside the heredoc.
- [ ] Pre-push hooks are installed via `git rev-parse --git-path hooks` (worktree-safe), not `.git/hooks`.

## Git & Auth
- [ ] `git remote -v` shows clean HTTPS URLs (no tokens in the remote).
- [ ] `gh auth setup-git` has been run; pushes use GitHub token, not embedded PATs.
- [ ] If Push Protection flagged a secret, history was scrubbed and token rotated (never "Allow secret").

## CI & Evidence
- [ ] Unit lane is hermetic (PP_EDGE_TEST_MODE=1; no network).
- [ ] CI uploads artifacts before gates (edgesheet, rollup, calibration/drift JSON, run_meta).
- [ ] QA gate only fails when `CSV_ROWS>0 AND QA_STATE=FAIL`.

## Semantics
- [ ] Demon/Goblin treated as payout classes; payout ladders documented in config.
- [ ] No docs or code treat Demon/Goblin as internal personas.
