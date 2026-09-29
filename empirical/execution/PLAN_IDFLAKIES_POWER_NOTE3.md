# Resource-budget reduction (2026-09-29, 18:30 JST)

At the user's request, reduce the target to finish before the existing 22:00 JST
deadline rather than pursue 2,000 runs per cell. This is a mid-run resource decision
based on measured throughput, not an effect estimate or a significance test.

- aismessages: 1,000 runs per variant, using seeds 1..500 and 1001..1500.
  The original scheduler already split seeds into 1..1000 and 1001..2000;
  retaining the first 500 of each shard preserves all already executed work.
- http-request: 400 runs per variant, using seeds 1..400.
- GATE, IID, PAIR retain identical seed sets within each module. No detector,
  metric, or comparison changes. Analyze the intersection of complete seeds;
  report incomplete runs separately and retain all existing output.
- Drain currently running Maven jobs before replacing the schedulers. Recovered
  runs retain the OS exit status and are marked as scheduler-resize recovery;
  their elapsed time is sampled at drain polling, not the original worker timer.
- Existing 22:00 JST hard deadline remains a fallback; a separate guard stops
  still-running experiment JVM groups at that time, leaving workers to extract
  partial results. Interrupted runs are not counted as complete.
- Final automatic full result retrieval is scheduled for 22:02 JST, with bounded
  retries aimed at completing by 22:10 JST. This requires the local machine to
  remain awake and connected. Results go to idflakies/server-results/.

The target counts are a throughput-based budget, not a statistical power claim.
