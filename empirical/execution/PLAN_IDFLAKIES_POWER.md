# Amendment 3: powered policy comparison with the real iDFlakies tool — frozen before any run

Date: 2026-09-29, 16:50 JST. Written before any iDFlakies detector run. It extends
`PLAN_IDFLAKIES.md`, whose fidelity checks stay in force.

## Variants

Each variant is iDFlakies at commit `f54b3f027fd39f3ecc510b8459a44ba9bea3d839`
with detector type `random-class-method`.

- **GATE**: the unmodified tool.
- **IID**: the minimal patch that always requests a fresh shuffled order, so the
  tool never reverses.
- **PAIR** (secondary): the minimal patch that reverses after every fresh order,
  regardless of outcome.

Each patch must be a diff of only a few lines in the detector's decision code,
saved as `idflakies/patches/*.diff`. No other behaviour may change, including
confirmation reruns and result classification.

## Subjects, sample, stopping

- Subjects: `aismessages` and `http-request/lib` at the dataset revisions, run on
  the remote server only.
- 20 rounds per detector run. Detector-run seeds are 1, 2, 3, and so on, with the
  same seed list for every variant. If the tool exposes a seed, the same seed
  gives the same first order across variants.
- Target: 400 detector runs per (module, variant) for GATE and IID; then PAIR if
  time remains.
- Work is scheduled seed by seed, round-robin over variants and modules, so every
  cell grows at the same rate.
- Hard stop at 21:30 JST. The analysis uses only the seeds completed for **all**
  compared variants of a module; the completed counts are reported. No extension,
  and no dropping of runs.

## Outcomes

For every round, extract from the tool's logs the executed order and the
pass/fail outcome of each published target. Then:

- KR detection: a target is detected at its first failing round.
- NR detection: a target is detected once it has both passed and failed.
- Also report the tool's own reported flaky-test set.

The primary contrast is GATE - IID in detected targets (% of the module's
targets) at r = 2, 4, 10, 20 under KR and NR, with 95% bootstrap CIs over detector
runs. The secondary contrasts are PAIR - IID and PAIR - GATE.

## Pre-stated comparison

Compare each contrast with the replay of the recorded real executions
(`replay/`) and with the corrected simulator. Agreement within CIs supports the
simulation. Any disagreement is reported as a result.
