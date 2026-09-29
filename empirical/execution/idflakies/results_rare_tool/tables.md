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
