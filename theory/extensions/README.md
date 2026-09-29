# Extensions: exact checker

Companion to the supplement's section "Extensions: cyclic cut, the all-real window identity, and composition" (statements A.1–A.16). The proofs are in the supplement; this directory holds an exact checker for them.

## Files

- `verify.py`: standard-library-only checker (Python 3.10+) using integer arithmetic and `fractions.Fraction`.
- `verification.json`: output of the checker; status `PASS`.
- `strict_extension_orders.csv`: all 24 legal orders of the five-test strict-coverage example, with both failure indicators.

```sh
python verify.py --output verification.json
```

Randomly selected sanity-check instances use fixed seeds, and their probabilities are computed exactly by complete enumeration of legal orders. The small cleaner-family enumeration fixes `P = {1, ..., a}` and varies every cleaner subset: 4,771 configurations covering all flat role assignments up to relabeling, on at most five ambient tests. The reported test-family counts overlap.

## Strict-coverage example

Classes `{v}`, `{p1, g}`, `{p2, e}`; polluters `{p1, p2}`; cleaner sets `C[p1] = {g}`, `C[p2] = {g, e}`. Exact values: `f = 3/8`, `B = 1/12`, `f² − B = 11/192`. The example satisfies the extended theorem but not the two earlier two-level theorems, so the extended region is strictly larger.

## Scope

The checks are finite. They support, but do not replace, the written proofs, and they are not a proof-assistant formalization. `../crosscheck/` re-derives the same results with separate code.
