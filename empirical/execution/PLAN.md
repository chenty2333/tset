# Bounded real-execution model check — frozen before builds

Date: 2026-09-28. Scope: at most two dataset modules; execution validation,
not a new detector or a representative benchmark. No result-driven replacement.

## Selection and budget

Use dataset revisions, without modifying production/test logic. Select small
standalone/root or shallow modules ahead of large reactors. The fixed candidate
order is:

- Reference-consistent stratum: **tbsalling/aismessages**, root,
  dataset revision `7b0c4c708b6bb9a6da3d5737bcad1857ade8a931`;
  44 recorded tests, 2 OD targets, both reference-consistent, both model B>0.
  If technically ineligible only: **ktuukkan/marine-api**, root,
  revision `af0003847db9ba822f67d4f1dceb8de3fe63250a` (926 tests, 12 targets).
- Contains-inconsistent stratum: **kevinsawicki/http-request**, `lib`,
  revision `2d62a3e9da726942a93cf16b6e91c0187e6c0136`;
  163 recorded tests, 25 OD targets, 6 reference-inconsistent, model B=0.
  If technically ineligible only: **wro4j/wro4j**, `wro4j-core`,
  revision `185ab607f1d649ca38b4a772831ee754cd4649fb` (851 tests, 15 targets).

These are feasibility-selected cases, not a random sample. All dataset OD targets
of each selected module are reported. Mismatch, absent OD failures, or original-
order failure are outcomes, never reasons to substitute another candidate.
At most 60 minutes build/runner repair per candidate and 4 hours total engineering
before reassessment. Do not upgrade project revisions or alter assertions/fixtures.
Local build-tool/JDK installation and documented build-only configuration are
allowed. External service requirements or uncontrollable runners are ineligibility,
not model failures. No global environment changes.

## Execution protocol

1. Build the original revision and discover the complete module's executable tests.
   Reconcile the discovered inventory with the recorded original order; explain
   differences, never silently run only polluters/victims. Missing model-relevant
   tests or inability to preserve ordinary class fixtures makes a target/module
   non-evaluable, not a negative result.
2. Use the project's JUnit lifecycle; one fresh JVM per complete suite order, all
   test classes in that JVM, normal before/after-class and per-method fixtures.
   Keep cwd/resources/environment fixed; isolate or reset filesystem state when
   required. Check the observed start order against the requested order on every
   execution. Infrastructure/initialization errors are not target assertion failures.
3. Run the recorded original order three times (if complete/executable) and five
   fixed random orders twice each, with pilot seed 2026092801. These pilot runs are
   excluded from estimation. Non-repeatable outcomes are reported as a departure
   from deterministic order-only semantics, not erased by majority vote.
4. Formal sample: **300 independent class-contiguous anchor orders**, RNG seed
   2026092802; independently shuffle classes and methods within classes. Execute
   each anchor and its exact whole-order reversal in separate reset runs. Include
   every executable module test. Maximum 180 seconds per suite run and 2 hours per
   module formal sampling. If this cap prevents 300 pairs, report the incomplete
   sample and timeouts; do not claim the planned sample completed. No extension
   based on significance. Abort a module on repeated infrastructure failures.
5. Evaluate S1 (primary) and S2 (sensitivity) on the **same actual orders**, without
   fitting cleaner sets or repairing the outcome model after seeing results.

## Measurements and interpretation

For every target: all four pair outcome counts; f from anchor outcomes and the
reverse marginal separately; B from joint failures; pointwise 95% Wilson intervals
for these Bernoulli proportions (one observation per independent pair). For zero
joint failures also give the exact one-sided 95% upper bound, not B=0. Report
model probabilities and matched-order predictions, and actual-vs-model outcome
disagreements, separating predicted-pass/observed-fail and the converse. Use
pair-cluster bootstrap for disagreement uncertainty if needed; do not treat the
600 directions as 600 independent observations.

Report build failures, inventory gaps, skips, infrastructure faults, non-OD
variability, and completed pairs explicitly. No extrapolation to all 289 models;
no claim that 300 pairs establish B<=f^2 for rare events. Use the existing paper's
simulation results unchanged. Add only the completed, interpretable execution
findings and their scope to the manuscript.
