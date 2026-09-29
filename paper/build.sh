#!/usr/bin/env bash
# Builds the submission PDF and the supplementary proofs.
set -euo pipefail
cd "$(dirname "$0")"
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex
latexmk -c main.tex supplement.tex >/dev/null 2>&1 || true
pdfinfo main.pdf | grep -E "Pages|Page size"
