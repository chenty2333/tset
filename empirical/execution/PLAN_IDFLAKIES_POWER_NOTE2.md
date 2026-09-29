# Note 2 to PLAN_IDFLAKIES_POWER.md (2026-09-29 ~17:15 JST, before any production run)

The server smoke test showed that one 20-round detector run of aismessages takes
about 30 s. At that speed, the planned 400 runs per cell would use the 64-thread
server for only a few minutes. Before any production run, and without looking at
any outcome, the sample is therefore changed as follows:

- The target rises to 2,000 detector runs per (module, variant), with seeds
  1..2000.
- All three variants (GATE, IID, PAIR) run round-robin from the start instead of
  running PAIR afterwards. This changes scheduling only.
- A module may start as soon as its pipeline passes the smoke test. Balance is
  required within a module, not across modules.
- The hard stop stays at 22:00 JST. The analysis uses only the seeds completed
  for all three variants of a module.
