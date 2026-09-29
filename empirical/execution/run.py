"""Bounded execution validation. See PLAN.md before running.

Uses an external pinned subject checkout and project-resolved test classpath.
Whole-module discovery is cross-checked with its native Maven test inventory.
No production/test source rewriting, model fitting, or per-method JUnit requests.
"""
from __future__ import annotations
import argparse
import collections
import csv
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'src'))
from common import Sampler, Evaluator, load_modules, class_of

SUBJECTS = {
    'aismessages': ('tbsalling/aismessages', '.'),
    'http-request': ('kevinsawicki/http-request', './lib'),
    'marine-api': ('ktuukkan/marine-api', '.'),
}
PILOT_SEED = 2026092801
FORMAL_SEED = 2026092802
PAIRS = 300
# Constants of the two original subjects (PLAN.md); kept unchanged.
DEFAULTS = dict(pilot_seed=PILOT_SEED, formal_seed=FORMAL_SEED, pairs=PAIRS,
                timeout=180, cap=7200, output=HERE / 'results', extra_meta=False, runner='runner')
# Subject-specific settings frozen in PLAN_RARE.md; anything absent uses DEFAULTS.
SETTINGS = {
    'marine-api': dict(pilot_seed=2026100101, formal_seed=2026100102, pairs=1000,
                       timeout=300, cap=12 * 3600, output=HERE / 'results_rare', extra_meta=True,
                       runner='runner_rare'),  # compiled from rare/OrderedJUnit.java (JUnit 3 order control)
}


def settings(name):
    return {**DEFAULTS, **SETTINGS.get(name, {})}


def model(name):
    repo, path = SUBJECTS[name]
    return next(m for m in load_modules() if m.slug.endswith('/' + repo) and m.path == path)


def parse_events(path):
    started, ended, skipped, assumed, failures = [], [], [], [], {}
    done = None
    for line in path.read_text().splitlines():
        p = line.split('\t')
        if p[0] == 'START': started.append(p[1])
        elif p[0] == 'END': ended.append(p[1])
        elif p[0] == 'SKIP': skipped.append(p[1])
        elif p[0] == 'ASSUME': assumed.append(p[1])
        elif p[0] == 'FAIL': failures.setdefault(p[1], []).append({'type': p[2], 'message': '\t'.join(p[3:])})
        elif p[0] == 'FRAME' and p[1] in failures: failures[p[1]][-1]['frame'] = p[2]
        elif p[0] == 'DONE': done = list(map(int, p[1:]))
    return dict(started=started, ended=ended, skipped=skipped, assumed=assumed,
                failures=failures, junit_result=done)


def order_indices(sampler, rng):
    return np.argsort(sampler.positions(rng, 1)[0]).tolist()


class Experiment:
    def __init__(self, args):
        self.args, self.m = args, model(args.subject)
        self.cfg = settings(args.subject)
        self.work = args.work.resolve()
        repo = self.m.slug.split('/')[-1]
        self.cwd = self.work / 'subjects' / (repo + '-' + self.m.sha) / self.m.path.lstrip('./')
        self.java = args.java.resolve()
        self.out = (args.output or self.cfg['output']).resolve() / args.subject
        self.out.mkdir(parents=True, exist_ok=True)
        self.cp = os.pathsep.join(map(str, [self.work / self.cfg['runner'], self.cwd / 'target/test-classes', self.cwd / 'target/classes']))
        self.cp += os.pathsep + (self.work / (args.subject + '.classpath')).read_text().strip()
        self.jvm_flags = ['-ea']
        if args.subject == 'aismessages':
            self.jvm_flags.append('-Djava.util.logging.config.file=logging.properties')

    def process(self, mode, inp, out, tmp):
        cmd = [str(self.java), *self.jvm_flags, '-Djava.io.tmpdir=' + str(tmp),
               '-cp', self.cp, 'OrderedJUnit', mode, str(inp), str(out)]
        start = time.monotonic()
        # Kill the entire process group on timeout, including subprocesses.
        with tempfile.TemporaryFile() as log:
            p = subprocess.Popen(cmd, cwd=self.cwd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            timeout = False
            try:
                p.wait(timeout=self.cfg['timeout'])
            except subprocess.TimeoutExpired:
                timeout = True
                os.killpg(p.pid, signal.SIGKILL)
                p.wait()
            tail = ''
            if timeout or p.returncode:
                log.seek(max(0, log.tell() - 6000)); tail = log.read().decode(errors='replace')
        return dict(exit_code=p.returncode, timeout=timeout, seconds=time.monotonic()-start, error_output=tail)

    def discover(self):
        if (self.out / 'formal.jsonl').exists():
            raise RuntimeError('Do not overwrite discovery after formal sampling')
        native = []
        native_skipped = []
        baseline = collections.Counter()
        for path in sorted((self.cwd / 'target/surefire-reports').glob('TEST-*.xml')):
            root = ET.parse(path).getroot()
            for tc in root.iter('testcase'):
                native.append(tc.attrib['classname'] + '.' + tc.attrib['name'])
                baseline['tests'] += 1
                for status in ('failure', 'error', 'skipped'):
                    baseline[status] += int(tc.find(status) is not None)
                if tc.find('skipped') is not None:
                    native_skipped.append(tc.attrib['classname'] + '.' + tc.attrib['name'])
        if not native or len(native) != len(set(native)):
            raise RuntimeError('Missing or duplicate native test inventory')
        classes = sorted({class_of(t) for t in native})
        with tempfile.TemporaryDirectory(prefix='icst-discovery-') as tmp:
            tmp = Path(tmp); inp, out = tmp / 'classes', tmp / 'events'
            inp.write_text('\n'.join(classes) + '\n')
            proc = self.process('discover', inp, out, tmp)
            if proc['timeout'] or proc['exit_code'] or not out.exists():
                raise RuntimeError(proc)
            discovered = [l.split('\t', 1)[1] for l in out.read_text().splitlines() if l.startswith('TEST\t')]
        if sorted(discovered) != sorted(native):
            raise RuntimeError('JUnit/native inventory mismatch: ' + str(set(native)^set(discovered)))
        tests = sorted(discovered)
        missing_relevant = sorted(set(self.m.relevant_tests()) - set(tests))
        meta = dict(subject=self.args.subject, repository=self.m.slug, revision=self.m.sha,
                    module=self.m.path, tests=tests, native_baseline=dict(baseline),
                    original_count=len(self.m.original), missing_original=sorted(set(self.m.original)-set(tests)),
                    extra_discovered=sorted(set(tests)-set(self.m.original)),
                    missing_relevant=missing_relevant, targets=[t.name for t in self.m.targets],
                    jvm_flags=self.jvm_flags, pilot_seed=self.cfg['pilot_seed'], formal_seed=self.cfg['formal_seed'],
                    planned_pairs=self.cfg['pairs'],
                    java_version=subprocess.check_output([str(self.java), '-version'], stderr=subprocess.STDOUT, text=True).strip())
        if self.cfg['extra_meta']:
            # Tests the project's own native run skips (@Ignore). They cannot fail and are
            # expected to be reported as skipped, not started, in every ordered run.
            meta.update(timeout_seconds=self.cfg['timeout'], formal_cap_seconds=self.cfg['cap'],
                        expected_ignored=sorted(native_skipped))
        (self.out / 'metadata.json').write_text(json.dumps(meta, indent=2) + '\n')
        print(json.dumps({k:v for k,v in meta.items() if k not in ('tests','targets')}, indent=2), flush=True)
        if missing_relevant: raise RuntimeError('Missing model-relevant tests; non-evaluable')

    def initialize(self):
        self.meta = json.loads((self.out / 'metadata.json').read_text())
        self.tests = self.meta['tests']
        self.ignored = set(self.meta.get('expected_ignored', []))  # empty for the original subjects
        self.sampler = Sampler(self.tests)
        self.eval = {sem: Evaluator(self.m.targets, self.sampler, sem) for sem in ('S1','S2')}

    def execute(self, indices, **tags):
        requested = [self.tests[i] for i in indices]
        with tempfile.TemporaryDirectory(prefix='icst-suite-') as tmp:
            tmp = Path(tmp); inp, out = tmp / 'order', tmp / 'events'
            inp.write_text('\n'.join(requested) + '\n')
            proc = self.process('run', inp, out, tmp)
            events = parse_events(out) if out.exists() else dict(started=[],ended=[],skipped=[],assumed=[],failures={},junit_result=None)
        skipped = [t for t in requested if t in self.ignored]
        runnable = [t for t in requested if t not in self.ignored]
        valid = (proc['exit_code'] == 0 and not proc['timeout'] and events['junit_result'] is not None
                 and events['started'] == runnable and events['ended'] == runnable
                 and events['skipped'] == skipped and not events['assumed']
                 and set(events['failures']) <= set(requested)
                 and events['junit_result'][0] == len(runnable)
                 and events['junit_result'][2] == len(skipped))
        positions = np.argsort(indices)[None, :]
        predicted = {sem: ev.fails(positions)[0].astype(int).tolist() for sem,ev in self.eval.items()}
        observed = [int(t.name in events['failures']) for t in self.m.targets] if valid else None
        result = dict(**tags, **proc, valid=valid, order=indices,
                      actual_order=[self.sampler.index.get(t, t) for t in events['started']],
                      observed=observed, predicted=predicted, failures=events['failures'],
                      skipped=events['skipped'], assumed=events['assumed'], junit_result=events['junit_result'])
        return result

    def pilot(self):
        self.initialize()
        path = self.out / 'pilot.jsonl'
        if path.exists(): raise RuntimeError('Pilot already exists; preserve it')
        if set(self.m.original) != set(self.tests) or len(self.m.original) != len(self.tests):
            raise RuntimeError('Original inventory differs: explicit protocol amendment required')
        original = [self.sampler.index[t] for t in self.m.original]
        rng = np.random.default_rng(self.cfg['pilot_seed'])
        orders = [('original', 0, original, 3)] + [('random', i, order_indices(self.sampler, rng), 2) for i in range(5)]
        with path.open('x') as fh:
            for kind, oi, order, reps in orders:
                for rep in range(reps):
                    record = self.execute(order, phase='pilot', kind=kind, order_id=oi, repeat=rep)
                    fh.write(json.dumps(record) + '\n'); fh.flush()
                    print(self.args.subject,kind,oi,rep,'valid=',record['valid'],'failures=',len(record['failures']), 'seconds=',round(record['seconds'],2),flush=True)
                    if not record['valid']: raise RuntimeError('Invalid pilot; no formal sampling')

    def sample(self):
        self.initialize()
        pilot = [json.loads(l) for l in (self.out/'pilot.jsonl').read_text().splitlines()]
        if len(pilot) != 13 or not all(r['valid'] for r in pilot):
            raise RuntimeError('Pilot incomplete/invalid')
        path = self.out / 'formal.jsonl'
        # Never silently restart/overwrite an incomplete experiment.
        if path.exists(): raise RuntimeError('Formal output exists; explicit diagnosis needed before continuing')
        rng = np.random.default_rng(self.cfg['formal_seed'])
        start = time.monotonic()
        bad = 0
        status = dict(stop_reason='completed', completed_pair_attempts=0)
        with path.open('x') as fh:
            for pair in range(self.cfg['pairs']):
                order = order_indices(self.sampler, rng)
                if time.monotonic()-start >= self.cfg['cap']:
                    print('Formal module time cap reached',flush=True); status['stop_reason']='time_cap'; break
                for direction, indices in [('anchor',order),('reverse',list(reversed(order)))]:
                    record = self.execute(indices, phase='formal', pair=pair, direction=direction)
                    fh.write(json.dumps(record) + '\n'); fh.flush()
                    bad = bad + 1 if not record['valid'] else 0
                    if bad >= 2:
                        print('Repeated infrastructure/order faults; stopping',flush=True)
                        status['stop_reason']='repeated_invalid'; status['completed_pair_attempts']=pair+1
                        self.write_status(status,start); return
                status['completed_pair_attempts']=pair+1
                if (pair+1)%25 == 0:
                    print(self.args.subject,'completed pairs',pair+1,'seconds',round(time.monotonic()-start,1),flush=True)
        self.write_status(status,start)

    def write_status(self, status, start):
        # Only the rare-stratum subject records a stop reason; original outputs are untouched.
        if self.cfg['extra_meta']:
            status['formal_wall_seconds'] = time.monotonic() - start
            (self.out / 'formal_status.json').write_text(json.dumps(status, indent=2) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage',choices=['discover','pilot','sample'])
    ap.add_argument('subject',choices=SUBJECTS)
    ap.add_argument('--work',type=Path,default=Path('/tmp/execution'))
    ap.add_argument('--java',type=Path,default=Path('/tmp/execution/deps/jdk8u504-b01/bin/java'))
    ap.add_argument('--output',type=Path,default=None,help='default: subject-specific (results/ or results_rare/)')
    args=ap.parse_args()
    getattr(Experiment(args), args.stage)()


if __name__=='__main__': main()
