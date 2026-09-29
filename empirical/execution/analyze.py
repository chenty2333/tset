"""Analyze frozen matched-order execution measurements; no fitting of S1/S2.

Pointwise Wilson intervals use independent pairs, never 600 independent orders.
Primary f is anchor-only. The reverse marginal and joint B are reported separately.
"""
from __future__ import annotations
import argparse
import collections
import csv
import json
import math
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run import model


def wilson(k,n,z=1.959963984540054):
    if n==0:return [None,None]
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [0.0 if k == 0 else max(0,c-h), 1.0 if k == n else min(1,c+h)]


def analyze_subject(path):
    meta=json.loads((path/'metadata.json').read_text())
    pilot=[json.loads(l) for l in (path/'pilot.jsonl').read_text().splitlines()]
    formal=[json.loads(l) for l in (path/'formal.jsonl').read_text().splitlines()]
    pairs=collections.defaultdict(dict)
    for r in formal:
        if r['direction'] in pairs[r['pair']]: raise ValueError('Duplicate pair direction')
        pairs[r['pair']][r['direction']]=r
    valid=[]; invalid=[]
    for pi,dd in sorted(pairs.items()):
        if set(dd)=={'anchor','reverse'} and all(r['valid'] for r in dd.values()):
            a,b=dd['anchor'],dd['reverse']
            assert a['order']==list(reversed(b['order']))
            assert a['actual_order']==a['order'] and b['actual_order']==b['order']
            valid.append((a,b))
        else: invalid.append(pi)
    n=len(valid)
    if not n:
        raise ValueError(f'{path.name}: no evaluable pairs; do not generate effect estimates')
    per=list(csv.DictReader(open(HERE.parent/'results/pertest_S1.csv')))
    mod=model(meta['subject'])
    per={r['test']:r for r in per if r['slug']==mod.slug and r['path']==mod.path}
    groups=collections.defaultdict(list)
    for r in pilot:groups[(r['kind'],r['order_id'])].append(r)
    unstable=[list(k) for k,rr in groups.items() if len({tuple(sorted(r['failures'])) for r in rr})>1]
    original=groups[('original',0)]
    result=dict(subject=meta['subject'],repository=meta['repository'],revision=meta['revision'],
                tests=len(meta['tests']),targets=len(meta['targets']),planned_pairs=meta['planned_pairs'],
                completed_valid_pairs=n,invalid_or_incomplete_pairs=invalid,
                attempted_runs=len(formal),valid_runs=sum(r['valid'] for r in formal),
                pilot_runs=len(pilot),unstable_repeated_pilot_orders=unstable,
                native_baseline=meta['native_baseline'],
                original_target_failures=sum(original[0]['observed']),
                original_all_failures=len(original[0]['failures']),
                original_target_predictions_match=all(r['observed']==r['predicted']['S1'] for r in original),
                formal_seconds=sum(r['seconds'] for r in formal),per_target=[])
    for j,name in enumerate(meta['targets']):
        cells=collections.Counter((a['observed'][j],b['observed'][j]) for a,b in valid)
        ka=cells[1,0]+cells[1,1]; kr=cells[0,1]+cells[1,1]; kb=cells[1,1]
        out=dict(test=name,reference_consistent=per[name]['original_outcome']=='pass',
                 n=n,n00=cells[0,0],n01=cells[0,1],n10=cells[1,0],n11=cells[1,1],
                 f_anchor=ka/n if n else None,f_anchor_ci95=wilson(ka,n),
                 f_reverse=kr/n if n else None,f_reverse_ci95=wilson(kr,n),
                 B=kb/n if n else None,B_ci95=wilson(kb,n),
                 B_zero_one_sided95_upper=1-math.pow(.05,1/n) if n and kb==0 else None,
                 model_f=float(per[name]['f_float']),model_B=float(per[name]['B_float']),semantics={})
        for sem in ('S1','S2'):
            pc=collections.Counter((a['predicted'][sem][j],b['predicted'][sem][j]) for a,b in valid)
            conf=collections.Counter()
            discordant_pairs=0
            for a,b in valid:
                discordant_pairs += any(r['predicted'][sem][j]!=r['observed'][j] for r in (a,b))
                conf.update((r['predicted'][sem][j],r['observed'][j]) for r in (a,b))
            out['semantics'][sem]=dict(
                predicted_pair_cells={f'{x}{y}':pc[x,y] for x,y in [(0,0),(0,1),(1,0),(1,1)]},
                confusion={f'pred{x}_actual{y}':conf[x,y] for x,y in [(0,0),(0,1),(1,0),(1,1)]},
                disagreeing_directions=conf[0,1]+conf[1,0],
                disagreeing_pairs=discordant_pairs,
                pair_disagreement_ci95=wilson(discordant_pairs,n))
        result['per_target'].append(out)
    # Module-level agreement does not count correlated targets as independent.
    for sem in ('S1','S2'):
        bad=sum(any(r['observed']!=r['predicted'][sem] for r in pair) for pair in valid)
        result[sem]=dict(disagreeing_target_outcomes=sum(t['semantics'][sem]['disagreeing_directions'] for t in result['per_target']),
                         target_outcome_comparisons=2*n*len(meta['targets']),
                         pairs_with_any_target_disagreement=bad,
                         pair_disagreement_ci95=wilson(bad,n),
                         zero_pair_disagreement_one_sided95_upper=1-math.pow(.05,1/n) if n and bad==0 else None)
    result['non_target_failures']=dict(collections.Counter(
        t for r in formal if r['valid'] for t in r['failures'] if t not in meta['targets']))
    return result


def write_outputs(results,out,texdir):
    out.mkdir(parents=True,exist_ok=True)
    (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
    fields=['subject','test','reference_consistent','n','n00','n01','n10','n11','f_anchor','f_anchor_ci95',
            'f_reverse','f_reverse_ci95','B','B_ci95','B_zero_one_sided95_upper','model_f','model_B',
            'S1_disagreeing_directions','S2_disagreeing_directions']
    with (out/'per_target.csv').open('w') as fh:
        writer=csv.DictWriter(fh,fieldnames=fields);writer.writeheader()
        for mod in results:
            for t in mod['per_target']:
                row={k:t[k] for k in fields if k in t};row['subject']=mod['subject']
                for sem in ('S1','S2'):row[sem+'_disagreeing_directions']=t['semantics'][sem]['disagreeing_directions']
                writer.writerow(row)
    if texdir:
        texdir.mkdir(parents=True,exist_ok=True)
        lines=[]
        for mod in results:
            ts=mod['per_target'];fs=[t['f_anchor'] for t in ts];bs=[t['B'] for t in ts]
            def ran(v):return f'{min(v):.3f}' if min(v)==max(v) else f'{min(v):.3f}--{max(v):.3f}'
            lines.append(f"{mod['subject']} & {mod['tests']}/{mod['targets']} & {mod['completed_valid_pairs']} & {ran(fs)} & {ran(bs)} & {mod['S1']['disagreeing_target_outcomes']}/{mod['S1']['target_outcome_comparisons']} " + r'\\')
        (texdir/'table_execution.tex').write_text('\n'.join(lines)+'\n')
        detailed=[]
        for mod in results:
            model_f=mod['per_target'][0]['model_f'];model_B=mod['per_target'][0]['model_B']
            assert all(t['model_f']==model_f and t['model_B']==model_B for t in mod['per_target'])
            detailed.append(r"\multicolumn{3}{l}{\textbf{" + mod['subject'] + "}, model $f=" + f"{model_f:.3f}" + ",$ $B=" + f"{model_B:.3f}" + r"$}\\")
            for t in mod['per_target']:
                def estimate(v,ci):return f"${v:.3f}\\;[{ci[0]:.3f},{ci[1]:.3f}]$"
                name=t['test'].split('.')[-1].replace('_',r'\_')
                detailed.append(r"\texttt{"+name+"} & "+estimate(t['f_anchor'],t['f_anchor_ci95'])+" & "+estimate(t['B'],t['B_ci95'])+r" \\")
        (texdir/'table_execution_targets.tex').write_text("\n".join(detailed)+"\n")
        values={
            'ExecModules':len(results),
            'ExecTargets':sum(r['targets'] for r in results),
            'ExecRuns':sum(r['valid_runs'] for r in results),
            'ExecComparisons':sum(r['S1']['target_outcome_comparisons'] for r in results),
            'ExecMismatches':sum(r['S1']['disagreeing_target_outcomes'] for r in results),
            'ExecPilotRuns':sum(r['pilot_runs'] for r in results),
            'ExecMarginalOutside':sum(not t['f_anchor_ci95'][0]<=t['model_f']<=t['f_anchor_ci95'][1]
                                      for r in results for t in r['per_target']),
        }
        (texdir/'macros_execution.tex').write_text('\n'.join(
            r'\newcommand{'+chr(92)+k+'}{'+format(v,',').replace(',',r'{,}')+'}' for k,v in values.items())+'\n')




def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,default=HERE/'results')
    p.add_argument('--texdir',type=Path)
    args=p.parse_args()
    results=[analyze_subject(args.results/name) for name in ('aismessages','http-request')]
    write_outputs(results,args.results,args.texdir)
    for r in results:
        print(json.dumps({k:v for k,v in r.items() if k not in ('per_target','non_target_failures')},indent=2))
        for t in r['per_target']:
            print(t['test'].split('.')[-1], 'f=',round(t['f_anchor'],4),'B=',round(t['B'],4),'mismatches=',t['semantics']['S1']['disagreeing_directions'])

if __name__=='__main__':main()
