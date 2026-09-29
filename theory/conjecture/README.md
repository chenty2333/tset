# Two-level orders: Theorems 3–4 and what remains of Conjecture 1

The full proofs are in `paper/supplement.pdf`, section "Two-level orders: two further theorems".

| Script | Purpose | Result |
|---|---|---|
| `check_thm34.py` | Exact random checks of Theorem 3 (one-sided classes) and Theorem 4 (global + class-local cleaners), up to 9 tests | 249 + 249 instances pass (`check_thm34.json`) |
| `local_lemma.py` | Window lemma: victim's class with independent constant tails, `H(x) >= 0` for x in [0, 1]; also shows that position monotonicity fails (why a new argument was needed) | 7,500 exact cases, no violation; 145 non-monotone profiles |
| `local_disc.py` | Stronger form: `H >= 0` on all of R, i.e., the cross-covariance matrix of (fail, undecided) is negative semidefinite | 2,500 exact cases, no violation (not needed for the theorem) |
| `decompose.py`, `pointwise.py` | Total-covariance split over (u, w) for general two-level instances: both terms are <= 0 numerically, and the conditional term is <= 0 pointwise | exploratory |
| `c1_test.py` | Class level with asymmetric locally-cleaned polluter sets: covariance can be **positive** (+0.055), so a proof must average over the victim's class | counterexample to a naive decomposition |
| `c1_nodead.py` | The same without locally cleaned sets: no positive case | exploratory |
| `c2_test.py` | Victim's class with arbitrary decreasing tail functions: no positive case | exploratory |

On the ISSTA'23 data, `empirical/src/coverage.py` assigns 258 tests to Theorem 1, 20 to Theorem 3 and 10 to Theorem 4. One test has overlapping roles.

Run the key checks with `bash run.sh`.
