#!/usr/bin/env python3
"""Audit normalized single-test profiles; no empirical data are bundled.
Input: {"provenance":..., "probabilities":"exact"|"estimated", "tests":[
 {"id":...,"module":...,"f":"1/4","B":"0"}, ...]}.
Use --both-outcomes when no prior opposite-outcome reference is supplied.
A source-style adaptive suite policy CANNOT be reconstructed from these scalars.
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict
from fractions import Fraction as Q
from pathlib import Path
from reversal_theory import budget, hitting_times, validate_profile

def number(x):
    if isinstance(x,bool) or not isinstance(x,(str,int,float)):
        raise ValueError('Probability must be a rational string or number')
    return Q(str(x))

def serial(x):
    if isinstance(x,Q):return {'exact':str(x),'decimal':float(x)}
    if isinstance(x,dict):return {k:serial(v) for k,v in x.items()}
    if isinstance(x,list):return [serial(v) for v in x]
    return x

def audit(data, runs, both):
    rows=data.get('tests',[])
    if not rows:raise ValueError('No tests supplied')
    seen=set(); profiles=[]
    for row in rows:
        if 'id' not in row or 'module' not in row:raise ValueError('Need id and module')
        key=(row['module'],row['id'])
        if key in seen:raise ValueError(f'Duplicate {key}')
        seen.add(key);f=number(row['f']);B=number(row['B']);validate_profile(f,B)
        profiles.append((row,f,B))
    reports=[]
    for r in runs:
        entries=[]; bymodule=defaultdict(list)
        for row,f,B in profiles:
            x=budget(f,B,r,both_outcomes=both)
            entries.append(x);bymodule[row['module']].append(x)
        keys=entries[0].keys()
        micro={k:sum((x[k] for x in entries),Q(0))/len(entries) for k in keys}
        macro={k:sum((sum((x[k] for x in rs),Q(0))/len(rs) for rs in bymodule.values()),Q(0))/len(bymodule) for k in keys}
        rare=[(row,f,B) for row,f,B in profiles if f<Q(1,10)]
        miss=sum((1-budget(f,B,r,both_outcomes=both)['iid'] for _,f,B in profiles),Q(0))
        raremiss=sum((1-budget(f,B,r,both_outcomes=both)['iid'] for _,f,B in rare),Q(0))
        reports.append({'runs':r,'test_weighted':micro,'module_weighted':macro,
                        'f_below_0.1_count':len(rare),'iid_miss_fraction_from_f_below_0.1':None if miss==0 else raremiss/miss})
    warnings=[]
    if data.get('probabilities')!='exact':
        warnings.append('Estimated f and B: plug-in curves only; no confidence interval or exact optimality certificate.')
    positive=[row['id'] for row,f,B in profiles if B>f*f]
    if positive:warnings.append('Positive covariance profiles exist; noninferiority is not certified for these tests.')
    return {'input_provenance':data.get('provenance','UNSPECIFIED'),
            'mode':'both outcomes within budget' if both else 'known passing reference outside budget',
            'tests':len(rows),'modules':len({r['module'] for r,_,_ in profiles}),
            'adaptive_policy':'NOT COMPUTABLE from f,B alone',
            'ceiling_scope':'independent blocks with equally distributed per-run marginals; not arbitrary pairing',
            'positive_covariance_test_ids':positive,'warnings':warnings,'reports':reports,
            'hitting_times':[{'id':row['id'],'module':row['module'],**hitting_times(f,B)} for row,f,B in profiles]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--runs',type=int,nargs='+',default=[2,4,10,20])
    p.add_argument('--both-outcomes',action='store_true')
    a=p.parse_args()
    try:
        result=audit(json.loads(a.input.read_text()),a.runs,a.both_outcomes)
    except (ValueError,KeyError,OSError,json.JSONDecodeError) as e:
        p.error(str(e))
    text=json.dumps(serial(result),indent=2,ensure_ascii=False)+'\n'
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text)
    else:print(text,end='')
if __name__=='__main__':main()
