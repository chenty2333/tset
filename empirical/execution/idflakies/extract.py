"""Extract per-round data from an iDFlakies run directory (.dtfixingtools) into compact JSON.

usage: extract.py RUNS_DIR OUT_DIR   (RUNS_DIR/<subject>/runNN with status.json and repo/)
"""
import gzip, json, re, sys
from pathlib import Path

def load(p): return json.loads(Path(p).read_text())

def extract(run: Path, full=True):
    st = load(run / 'status.json')
    dt = run / 'repo' / ('lib' if st['subject'] == 'http-request' else '.') / '.dtfixingtools'
    out = dict(subject=st['subject'], variant=st.get('variant', 'gate'), run=st['run'], seed=st['seed'], exit_code=st['exit_code'],
               timeout=st['timeout'], seconds=st['seconds'], rounds_requested=st['rounds'])
    if not dt.exists():
        out['error'] = 'no .dtfixingtools'; return out
    log = (run / 'mvn.log').read_text(errors='replace')
    out['mvn_build_success'] = 'BUILD SUCCESS' in log
    out['log_flags'] = dict(no_passing_original='No passing order' in log,
                            exception_lines=len(re.findall(r'^\S*Exception', log, re.M)))
    ver = re.findall(r'^Verified (\S+), status: expected (\w+), got (\w+)$', log, re.M)
    out['verified_lines'] = [list(v) for v in ver]
    tests = [l for l in (dt / 'selected-tests').read_text().splitlines() if l]
    idx = {t: i for i, t in enumerate(tests)}
    out['tests'] = tests
    runs = dt / 'test-runs' / 'results'
    def res(id_):
        d = load(runs / id_)
        return d
    def compact(d):
        return dict(id=d['id'], order=[idx.get(t, t) for t in d['testOrder']],
                    nonpass={k: v['result'] for k, v in d['results'].items() if v['result'] != 'PASS'},
                    n_results=len(d['results']), results_keys_match_order=set(d['results']) == set(d['testOrder']))
    out['full'] = full
    out['orig'] = [compact(res(l.strip())) for l in (dt / 'detection-results/original-results-ids').read_text().splitlines() if l.strip()]
    rounds = []
    rdir = dt / 'detection-results/random-class-method'
    files = sorted(rdir.glob('round*.json'), key=lambda p: int(re.findall(r'\d+', p.name)[0])) if rdir.exists() else []
    for f in files:
        r = load(f); n = int(re.findall(r'\d+', f.name)[0])
        assert len(r['testRunIds']) == 1
        c = compact(res(r['testRunIds'][0]))
        def dts(k): return [dict(name=t['name'], type=t.get('type'), intended=t['intended']['result'],
                                 revealed=t['revealed']['result']) for t in r[k]['dts']]
        c.update(round=n, unfiltered=dts('unfilteredTests'), filtered=dts('filteredTests'), round_time=r['roundTime'])
        rounds.append(c)
    out['rounds'] = rounds
    conf = []
    for d in sorted((dt / 'detection-results').glob('random-class-method-*')):
        kind = d.name[len('random-class-method-'):]
        for sub in sorted(d.iterdir()):
            n = int(re.findall(r'\d+', sub.name)[0])
            for f in sorted(sub.iterdir()):
                m = re.match(r'(.*)-(PASS|FAILURE|ERROR|SKIPPED)-round(\d+)\.json$', f.name)
                r = load(f)
                test = m.group(1)
                rec = dict(kind=kind, absround=n, test=test, expected=m.group(2), file=f.name, id=r['id'],
                           order_len=len(r['testOrder']),
                           got=r['results'][test]['result'] if test in r['results'] else None,
                           nonpass={k: v['result'] for k, v in r['results'].items() if v['result'] != 'PASS'})
                if full: rec['order'] = [idx.get(t, t) for t in r['testOrder']]
                conf.append(rec)
    out['confirmations'] = conf
    out['total_test_runs_recorded'] = len(list(runs.iterdir()))
    return out

def main():
    runs, outd = Path(sys.argv[1]), Path(sys.argv[2])
    outd.mkdir(parents=True, exist_ok=True)
    for sd in sorted(runs.iterdir()):
        for run in sorted(sd.glob('run*')):
            if not (run / 'status.json').exists():
                print('incomplete (no status):', run); continue
            e = extract(run)
            (outd / f'{e["subject"]}-run{e["run"]:02d}.json').write_text(json.dumps(e, separators=(',', ':')))
            print(run.name, sd.name, 'rounds', len(e.get('rounds', [])))

if __name__ == '__main__': main()
