"""Compare confirm_runs.jsonl failures with the S1 model over the 25 dataset victims plus the 3 new tests.
Run from workspace root."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'empirical/src'))
from common import load_modules, Target, fails_single
m = [m for m in load_modules() if 'http-request' in m.slug and m.path == './lib'][0]
PFX = 'com.github.kevinsawicki.http.HttpRequestTest.'
P, C = PFX+'customConnectionFactory', PFX+'nullConnectionFactory'
new = [Target(PFX+n, 'victim', polluters={P: [(C,)]}) for n in
       ('postWithNumericQueryParams','postWithEscapedVarargsQueryParams','putWithVarargsQueryParams')]
targets = m.targets + new
tot = ok = 0
for l in open(Path(__file__).with_name('confirm_runs.jsonl')):
    r = json.loads(l); o = r['requested_order']
    pred = {t.name for t in targets if fails_single(o, t)}
    obs = set(r['failures'])
    print(r['name'], 'valid', r['valid'], 'pred', len(pred), 'obs', len(obs), 'exact set match', pred == obs,
          'obs-pred', sorted(obs-pred), 'pred-obs', sorted(pred-obs))
    tot += 1; ok += pred == obs
print(ok, '/', tot, 'runs where the observed failing set equals the model (25 targets + 3 new) exactly')
