#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 src/verify_theory.py
python3 src/verify_predictor.py
python3 src/audit_profiles.py examples/synthetic_profiles.json --output results/synthetic_profile_audit.json
python3 src/audit_profiles.py examples/synthetic_profiles.json --both-outcomes --output results/synthetic_both_outcomes_audit.json
bash strengthen/run.sh
printf '\nAll exact synthetic checks passed. The real-data analysis is in ../empirical (bash ../empirical/run.sh).\n'
