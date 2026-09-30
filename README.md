# tset

*tset* is *test* reversed.

Code, data, proofs, and paper source for **"At Most Half a Run: Guarantees and Limits of Reversal-Based Detection of Order-Dependent Flaky Tests."**

An order-dependent (OD) flaky test passes or fails on the same code depending on which tests ran before it. Detectors such as iDFlakies therefore rerun the suite in different orders, and when a round finds nothing new they run the *reverse* of the previous order, because reversing a passing order is more likely to fail. This work asks how much that reversal can actually save, and proves it is less than intuition suggests.

## Results

1. **Reversal is safe.** In four structural classes of OD tests, an order and its reversal have nonpositively correlated failure events, so an independent order/reversal pair detects a test at least as often as two independent random orders. These classes cover all 289 published OD models we study (259 / 20 / 10 by class). The proofs combine a composable sum-of-squares certificate, a cyclic-cut reduction to Harris' inequality, and a two-square window identity. Counterexamples mark where the property fails.
2. **The saving is at most half a run.** Independent reversal pairs save at most half a suite run in the expected time to a test's first failure. Independent blocks of `k` runs save at most `(k-1)/2` runs when `kf ≤ 1`, where `f` is the failure probability. A small fixed block cannot give a constant-factor gain on rare failures.
3. **Broader schedules have their own lower bounds.** Uniform-marginal and reverse-or-fresh schedules are analyzed per target. Whether one schedule can realize the gap to these bounds for all targets of a suite at once is not evaluated here; covering designs are the natural candidates.
4. **What a predictor must achieve.** For an imperfect reversal predictor with recall `s` and false-alarm rate `a`, we give the exact expected number of runs and the break-even condition against a per-period cost `c`.
5. **Simulation at scale.** Across the 289 OD tests in 47 Maven modules, independent reversal pairs save 0.40 runs per test on average and add 0.19–0.33 percentage points of detection at 20 runs. iDFlakies' outcome-gated reversal changes the order distribution and inherits neither guarantee, so it is evaluated separately.
6. **Real executions agree with the model.** Three complete modules (`aismessages`, `http-request/lib`, and the rare-failure module `marine-api` with model `f = 1/32`), 39 OD targets, 300 to 1,000 order/reversal pairs each: all 40,200 target outcomes match the model's same-order predictions. The executions also reveal three OD victims that the dataset misses.
7. **The real tool follows the simulated gate.** We ran the unmodified iDFlakies and two minimal patches of its decision code (4,731 complete 20-round detector runs on the three modules). The tool reverses exactly when the simulated gate rule predicts, in all 29,963 gate decisions, and all 847,440 target outcomes on the tool's own orders match the model.

## Repository layout

| Directory | Contents |
|---|---|
| `paper/` | `main.tex` (9 pages including references) and `supplement.tex` (full proofs), references, generated tables and figures, `build.sh` |
| `theory/` | Exact rational verification of every theorem; exhaustive searches at the frontier of the conjecture; independent cross-checks |
| `empirical/` | Simulation pipeline (`src/`, `run.sh`), all outputs (`results/`), the real-execution validation of three modules, and the real iDFlakies runs (`execution/`) |
| `data/issta23/` | Public inputs from the ISSTA'23 artifact of Li et al.: 289 OD tests, recorded original orders, the authors' reference simulator, with provenance and checksums |
| `replication/` | `build_package.sh` and the paper-to-artifact mapping in `README_package.md` |

## Reproducing

Requirements: Python ≥ 3.10, numpy ≥ 2.0, matplotlib; TeX Live with IEEEtran to build the paper. The real-execution study additionally needs a JDK 8 and Maven.

```sh
bash theory/run_all.sh                          # exact checks of the theory, a few minutes
bash empirical/run.sh                           # 47-module simulation, about 10 minutes
python3 empirical/execution/check_results.py    # integrity of the stored real-execution results
python3 empirical/execution/analyze.py --texdir paper/generated   # rebuild the execution tables
bash paper/build.sh                             # compile the paper and supplement
```

`empirical/execution/README.md` (two frequently failing modules), `empirical/execution/results_rare/README.md` (`marine-api`), and `empirical/execution/idflakies/REPORT.md` (real iDFlakies runs) document the real-execution studies and how to rerun them. `replication/README_package.md` maps every claim in the paper to the script and file that supports it.

## Scope

- The model guarantees concern independent reversal pairs under explicit OD-model hypotheses. They are not guarantees for outcome-gated policies as deployed.
- The 47-module policy comparison relies on the polluter/cleaner abstraction of the ISSTA'23 dataset. For 108 of the 289 models the abstraction predicts that the recorded original order fails; results are reported for all models and for the 181 consistent ones.
- Real executions cover three buildable modules (39 of the 289 targets; the rarest has `f = 1/32`) and one iDFlakies commit. They do not extend to the other 250 models, other JDKs, or detector wall-clock time. Targets within a module share polluters and cleaners, so the 12 `marine-api` targets and the 25 `http-request` targets are not independent confirmations.
- The rare tail of the dataset is concentrated. Of the 71 targets with `f < 0.1`, 49 lie in two modules: `dubbo-config-api` (37 brittles of one test class) and `marine-api` (12 victims of one polluter). Without these two modules, the remaining 22 rare targets still cause 80% and 94% of the random-order misses among the other 240 targets at 10 and 20 runs (known-reference protocol), but per-target percentages should be read with this clustering in mind.
- One open case remains: the covariance conjecture for general two-level orders with disjoint roles that violate both the one-sided and the global/local conditions. No result in the paper depends on it. Exhaustive search finds no counterexample up to 7 tests.
