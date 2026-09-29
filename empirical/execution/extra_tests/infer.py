"""Statistical inference of victim/brittle models for 3 unlisted failing tests.
Run from workspace root: python3 empirical/execution/extra_tests/infer.py
Read-only on results/. Data: pilot.jsonl + formal.jsonl of http-request."""
import json, sys, itertools
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'empirical/src'))
from common import load_modules
R = ROOT/'empirical/execution/results/http-request'
meta = json.load(open(R/'metadata.json')); T = meta['tests']
recs = [json.loads(l) for f in ('pilot.jsonl','formal.jsonl') for l in open(R/f)]
print('records', len(recs), 'valid', sum(r['valid'] for r in recs))
recs = [r for r in recs if r['valid']]
POS = [{t: i for i, t in enumerate(r['order'])} for r in recs]   # index -> position
short = lambda t: t.split('.')[-1]
NAMES = ['postWithNumericQueryParams','postWithEscapedVarargsQueryParams','putWithVarargsQueryParams']
full = {short(t): t for t in T}
idx = {t: i for i, t in enumerate(T)}

def fail_of(r, v): return v in r['failures'] if False else (T[v] in r['failures'])

def victim_pred(pos, v, polls):  # polls: {p: [cleaners]}; S1
    for p, cl in polls.items():
        if pos[p] < pos[v] and not any(pos[p] < pos[c] < pos[v] for c in cl): return True
    return False

out = {}
for n in NAMES:
    v = idx[full[n]]
    y = [T[v] in r['failures'] for r in recs]
    print('\n==', n, 'fails', sum(y), 'of', len(y))
    ftypes = {}
    for r in recs:
        for f in r['failures'].get(T[v], []): ftypes[(f['type'], f['message'][:100], f.get('frame','')[:90])] = ftypes.get((f['type'], f['message'][:100], f.get('frame','')[:90]),0)+1
    for k, c in ftypes.items(): print('  failure', c, k)
    # single-polluter candidates: fail iff p before v
    cands = []
    for p in range(len(T)):
        if p == v: continue
        agree = sum((pos[p] < pos[v]) == f for pos, f in zip(POS, y))
        cands.append((agree, p))
    cands.sort(reverse=True)
    print(' top single-test "precedes" candidates (agree/%d):' % len(y), [(a, short(T[p])) for a, p in cands[:4]])
    # P(fail | p before v) and P(fail | p after v)
    p = cands[0][1]
    # cleaner search: among runs with p before v, which test between p and v explains passing
    before = [(pos, f) for pos, f in zip(POS, y) if pos[p] < pos[v]]
    print(' polluter cand', short(T[p]), 'runs p<v:', len(before), 'fail:', sum(f for _, f in before),
          '; runs p>v fail:', sum(f for pos, f in zip(POS, y) if pos[p] > pos[v]))
    best = []
    for c in range(len(T)):
        if c in (p, v): continue
        # fail iff p<v and not (p<c<v)
        agree = sum(((pos[p] < pos[v]) and not (pos[p] < pos[c] < pos[v])) == f for pos, f in zip(POS, y))
        best.append((agree, c))
    best.sort(reverse=True)
    print(' polluter+single cleaner top:', [(a, short(T[c])) for a, c in best[:3]])
    a, c = best[0]
    cl = [c]
    # greedy add of more cleaners (S1 semantic: any cleaner cleans)
    cur = a
    while cur < len(y):
        gain = []
        for c2 in range(len(T)):
            if c2 in (p, v) or c2 in cl: continue
            ag = sum(victim_pred(pos, v, {p: cl+[c2]} ) == f for pos, f in zip(POS, y))
            gain.append((ag, c2))
        gain.sort(reverse=True)
        if not gain or gain[0][0] <= cur: break
        cur = gain[0][0]; cl.append(gain[0][1])
    ag = sum(victim_pred(pos, v, {p: cl}) == f for pos, f in zip(POS, y))
    print(' FINAL victim model: polluter', short(T[p]), 'cleaners', [short(T[c]) for c in cl], 'exact agreement', ag, '/', len(y))
    exc = [i for i, (pos, f) in enumerate(zip(POS, y)) if victim_pred(pos, v, {p: cl}) != f]
    print(' exceptions (record idx):', exc[:20])
    # brittle model (state-setters): fail iff no setter precedes
    bag = sum((all(pos[s] > pos[v] for s in [p])) == f for pos, f in zip(POS, y))
    print(' (for reference: brittle model with setter=%s agrees %d)' % (short(T[p]), bag))
    out[n] = dict(polluter=T[p], cleaners=[T[c] for c in cl], agree=ag, total=len(y), fails=sum(y))
json.dump(out, open(Path(__file__).with_name('inferred_models.json'), 'w'), indent=1)
