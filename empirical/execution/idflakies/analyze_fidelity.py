"""Fidelity analysis for PLAN_IDFLAKIES.md (first 20 GATE seeds per module).
usage: analyze.py OUT_DIR RESULT_DIR   (OUT_DIR contains gate/<subject>/seedNNNN.json.gz from server_run.py)
Writes summary.json and mismatches.json into RESULT_DIR."""
import gzip, json, sys, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'src'))
from common import load_modules, fails_single, class_of

REPO = {'aismessages': ('tbsalling/aismessages', '.'), 'http-request': ('kevinsawicki/http-request', './lib'),
        'marine-api': ('ktuukkan/marine-api', '.')}
FAIL = ('FAILURE', 'ERROR')

def model(name):
    repo, path = REPO[name]
    return next(m for m in load_modules() if m.slug.endswith('/' + repo) and m.path == path)

def contiguous(order):
    seen, prev = set(), None
    for t in order:
        c = class_of(t)
        if c != prev:
            if c in seen: return False
            seen.add(c); prev = c
    return True

def main():
    ex, out = Path(sys.argv[1]), Path(sys.argv[2])
    runs = collections.defaultdict(list)
    for f in sorted(ex.glob('gate/*/seed*.json.gz')):
        e = json.load(gzip.open(f, 'rt'))
        if e['seed'] <= 20: e['run'] = e['seed']; runs[e['subject']].append(e)
    summary, mism = {}, collections.defaultdict(list)
    for subj, rs in runs.items():
        m = model(subj); meta = json.loads(((HERE.parent / 'results' / subj / 'metadata.json') if (HERE.parent / 'results' / subj).is_dir() else (HERE.parent / 'results_rare' / subj / 'metadata.json')).read_text())
        dataset_inv = sorted(meta['tests'])
        S = collections.Counter(); per_run = []
        S['detector_runs'] = len(rs)
        cmp = {k: collections.Counter() for k in ('round', 'orig', 'confirm')}
        for e in rs:
            R = dict(run=e['run'], seed=e['seed'], exit_code=e['exit_code'], timeout=e['timeout'],
                     seconds=round(e['seconds'], 1), rounds_recorded=len(e.get('rounds', [])))
            complete = (not e['timeout'] and e['exit_code'] == 0 and e.get('mvn_build_success')
                        and len(e.get('rounds', [])) == e['rounds_requested'])
            R['complete'] = bool(complete); S['complete_runs'] += complete
            per_run.append(R)
            if 'tests' not in e: continue
            tests = e['tests']; inv = sorted(tests)
            if inv != dataset_inv: S['inventory_differs_from_dataset_metadata_runs'] += 1
            tset = set(tests)
            def names(order): return [tests[i] if isinstance(i, int) else i for i in order]
            def check_full(order_idx, cat, label, rec):
                order = names(order_idx)
                full = len(order) == len(tests) and set(order) == tset
                cont = contiguous(order)
                S[f'{cat}_orders'] += 1; S[f'{cat}_not_full_permutation'] += (not full); S[f'{cat}_not_class_contiguous'] += (not cont)
                if not full or not cont: mism['contiguity'].append(dict(subject=subj, run=e['run'], where=label, full=full, contiguous=cont))
                # outcomes
                for sem in ('S1', 'S2'):
                    for t in m.targets:
                        obs = rec['nonpass'].get(t.name) in FAIL if t.name in order else None
                        if obs is None:
                            cmp[cat][f'{sem}_target_missing'] += 1; continue
                        pred = fails_single(order, t, sem)
                        cmp[cat][f'{sem}_comparisons'] += 1
                        if pred != obs:
                            cmp[cat][f'{sem}_mismatches'] += 1
                            mism['outcome'].append(dict(subject=subj, run=e['run'], where=label, target=t.name, sem=sem,
                                                        predicted=pred, observed=rec['nonpass'].get(t.name, 'PASS')))
                tgt = {t.name for t in m.targets}
                nt = {k: v for k, v in rec['nonpass'].items() if k not in tgt and v in FAIL}
                S[f'{cat}_orders_with_nontarget_failures'] += bool(nt)
                S[f'{cat}_nontarget_failure_instances'] += len(nt)
                for k in nt: S['nontarget_failing_tests:' + k] += 1
                return order
            for i, o in enumerate(e['orig']): check_full(o['order'], 'orig', f'orig{i}', o)
            prev = prev_rev = prev_filtered = None
            rounds_orders = []
            for r in e['rounds']:
                order = check_full(r['order'], 'round', f"round{r['round']}", r)
                rounds_orders.append(order)
                S['rounds'] += 1
                S['rounds_with_recorded_new_detection'] += bool(r['filtered'])
                S['rounds_with_unfiltered_detection'] += bool(r['unfiltered'])
                S['unfiltered_detections'] += len(r['unfiltered']); S['recorded_new_detections'] += len(r['filtered'])
                S['recorded_new_detections_targets'] += sum(d['name'] in {t.name for t in m.targets} for d in r['filtered'])
                S['recorded_new_detections_nontargets'] += sum(d['name'] not in {t.name for t in m.targets} for d in r['filtered'])
                is_rev = prev is not None and order == prev[::-1]
                r['is_reverse_of_previous'] = is_rev
                if prev is not None:
                    S['transitions'] += 1
                    expected_rev = (not prev_filtered) and not prev_rev
                    S['transitions_reverse'] += is_rev; S['transitions_fresh'] += (not is_rev)
                    key = 'gate_expect_reverse' if expected_rev else 'gate_expect_fresh'
                    S[key] += 1
                    if is_rev == expected_rev:
                        S['gate_matches'] += 1
                    else:
                        S['gate_mismatches'] += 1
                        mism['gate'].append(dict(subject=subj, run=e['run'], round=r['round'], prev_filtered=[d['name'] for d in prev_f_list],
                                                 prev_was_reverse=prev_rev, expected='reverse' if expected_rev else 'fresh',
                                                 observed='reverse' if is_rev else 'fresh'))
                    if not prev_filtered and prev_rev: S['prev_empty_but_prev_was_reverse_fallback_transitions'] += 1
                prev, prev_rev, prev_filtered, prev_f_list = order, is_rev, bool(r['filtered']), r['filtered']
            # confirmation runs
            for c in e['confirmations']:
                S['confirmation_runs_' + c['kind']] += 1
                S['confirmation_expected_%s_got_same' % c['kind']] += (c['got'] == c['expected'])
                S['confirmation_expected_%s_got_different' % c['kind']] += (c['got'] != c['expected'])
                order = names(c['order'])
                full = len(order) == len(tests)
                S['confirmation_full_length'] += full
                S['confirmation_prefix_runs'] += (not full)
                S['confirmation_class_noncontiguous'] += (not contiguous(order))
                # predictions for the confirmed test only, with unrun tests appended after the target
                # (victim/brittle outcomes depend only on tests before the target)
                full_order = order + [t for t in tests if t not in set(order)]
                for t in m.targets:
                    if t.name == c['test']:
                        obs = c['got'] in FAIL
                        for sem in ('S1', 'S2'):
                            cmp['confirm'][f'{sem}_comparisons'] += 1
                            if fails_single(full_order, t, sem) != obs:
                                cmp['confirm'][f'{sem}_mismatches'] += 1
                                mism['confirm_outcome'].append(dict(subject=subj, run=e['run'], test=c['test'], sem=sem, observed=c['got']))
                S['confirmation_of_target_tests'] += any(t.name == c['test'] for t in m.targets)
            S['verified_lines_mismatched'] += sum(1 for v in e['verified_lines'] if v[1] != v[2])
            S['verified_lines'] += len(e['verified_lines'])
            S['identical_round_orders_within_run'] += len(rounds_orders) - len({tuple(o) for o in rounds_orders})
        # cross-run: orders shared across runs (seed independence check)
        summary[subj] = dict(counts=dict(S), comparisons={k: dict(v) for k, v in cmp.items()},
                             per_run=per_run, model_targets=[t.name for t in m.targets],
                             dataset_inventory_size=len(dataset_inv))
    (out).mkdir(parents=True, exist_ok=True)
    (out / 'summary.json').write_text(json.dumps(summary, indent=1))
    (out / 'mismatches.json').write_text(json.dumps(mism, indent=1))
    for s, v in summary.items():
        print('==', s); print(json.dumps(v['counts'], indent=0)[:3000]); print(v['comparisons'])
    print({k: len(v) for k, v in mism.items()})

if __name__ == '__main__': main()
