# Amendment 1: rare-failure execution check — frozen before any build

Date: 2026-09-29. Frozen before building or running any module named here.
`PLAN.md` stays in force for everything not changed below. Its two completed
modules (aismessages, http-request) and their results are not rerun, extended,
or modified.

## Purpose

The first check covered only models with f >= 1/3. The paper's argument concerns
rare failures. This amendment tests, in the rare regime, whether the S1/S2 model
predicts real outcomes order by order. It does **not** attempt to measure the
half-run saving directly: at f ~ 0.03, 1,000 pairs cannot resolve a 0.5-run
difference in expected time to first failure.

## Selection (fixed order; substitution only for technical ineligibility)

1. **Primary: ktuukkan/marine-api**, root module, dataset revision
   `af0003847db9ba822f67d4f1dceb8de3fe63250a`. 926 recorded tests; 12 OD targets,
   all reference-consistent, each with model f = 1/32 and B = 0 (S1).
2. Fallback 1: **hexagonframework/spring-data-ebean**, root, revision
   `dd11b97654982403b50dd1d5369cadad71fce410`. 48 tests; 1 target, f = 1/82.
3. Fallback 2: **wikidata/wikidata-toolkit**, `wdtk-dumpfiles`, revision
   `20de6f7f12319f54eb962ff6e8357b3f5695d54d`. 50 tests; 3 targets, f ~ 0.07.

A fallback is used only if the previous candidate is technically ineligible
under the `PLAN.md` rules: it fails to build at the dataset revision within
60 minutes of build/runner repair; its native inventory cannot be reconciled
with the recorded original order; a model-relevant test is missing; it needs
an external service; or the pilot is invalid. Model/actual disagreement,
original-order failure, or absent failures are results, never grounds for
substitution. The whole amendment has a 4-hour engineering budget.

## Protocol changes relative to PLAN.md

- Seeds: pilot 2026100101, formal 2026100102.
- Formal sample: **1,000 independent class-contiguous anchor orders**, each
  followed by its whole-order reversal in a separate fresh JVM.
- Per-suite timeout 300 s. Formal sampling cap is 12 hours per module. If the
  cap stops sampling, report the completed pairs; do not extend.
- Pilot, validity rules, order checking, fixtures, and JVM isolation are
  unchanged: original order x3, five random orders x2, excluded from estimation.
- All targets of the executed module are reported.

## Measurements and interpretation

These are as in `PLAN.md`. In addition, report:

- the number of anchor and reverse directions in which any target failed;
- S1/S2 agreement restricted to those failing directions;
- the pair-level one-sided 95% upper bound on the mismatch probability when
  no mismatch is observed.

With identical f for all 12 marine-api targets, target outcomes are expected to
be highly correlated, so the pair is the independent unit. Allowed claims:
order-level agreement of the abstraction for this module in the rare regime.
Not allowed: an empirical half-run saving, or generalisation to other rare
models, JDKs, or the deployed gate.
