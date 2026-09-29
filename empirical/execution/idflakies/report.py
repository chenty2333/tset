"""Builds REPORT.md tables from summary.json (fidelity) and power.json (powered comparison).
usage: report.py RESULT_DIR   -> writes RESULT_DIR/tables.md (pasted into REPORT.md)"""
import json, sys
from pathlib import Path

def main():
    d = Path(sys.argv[1]); fid = json.loads((d / 'summary.json').read_text()); pw = json.loads((d / 'power.json').read_text())
    L = []
    for subj, v in fid.items():
        c = v['counts']; cm = v['comparisons']
        L += [f'### Fidelity sample: {subj} (GATE seeds 1-20)', '', '| quantity | value |', '|---|---|']
        keys = ['detector_runs', 'complete_runs', 'orig_orders', 'orig_not_full_permutation', 'orig_not_class_contiguous',
                'round_orders', 'round_not_full_permutation', 'round_not_class_contiguous', 'transitions', 'transitions_reverse',
                'transitions_fresh', 'gate_expect_reverse', 'gate_expect_fresh', 'gate_matches', 'gate_mismatches',
                'prev_empty_but_prev_was_reverse_fallback_transitions', 'rounds_with_recorded_new_detection', 'recorded_new_detections',
                'recorded_new_detections_targets', 'recorded_new_detections_nontargets', 'unfiltered_detections',
                'confirmation_runs_verify', 'confirmation_runs_confirmation-sampling', 'verified_lines', 'verified_lines_mismatched',
                'round_orders_with_nontarget_failures', 'round_nontarget_failure_instances', 'orig_orders_with_nontarget_failures',
                'inventory_differs_from_dataset_metadata_runs', 'identical_round_orders_within_run']
        for k in keys: L.append(f'| {k} | {c.get(k, 0)} |')
        L += ['', '| order class | target comparisons S1 | mismatches S1 | comparisons S2 | mismatches S2 |', '|---|---|---|---|---|']
        for k, x in cm.items():
            L.append(f"| {k} | {x.get('S1_comparisons', 0)} | {x.get('S1_mismatches', 0)} | {x.get('S2_comparisons', 0)} | {x.get('S2_mismatches', 0)} |")
        L.append('')
    for subj, i in pw.items():
        L += [f'### Powered comparison: {subj} ({i["targets"]} targets)', '',
              f'launched {i["launched"]}, complete {i["complete"]}, seeds complete for all three variants: {i.get("seeds_used", 0)}', '']
        if 'structure' in i:
            L += ['| variant | rounds | not full perm. | not class-contig. | transitions | reversals | tool-recorded rounds with new detection | S1 comp. | S1 mism. | S2 comp. | S2 mism. |', '|---|---|---|---|---|---|---|---|---|---|---|']
            for v, s in i['structure'].items():
                L.append(f"| {v} | {s.get('rounds',0)} | {s.get('not_full_permutation',0)} | {s.get('not_class_contiguous',0)} | {s.get('transitions',0)} | {s.get('reversals',0)} | {s.get('rounds_with_new_detection',0)} | {s['target_comparisons_S1']} | {s['mismatches_S1']} | {s['target_comparisons_S2']} | {s['mismatches_S2']} |")
            L.append('')
            L += ['Mean detected targets (% of module targets):', '', '| metric | variant | r=2 | r=4 | r=10 | r=20 |', '|---|---|---|---|---|---|']
            for m in ('KR', 'NR', 'TOOL'):
                for v in ('gate', 'iid', 'pair'):
                    L.append(f'| {m} | {v} | ' + ' | '.join(f"{i['detected_pct_mean'][f'{m}/{v}/r{r}']:.2f}" for r in (2, 4, 10, 20)) + ' |')
            L += ['', 'Paired contrasts in percentage points of targets detected, mean [95% bootstrap CI over seeds]:', '',
                  '| metric | contrast | r=2 | r=4 | r=10 | r=20 |', '|---|---|---|---|---|---|']
            for m in ('KR', 'NR', 'TOOL'):
                for a, b in (('gate', 'iid'), ('pair', 'iid'), ('pair', 'gate')):
                    L.append(f'| {m} | {a.upper()}-{b.upper()} | ' + ' | '.join(
                        "{mean_pp:+.2f} [{lo:+.2f}, {hi:+.2f}]".format(**i['contrasts'][f'{m}:{a}-{b}:r{r}']) for r in (2, 4, 10, 20)) + ' |')
        L.append('')
    (d / 'tables.md').write_text('\n'.join(L))

if __name__ == '__main__': main()
