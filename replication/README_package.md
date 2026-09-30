# Replication package: "At Most Half a Run: Guarantees and Limits of Reversal-Based Detection of Order-Dependent Flaky Tests"

Everything needed to reproduce the theory checks, the simulation study, and the real-execution validation.

## Contents

| Path | What |
|---|---|
| `docs/supplement_proofs.pdf` | Complete proofs of all theorems, propositions, and examples, the corrected two-level formulas, and computation details |
| `theory/` | Exact rational checks of the theory. `bash theory/run_all.sh` takes about 3 min; `theory/strengthen/run.sh --all` adds the long exhaustive searches. `theory/src/audit_profiles.py` evaluates a user-supplied table of (f, B) values |
| `empirical/` | The empirical pipeline (`bash empirical/run.sh`, about 10 min) and all its outputs in `empirical/results/`. `empirical/README.md` documents every script |
| `data/issta23/` | Inputs from the public ISSTA'23 artifact of Li et al.: 289 OD tests with polluters, cleaners and state-setters, plus recorded original orders and the authors' reference simulator. Provenance is in `PROVENANCE.md`, hashes in `SHA256SUMS`, and `fetch.sh` re-downloads the files |
| `paper/generated`, `paper/figures` | The macros, tables, and figures that the pipeline writes and the paper includes |

## Requirements

Python ≥ 3.10, numpy ≥ 2.0, and matplotlib. No network access is needed, except by `data/issta23/fetch.sh`.

## Mapping from paper to artifacts

| Paper | Artifact |
|---|---|
| Safety theorem (main Theorem 1), frontier | `docs/supplement_proofs.pdf`; `theory/src/verify_theory.py`, `theory/strengthen/`, `theory/conjecture/`, `theory/crosscheck/` |
| Block limit (Theorem 2), broader bounds (Theorem 3) | Supplement section "Limits of scheduling"; `theory/strengthen/verify_new.py`, `theory/src/verify_predictor.py` |
| Predictor tradeoff and target-aware attainment | Supplement sections on the imperfect predictor and uniform-marginal attainment; `theory/src/verify_predictor.py` |
| RQ1: coverage, per-test benefit, limits map (Fig. 1, Table III; supplement tables on audit, per-test detection, breakdown) | `empirical/results/coverage_S1.json`, `pertest_S1.csv`, `summary_S1.json` → `pertest`; `table_pertest_S1.tex`, `table_breakdown_S1.tex`, `macros_limits_S1.tex`. Coverage files keep historical theorem IDs: 1→main 1(a), 3→1(c), 4→1(d) |
| RQ2: suite policies and robustness (Table IV; supplement figure and tables on modules and reference consistency) | `suite_S1.json`, `suite_S2.json`, `summary_S1.json` → `suite`; `table_suite_S1.tex`, `table_modules_S1.tex`, `table_reference_sensitivity.tex`. Consistent-target scoring keeps the original all-target gate decisions |
| RQ2: real iDFlakies runs (Table V) | `empirical/execution/idflakies/` (REPORT.md, patches, per-round results) |
| RQ3: real executions (Table VI) | `empirical/execution/` (see below); the rare-failure module `marine-api` is in `empirical/execution/results_rare/`; the extra http-request victims are in `empirical/execution/extra_tests/REPORT.md` |
| Implementation validation (not project execution) | `validation_S1.json`, `validation_S2.json`, `pertest_S1_validation.json` |

## Bounded real-execution check

`empirical/execution/` contains three frozen execution protocols (two frequently failing modules; the rare-failure module `marine-api`; real iDFlakies runs on all three), the ordered whole-class JUnit runner, result analysis, and execution measurements. This is distinct from the 47-module simulation. See `empirical/execution/README.md`, `results_rare/README.md`, and `idflakies/REPORT.md` for the pinned subjects and external JDK/Maven setup; unlike simulation, reproduction needs downloads and a Java execution environment.
