"""Driver for PLAN_IDFLAKIES.md: one unmodified iDFlakies detector run per fresh module copy.

usage: run_detector.py SUBJECT RUN_INDEX(1..20) [--work DIR] [--rounds 20] [--timeout 1800]
Settings beyond the plan: -Ddt.detector.original_order.all_must_pass=false (see REPORT.md).
"""
import argparse, os, shutil, signal, subprocess, sys, time, json
from pathlib import Path

SUBJ = {  # dir under subjects/, module subdirectory
    'aismessages': ('aismessages-7b0c4c708b6bb9a6da3d5737bcad1857ade8a931', '.'),
    'http-request': ('http-request-2d62a3e9da726942a93cf16b6e91c0187e6c0136', 'lib'),
}
TOOLS = Path('/tmp/icst-execution')
JAVA = TOOLS / 'deps/jdk8u504-b01'
MVN = TOOLS / 'deps/apache-maven-3.9.9/bin/mvn'
M2 = Path('${HOME}/icst-idflakies/m2')
SRC = TOOLS / 'subjects'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('subject'); ap.add_argument('idx', type=int)
    ap.add_argument('--work', default='${HOME}/icst-idflakies/runs')
    ap.add_argument('--rounds', type=int, default=20)
    ap.add_argument('--timeout', type=int, default=1800)
    a = ap.parse_args()
    d, mod = SUBJ[a.subject]
    seed = 2026092900 + a.idx
    root = Path(a.work) / a.subject / f'run{a.idx:02d}'
    if root.exists(): sys.exit(f'{root} exists; refusing to overwrite')
    root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC / d, root / 'repo', symlinks=True)   # fresh copy of the subject tree
    cwd = root / 'repo' / mod
    cmd = [str(MVN), '-B', '-ntp', '-o', f'-Dmaven.repo.local={M2}',
           'edu.illinois.cs:idflakies-maven-plugin:2.0.1-SNAPSHOT:detect',
           '-Ddetector.detector_type=random-class-method', f'-Ddt.randomize.rounds={a.rounds}',
           f'-Ddt.seed={seed}', '-Ddt.detector.original_order.all_must_pass=false']
    env = dict(os.environ, JAVA_HOME=str(JAVA), PATH=f'{JAVA}/bin:' + os.environ['PATH'])
    t0 = time.time(); timed_out = False
    with open(root / 'mvn.log', 'wb') as log:
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try: p.wait(timeout=a.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True; os.killpg(p.pid, signal.SIGKILL); p.wait()
    (root / 'status.json').write_text(json.dumps(dict(
        subject=a.subject, run=a.idx, seed=seed, rounds=a.rounds, exit_code=p.returncode,
        timeout=timed_out, seconds=time.time() - t0, cmd=cmd, dtdir=str(cwd / '.dtfixingtools'))) + '\n')
    print(a.subject, a.idx, 'exit', p.returncode, 'timeout', timed_out, round(time.time() - t0), 's', flush=True)

main()
