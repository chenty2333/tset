#!/usr/bin/env bash
# Regenerates every empirical number, table and figure of the paper.
# Requirements: Python >= 3.10, numpy >= 2.0, matplotlib.  About 10 minutes
# on a laptop (single core).  Outputs: empirical/results/, paper/generated/,
# paper/figures/.
set -euo pipefail
cd "$(dirname "$0")/src"
python3 pertest.py S1          # exact / Monte Carlo (f, B) per OD test
python3 pertest.py S2          # sensitivity semantics
python3 suite.py S1 100000     # suite-level policies, 1e5 detector runs/module
python3 suite.py S2 50000
python3 validate.py S1         # closed forms + ISSTA'23 reference simulator
python3 validate.py S2
python3 analyze.py S2
python3 coverage.py            # which theorem covers each OD test
python3 analyze.py S1          # tables, macros, figures (S1 last)
echo "done: see ../results and ../../paper/generated"
