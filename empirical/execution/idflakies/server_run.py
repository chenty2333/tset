"""Server-side scheduler/worker for PLAN_IDFLAKIES.md and PLAN_IDFLAKIES_POWER.md.

Each job = (variant, subject, seed): copy the prepared module tree (with the Surefire reports and mvn-test.log
produced by one `mvn test`), run the iDFlakies detector goal from that variant's Maven repo, extract the
per-round data to JSON.gz, delete the copy.

usage: server_run.py --workers 56 --seeds 400 --subject S --stop 'YYYY-mm-dd HH:MM' (server-local time)
"""
import argparse, concurrent.futures as cf, gzip, json, os, shutil, signal, subprocess, sys, threading, time
from pathlib import Path

R = Path('/root/icst')
SUBJ = {'aismessages': ('aismessages-7b0c4c708b6bb9a6da3d5737bcad1857ade8a931', '.'),
        'http-request': ('http-request-2d62a3e9da726942a93cf16b6e91c0187e6c0136', 'lib')}
sys.path.insert(0, str(R / 'scripts'))
import extract

def job(variant, subject, seed, timeout, stop_epoch):
    out = R / 'out' / variant / subject / f'seed{seed:04d}.json.gz'
    if out.exists(): return 'exists'
    # http-request runs take ~10 min: do not start one that cannot finish before the stop time
    margin = 2400 if subject == 'http-request' else 120
    if time.time() + margin > stop_epoch: return 'skipped-late'
    d, mod = SUBJ[subject]
    root = R / 'work' / f'{variant}-{subject}-{seed:04d}'
    if root.exists(): return 'running-elsewhere'
    root.mkdir(parents=True)
    shutil.copytree(R / 'base' / subject, root / 'repo', symlinks=True, copy_function=shutil.copy2)
    (root / 'tmp').mkdir()
    cwd = root / 'repo' / mod
    java = R / 'deps/jdk8u504-b01'
    cmd = [str(R / 'deps/apache-maven-3.9.9/bin/mvn'), '-B', '-ntp', '-o', f'-Dmaven.repo.local={R}/m2-{variant}',
           'edu.illinois.cs:idflakies-maven-plugin:2.0.1-SNAPSHOT:detect',
           '-Ddetector.detector_type=random-class-method', '-Ddt.randomize.rounds=20', f'-Ddt.seed={seed}']
    if subject == 'http-request':   # the tool's own reference (Surefire XML) order fails in the tool's runner: see REPORT.md
        cmd.append('-Ddt.detector.original_order.all_must_pass=false')
    env = dict(os.environ, JAVA_HOME=str(java), PATH=f'{java}/bin:' + os.environ['PATH'],
               JAVA_TOOL_OPTIONS=f'-Djava.io.tmpdir={root}/tmp -XX:+UseSerialGC -XX:TieredStopAtLevel=1 -XX:CICompilerCount=1 -XX:-UsePerfData -Xmx2g -Xshare:auto')  # per-JVM limits: 64-core defaults spawn dozens of GC/compiler threads
    t0 = time.time(); to = False
    with open(root / 'mvn.log', 'wb') as log:
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try: p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            to = True; os.killpg(p.pid, signal.SIGKILL); p.wait()
    (root / 'status.json').write_text(json.dumps(dict(subject=subject, variant=variant, run=seed, seed=seed, rounds=20,
        exit_code=p.returncode, timeout=to, seconds=time.time() - t0, cmd=cmd)))
    try:
        e = extract.extract(root, full=(variant == 'gate' and seed <= 20))
    except Exception as ex:   # keep the failure as data, never drop
        e = dict(subject=subject, variant=variant, run=seed, seed=seed, exit_code=p.returncode, timeout=to,
                 seconds=time.time() - t0, rounds_requested=20, error='extract failed: %r' % ex)
    e['log_tail'] = (root / 'mvn.log').read_text(errors='replace')[-3000:] if (to or p.returncode or 'error' in e or len(e.get('rounds', [])) != 20) else ''
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix('.tmp')
    with gzip.open(tmp, 'wt') as fh: json.dump(e, fh, separators=(',', ':'))
    tmp.rename(out)
    if seed <= 20 and variant == 'gate':   # keep the full tool log for the fidelity sample
        shutil.copy(root / 'mvn.log', out.with_name(f'seed{seed:04d}.mvn.log'))
    shutil.rmtree(root, ignore_errors=True)
    return f'{variant} {subject} {seed} exit={p.returncode} timeout={to} {time.time()-t0:.0f}s rounds={len(e.get("rounds", []))}'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=56); ap.add_argument('--seeds', type=int, default=2000)
    ap.add_argument('--stop', required=True); ap.add_argument('--subject', required=True)
    ap.add_argument('--timeout', type=int, default=1800); ap.add_argument('--first', type=int, default=1)
    a = ap.parse_args()
    stop = time.mktime(time.strptime(a.stop, '%Y-%m-%d %H:%M'))
    # seed-major round-robin over the three variants (PLAN_IDFLAKIES_POWER_NOTE2)
    jobs = [(v, a.subject, k) for k in range(a.first, a.seeds + 1) for v in ('gate', 'iid', 'pair')]
    log = open(R / f'scheduler-{a.subject}.log', 'a')
    lock = threading.Lock()
    def run(j):
        if time.time() > stop: return
        try: r = job(*j, a.timeout, stop)
        except Exception as ex: r = f'{j} EXC {ex!r}'
        with lock: log.write(time.strftime('%H:%M:%S ') + str(r) + '\n'); log.flush()
    with cf.ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(run, jobs))
    log.write('SCHEDULER DONE\n'); log.close()

if __name__ == '__main__': main()
