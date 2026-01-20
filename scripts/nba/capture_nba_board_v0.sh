#!/usr/bin/env bash
set -euo pipefail

: "${DAY:?Set DAY=YYYY-MM-DD before calling this script}"

ROOT="/Users/raymonlacy/pp_edge_wt2"
OUT_DIR="$ROOT/data/pp_board/sport=nba/day=${DAY}"
OUT_PATH="$OUT_DIR/pp_raw.json"

mkdir -p "$OUT_DIR"

echo "[capture_nba_board_v0] Writing clipboard to $OUT_PATH"
# Assumes you have the JSON response in your macOS clipboard (Cmd+C in devtools)
pbpaste > "$OUT_PATH"

# Quick sanity check: file non-empty?
if [[ ! -s "$OUT_PATH" ]]; then
  echo "[capture_nba_board_v0] ERROR: $OUT_PATH is empty. Did you copy the JSON?"
  exit 1
fi

echo "[capture_nba_board_v0] Done."
