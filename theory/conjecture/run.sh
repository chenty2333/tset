#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 check_thm34.py
python3 local_lemma.py
echo "two-level theorem checks passed"
