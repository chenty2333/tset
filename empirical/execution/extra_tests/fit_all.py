"""Whole-suite check on the 613 recorded runs: failing set == S1 model over 25 dataset victims + 3 new tests?
Run from workspace root."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'empirical/src'))
from common import load_modules, Target, fails_single
m = [m for m in load_modules() if 'http-request' in m.slug and m.path == './lib'][0]
R = ROOT/'empirical/execution/results/http-request/'
T = json.load(open(R/'metadata.json'))['tests']
PFX = 'com.github.kevinsawicki.http.HttpRequestTest.'
P, C = PFX+'customConnectionFactory', PFX+'nullConnectionFactory'
new = [Target(PFX+n, 'victim', polluters={P: [(C,)]}) for n in
       ('postWithNumericQueryParams','postWithEscapedVarargsQueryParams','putWithVarargsQueryParams')]
recs = [json.loads(l) for f in ('pilot','formal') for l in open(R/(f+'.jsonl'))]
ok = 0; cnt = {t.name: [0, 0] for t in new}
for r in recs:
    o = [T[i] for i in r['order']]
    pred = {t.name for t in m.targets + new if fails_single(o, t)}
    ok += pred == set(r['failures'])
    for t in new:
        cnt[t.name][r['phase'] == 'formal'] += t.name in r['failures']
print(len(recs), 'runs;', ok, 'have failing set exactly equal to model (25 targets + 3 new; ANY other failing test would break equality)')
print('failure counts (pilot, formal):', cnt)
