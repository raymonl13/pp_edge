#!/usr/bin/env bash
set -euo pipefail

echo "=== PP-EDGE Workstation Check v3 (non-blocking) ==="
echo "PWD: $(pwd)"
echo

echo "[0] Repo sanity"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "  - git: OK ($(git rev-parse --short HEAD))"
else
  echo "  - git: FAIL (not in a git repo)"
fi
echo

echo "[1] Git status (short)"
git status -sb 2>/dev/null || true
echo

echo "[2] Key directories (presence only)"
for d in data model_assets runs scripts docs; do
  if [ -d "$d" ]; then
    echo "  - $d: present"
  else
    echo "  - $d: MISSING"
  fi
done
echo

echo "[3] Shell / bash reality (important nuance)"
echo "  - SHELL env: ${SHELL:-}"
echo "  - script bash (this file): ${BASH_VERSION:-}"
echo "  - /bin/bash version: $(/bin/bash --version 2>/dev/null | head -1 || echo 'unknown')"
if [ -x /opt/homebrew/bin/bash ]; then
  echo "  - homebrew bash: $(/opt/homebrew/bin/bash --version | head -1)"
else
  echo "  - homebrew bash: not found at /opt/homebrew/bin/bash"
fi
echo

echo "[4] .inputrc / bracketed paste"
if [ -f "$HOME/.inputrc" ]; then
  echo "  - ~/.inputrc present"
  if grep -q 'set enable-bracketed-paste on' "$HOME/.inputrc" 2>/dev/null; then
    echo "  - bracketed paste: configured (line present)"
  else
    echo "  - bracketed paste: NOT configured (missing line)"
  fi
else
  echo "  - ~/.inputrc missing"
fi
echo

echo "[5] Python / venv"
if command -v python3 >/dev/null 2>&1; then
  echo "  - python3: $(python3 --version)"
else
  echo "  - python3: NOT FOUND"
fi

if [ -n "${VIRTUAL_ENV:-}" ]; then
  echo "  - VIRTUAL_ENV: $VIRTUAL_ENV"
else
  echo "  - VIRTUAL_ENV: (not active)"
fi

if [ -d "venvs/pp_edge" ]; then
  echo "  - venvs/pp_edge: present"
else
  echo "  - venvs/pp_edge: missing"
fi
echo

echo "=== Workstation check v3 complete ==="
