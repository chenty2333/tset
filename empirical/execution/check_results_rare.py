"""Integrity check of results_rare/ (PLAN_RARE.md): regenerate orders from the frozen seeds and
verify recorded orders, reversals, observed-order equality and stored S1/S2 predictions.
Measurement consistency only; model/actual disagreements are data, not assertion failures.
"""
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / 'src'))
from run import model, order_indices, settings
from common import Sampler, class_of, fails_single

SUBJECT = 'marine-api'


def check(path):
    meta = json.loads((path / 'metadata.json').read_text())
    cfg = settings(meta['subject'])
    assert meta['pilot_seed'] == cfg['pilot_seed'] == 2026100101 and meta['formal_seed'] == cfg['formal_seed'] == 2026100102
    assert meta['planned_pairs'] == cfg['pairs'] == 1000
    tests, mod = meta['tests'], model(meta['subject'])
    sampler = Sampler(tests)
    assert set(tests) == set(mod.original) and len(tests) == len(mod.original)
    assert set(mod.relevant_tests()) <= set(tests)
    ign = set(meta['expected_ignored']); ign_idx = {tests.index(t) for t in ign}
    count = disagreements = valid_runs = 0
    for phase, seed, n_orders in [('pilot', cfg['pilot_seed'], 5), ('formal', cfg['formal_seed'], cfg['pairs'])]:
        rows = [json.loads(l) for l in (path / (phase + '.jsonl')).read_text().splitlines()]
        rng = np.random.default_rng(seed)
        orders = [order_indices(sampler, rng) for _ in range(n_orders)]
        seen = set()
        if phase == 'pilot':
            assert len(rows) == 13 and all(r['valid'] for r in rows)
        for r in rows:
            assert sorted(r['order']) == list(range(len(tests)))
            if phase == 'formal':
                key = (r['pair'], r['direction']); assert key not in seen; seen.add(key)
                expected = orders[r['pair']]
                if r['direction'] == 'reverse': expected = list(reversed(expected))
                else: assert r['direction'] == 'anchor'
            elif r['kind'] == 'original': expected = [sampler.index[t] for t in mod.original]
            else: expected = orders[r['order_id']]
            assert r['order'] == expected
            order = [tests[i] for i in r['order']]
            if phase == 'formal':
                blocks = [class_of(t) for i, t in enumerate(order) if i == 0 or class_of(order[i - 1]) != class_of(t)]
                assert len(blocks) == len(set(blocks)), 'anchor/reverse must be class-contiguous'
            if r['valid']:
                valid_runs += 1
                assert r['actual_order'] == [i for i in r['order'] if i not in ign_idx]  # observed == requested
                assert r['junit_result'][0] == len(tests) - len(ign) and r['junit_result'][2] == len(ign)
                assert r['observed'] == [int(t.name in r['failures']) for t in mod.targets]
                assert not r['timeout'] and r['exit_code'] == 0
            for sem in ('S1', 'S2'):
                scalar = [int(fails_single(order, t, sem)) for t in mod.targets]
                assert scalar == r['predicted'][sem], (phase, sem)
                if r['valid']: disagreements += sum(a != b for a, b in zip(scalar, r['observed']))
                count += len(scalar)
        if phase == 'formal':
            # A reverse record must follow its own anchor; pairs are contiguous in the file.
            for p in {k[0] for k in seen}:
                if (p, 'reverse') in seen: assert (p, 'anchor') in seen
            if (path / 'formal_status.json').exists():
                st = json.loads((path / 'formal_status.json').read_text())
                assert st['stop_reason'] in ('completed', 'time_cap', 'repeated_invalid')
    print(meta['subject'], count, 'scalar predictions checked over', valid_runs, 'valid runs; actual disagreements across S1/S2:', disagreements)


if __name__ == '__main__':
    check(HERE / 'results_rare' / SUBJECT)
