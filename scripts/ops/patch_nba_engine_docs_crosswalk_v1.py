#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

ROADMAP_PATH = Path("docs/nba_engine_roadmap_v01.md")
STATUS_PATH  = Path("docs/nba_engine_status_v01.md")

CROSSWALK_BEGIN = "<!-- BEGIN: ROADMAP_CROSSWALK_M0_M7_TO_NB_F -->"
CROSSWALK_END   = "<!-- END: ROADMAP_CROSSWALK_M0_M7_TO_NB_F -->"

NB_F2_BEGIN = "<!-- BEGIN: NB_F2_POINTS_V2_FEATURES_OPTION_A -->"
NB_F2_END   = "<!-- END: NB_F2_POINTS_V2_FEATURES_OPTION_A -->"

STATUS_BEGIN = "<!-- BEGIN: PLANNED_POINTS_V2_FEATURE_SET_OPTION_A -->"
STATUS_END   = "<!-- END: PLANNED_POINTS_V2_FEATURE_SET_OPTION_A -->"

CROSSWALK_BLOCK = f"""{CROSSWALK_BEGIN}
## Roadmap taxonomy crosswalk (canonical)

Global milestones: M0–M7  
NBA workstream: NB‑F0…NB‑F7

Rule: every NB‑F phase must declare:
- Roadmap anchor (M#)
- Lane (A vs B)
- Promotion gate (evidence pack + tag)
- Dependencies (files/columns/scripts)

{CROSSWALK_END}
"""

NB_F2_BLOCK = f"""{NB_F2_BEGIN}
#### Option A feature scope (use existing joined columns)

Roadmap anchor: M5  
Lane: B  
Promotion gate: F2 evidence pack + tag (no Lane A changes until promoted)

Exact column names available today (joined_with_phit):
- line
- stat_ppg
- usagePercent
- tsPercent
- per
- vorp
- games
- minutesPg
- points
- odds_type

Derived features:
- minutes_per_game = minutesPg / games
- pts_per_min_season = points / minutesPg
- line_minus_stat = line - stat_ppg
- line_over_stat = line / max(stat_ppg, 1e-6)
- is_goblin = (odds_type == "goblin")
- is_demon  = (odds_type == "demon")

Out of scope (Option A):
- minutes_proj / pace_proj / home/rest flags (these are M2 “file-first features” work)

{NB_F2_END}
"""

STATUS_NOTE = f"""{STATUS_BEGIN}
Planned Points v2 feature set (Option A, Lane B only):  
Use joined_with_phit columns (line, stat_ppg, usagePercent, tsPercent, per, vorp, games, minutesPg, points, odds_type) + derived features (minutes_per_game, pts_per_min_season, line_minus_stat, line_over_stat, is_goblin, is_demon).  
No Lane A changes until an F2 evidence pack is complete and we explicitly promote.
{STATUS_END}
"""

def upsert(text: str, begin: str, end: str, block: str, insert_after_regex: str | None = None) -> str:
  pat = re.compile(re.escape(begin) + r".*?" + re.escape(end), flags=re.S)
  if pat.search(text):
    return pat.sub(block, text)
  if insert_after_regex:
    m = re.search(insert_after_regex, text, flags=re.M)
    if m:
      i = m.end()
      return text[:i] + "\n\n" + block + "\n" + text[i:]
  return block + "\n\n" + text

def main() -> int:
  for p in (ROADMAP_PATH, STATUS_PATH):
    if not p.exists():
      print(f"ERROR: missing {p}")
      return 2

  roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
  status  = STATUS_PATH.read_text(encoding="utf-8")

  roadmap2 = roadmap
  roadmap2 = upsert(roadmap2, CROSSWALK_BEGIN, CROSSWALK_END, CROSSWALK_BLOCK, insert_after_regex=r"^# .*$")
  roadmap2 = upsert(roadmap2, NB_F2_BEGIN, NB_F2_END, NB_F2_BLOCK, insert_after_regex=r"^#{2,4} .*NB[\-\s]?F2.*$")

  status2 = status
  status2 = upsert(status2, STATUS_BEGIN, STATUS_END, STATUS_NOTE, insert_after_regex=r"^# .*$")

  if roadmap2 != roadmap:
    ROADMAP_PATH.write_text(roadmap2, encoding="utf-8")
    print(f"Patched: {ROADMAP_PATH}")
  else:
    print(f"No change: {ROADMAP_PATH}")

  if status2 != status:
    STATUS_PATH.write_text(status2, encoding="utf-8")
    print(f"Patched: {STATUS_PATH}")
  else:
    print(f"No change: {STATUS_PATH}")

  return 0

if __name__ == "__main__":
  raise SystemExit(main())
