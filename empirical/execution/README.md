# Matched-order real-execution validation

Read `PLAN.md` for the frozen population, seeds, sample size, and stopping rules.
This experiment measures the outcome abstraction, not the deployed iDFlakies gate.
No subject production code, test code, dependency version, or fixture is changed.

**Scope of this file.** It documents the first frozen protocol (`PLAN.md`: `aismessages` and `http-request/lib`, model f >= 1/3). Two later protocols are documented separately: the rare-failure check on `marine-api` (`PLAN_RARE.md`, `results_rare/README.md`) and the real iDFlakies runs on all three modules (`PLAN_IDFLAKIES*.md`, `idflakies/REPORT.md`). The three unlisted victims found in `http-request/lib` are in `extra_tests/REPORT.md`.

## Setup used

- Linux x86-64; Temurin JDK 8u504-b01; Apache Maven 3.9.9.
- aismessages at the dataset revision: JUnit 4.12, project Surefire 2.22.0.
- http-request/lib at the dataset revision: JUnit 4.10; Maven 3.9.9's default
  Surefire 3.2.5 for the native baseline. The ordered executions use project JUnit
  directly, not a replacement Surefire provider.
- One fresh JVM and temporary directory per full suite. The working directory is
  the unchanged module directory. Java assertions are enabled, as in Surefire.
  aismessages retains its configured logging.properties system property.
- The http-request fixtures start and stop their ordinary local Jetty server/proxy
  on ephemeral ports; the runner does not reset state between individual tests.

Source/tool checkouts and build caches live outside the paper checkout, under
`/tmp/execution` in this run. `results/` contains the experiment's measurements,
not copied repositories. Existing simulation outputs are not
rewritten by this experiment.

## Reproduce

Obtain Maven 3.9.9 and Temurin JDK 8u504-b01 locally (no system installation needed).
Set `WORK` and `JAVA_HOME`; the following commands describe the actual build:

```sh
WORK=/tmp/execution
export JAVA_HOME="$WORK/deps/jdk8u504-b01"
export PATH="$JAVA_HOME/bin:$WORK/deps/apache-maven-3.9.9/bin:$PATH"
mkdir -p "$WORK/subjects" "$WORK/runner"
# Extract the source snapshots from GitHub's codeload endpoint:
# https://codeload.github.com/tbsalling/aismessages/tar.gz/7b0c4c708b6bb9a6da3d5737bcad1857ade8a931
# https://codeload.github.com/kevinsawicki/http-request/tar.gz/2d62a3e9da726942a93cf16b6e91c0187e6c0136
# The archive's top-level directories must remain repo-REVISION.
# In each module directory (http-request uses its lib/ subdirectory):
mvn -B -ntp -Dmaven.repo.local="$WORK/deps/m2" test-compile \
    dependency:build-classpath -Dmdep.outputFile="$WORK/aismessages.classpath"
mvn -B -ntp -Dmaven.repo.local="$WORK/deps/m2" test
# Repeat these two Maven commands in http-request/lib, changing the classpath
# output file to $WORK/http-request.classpath.

# From the repository root:
javac -cp "$(cat "$WORK/http-request.classpath")" -d "$WORK/runner" \
    empirical/execution/OrderedJUnit.java
python3 empirical/execution/test_runner.py
for subject in aismessages http-request; do
    python3 empirical/execution/run.py discover "$subject"
    python3 empirical/execution/run.py pilot "$subject"
    python3 empirical/execution/run.py sample "$subject"
done
python3 empirical/execution/check_results.py
python3 empirical/execution/test_analysis.py
python3 empirical/execution/analyze.py --texdir paper/generated
```

For a rerun, supply a fresh `--output DIRECTORY` to every `run.py` invocation;
existing pilot/formal measurements are deliberately not overwritten. Change
`--work` and `--java` explicitly if tools/checkouts live elsewhere. The small
runner regression accepts `EXEC_WORK` and `EXEC_JDK` environment overrides.

## What is actually verified

The [JUnit Request API](https://junit.org/junit4/javadoc/4.12/org/junit/runner/Request.html) supplies the ordinary sorting mechanism.
The native Maven baseline's complete test inventory is reconciled with JUnit
runner discovery and the dataset's original-order inventory, including all
model-relevant tests. `Request.classes(...).sortWith(...)` orders the ordinary
whole-class runners; it does **not** invoke one method request at a time, which
would repeat class fixtures and change semantics. A separate listener checks every
actual start and finish sequence against the requested order. The regression test
exercises class/method fixtures, expected exceptions, assertion failure, reversal,
fresh-process reset, and class-initialization failure.

Formal JSONL records store requested and observed order indices into metadata's
complete inventory, observed target outcomes, S1/S2 predictions, all test failures,
skips/assumptions, completion status and elapsed time. Class-level initialization
failures, missing tests, order mismatches, process faults, and timeouts invalidate
a run rather than being counted as OD detections. Ordinary test failures are
preserved, including failures of tests not in the published target list.

Pointwise 95% Wilson intervals are based on 300 independent pairs: f uses the
anchor marginal, the reversed marginal is separate, and B uses pairwise joint
failures. A zero B observation has an exact one-sided upper bound, not a proof
that B=0. Module-level agreement uncertainty uses the indicator that **any**
target disagrees within a pair; correlated tests/directions are not independent
replicates. Intervals do not measure project-selection or environment uncertainty.

## Completed run

Both primary candidates completed; no fallback was attempted. Each had 13 excluded pilot executions and 600 formal full-suite executions (300 pairs), with no invalid runs, skipped tests, or timeouts. The ordinary Maven baselines passed all tests. All repeated pilot failure sets were stable.

| Module | Complete tests / preselected targets | Model f, B | Observed anchor f | Observed B | S1/S2 target mismatches |
|---|---:|---|---|---|---:|
| aismessages | 44 / 2 | 2/3, 1/3 | 0.673 (both targets) | 0.293–0.307 | 0 / 1,200 |
| http-request/lib | 163 / 25 | 1/3, 0 | 0.313–0.407 | 0 observed | 0 / 15,000 |

Ranges are across targets, not confidence intervals. Full per-target counts, both marginals and intervals are in `results/per_target.csv`. Two theoretical anchor rates lie outside the observed pointwise 95% intervals; the same deviations occur in model predictions on the identical sampled orders, so they are not outcome disagreements. With 300 pairs, an observed zero has a one-sided 95% upper bound of 0.009936, not a proven zero probability.

The recorded http-request original order consistently failed six known targets and three other tests, unlike the native Maven baseline. Both models correctly predicted the six target failures. This is a failure to reproduce the historical passing-reference assumption in this environment, not evidence of model/actual disagreement for these targets. The three additional tests were retained but not added post hoc to the target sample.

The two cases of this first protocol have model f >= 1/3; rare failures are covered by the second protocol (`results_rare/`) and the deployed gate by the third (`idflakies/`). Do not generalize these results to all 289 models, other JDKs, or detector wall-clock savings.
