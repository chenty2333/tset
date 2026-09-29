# Three unlisted failing tests in http-request/lib

Tests: `HttpRequestTest.postWithNumericQueryParams`, `postWithEscapedVarargsQueryParams`, `putWithVarargsQueryParams`.
Revision 2d62a3e9da726942a93cf16b6e91c0187e6c0136, module `lib` (163 tests, 161 in `HttpRequestTest`, 2 in `EncodeTest`).

Scripts (run from the workspace root): `infer.py` (fit per test), `fit_all.py` (whole-suite check on all 613 runs), `confirm.py` (14 confirmation executions -> `confirm_runs.jsonl`), `verify_confirm.py` (compares confirmation failures with the model). `inferred_models.json` is the output of `infer.py`. Nothing under `results/`, `run.py`, `analyze.py` or `check_results.py` was modified.

## 1. Dataset presence

Under `data/issta23/` the three names occur only in `original-orders/kevinsawicki_http-request-lib-2d62a3e-original_order` (lines 79, 101, 110), i.e. as ordinary members of the module's test list. They do not occur in `all-polluter-cleaner-info-combined.csv` in any role (victim, brittle, polluter, cleaner, state-setter) or in any other file or module. The module has 25 dataset targets, all victims, each with the single polluter `customConnectionFactory` and single cleaner `nullConnectionFactory`.

## 2. Inference from the 613 recorded runs (13 pilot + 600 formal, all valid)

Failure counts: formal 199 / 195 / 216 (pilot 5 / 7 / 5 of 13, including the original order). Every failure is a `java.lang.AssertionError` "expected:<X> but was:<null>" raised in the test itself (the server saw no query parameters).

For each test, the single best "precedes" predictor among the other 162 tests was `customConnectionFactory` (about 506-525 of 613 agree). It explains every failure: the test never failed in a run where `customConnectionFactory` came after it (0 failures in about 304 such runs), and it failed in 204/309, 202/309 and 221/309 of the runs where the polluter came before it. Adding one cleaner gave exact agreement only for `nullConnectionFactory` (613/613; the next best cleaner reached at most 533). A greedy search for further cleaners found none.

Fitted model for all three tests, in the dataset's semantics (S1):
victim; polluter `HttpRequestTest.customConnectionFactory`; cleaner `HttpRequestTest.nullConnectionFactory`. The test fails iff the polluter precedes it and the cleaner is not strictly between them.

| test | fails / 613 | exact agreement | exceptions |
|---|---|---|---|
| postWithNumericQueryParams | 204 | 613/613 | none |
| postWithEscapedVarargsQueryParams | 202 | 613/613 | none |
| putWithVarargsQueryParams | 221 | 613/613 | none |

The brittle model (fails iff no state-setter precedes) fits badly (about 88-107/613), so a victim is the correct role. `S2` coincides with `S1` here because the cleaner group has one member.

Stronger check (`fit_all.py`): the set of all failing tests in each of the 613 runs equals, exactly, the S1 prediction over the 25 dataset victims plus these 3 tests (613/613 runs). So no other test fails in any recorded run, and the three tests behave identically to the 25 known targets (same polluter, same cleaner). Their absence from the dataset is the only difference.

## 3. Mechanism (source citations)

Shared state is a static field in production code: `lib/src/main/java/com/github/kevinsawicki/http/HttpRequest.java:398` (`private static ConnectionFactory CONNECTION_FACTORY`), set by `setConnectionFactory` (lines 403-408) and read in `createConnection` (lines 1501/1503).
- Polluter, `HttpRequestTest.java:3457-3479`: installs a factory whose `create(URL otherUrl)` ignores its argument and opens the test's server `url` (line ~3470), and calls `HttpRequest.setConnectionFactory(factory)` at line 3477. Nothing resets it (the `@AfterClass tearDown` in `ServerTestCase.java:207-213` only stops servers).
- Cleaner, `HttpRequestTest.java:3486-3499`: `HttpRequest.setConnectionFactory(null)` at line 3495 restores `ConnectionFactory.DEFAULT`.
- Victims: `postWithNumericQueryParams` (`HttpRequestTest.java:2565-2589`), `postWithEscapedVarargsQueryParams` (2539-2559) and `putWithVarargsQueryParams` (2843-2864) append query parameters to `url` and then assert that the handler read them. Under the leaked factory the request goes to the bare server `url` and discards the appended query string, so `request.getParameter(...)` returns null. This matches the observed "expected:<2> but was:<null>", "expected:<us er> but was:<null>" and "expected:<user> but was:<null>".

## 4. Confirmation executions (14 runs, `confirm_runs.jsonl`)

Every run used all 163 tests, class-contiguous orders, a fresh JVM and temp dir, the run.py classpath (runner + test-classes + classes + http-request.classpath, cwd = `lib`, `-ea`, JDK 8u504) and the same validity checks as run.py (exit 0, no timeout, observed start/end order == requested, no skip/assumption, run count 163). All 14 were valid. P = customConnectionFactory, C = nullConnectionFactory, V1/V2/V3 = the three tests (order as in the title), CTRL = known victim `getWithVarargsQueryParams`.

| run | order (relevant part) | predicted | observed |
|---|---|---|---|
| A | P, V1, V2, V3, CTRL, ..., C | all fail | all fail |
| B | V1, V2, V3, CTRL, P, ..., C | all pass | all pass |
| C | P, C, V1, V2, V3, CTRL | all pass | all pass (0 failures in the suite) |
| D | P, V1, C, V2, V3, CTRL | V1 only | V1 only |
| E | C, P, V1, V2, V3, CTRL | all fail | all fail |
| F | P, ..., V1, V2, V3, CTRL, C (far from P) | all fail | all fail |
| G | V1, P, V2, V3, CTRL, C | V2, V3, CTRL | V2, V3, CTRL |
| H | V1, ..., P, V2, V3, CTRL, C | V2, V3, CTRL | V2, V3, CTRL |
| I | P, V2, C, V1, V3, CTRL | V2 only | V2 only |
| J | P, V3, C, V1, V2, CTRL | V3 only | V3 only |
| K | recorded original order | V1, V2, V3 fail; CTRL passes | as predicted |
| L | reverse original order | V1-V3 pass; CTRL fails | as predicted |
| M | as A with `EncodeTest` class first | all fail | all fail |
| N | V1-V3, CTRL, ..., P, C | all pass | all pass |

`verify_confirm.py`: in 14/14 runs the complete observed failing set equals the S1 prediction over the 25 dataset victims plus the three new tests (no unexpected failures, no missing ones). Run C shows that the single cleaner between polluter and victim suffices; D, I and J show that the cleaner cleans only victims that come after it; E shows a cleaner before the polluter does not help.

## 5. Conclusion

Consistent with three OD victims that the dataset missed. In this module they have the same polluter/cleaner pair as the 25 listed victims (`customConnectionFactory` / `nullConnectionFactory`). The evidence is: a model of exactly that form reproduces all 613 recorded outcomes of each test with no exception, the mechanism is directly visible in the source (static `CONNECTION_FACTORY`), and 14 targeted complete-suite runs matched every prediction. The evidence does not show why the dataset omits them (e.g. detection sampling in ISSTA'23), and it covers only this revision, JDK and runner. It does not exclude further polluters that never occurred before the victim in the runs; but the exact fit and the observed non-failure of other tests make this unlikely.

Semantics: the inferred model is exactly the paper's S1 (and S2, identical for a one-member cleaner group). They do not need brittle or state-setter semantics.

Suggested wording: "Our real executions also showed three further tests in http-request/lib (postWithNumericQueryParams, postWithEscapedVarargsQueryParams, putWithVarargsQueryParams) that behave as victims of the same polluter/cleaner pair but are absent from the ISSTA'23 dataset; we did not include them in the target set and report them only as a limitation/observation."
