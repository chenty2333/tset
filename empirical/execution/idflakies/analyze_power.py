"""Powered comparison (PLAN_IDFLAKIES_POWER.md) + structural checks for all variants.

usage: analyze_power.py OUT_DIR RESULT_DIR        (OUT_DIR = .../out with <variant>/<subject>/seedNNNN.json.gz)
Writes RESULT_DIR/power.json.
KR: target detected at its first failing round.  NR: detected once it has both passed and failed.
Contrasts are paired by seed, over seeds completed for all three variants of the module; 95% percentile bootstrap.
"""
import collections, glob, gzip, json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'src'))
from common import Sampler, Evaluator, class_of
sys.path.insert(1, str(HERE)); from analyze_fidelity import model, contiguous

FAIL = ('FAILURE', 'ERROR')
VARIANTS = ('gate', 'iid', 'pair')
RS = (2, 4, 10, 20)

def load(out, subject):
    recs = {v: {} for v in VARIANTS}
    for v in VARIANTS:
        for f in sorted(glob.glob(f'{out}/{v}/{subject}/seed*.json.gz')):
            e = json.load(gzip.open(f, 'rt'))
            recs[v][e['seed']] = e
    return recs

def complete(e):
    return (not e.get('error') and not e.get('timeout') and e.get('exit_code') == 0
            and len(e.get('rounds', [])) == e.get('rounds_requested', 20) == 20)

def boot(diff, rng, B=10000):
    n = len(diff)
    idx = rng.integers(0, n, size=(B, n))
    m = diff[idx].mean(axis=1)
    return float(diff.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))

def main():
    out, resd = sys.argv[1], Path(sys.argv[2]); resd.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260929)
    res = {}
    for subject in ('aismessages', 'http-request'):
        recs = load(out, subject)
        if not any(recs.values()): continue
        m = model(subject); T = len(m.targets); tn = [t.name for t in m.targets]
        info = dict(targets=T, launched={v: len(recs[v]) for v in VARIANTS},
                    complete={v: sum(complete(e) for e in recs[v].values()) for v in VARIANTS},
                    incomplete={v: sorted((s, e.get('exit_code'), e.get('timeout'), len(e.get('rounds', [])),
                                           (e.get('error') or '')[:60]) for s, e in recs[v].items() if not complete(e))[:50] for v in VARIANTS})
        ok = set.intersection(*[{s for s, e in recs[v].items() if complete(e)} for v in VARIANTS])
        seeds = sorted(ok); info['seeds_used'] = len(seeds)
        if not seeds: res[subject] = info; continue
        inv = sorted(recs['gate'][seeds[0]]['tests']) if seeds else []
        sampler = Sampler(sorted(inv)); ev = {s: Evaluator(m.targets, sampler, s) for s in ('S1', 'S2')}
        # per-variant arrays: fail[seed, round, target], and structure counters
        F, tool = {}, {}
        struct = {}
        for v in VARIANTS:
            Fv = np.zeros((len(seeds), 20, T), dtype=bool); tv = np.zeros((len(seeds), 20, T), dtype=bool)
            S = collections.Counter(); pred = {s: 0 for s in ('S1', 'S2')}; mis = {s: 0 for s in ('S1', 'S2')}
            toolcount = []
            for i, sd in enumerate(seeds):
                e = recs[v][sd]; tests = e['tests']
                if sorted(tests) != inv: S['inventory_mismatch'] += 1
                orders = []
                prev = prev_rev = None; prev_f = False
                for r in e['rounds']:
                    names = [tests[j] for j in r['order']]
                    orders.append(names)
                    S['rounds'] += 1
                    S['not_full_permutation'] += (len(names) != len(inv) or set(names) != set(inv))
                    S['not_class_contiguous'] += (not contiguous(names))
                    isrev = prev is not None and names == prev[::-1]
                    if prev is not None:
                        S['transitions'] += 1; S['reversals'] += isrev
                        exp = (not prev_f) and not prev_rev
                        S['gate_rule_reverse_expected'] += exp; S['gate_rule_matches'] += (exp == isrev)
                        if v == 'iid': S['iid_violations'] += isrev
                        if v == 'pair': S['pair_violations'] += (isrev != (not prev_rev))
                    for j, t in enumerate(tn):
                        Fv[i, r['round'], t is None or j] = False
                    for j, t in enumerate(tn):
                        Fv[i, r['round'], j] = r['nonpass'].get(t) in FAIL
                    S['rounds_with_new_detection'] += bool(r['filtered'])
                    for d in r['filtered']:
                        if d['name'] in tn: tv[i, r['round'], tn.index(d['name'])] = True
                    S['tool_detections'] += len(r['filtered'])
                    prev, prev_rev, prev_f = names, isrev, bool(r['filtered'])
                toolcount.append(sum(len(r['filtered']) for r in e['rounds']))
                # predictions vs observed, all rounds (vectorised evaluator, same semantics as fails_single)
                pos = np.empty((20, len(inv)), dtype=np.int32)
                for k, names in enumerate(orders):
                    for p, t in enumerate(names): pos[k, sampler.index[t]] = p
                for s in ('S1', 'S2'):
                    P = ev[s].fails(pos)
                    pred[s] += P.size; mis[s] += int((P != Fv[i]).sum())
            struct[v] = dict(S); struct[v].update(target_comparisons_S1=pred['S1'], mismatches_S1=mis['S1'],
                                                   target_comparisons_S2=pred['S2'], mismatches_S2=mis['S2'],
                                                   mean_tool_reported_tests_per_run=float(np.mean(toolcount)))
            F[v] = Fv; tool[v] = np.cumsum(tv, axis=1) > 0
        info['structure'] = struct
        def r0(v, sd):
            e = recs[v][sd]; return [e['tests'][j] for j in e['rounds'][0]['order']]
        info['round0_order_identical_across_variants_seeds'] = sum(r0('gate', sd) == r0('iid', sd) == r0('pair', sd) for sd in seeds)
        def firstfresh_match(sd):   # round 1: IID always fresh; GATE fresh iff gate rule says fresh
            g, i = recs['gate'][sd], recs['iid'][sd]
            gn = [g['tests'][j] for j in g['rounds'][1]['order']]; inn = [i['tests'][j] for j in i['rounds'][1]['order']]
            g0 = [g['tests'][j] for j in g['rounds'][0]['order']]
            return (gn == g0[::-1]) or (gn == inn)
        info['gate_round1_is_reverse_or_iid_round1_seeds'] = sum(firstfresh_match(sd) for sd in seeds)
        def kr(Fv): return np.cumsum(Fv, axis=1) > 0                       # [seed, r, target]
        def nr(Fv):
            return (np.cumsum(Fv, axis=1) > 0) & (np.cumsum(~Fv, axis=1) > 0)
        met = {'KR': kr, 'NR': nr}
        det = {}
        for mname, fn in met.items():
            for v in VARIANTS:
                det[(mname, v)] = fn(F[v]).mean(axis=2) * 100          # % of targets, [seed, r]
        for v in VARIANTS: det[('TOOL', v)] = tool[v].mean(axis=2) * 100
        info['detected_pct_mean'] = {f'{k[0]}/{k[1]}/r{r}': float(det[k][:, r - 1].mean()) for k in det for r in RS}
        info['curves_pct_mean'] = {f'{k[0]}/{k[1]}': [float(x) for x in det[k].mean(axis=0)] for k in det}
        info['contrasts'] = {}
        for mname in ('KR', 'NR', 'TOOL'):
            for a, b in (('gate', 'iid'), ('pair', 'iid'), ('pair', 'gate')):
                for r in RS:
                    d = det[(mname, a)][:, r - 1] - det[(mname, b)][:, r - 1]
                    mean, lo, hi = boot(d, rng)
                    info['contrasts'][f'{mname}:{a}-{b}:r{r}'] = dict(mean_pp=mean, lo=lo, hi=hi)
        res[subject] = info
    (resd / 'power.json').write_text(json.dumps(res, indent=1))
    print(json.dumps({s: {k: v for k, v in i.items() if k in ('launched', 'complete', 'seeds_used')} for s, i in res.items()}, indent=1))

if __name__ == '__main__': main()
