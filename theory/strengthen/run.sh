#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 verify_new.py > /dev/null && echo "verify_new: ok"
python3 exhaust2.py 2 3 4 5 6
python3 exhaust2_overlap.py 3 4 5
if [[ "${1:-}" == "--all" ]]; then
  python3 exhaust2.py 7
  python3 flat_overlap_exhaust.py 2 3 4 5 6
fi
echo "strengthened-theory checks passed"
