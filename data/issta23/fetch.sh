#!/usr/bin/env bash
# Re-downloads the ISSTA'23 artifact archives and extracts the files used here.
set -euo pipefail
cd "$(dirname "$0")"
get() {  # $1 = drive id, $2 = output file
  local html uuid
  html=$(curl -sL -A "Mozilla/5.0" "https://drive.google.com/uc?export=download&id=$1")
  uuid=$(printf '%s' "$html" | grep -o 'name="uuid" value="[^"]*"' | sed 's/.*value="//;s/"//' || true)
  curl -sL -A "Mozilla/5.0" -o "$2" "https://drive.usercontent.google.com/download?id=$1&export=download&confirm=t&uuid=$uuid"
}
tmp=$(mktemp -d)
get 1UYiJ2Ki2-oppV9VvRrmnOPEm5O6I2IL_ "$tmp/data.tar.gz"
get 1y-x8db3rqW0HodOx5BAig8jNa5Tq42I9 "$tmp/stats.tar.gz"
tar xzf "$tmp/data.tar.gz" -C "$tmp"; tar xzf "$tmp/stats.tar.gz" -C "$tmp"
cp "$tmp/data/all-polluter-cleaner-info-combined.csv" "$tmp/data/subjects.csv" "$tmp/data/README.md" .
rm -rf original-orders && cp -r "$tmp/data/original-orders" original-orders && rm -f original-orders/._*
mkdir -p reference_simulator
cp "$tmp/stats/simulation/simulator.py" "$tmp/stats/simulation/README.md" reference_simulator/
rm -rf "$tmp"
sha256sum -c SHA256SUMS
