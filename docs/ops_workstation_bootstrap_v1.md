# PP-EDGE Operator Workstation Bootstrap — v1.0 (macOS)

_Last updated: 2025-12-25_

Purpose: bring up a new macOS workstation (including a temporary loaner) so it can run:
- Daily SLP (Lane A) — production PrizePicks flows
- Engine work (Lane B) — NBA Engine experiments and evaluation

This doc is workstation-only (brew/git/python/venv/data restore). It does NOT change Lane A logic.

Core rails:
- Use RRHM heredocs for file updates.
- No notebook magics.
- Do not paste prose/bullets into a shell: only paste code blocks.

Local-only artifacts:
- runs/, data/, model_assets/ are typically untracked. Back them up and restore them during migrations.

Sections:
1) Xcode CLT
2) Homebrew
3) git + gh + python3
4) bash + bracketed paste (~/.inputrc)
5) Repo clone/refresh
6) Restore local-only artifacts
7) Create venv + install requirements-unit.txt
8) Validate with scripts/ops/ops_workstation_check_v3.sh and one NBA golden run

