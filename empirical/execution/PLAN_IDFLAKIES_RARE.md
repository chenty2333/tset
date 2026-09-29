# Amendment 4: real iDFlakies in the rare-failure regime (frozen before any run)

Date: 2026-09-30. Written before marine-api was built on the server. The rules of
`PLAN_IDFLAKIES.md` and `PLAN_IDFLAKIES_POWER.md` apply unless changed below.

## Subject and variants

- Subject: ktuukkan/marine-api (root) at `af0003847db9ba822f67d4f1dceb8de3fe63250a`,
  the module of PLAN_RARE.md. It has 12 targets with model f = 1/32 and B = 0.
- Variants: the same three variants as before, GATE (unmodified), IID and PAIR,
  built from the same binaries.
- Settings: 20 rounds per detector run, with the seed shared across variants.
- The tool's default original-order handling (all_must_pass=true) is used. The
  fallback `all_must_pass=false` is allowed only if the tool aborts, and must then
  be documented.

## Sample and stopping

- Seeds 1..1000 per variant, scheduled round-robin over seeds.
- Hard stop at the server timer minus 20 minutes. The analysis uses the seeds
  completed for all three variants; completed counts are reported.

## Primary purpose and allowed claims

This is a fidelity check in the rare regime. It measures:

- class-contiguous full permutations;
- agreement of GATE decisions with the simulated rule;
- S1 agreement of target outcomes on every executed order, including original
  and confirmation runs.

The contrasts GATE-IID, PAIR-IID and PAIR-GATE are reported with 95% bootstrap
CIs. Theory bounds the gain by about f/(2e), roughly 0.6 pp, which is far below
the resolution of this sample. The contrasts may therefore be reported only as
consistent or inconsistent with the bound, never as a measured saving.
