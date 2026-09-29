# Amendment 2: fidelity check with the unmodified iDFlakies tool — frozen before any run

Date: 2026-09-29. Written before iDFlakies was built or run. `PLAN.md` stays in
force for subjects, revisions, and environment unless this file changes them.

## Purpose

The paper simulates iDFlakies' outcome-gated reversal (GATE). This check runs the
**unmodified** tool and verifies three fidelity claims:

1. every order it executes is a class-contiguous permutation of the complete module;
2. its choice between a fresh order and the reverse of the previous order follows
   the simulated GATE rule: reverse iff the previous round detected no new flaky
   test and the previous order was not itself a reversal (with the tool's fallback
   to a fresh order when that reversal was already issued);
3. on each executed order, the known targets' observed outcomes equal the S1 and
   S2 predictions.

This is **not** a powered comparison of policies. Policy effect sizes on real
outcomes come from replaying the recorded pairs; see `replay/`.

## Tool and subjects

- iDFlakies from https://github.com/UT-SE-Research/iDFlakies at commit
  `f54b3f027fd39f3ecc510b8459a44ba9bea3d839`, built from source without source
  changes. Only build configuration may be adapted, and it must be documented.
- Detector type `random-class-method`, the paper's order model. Other settings stay
  at the tool's defaults unless a setting is needed to make the tool run; any such
  setting is documented.
- Subjects: `aismessages` (root) and `http-request/lib`, at the dataset revisions
  already used in `PLAN.md`. The only change to a subject is the plugin
  configuration needed to invoke iDFlakies.

## Sample

- Per module: 20 independent detector runs of 20 rounds each. Seeds are
  2026092901 to 2026092920, set if the tool exposes a seed property; otherwise
  record the tool's randomness source.
- Each detector run uses a fresh copy of the module directory, so no tool state
  carries over between runs.
- Timeouts: 30 minutes per detector run. Report any run that fails to complete; do
  not replace it.

## Analysis

From the tool's own per-round logs, report:

- per round: whether the order is a class-contiguous permutation of the complete
  inventory; whether it is the exact reverse of the previous round; the tool's
  recorded newly detected flaky tests;
- the fraction of round transitions whose fresh/reverse decision matches the
  GATE rule applied to the tool's own recorded detections;
- for every executed order: the observed outcome of each known target, compared
  with the S1/S2 prediction for that order;
- confirmation or rerun behaviour the tool performs, and non-target failures.

Any disagreement is a result and must be reported, never tuned away.

## Allowed claims

Fidelity of the simulated order model and gate rule to the unmodified tool on two
modules, and order-level agreement of the abstraction on the tool's own orders.
Not allowed: detection-rate comparisons between policies from these 40 detector
runs.
