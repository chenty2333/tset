"""Targeted confirmation runs (complete suite, class-contiguous, fresh JVM+tmpdir).
Run from workspace root: python3 empirical/execution/extra_tests/confirm.py
Appends nothing to results/; writes extra_tests/confirm_runs.jsonl (overwritten each run)."""
import json, os, sys, tempfile, time, signal, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT/'empirical/execution'))
from run import parse_events          # read-only import
WORK = Path('/tmp/icst-execution'); JAVA = WORK/'deps/jdk8u504-b01/bin/java'
CWD = WORK/'subjects/http-request-2d62a3e9da726942a93cf16b6e91c0187e6c0136/lib'
CP = os.pathsep.join(map(str, [WORK/'runner', CWD/'target/test-classes', CWD/'target/classes'])) \
     + os.pathsep + (WORK/'http-request.classpath').read_text().strip()
meta = json.load(open(ROOT/'empirical/execution/results/http-request/metadata.json'))
T = meta['tests']; PFX = 'com.github.kevinsawicki.http.HttpRequestTest.'
orig = [l.strip() for l in open(ROOT/'data/issta23/original-orders/kevinsawicki_http-request-lib-2d62a3e-original_order') if l.strip()]
assert sorted(orig) == sorted(T) and len(T) == 163
P, C = PFX+'customConnectionFactory', PFX+'nullConnectionFactory'
V = [PFX+n for n in ('postWithNumericQueryParams','postWithEscapedVarargsQueryParams','putWithVarargsQueryParams')]
CTRL = PFX+'getWithVarargsQueryParams'      # known dataset victim (positive control)
ENC = [t for t in T if not t.startswith(PFX)]
HR = [t for t in orig if t.startswith(PFX)]
rest = [t for t in HR if t not in [P, C, *V, CTRL]]

def build(head, tail=(), classes_first='HR'):
    used = set(head) | set(tail)
    body = list(head) + [t for t in rest if t not in used] + list(tail)
    body += [t for t in [CTRL] if t not in used and t not in body]
    hr = body
    assert sorted(hr) == sorted(HR), (len(hr), len(HR))
    return hr + ENC if classes_first == 'HR' else ENC + hr

def predict(order, v):   # dataset S1 semantics, polluter P, cleaner C
    pos = {t: i for i, t in enumerate(order)}
    return pos[P] < pos[v] and not (pos[P] < pos[C] < pos[v])

RUNS = {
 'A_P_then_V123':            build([P, *V, CTRL], [C]),
 'B_V123_then_P':            build([*V, CTRL, P], [C]),
 'C_P_C_then_V123':          build([P, C, *V, CTRL]),
 'D_P_V1_C_V2_V3':           build([P, V[0], C, V[1], V[2], CTRL]),
 'E_C_P_then_V123':          build([C, P, *V, CTRL]),
 'F_P_first_C_last_far':     build([P], [*V, CTRL, C]),
 'G_V1_P_V2_V3_C':           build([V[0], P, V[1], V[2], CTRL, C]),
 'H_no_C_before_V_P_mid':    build([V[0]], [P, V[1], V[2], CTRL, C]),  # V1 before P; V2,V3 after P, C last
 'I_P_V2_C_V1_V3':           build([P, V[1], C, V[0], V[2], CTRL]),
 'J_P_V3_C_V1_V2':           build([P, V[2], C, V[0], V[1], CTRL]),
 'K_original_order':         orig,
 'L_reverse_original':       list(reversed(orig)),
 'M_encodetest_first_P_V':   build([P, *V, CTRL], [C], classes_first='ENC'),
 'N_V_P_C_all_cleaned_late': build([*V, CTRL], [P, C]),
}
def run(name, order):
    with tempfile.TemporaryDirectory(prefix='icst-confirm-') as tmp:
        tmp = Path(tmp); inp, out = tmp/'order', tmp/'events'
        inp.write_text('\n'.join(order)+'\n')
        cmd = [str(JAVA), '-ea', '-Djava.io.tmpdir='+str(tmp), '-cp', CP, 'OrderedJUnit', 'run', str(inp), str(out)]
        t0 = time.monotonic()
        with tempfile.TemporaryFile() as log:
            p = subprocess.Popen(cmd, cwd=CWD, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            to = False
            try: p.wait(timeout=180)
            except subprocess.TimeoutExpired:
                to = True; os.killpg(p.pid, signal.SIGKILL); p.wait()
        ev = parse_events(out) if out.exists() else dict(started=[],ended=[],skipped=[],assumed=[],failures={},junit_result=None)
        valid = (p.returncode == 0 and not to and ev['junit_result'] is not None and ev['started'] == order
                 and ev['ended'] == order and not ev['skipped'] and not ev['assumed']
                 and set(ev['failures']) <= set(order) and ev['junit_result'][0] == len(order) == 163
                 and ev['junit_result'][2] == 0)
    return dict(name=name, requested_order=order, observed_order=ev['started'], valid=valid, exit_code=p.returncode,
                seconds=time.monotonic()-t0, junit_result=ev['junit_result'], failures=ev['failures'],
                predicted={t: predict(order, t) for t in [*V, CTRL]})
if __name__ == '__main__':
    rows = []
    with open(HERE/'confirm_runs.jsonl', 'w') as fh:
        for n, o in RUNS.items():
            r = run(n, o); fh.write(json.dumps(r)+'\n'); fh.flush(); rows.append(r)
            obs = {t.split('.')[-1]: (t in r['failures']) for t in [*V, CTRL]}
            ok = all((t in r['failures']) == r['predicted'][t] for t in [*V, CTRL])
            print(n, 'valid', r['valid'], 'match_pred', ok, 'nfail', len(r['failures']), obs)
