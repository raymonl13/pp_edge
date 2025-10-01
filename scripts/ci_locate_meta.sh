#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?}"
find "$ROOT" -type f -name run_meta.txt -print -quit
