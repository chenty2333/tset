# Real iDFlakies runs: fidelity check and powered policy comparison

Protocols: `../PLAN_IDFLAKIES.md`, `../PLAN_IDFLAKIES_POWER.md`, and Notes 1–3. All were frozen before the runs they govern; the hashes are in the `*.sha256` files.

- **Tool:** iDFlakies at commit f54b3f027fd39f3ecc510b8459a44ba9bea3d839, built from source.
- **Variants:** GATE is the unmodified tool. IID and PAIR are minimal patches of `RandomDetector.results()`; see `patches/`.
- **Settings:** detector type `random-class-method`, 20 rounds per detector run, and `-Ddt.seed` equal to the run's seed, shared across variants.
- **Server:** Ubuntu 24.04 with 64 hardware threads, JDK 8u504, and Maven 3.9.9. Each detector run used a fresh copy of the module.
- **Completed runs:** aismessages 1,000 detector runs per variant (seeds 1–500 and 1001–1500, Note 3); http-request 400 per variant (seeds 1–400). All runs completed, with none incomplete.
- **Result retrieval:** the planned 22:02 retrieval did not happen, because the local machine shut down. The results were copied from the restarted server on 2026-09-30 at 01:44 JST, after the server's own 22:00 deadline guard had stopped all work. Nothing was run after the deadline.
- **Deviation on http-request:** with its original-order input (the Surefire XML order), the tool's own runner fails 15 of the 25 targets, although native Maven passes all tests. The default `all_must_pass=true` then aborts before round 0, so http-request ran with `-Ddt.detector.original_order.all_must_pass=false` (see `server_run.py`). As a consequence, round-0 *passes* of those 15 targets count as new detections, and the GATE variant never reverses in round 1.
- **Reproduce the analysis:** `python3 analyze_fidelity.py server-results/out results && python3 analyze_power.py server-results/out results && python3 report.py results && python3 make_tex.py`

## Results
### Fidelity sample: aismessages (GATE seeds 1-20)

| quantity | value |
|---|---|
| detector_runs | 20 |
| complete_runs | 20 |
| orig_orders | 20 |
| orig_not_full_permutation | 0 |
| orig_not_class_contiguous | 0 |
| round_orders | 400 |
| round_not_full_permutation | 0 |
| round_not_class_contiguous | 0 |
| transitions | 380 |
| transitions_reverse | 183 |
| transitions_fresh | 197 |
| gate_expect_reverse | 183 |
| gate_expect_fresh | 197 |
| gate_matches | 380 |
| gate_mismatches | 0 |
| prev_empty_but_prev_was_reverse_fallback_transitions | 171 |
| rounds_with_recorded_new_detection | 26 |
| recorded_new_detections | 40 |
| recorded_new_detections_targets | 40 |
| recorded_new_detections_nontargets | 0 |
| unfiltered_detections | 546 |
| confirmation_runs_verify | 80 |
| confirmation_runs_confirmation-sampling | 202 |
| verified_lines | 282 |
| verified_lines_mismatched | 0 |
| round_orders_with_nontarget_failures | 0 |
| round_nontarget_failure_instances | 0 |
| orig_orders_with_nontarget_failures | 0 |
| inventory_differs_from_dataset_metadata_runs | 0 |
| identical_round_orders_within_run | 0 |

| order class | target comparisons S1 | mismatches S1 | comparisons S2 | mismatches S2 |
|---|---|---|---|---|
| round | 800 | 0 | 800 | 0 |
| orig | 40 | 0 | 40 | 0 |
| confirm | 282 | 0 | 282 | 0 |

### Fidelity sample: http-request (GATE seeds 1-20)

| quantity | value |
|---|---|
| detector_runs | 20 |
| complete_runs | 20 |
| orig_orders | 60 |
| orig_not_full_permutation | 0 |
| orig_not_class_contiguous | 0 |
| round_orders | 400 |
| round_not_full_permutation | 0 |
| round_not_class_contiguous | 0 |
| transitions | 380 |
| transitions_reverse | 154 |
| transitions_fresh | 226 |
| gate_expect_reverse | 154 |
| gate_expect_fresh | 226 |
| gate_matches | 380 |
| gate_mismatches | 0 |
| prev_empty_but_prev_was_reverse_fallback_transitions | 124 |
| rounds_with_recorded_new_detection | 102 |
| recorded_new_detections | 560 |
| recorded_new_detections_targets | 500 |
| recorded_new_detections_nontargets | 60 |
| unfiltered_detections | 5771 |
| confirmation_runs_verify | 1120 |
| confirmation_runs_confirmation-sampling | 2162 |
| verified_lines | 3282 |
| verified_lines_mismatched | 0 |
| round_orders_with_nontarget_failures | 241 |
| round_nontarget_failure_instances | 399 |
| orig_orders_with_nontarget_failures | 0 |
| inventory_differs_from_dataset_metadata_runs | 0 |
| identical_round_orders_within_run | 0 |

| order class | target comparisons S1 | mismatches S1 | comparisons S2 | mismatches S2 |
|---|---|---|---|---|
| round | 10000 | 0 | 10000 | 0 |
| orig | 1500 | 0 | 1500 | 0 |
| confirm | 3022 | 0 | 3022 | 0 |

### Powered comparison: aismessages (2 targets)

launched {'gate': 1000, 'iid': 1000, 'pair': 1000}, complete {'gate': 1000, 'iid': 1000, 'pair': 1000}, seeds complete for all three variants: 1000

| variant | rounds | not full perm. | not class-contig. | transitions | reversals | tool-recorded rounds with new detection | S1 comp. | S1 mism. | S2 comp. | S2 mism. |
|---|---|---|---|---|---|---|---|---|---|---|
| gate | 20000 | 0 | 0 | 19000 | 9169 | 1332 | 40000 | 0 | 40000 | 0 |
| iid | 20000 | 0 | 0 | 19000 | 0 | 1407 | 40000 | 0 | 40000 | 0 |
| pair | 20000 | 0 | 0 | 19000 | 10000 | 1332 | 40000 | 0 | 40000 | 0 |

Mean detected targets (% of module targets):

| metric | variant | r=2 | r=4 | r=10 | r=20 |
|---|---|---|---|---|---|
| KR | gate | 94.95 | 100.00 | 100.00 | 100.00 |
| KR | iid | 88.85 | 98.75 | 100.00 | 100.00 |
| KR | pair | 100.00 | 100.00 | 100.00 | 100.00 |
| NR | gate | 50.50 | 84.75 | 99.40 | 99.95 |
| NR | iid | 44.40 | 78.85 | 98.25 | 100.00 |
| NR | pair | 66.80 | 88.55 | 99.60 | 100.00 |
| TOOL | gate | 94.95 | 100.00 | 100.00 | 100.00 |
| TOOL | iid | 88.85 | 98.75 | 100.00 | 100.00 |
| TOOL | pair | 100.00 | 100.00 | 100.00 | 100.00 |

Paired contrasts in percentage points of targets detected, mean [95% bootstrap CI over seeds]:

| metric | contrast | r=2 | r=4 | r=10 | r=20 |
|---|---|---|---|---|---|
| KR | GATE-IID | +6.10 [+4.90, +7.45] | +1.25 [+0.80, +1.75] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| KR | PAIR-IID | +11.15 [+9.70, +12.65] | +1.25 [+0.80, +1.75] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| KR | PAIR-GATE | +5.05 [+4.10, +6.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| NR | GATE-IID | +6.10 [+4.85, +7.40] | +5.90 [+4.10, +7.75] | +1.15 [+0.55, +1.80] | -0.05 [-0.15, +0.00] |
| NR | PAIR-IID | +22.40 [+19.30, +25.45] | +9.70 [+7.60, +11.75] | +1.35 [+0.75, +2.00] | +0.00 [+0.00, +0.00] |
| NR | PAIR-GATE | +16.30 [+13.35, +19.25] | +3.80 [+2.10, +5.50] | +0.20 [-0.15, +0.55] | +0.05 [+0.00, +0.15] |
| TOOL | GATE-IID | +6.10 [+4.85, +7.40] | +1.25 [+0.80, +1.75] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| TOOL | PAIR-IID | +11.15 [+9.65, +12.65] | +1.25 [+0.80, +1.75] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| TOOL | PAIR-GATE | +5.05 [+4.15, +6.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |

### Powered comparison: http-request (25 targets)

launched {'gate': 400, 'iid': 400, 'pair': 400}, complete {'gate': 400, 'iid': 400, 'pair': 400}, seeds complete for all three variants: 400

| variant | rounds | not full perm. | not class-contig. | transitions | reversals | tool-recorded rounds with new detection | S1 comp. | S1 mism. | S2 comp. | S2 mism. |
|---|---|---|---|---|---|---|---|---|---|---|
| gate | 8000 | 0 | 0 | 7600 | 3031 | 2074 | 200000 | 0 | 200000 | 0 |
| iid | 8000 | 0 | 0 | 7600 | 0 | 2152 | 200000 | 0 | 200000 | 0 |
| pair | 8000 | 0 | 0 | 7600 | 4000 | 1620 | 200000 | 0 | 200000 | 0 |

Mean detected targets (% of module targets):

| metric | variant | r=2 | r=4 | r=10 | r=20 |
|---|---|---|---|---|---|
| KR | gate | 55.27 | 80.26 | 99.04 | 100.00 |
| KR | iid | 55.27 | 79.86 | 98.02 | 99.94 |
| KR | pair | 67.78 | 89.23 | 99.67 | 100.00 |
| NR | gate | 45.12 | 79.16 | 99.04 | 100.00 |
| NR | iid | 45.12 | 78.73 | 98.02 | 99.94 |
| NR | pair | 67.78 | 89.23 | 99.67 | 100.00 |
| TOOL | gate | 76.55 | 91.71 | 99.64 | 100.00 |
| TOOL | iid | 76.55 | 91.50 | 99.18 | 99.96 |
| TOOL | pair | 87.37 | 95.81 | 99.91 | 100.00 |

Paired contrasts in percentage points of targets detected, mean [95% bootstrap CI over seeds]:

| metric | contrast | r=2 | r=4 | r=10 | r=20 |
|---|---|---|---|---|---|
| KR | GATE-IID | +0.00 [+0.00, +0.00] | +0.40 [-0.46, +1.28] | +1.02 [+0.67, +1.38] | +0.06 [+0.02, +0.11] |
| KR | PAIR-IID | +12.51 [+9.86, +15.13] | +9.37 [+7.48, +11.22] | +1.65 [+1.27, +2.05] | +0.06 [+0.02, +0.11] |
| KR | PAIR-GATE | +12.51 [+9.85, +15.09] | +8.97 [+7.09, +10.83] | +0.63 [+0.34, +0.93] | +0.00 [+0.00, +0.00] |
| NR | GATE-IID | +0.00 [+0.00, +0.00] | +0.43 [-0.45, +1.31] | +1.02 [+0.67, +1.37] | +0.06 [+0.02, +0.11] |
| NR | PAIR-IID | +22.66 [+20.15, +25.12] | +10.50 [+8.64, +12.39] | +1.65 [+1.26, +2.05] | +0.06 [+0.02, +0.11] |
| NR | PAIR-GATE | +22.66 [+20.14, +25.20] | +10.07 [+8.28, +11.88] | +0.63 [+0.34, +0.93] | +0.00 [+0.00, +0.00] |
| TOOL | GATE-IID | +0.00 [+0.00, +0.00] | +0.21 [-0.17, +0.60] | +0.46 [+0.25, +0.68] | +0.04 [+0.01, +0.08] |
| TOOL | PAIR-IID | +10.82 [+9.61, +12.05] | +4.31 [+3.42, +5.21] | +0.73 [+0.52, +0.95] | +0.04 [+0.01, +0.08] |
| TOOL | PAIR-GATE | +10.82 [+9.62, +12.04] | +4.10 [+3.26, +4.95] | +0.27 [+0.13, +0.42] | +0.00 [+0.00, +0.00] |

# Rare regime: marine-api (PLAN_IDFLAKIES_RARE.md, frozen before the build)

- **Setup:** marine-api was built on the server at the dataset revision (native `mvn test`: 926 tests run, 0 failures, 1 natively skipped). The tool's default original-order handling was used (`all_must_pass=true`), and no fallback was needed. A smoke test with seed 9001 was kept separately in `/root/icst/out_smoke` and is excluded from the analysis.
- **Stop:** under load, one detector run took 5–18 minutes. The scheduler stopped issuing runs at the frozen hard stop (04:23 CST). The server was then shut down for billing reasons before the planned 05:31 JST retrieval, and the results were retrieved from the restarted server at 08:15 JST. No run was added after the stop.
- **Completed runs:** gate 188, iid 183, pair 183. Nine runs hit the 30-minute timeout, and 14 were interrupted at shutdown; all of these are excluded. 177 seeds are complete for all three variants.
- **Fidelity:** every executed order was a class-contiguous full permutation. GATE followed the simulated rule in all 3,363 of its decisions. All 127,440 target outcomes (42,480 per variant) matched S1 and S2, including the original-order and confirmation runs of the fidelity sample.
- **Contrasts:** KR GATE-IID at r=20 is +3.4 pp [-3.7, +10.6], and all CIs include 0. Theory bounds the gain by about f/(2e) ≈ 0.6 pp, so these contrasts are only *consistent with* the bound, as the plan states.

### Fidelity sample: marine-api (GATE seeds 1-20)

| quantity | value |
|---|---|
| detector_runs | 20 |
| complete_runs | 20 |
| orig_orders | 20 |
| orig_not_full_permutation | 0 |
| orig_not_class_contiguous | 0 |
| round_orders | 400 |
| round_not_full_permutation | 0 |
| round_not_class_contiguous | 0 |
| transitions | 380 |
| transitions_reverse | 195 |
| transitions_fresh | 185 |
| gate_expect_reverse | 195 |
| gate_expect_fresh | 185 |
| gate_matches | 380 |
| gate_mismatches | 0 |
| prev_empty_but_prev_was_reverse_fallback_transitions | 175 |
| rounds_with_recorded_new_detection | 10 |
| recorded_new_detections | 105 |
| recorded_new_detections_targets | 105 |
| recorded_new_detections_nontargets | 0 |
| unfiltered_detections | 129 |
| confirmation_runs_verify | 210 |
| confirmation_runs_confirmation-sampling | 8 |
| verified_lines | 218 |
| verified_lines_mismatched | 0 |
| round_orders_with_nontarget_failures | 0 |
| round_nontarget_failure_instances | 0 |
| orig_orders_with_nontarget_failures | 0 |
| inventory_differs_from_dataset_metadata_runs | 20 |
| identical_round_orders_within_run | 0 |

| order class | target comparisons S1 | mismatches S1 | comparisons S2 | mismatches S2 |
|---|---|---|---|---|
| round | 4800 | 0 | 4800 | 0 |
| orig | 240 | 0 | 240 | 0 |
| confirm | 218 | 0 | 218 | 0 |

### Powered comparison: marine-api (12 targets)

launched {'gate': 189, 'iid': 186, 'pair': 188}, complete {'gate': 188, 'iid': 183, 'pair': 183}, seeds complete for all three variants: 177

| variant | rounds | not full perm. | not class-contig. | transitions | reversals | tool-recorded rounds with new detection | S1 comp. | S1 mism. | S2 comp. | S2 mism. |
|---|---|---|---|---|---|---|---|---|---|---|
| gate | 3540 | 0 | 0 | 3363 | 1721 | 106 | 42480 | 0 | 42480 | 0 |
| iid | 3540 | 0 | 0 | 3363 | 0 | 101 | 42480 | 0 | 42480 | 0 |
| pair | 3540 | 0 | 0 | 3363 | 1770 | 106 | 42480 | 0 | 42480 | 0 |

Mean detected targets (% of module targets):

| metric | variant | r=2 | r=4 | r=10 | r=20 |
|---|---|---|---|---|---|
| KR | gate | 2.68 | 8.62 | 25.99 | 43.50 |
| KR | iid | 3.11 | 8.90 | 21.33 | 40.11 |
| KR | pair | 2.68 | 8.62 | 25.99 | 43.50 |
| NR | gate | 2.68 | 8.62 | 25.99 | 43.50 |
| NR | iid | 3.11 | 8.90 | 21.33 | 40.11 |
| NR | pair | 2.68 | 8.62 | 25.99 | 43.50 |
| TOOL | gate | 2.68 | 8.62 | 25.99 | 43.50 |
| TOOL | iid | 3.11 | 8.90 | 21.33 | 40.11 |
| TOOL | pair | 2.68 | 8.62 | 25.99 | 43.50 |

Paired contrasts in percentage points of targets detected, mean [95% bootstrap CI over seeds]:

| metric | contrast | r=2 | r=4 | r=10 | r=20 |
|---|---|---|---|---|---|
| KR | GATE-IID | -0.42 [-3.39, +2.40] | -0.28 [-5.08, +4.38] | +4.66 [-1.70, +11.02] | +3.39 [-3.67, +10.59] |
| KR | PAIR-IID | -0.42 [-3.39, +2.54] | -0.28 [-5.08, +4.52] | +4.66 [-1.69, +10.88] | +3.39 [-3.96, +10.59] |
| KR | PAIR-GATE | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| NR | GATE-IID | -0.42 [-3.39, +2.40] | -0.28 [-5.08, +4.38] | +4.66 [-1.69, +11.16] | +3.39 [-3.81, +10.59] |
| NR | PAIR-IID | -0.42 [-3.39, +2.40] | -0.28 [-5.08, +4.38] | +4.66 [-1.84, +11.02] | +3.39 [-3.95, +10.59] |
| NR | PAIR-GATE | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
| TOOL | GATE-IID | -0.42 [-3.39, +2.40] | -0.28 [-4.94, +4.24] | +4.66 [-1.55, +11.02] | +3.39 [-3.81, +10.73] |
| TOOL | PAIR-IID | -0.42 [-3.39, +2.54] | -0.28 [-4.94, +4.52] | +4.66 [-1.55, +11.02] | +3.39 [-3.95, +10.73] |
| TOOL | PAIR-GATE | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] | +0.00 [+0.00, +0.00] |
