# Theory: exact verification

Exact checks of the results in `paper/main.tex` and `paper/supplement.tex`. The proofs themselves are in the supplement; the code here confirms them on every instance small enough to enumerate and searches for counterexamples beyond the proven region. Finite checks complement the written proofs and do not replace them.

## Contents

| Path | What |
|---|---|
| `src/reversal_theory.py`, `src/verify_theory.py` | Exact rational computation of `f`, `B`, hitting times, and the half-run and block limits on synthetic state machines; the boundary counterexamples |
| `src/verify_predictor.py` | The imperfect-predictor renewal formula, the break-even cost thresholds, and the target-aware uniform-marginal construction |
| `src/audit_profiles.py` | Evaluates a user-supplied table of `(f, B)` values under both detection protocols (see below) |
| `strengthen/` | Interleaved orders, the frontier of the covariance guarantee, and exhaustive searches up to 7 tests; see its README |
| `conjecture/` | Class-contiguous orders: checks of the one-sided and global/local cases and the window lemma; see its README |
| `extensions/` | An independent exact checker for the cyclic-cut, window-identity, and composition results |
| `crosscheck/` | A second implementation that re-derives those results without reusing `extensions/verify.py` |
| `examples/`, `results/` | Synthetic profiles and the stored outputs of every check |

## Reproduce

Python ≥ 3.10; the core code uses only the standard library.

```sh
bash run_all.sh
```

The script regenerates the JSON files in `results/`. It runs entirely offline and does not execute Maven, JUnit, or iDFlakies. The long exhaustive searches are opt-in: `bash strengthen/run.sh --all`.

## Auditing a table of failure probabilities

`src/audit_profiles.py` takes rational strings when the probabilities are known exactly:

```json
{
  "provenance": "Describe the dataset and how probabilities were obtained",
  "probabilities": "exact",
  "tests": [{"id": "target", "module": "module", "f": "1/4", "B": "0"}]
}
```

`B` is the joint probability that a target fails under both an order and its reversal; it is not a covariance. Mark estimated or rounded values `"estimated"`: the auditor then reports plug-in values, not confidence intervals.

```sh
python3 src/audit_profiles.py profiles.json --runs 2 4 10 20 --output known_reference.json
python3 src/audit_profiles.py profiles.json --both-outcomes --output no_reference.json
```

The default assumes a known passing reference for every target. `--both-outcomes` requires a pass and a failure within the budget. For a known failing reference, relabel the event with `f' = 1-f` and `B' = 1-2f+B`. The auditor reports test-weighted and module-weighted averages. It cannot reconstruct an outcome-adaptive suite scheduler from `(f, B)` marginals; that needs a per-module joint outcome model.

## Assumptions

- Independent, uniform child permutations on a fixed hierarchy; children run contiguously.
- Distinct tests, each run once, with a clean state between complete runs.
- Nonpositive covariance: the conditions of main Theorem 1 (cases a–d).
- Independent anchor pairs for the hitting-time and product-of-misses formulas.
- No early termination, no nondeterminism for a fixed order, no hidden fixture side effects, and no wall-clock cost model.

The Fréchet and independent-block upper bounds do not need the common-cleaner model. The noninferiority lower bounds do need nonpositive covariance, and the six-test counterexample shows it can fail with disjoint, polluter-specific cleaners.
