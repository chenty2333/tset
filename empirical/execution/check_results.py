"""Independent result integrity and scalar-prediction cross-checks.

This checks measurement consistency, not whether projects match the model.
Model/actual disagreements are data and never cause a failed assertion here.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from run import model, FORMAL_SEED, PILOT_SEED, order_indices
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from common import Sampler, class_of, fails_single
import numpy as np


def check(path):
    meta=json.loads((path/'metadata.json').read_text())
    tests=meta['tests'];mod=model(meta['subject']);sampler=Sampler(tests)
    assert set(tests)==set(mod.original)
    assert set(mod.relevant_tests())<=set(tests)
    count=0;observed_disagreements=0
    for phase,seed in [('pilot',PILOT_SEED),('formal',FORMAL_SEED)]:
        rows=[json.loads(l) for l in (path/(phase+'.jsonl')).read_text().splitlines()]
        rng=np.random.default_rng(seed)
        orders=[order_indices(sampler,rng) for _ in range(300 if phase=='formal' else 5)]
        for r in rows:
            assert sorted(r['order'])==list(range(len(tests)))
            if phase=='formal':
                expected=orders[r['pair']]
                if r['direction']=='reverse':expected=list(reversed(expected))
            elif r['kind']=='original':expected=[sampler.index[t] for t in mod.original]
            else:expected=orders[r['order_id']]
            assert r['order']==expected
            order=[tests[i] for i in r['order']]
            if phase=='formal':
                blocks=[class_of(t) for i,t in enumerate(order) if i==0 or class_of(order[i-1])!=class_of(t)]
                assert len(blocks)==len(set(blocks))
            if r['valid']:
                assert r['actual_order']==r['order']
                assert r['junit_result'][0]==len(tests)
                assert r['observed']==[int(t.name in r['failures']) for t in mod.targets]
                assert len(set(r['actual_order']))==len(tests)
            for sem in ('S1','S2'):
                scalar=[int(fails_single(order,t,sem)) for t in mod.targets]
                assert scalar==r['predicted'][sem],(phase,sem)
                if r['valid']:
                    observed_disagreements+=sum(a!=b for a,b in zip(scalar,r['observed']))
                count+=len(scalar)
    print(meta['subject'],count,'scalar predictions checked; actual disagreements across S1/S2:',observed_disagreements)


if __name__=='__main__':
    root=Path(__file__).resolve().parent/'results'
    for name in ('aismessages','http-request'):check(root/name)
