#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile code_utils_slipqa_v2.py
python3 -m py_compile code_utils_allocator_v2.py
python3 -m py_compile scripts/run_qa_alloc.py
