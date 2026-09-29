# Rare-stratum execution check: ktuukkan/marine-api

Executes `../PLAN_RARE.md` (frozen, sha256 in `../PLAN_RARE.sha256`, verified unchanged) on top of `../PLAN.md`.
The first two subjects (`../results/`) are untouched. Nothing here writes to `paper/`.

## Setup
- Module: `ktuukkan/marine-api`, root, revision `af0003847db9ba822f67d4f1dceb8de3fe63250a`. Primary candidate; **no fallback** was needed.
  Model: 926 tests, 12 targets (all reference-consistent), S1 f = 1/32, B = 0.
- Linux x86-64, Temurin JDK 8u504-b01, Maven 3.9.9 with the project's own JUnit 4.12 and default Surefire.
  `mvn test-compile dependency:build-classpath` built at the first try, no build configuration. Native `mvn test`: 926 run, 0 failures, 0 errors, 1 skipped.
- Discovery: JUnit discovery = native inventory = recorded original order (926 tests, none missing, no extra, no missing model-relevant test).
- One fresh JVM per complete suite order (all 71 classes, `-ea`, unchanged cwd). Seeds: pilot 2026100101, formal 2026100102. 1,000 class-contiguous anchor orders, each followed by its exact reversal; 300 s per-suite timeout; 12 h cap.
- Pilot (excluded): original order x3 + five random orders x2 = 13 runs, all valid.

## What ran
- Formal sample completed by itself: **1,000 / 1,000 pairs**, 2,000 valid runs, 0 invalid runs, 0 timeouts (wall 2,337 s, about 1.2 s per run). `marine-api/formal_status.json`: `completed`.
- Pilot: 13/13 valid, 0 test failures of any kind (including the original order, three repeats), repeated pilot orders stable (identical failure sets), predictions match (no target failed, none predicted).
- Non-target failures in all formal runs: **none**. Skips: only the one native `@Ignore` test (see D1).

## Results (`summary.json`, `per_target.csv`, `tex/`)
| Quantity | Value |
|---|---|
| Observed anchor f per target | 0.028 (9 AbstractAISMessageListenerTest targets; Wilson 95% [0.019, 0.040]) and 0.030 (3 AISMessageFactoryTest targets; [0.021, 0.043]). Model 1/32 = 0.03125 lies inside every interval |
| Reverse marginal | 0.033 [0.024, 0.046] and 0.032 [0.023, 0.045] |
| 2x2 pair counts (n00, n01, n10, n11) | (939, 33, 28, 0) for the 9 listener targets; (938, 32, 30, 0) for the 3 factory targets |
| B (joint failure) | 0 observed for all 12 targets; exact one-sided 95% upper bound 1-0.05^(1/1000) = 0.002991 per target. Not a proof that B = 0 |
| Directions (of 2,000) with any target failure | 86 (anchor 41, reverse 45); in no pair did both directions fail. Targets failing per failing direction: 3 targets x25, 9 x24, 12 x37 (targets are strongly correlated, pair is the unit) |
| S1 and S2 order-level agreement | 0 / 2,000 directions with any target mismatch; 0 / 24,000 target outcomes (S1 and S2 predictions coincide here) |
| Restricted to the 86 failing directions | 0 / 1,032 target mismatches (S1 and S2); predicted-fail/observed-pass 0, predicted-pass/observed-fail 0 |
| Pair-level mismatch | 0 / 1,000 pairs; one-sided 95% upper bound on the pair mismatch probability 1-0.05^(1/1000) = **0.002991** (two-sided Wilson upper 0.00383) |
| Original order | all 926 tests pass in 3 repeats; models predict no target failure (match) |

Every failing direction was predicted, and every predicted failure occurred (86 predicted, 86 observed, same orders and targets).

## Deviations and engineering events (details in `ENGINEERING_LOG.md`)
- **D1 (validity rule for `@Ignore`).** The recorded order includes the `@Ignore` test `SentenceReaderTest.testSetDatagramSocket` (native "skipped 1"; not model-relevant). PLAN.md's "no skipped test" validity rule would have invalidated every run. `run.py` now records the natively skipped tests in metadata (`expected_ignored`) and accepts a run iff the started/ended order equals the requested order minus these tests, the skipped list is exactly those tests, and the JUnit counts are 925 run / 1 ignored. For the two original subjects this set is empty and validity is unchanged.
- **D2 (JUnit 3 class runner).** Pilot attempt 1 (runner v1) was aborted by the frozen rule at the first random order: `BODTest extends TestCase`; `JUnit38ClassRunner` ignores `Request.sortWith`, so its 19 methods ran in a different order than requested (runner defect, not a model outcome). Original-order runs of that attempt (3 valid) and the invalid record are kept as `pilot_attempt1_invalid_runner_v1.{jsonl,log}`. Repair (about 10 minutes): `../rare/OrderedJUnit.java` builds JUnit 3 classes as an ordered `TestSuite` run by the same `JUnit38ClassRunner`; all other classes use the unchanged default builders. The pilot was redone entirely (13 runs, same seed) before any formal run; no formal run ever used runner v1. The runner for the first two subjects is unchanged.
- The unmodified `OrderedJUnit.java`, `analyze.py`, `check_results.py`, `test_runner.py` were not changed; `run.py` gained per-subject settings (`DEFAULTS` = original constants, `SETTINGS['marine-api']` = rare values, incl. `runner_rare`, output `results_rare/`). `check_results.py` still passes for aismessages and http-request.
- No other deviation: no substitution, no tuning, no rerun, no early stop.

## Scope (PLAN_RARE.md)
Allowed: in this module, in the rare regime (f about 0.03), the S1/S2 outcome abstraction matched real JUnit outcomes order by order (0 mismatches in 2,000 orders, one-sided pair-level bound 0.003), including in all 86 orders where targets failed and in the absence of joint failures (B observed 0/1,000).
Not allowed: an empirical half-run saving (1,000 pairs cannot resolve it at f about 0.03); generalisation to other rare models, other JDKs, the deployed iDFlakies gate; or B <= f^2 as proven (B = 0 is only bounded by 0.003). The 12 targets share a small number of polluter-victim structures (two effective groups) and are not independent evidence.

## Reproduce
```sh
WORK=/tmp/icst-execution; export JAVA_HOME=$WORK/deps/jdk8u504-b01; export PATH=$JAVA_HOME/bin:$WORK/deps/apache-maven-3.9.9/bin:$PATH
# marine-api snapshot from codeload.github.com/ktuukkan/marine-api/tar.gz/af0003847db9ba822f67d4f1dceb8de3fe63250a into $WORK/subjects
# (in the module) mvn -B -ntp -Dmaven.repo.local=$WORK/deps/m2 test-compile dependency:build-classpath -Dmdep.outputFile=$WORK/marine-api.classpath
#                 mvn -B -ntp -Dmaven.repo.local=$WORK/deps/m2 test
mkdir -p $WORK/runner_rare; javac -cp "$(cat $WORK/marine-api.classpath)" -d $WORK/runner_rare empirical/execution/rare/OrderedJUnit.java
cd empirical/execution
for s in discover pilot sample; do python3 run.py $s marine-api --work $WORK --java $JAVA_HOME/bin/java; done
python3 check_results_rare.py && python3 check_results.py && python3 analyze_rare.py
```
Use a fresh `--output` for reruns; existing pilot/formal files are never overwritten.
