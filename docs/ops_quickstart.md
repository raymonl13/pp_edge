- Trigger: `gh workflow run nightly_edge_sheet.yml -f day=$(date -u +%F)`
- Verify:  `bash scripts/slp_verify.sh`
- Accept when:
  * Engine step: success (hard gate)
  * edgesheet: rows ≥ 2
  * outcomes_rollup.json: present (ROI); Brier/Logloss present when realized join exists
  * rollup_probe.json: present (join_rows >= 0)
- Notes:
  * If artifacts missing, re-run verify (fresh RID). Don’t reuse old RIDs between shells.
  * Use bash for verification; zsh globs `[]` and `#`.
