#!/usr/bin/env bash
# Assembles a self-contained, anonymized replication archive:
#   replication/reversal-od-replication.zip
# Contents: supplement (full proofs), theory checks, empirical pipeline with
# results, and the ISSTA'23 input data.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/replication/package"
rm -rf "$OUT" "$ROOT/replication/reversal-od-replication.zip"
mkdir -p "$OUT"/{theory,empirical,data,docs}

cp "$ROOT/paper/supplement.pdf" "$OUT/docs/supplement_proofs.pdf"
cp -r "$ROOT/theory/src" "$ROOT/theory/examples" "$ROOT/theory/results" "$OUT/theory/"
cp "$ROOT/theory/run_all.sh" "$OUT/theory/"
cp -r "$ROOT/theory/strengthen" "$ROOT/theory/conjecture" "$ROOT/theory/crosscheck" "$OUT/theory/"
mkdir -p "$OUT/theory/extensions"
cp "$ROOT/theory/extensions/verify.py" "$ROOT/theory/extensions/verification.json" "$ROOT/theory/extensions/strict_extension_orders.csv" "$OUT/theory/extensions/"
rm -f "$OUT/theory/strengthen/"*.log
cp -r "$ROOT/empirical/src" "$OUT/empirical/"
cp -r "$ROOT/empirical/execution" "$OUT/empirical/"
mkdir -p "$OUT/empirical/results"
cp "$ROOT"/empirical/results/*.json "$ROOT"/empirical/results/*.csv "$OUT/empirical/results/"
cp "$ROOT/empirical/run.sh" "$ROOT/empirical/README.md" "$OUT/empirical/"
cp -r "$ROOT/data/issta23" "$OUT/data/"
cp "$ROOT/replication/README_package.md" "$OUT/README.md"
# the empirical pipeline writes tables/figures next to a paper/ directory
mkdir -p "$OUT/paper/generated" "$OUT/paper/figures"
cp "$ROOT"/paper/generated/*.tex "$OUT/paper/generated/"
cp "$ROOT"/paper/figures/*.pdf "$OUT/paper/figures/"
find "$OUT" -name "__pycache__" -type d -prune -exec rm -rf {} +
find "$OUT" -name "._*" -delete

# anonymity check: fail if identifying strings appear anywhere in the package
# (set ANON_TERMS="name|handle|email-domain" to add author-specific terms)
if grep -rIl -i -E "claude|chatgpt|/home/|${ANON_TERMS:-@@none@@}" "$OUT"; then
  echo "anonymity check FAILED (files listed above)"; exit 1
fi
(cd "$ROOT/replication" && zip -qr reversal-od-replication.zip package)
echo "built $ROOT/replication/reversal-od-replication.zip"
du -sh "$ROOT/replication/reversal-od-replication.zip"
