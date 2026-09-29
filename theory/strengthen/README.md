# Strengthened theory: frontier of the covariance guarantee and limits of scheduling

Checks that support Theorem 2, Table II (classification), Conjecture 1, and Theorems 6–8 of the paper.
The full proofs are in `paper/supplement.pdf`, Sections "Interleaved orders…", "The frontier…", and "Limits of scheduling".

| Script | What it checks | Output | Time |
|---|---|---|---|
| `verify_new.py` | Theorem 2 and Lemma 2 on all 2,897 interleaved instances with ≤ 6 tests; Lemma 2 with overlapping roles; exact values of both boundary counterexamples; block limit on 2,000 random block laws (equality iff disjoint) | `verify_new.json` | ~5 s |
| `exhaust2.py N...` | Conjecture 1: all two-level instances with disjoint roles (578,658 instances for N = 2..7) | `exhaust2_disjoint.json` | N ≤ 6: ~1 min; N = 7: ~30 min |
| `exhaust2_overlap.py N...` | Two-level instances with overlapping roles, N ≤ 5 (none positive) | `exhaust2_overlap.json` | ~2 min |
| `flat_overlap_exhaust.py N...` | Interleaved orders with overlapping roles, N ≤ 6 (1,426,549 instances) | `flat_overlap_exhaust.json` | ~15 min |
| `climb.py`, `climb2.py`, `search_general.py` | Randomised and hill-climbing searches; `climb.py` found the 7-test two-level overlapping-roles counterexample | stdout | minutes |
| `flat_structure.py`, `flat_fixed.py` | Exploratory checks of the proof steps (conditional covariance given the victim's position; monotonicity of `a(u)`) | stdout | minutes |

Run the fast checks with `bash run.sh`, or all of them with `bash run.sh --all`.
