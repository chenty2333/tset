# Empirical study (ISSTA'23 dataset, 289 OD tests)

`bash run.sh` regenerates every empirical number, table, and figure used in the paper (about 10 minutes on one core).
Requirements: Python ≥ 3.10, numpy ≥ 2.0 (for `bitwise_count`), and matplotlib.

| Script | Role | Outputs (`results/`) |
|---|---|---|
| `src/common.py` | Dataset loading, S1/S2 semantics, uniform class-contiguous order sampler, vectorised and scalar outcome evaluators | — |
| `src/pertest.py SEM` | Per OD test: exact rational (f, B) when a closed form applies (258 tests), otherwise Monte Carlo cells (2e6 orders); consistency with the recorded original order | `pertest_SEM.csv`, `pertest_SEM_validation.json` |
| `src/suite.py SEM T` | Joint module-level simulation of IID / Pair / Gate (iDFlakies @ f54b3f0) / Strict under the NR and KR protocols. Uses T detector runs of 40 rounds per module and common random numbers | `suite_SEM.json` |
| `src/validate.py SEM` | (1) Simulated means vs. per-target closed forms for IID/Pair. (2) Our evaluator vs. the unmodified ISSTA'23 `simulator.py` | `validation_SEM.json` |
| `src/analyze.py SEM` | Aggregation, 95% CIs, per-module Bonferroni tests. Writes LaTeX macros and tables to `../paper/generated/` and figures to `../paper/figures/` | `summary_SEM.json` |

Semantics:
- **S1** (primary) is identical to the ISSTA'23 reference simulator: Definition 1 of TACAS'21, with cleaner groups `a|b` split into single cleaners.
- **S2** (sensitivity) makes a cleaner group clean only when all of its members lie between the polluter and the victim.

Protocols:
- **NR** is the ISSTA'23 definition: both a passing and a failing run within the budget.
- **KR** assumes a known passing original order, so a test is detected at its first failure.

Validation status (see `results/validation_S1.json`):
- The evaluator agrees with the ISSTA'23 reference simulator on all 289 OD tests.
- 6,272 simulated means match the closed forms, with max |z| = 3.26.
- The closed forms were checked by Monte Carlo, with max |z| = 2.73 over 516 checks.

Known limitation, stated in the paper: for 108 of the 289 tests, the dataset's polluter/cleaner abstraction predicts that the recorded original order fails. The paper therefore also reports the 181 consistent tests.

Reference consistency is reported alongside the main results. `analyze.py S1` generates `table_reference_sensitivity.tex` from the S1/S2 suite outputs at 20 rounds without resimulating. The consistent-target view restricts scoring only: inconsistent targets still drive the original gate decisions. The intervals quantify Monte Carlo error, not abstraction validity.

## Separate real-execution validation

`execution/` is a frozen two-module check, independent of the main simulation. Both original revisions built without changing tests or production code; the complete inventories are 44 and 163 tests. Each module completed 300 random/reversed pairs with exact requested/observed order agreement. All 16,200 outcomes of 27 preselected targets matched both S1 and S2 predictions. See `execution/README.md` for commands, intervals, pilot controls, and limits. The check does not cover the other 262 models or the deployed gate.
