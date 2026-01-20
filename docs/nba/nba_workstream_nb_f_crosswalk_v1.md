# NBA Workstream (NB‑F) Crosswalk — v1.0

_Last updated: 2025-12-25_

Purpose: make NB‑F phases first‑class and traceable to the global milestone ladder.

Canonical ladder:
- Global milestones: M0–M7 (Milestone Manifest)
- NBA workstream: NB‑F0…NB‑F7 (NBA Engine roadmap)

Rule:
Every NB‑F phase MUST declare:
- Roadmap anchor: which M# it belongs to
- Lane: A (prod) or B (experimental)
- Promotion gate: evidence pack + tag requirement
- Dependencies: exact files/columns/scripts required

Crosswalk (high level):
- NB‑F0: baseline NBA pipeline + daily capture discipline (anchors to M2 and depends on M0)
- NB‑F1: full-board eval harness + calibration slicing (anchors to M5, depends on M0/M2)
- NB‑F2: Points model v2 experiments (anchors to M5, depends on M2 data surface)
- NB‑F3/NB‑F4: EV logic + odds_type policies (anchors to M4, depends on M5)
- NB‑F6/NB‑F7: CI/golden/freeze promotion tooling (anchors to M7)

