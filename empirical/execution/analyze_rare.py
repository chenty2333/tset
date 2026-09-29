"""Analysis of the rare-stratum execution check (PLAN.md + PLAN_RARE.md).

Reads results_rare/<subject>/{metadata,pilot,formal}.jsonl, writes summary.json,
per_target.csv and tex/*.tex under results_rare/.  Never writes to results/ or paper/.
No model fitting.  The pair is the independent unit; directions are not.
"""
from __future__ import annotations
import argparse, collections, csv, json, math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run import model
import importlib.util
_spec = importlib.util.spec_from_file_location('exec_analyze', HERE / 'analyze.py')  # avoid src/analyze.py name clash
_mod = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mod)
wilson = _mod.wilson

SUBJECT = 'marine-api'


def upper0(n):
    return 1 - math.pow(.05, 1 / n) if n else None


def analyze(path):
    meta = json.loads((path / 'metadata.json').read_text())
    ign = set(meta.get('expected_ignored', []))
    pilot = [json.loads(l) for l in (path / 'pilot.jsonl').read_text().splitlines()]
    formal = [json.loads(l) for l in (path / 'formal.jsonl').read_text().splitlines()]
    status = json.loads((path / 'formal_status.json').read_text()) if (path / 'formal_status.json').exists() else None
    tests, targets = meta['tests'], meta['targets']
    ign_idx = {tests.index(t) for t in ign}
    pairs = collections.defaultdict(dict)
    for r in formal:
        if r['direction'] in pairs[r['pair']]:
            raise ValueError('duplicate pair direction')
        pairs[r['pair']][r['direction']] = r
    valid, invalid = [], []
    for pi, dd in sorted(pairs.items()):
        if set(dd) == {'anchor', 'reverse'} and all(r['valid'] for r in dd.values()):
            a, b = dd['anchor'], dd['reverse']
            assert a['order'] == list(reversed(b['order']))
            for r in (a, b):
                assert r['actual_order'] == [i for i in r['order'] if i not in ign_idx]
            valid.append((a, b))
        else:
            invalid.append(pi)
    n = len(valid)
    if not n:
        raise ValueError('no evaluable pairs')
    mod = model(SUBJECT)
    per = {r['test']: r for r in csv.DictReader(open(HERE.parent / 'results/pertest_S1.csv'))
           if r['slug'] == mod.slug and r['path'] == mod.path}
    groups = collections.defaultdict(list)
    for r in pilot:
        groups[(r['kind'], r['order_id'])].append(r)
    unstable = [list(k) for k, rr in groups.items() if len({tuple(sorted(x['failures'])) for x in rr}) > 1]
    orig = groups[('original', 0)]
    dirs = [r for a, b in valid for r in (a, b)]
    res = dict(subject=meta['subject'], repository=meta['repository'], revision=meta['revision'],
               tests=len(tests), targets=len(targets), expected_ignored=sorted(ign),
               planned_pairs=meta['planned_pairs'], completed_valid_pairs=n,
               invalid_or_incomplete_pairs=invalid, stop_reason=status and status['stop_reason'],
               formal_wall_seconds=status and status['formal_wall_seconds'],
               attempted_runs=len(formal), valid_runs=sum(r['valid'] for r in formal),
               invalid_runs=sum(not r['valid'] for r in formal), timeouts=sum(r['timeout'] for r in formal),
               pilot_runs=len(pilot), pilot_valid_runs=sum(r['valid'] for r in pilot),
               pilot_seed=meta['pilot_seed'], formal_seed=meta['formal_seed'],
               unstable_repeated_pilot_orders=unstable, native_baseline=meta['native_baseline'],
               original_runs=[dict(target_failures=sum(r['observed']), all_failures=sorted(r['failures']),
                                   matches_S1=r['observed'] == r['predicted']['S1'],
                                   matches_S2=r['observed'] == r['predicted']['S2']) for r in orig],
               pilot_failures_any=sum(bool(r['failures']) for r in pilot),
               per_target=[])
    for j, name in enumerate(targets):
        cells = collections.Counter((a['observed'][j], b['observed'][j]) for a, b in valid)
        ka, kr, kb = cells[1, 0] + cells[1, 1], cells[0, 1] + cells[1, 1], cells[1, 1]
        mf = float(per[name]['f_float'])
        out = dict(test=name, reference_consistent=per[name]['original_outcome'] == 'pass', n=n,
                   n00=cells[0, 0], n01=cells[0, 1], n10=cells[1, 0], n11=cells[1, 1],
                   f_anchor=ka / n, f_anchor_ci95=wilson(ka, n), f_reverse=kr / n, f_reverse_ci95=wilson(kr, n),
                   B=kb / n, B_ci95=wilson(kb, n), B_zero_one_sided95_upper=upper0(n) if kb == 0 else None,
                   model_f=mf, model_B=float(per[name]['B_float']),
                   model_f_inside_anchor_ci=wilson(ka, n)[0] <= mf <= wilson(ka, n)[1], semantics={})
        for sem in ('S1', 'S2'):
            pc = collections.Counter((a['predicted'][sem][j], b['predicted'][sem][j]) for a, b in valid)
            conf = collections.Counter(); dp = 0
            for a, b in valid:
                dp += any(r['predicted'][sem][j] != r['observed'][j] for r in (a, b))
                conf.update((r['predicted'][sem][j], r['observed'][j]) for r in (a, b))
            out['semantics'][sem] = dict(
                predicted_pair_cells={f'{x}{y}': pc[x, y] for x, y in [(0, 0), (0, 1), (1, 0), (1, 1)]},
                confusion={f'pred{x}_actual{y}': conf[x, y] for x, y in [(0, 0), (0, 1), (1, 0), (1, 1)]},
                predicted_pass_observed_fail=conf[0, 1], predicted_fail_observed_pass=conf[1, 0],
                disagreeing_directions=conf[0, 1] + conf[1, 0], disagreeing_pairs=dp,
                pair_disagreement_ci95=wilson(dp, n))
        res['per_target'].append(out)
    # Order-level (direction) and pair-level agreement across all targets.
    def anyfail(r): return any(r['observed'])
    for sem in ('S1', 'S2'):
        d_bad = [r for r in dirs if r['observed'] != r['predicted'][sem]]
        pair_bad = sum(any(r['observed'] != r['predicted'][sem] for r in p) for p in valid)
        failing = [r for r in dirs if anyfail(r)]
        pred_failing = [r for r in dirs if any(r['predicted'][sem])]
        res[sem] = dict(
            target_outcome_comparisons=len(dirs) * len(targets),
            disagreeing_target_outcomes=sum(t['semantics'][sem]['disagreeing_directions'] for t in res['per_target']),
            directions=len(dirs), directions_with_any_disagreement=len(d_bad),
            pairs_with_any_target_disagreement=pair_bad, pair_disagreement_ci95=wilson(pair_bad, n),
            zero_pair_disagreement_one_sided95_upper=upper0(n) if pair_bad == 0 else None,
            directions_with_predicted_failure=len(pred_failing),
            failing_directions_observed=len(failing),
            failing_directions_disagreeing=sum(r['observed'] != r['predicted'][sem] for r in failing),
            failing_direction_target_comparisons=len(failing) * len(targets),
            failing_direction_target_mismatches=sum(a != b for r in failing for a, b in zip(r['observed'], r['predicted'][sem])),
            predicted_fail_directions_disagreeing=sum(r['observed'] != r['predicted'][sem] for r in pred_failing))
    res['failing_directions_by_type'] = dict(
        anchor=sum(anyfail(a) for a, b in valid), reverse=sum(anyfail(b) for a, b in valid),
        pairs_with_any_failing_direction=sum(anyfail(a) or anyfail(b) for a, b in valid),
        pairs_both_directions_failing=sum(anyfail(a) and anyfail(b) for a, b in valid))
    res['failing_target_counts_per_failing_direction'] = dict(sorted(collections.Counter(
        sum(r['observed']) for r in dirs if anyfail(r)).items()))
    res['non_target_failures'] = dict(collections.Counter(
        t for r in dirs for t in r['failures'] if t not in targets))
    res['total_pair_seconds'] = sum(r['seconds'] for r in formal)
    return res


def write(res, out):
    out.mkdir(parents=True, exist_ok=True)
    (out / 'summary.json').write_text(json.dumps(res, indent=2) + '\n')
    fields = ['subject', 'test', 'reference_consistent', 'n', 'n00', 'n01', 'n10', 'n11', 'f_anchor', 'f_anchor_ci95',
              'f_reverse', 'f_reverse_ci95', 'B', 'B_ci95', 'B_zero_one_sided95_upper', 'model_f', 'model_B',
              'model_f_inside_anchor_ci', 'S1_pred_pass_obs_fail', 'S1_pred_fail_obs_pass', 'S1_disagreeing_directions',
              'S2_pred_pass_obs_fail', 'S2_pred_fail_obs_pass', 'S2_disagreeing_directions']
    with (out / 'per_target.csv').open('w') as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader()
        for t in res['per_target']:
            row = {k: t[k] for k in fields if k in t}; row['subject'] = res['subject']
            for s in ('S1', 'S2'):
                x = t['semantics'][s]
                row[s + '_pred_pass_obs_fail'] = x['predicted_pass_observed_fail']
                row[s + '_pred_fail_obs_pass'] = x['predicted_fail_observed_pass']
                row[s + '_disagreeing_directions'] = x['disagreeing_directions']
            w.writerow(row)
    tex = out / 'tex'; tex.mkdir(exist_ok=True)
    ts = res['per_target']
    def ran(v): return f'{min(v):.3f}' if min(v) == max(v) else f'{min(v):.3f}--{max(v):.3f}'
    (tex / 'table_execution_rare.tex').write_text(
        f"{res['subject']} & {res['tests']}/{res['targets']} & {res['completed_valid_pairs']} & "
        f"{ran([t['f_anchor'] for t in ts])} & {ran([t['B'] for t in ts])} & "
        f"{res['S1']['disagreeing_target_outcomes']}/{res['S1']['target_outcome_comparisons']} " + r'\\' + '\n')
    def fmt(v): return format(v, ',').replace(',', r'{,}') if isinstance(v, int) else v
    vals = {
        'ExecRareTests': res['tests'], 'ExecRareTargets': res['targets'],
        'ExecRarePairs': res['completed_valid_pairs'], 'ExecRarePlannedPairs': res['planned_pairs'],
        'ExecRareRuns': res['valid_runs'], 'ExecRareInvalidRuns': res['invalid_runs'],
        'ExecRareTimeouts': res['timeouts'], 'ExecRarePilotRuns': res['pilot_runs'],
        'ExecRareComparisons': res['S1']['target_outcome_comparisons'],
        'ExecRareMismatchesSOne': res['S1']['disagreeing_target_outcomes'],
        'ExecRareMismatchesSTwo': res['S2']['disagreeing_target_outcomes'],
        'ExecRareFailingDirections': res['S1']['failing_directions_observed'],
        'ExecRareFailingAnchor': res['failing_directions_by_type']['anchor'],
        'ExecRareFailingReverse': res['failing_directions_by_type']['reverse'],
        'ExecRareFailingMismatchesSOne': res['S1']['failing_direction_target_mismatches'],
        'ExecRareFailingMismatchesSTwo': res['S2']['failing_direction_target_mismatches'],
        'ExecRareFailingComparisons': res['S1']['failing_direction_target_comparisons'],
        'ExecRareOrderMismatchesSOne': res['S1']['directions_with_any_disagreement'],
        'ExecRareOrderMismatchesSTwo': res['S2']['directions_with_any_disagreement'],
        'ExecRareDirections': res['S1']['directions'],
        'ExecRareFMin': f"{min(t['f_anchor'] for t in ts):.3f}", 'ExecRareFMax': f"{max(t['f_anchor'] for t in ts):.3f}",
        'ExecRareBMax': f"{max(t['B'] for t in ts):.3f}",
        'ExecRareZeroBound': (f"{res['S1']['zero_pair_disagreement_one_sided95_upper']:.4f}"
                              if res['S1']['zero_pair_disagreement_one_sided95_upper'] is not None else 'n/a'),
        'ExecRareNonTargetFailures': sum(res['non_target_failures'].values()),
    }
    (tex / 'macros_execution_rare.tex').write_text('\n'.join(
        r'\newcommand{\\' [:-1] + k + '}{' + str(fmt(v)) + '}' for k, v in vals.items()) + '\n')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--results', type=Path, default=HERE / 'results_rare')
    args = ap.parse_args()
    res = analyze(args.results / SUBJECT); write(res, args.results)
    print(json.dumps({k: v for k, v in res.items() if k != 'per_target'}, indent=2))
    for t in res['per_target']:
        print(t['test'].split('.')[-1], 'f=', round(t['f_anchor'], 4), 'rev=', round(t['f_reverse'], 4), 'B=', round(t['B'], 4),
              'cells', t['n00'], t['n01'], t['n10'], t['n11'])


if __name__ == '__main__':
    main()
