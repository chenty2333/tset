#!/usr/bin/env python3
"""Exact synthetic checks. This script does NOT contain ISSTA'23 real data."""
from fractions import Fraction as Q
from itertools import product, permutations
from pathlib import Path
import json, time
from reversal_theory import (all_trees, all_orders, tree_summary, common_failure,
    definition1_failure, bits_failure, budget, hitting_times, pair_without_replacement,
    gate_law, two_run_suite, set_partitions, two_level_formula)

ROOT=Path(__file__).resolve().parents[1]
def safe_json(x):
    if isinstance(x,Q):return str(x)
    if isinstance(x,dict):return {str(k):safe_json(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [safe_json(v) for v in x]
    return x

def joint_counts(tree, predicate):
    orders=list(all_orders(tree)); n=len(orders)
    flags=[predicate(o) for o in orders]
    rev=[orders.index(o[::-1]) for o in orders]
    f=Q(sum(flags),n); B=Q(sum(flags[i] and flags[rev[i]] for i in range(n)),n)
    return f,B,orders,flags,rev

def check_trees():
    rows=[]
    for n in range(2,7):
        models=total=0
        for tr in all_trees(tuple(range(n))):
            orders=list(all_orders(tr))
            assert len(orders)==len(set(orders))
            for p in range(1,n):
                P=set(range(1,p+1)); C=set(range(p+1,n))
                s=tree_summary(tr,P,C); cert=s.certificate()
                nf=nb=0
                for o in orders:
                    a=common_failure(o,P,C); b=common_failure(o[::-1],P,C)
                    nf+=a; nb+=a and b
                assert (s.f,s.B)==(Q(nf,len(orders)),Q(nb,len(orders)))
                assert s.f*s.f-s.B==cert['gap']
                assert cert['square']>=0 and cert['variance']>=0
                models+=1; total+=len(orders)
        rows.append({'leaves':n,'trees':len(all_trees(tuple(range(n)))),
                     'models':models,'order_instances':total})
    neutrals=0
    for tr in all_trees(tuple(range(5))):
        s=tree_summary(tr,{1},{2});f,B,*_=joint_counts(tr,lambda o:common_failure(o,{1},{2}))
        assert (s.f,s.B)==(f,B); assert s.certificate()['gap']==f*f-B
        neutrals+=1
    s=tree_summary(((0,(1,2)),3),{1,3},{2})
    assert (s.f,s.B,s.certificate()['gap'])==(Q(1,2),Q(1,4),0)
    return {'by_n':rows,'models':sum(r['models'] for r in rows),
            'order_instances':sum(r['order_instances'] for r in rows),
            'neutral_models':neutrals,'zero_gain_example':safe_json(s.certificate())}


def check_corrected_formula():
    models=order_instances=printed_different=0
    for n in range(2,8):
        for groups in set_partitions(tuple(range(n))):
            oo=list(all_orders(groups));T=len(oo)
            home=next(g for g in groups if 0 in g)
            for p in range(1,n):
                P=set(range(1,p+1));C=set(range(p+1,n))
                a=len(P.intersection(home));b=len(C.intersection(home))
                others=[(len(P.intersection(g)),len(C.intersection(g))) for g in groups if g is not home]
                formula=two_level_formula(a,b,others)
                nf=nb=0
                for o in oo:
                    left=common_failure(o,P,C);right=common_failure(o[::-1],P,C)
                    nf+=left;nb+=left and right
                assert (formula['f'],formula['B'],formula['J'])==(Q(nf,T),Q(nb,T),Q(nf-nb,T))
                if 'printed_J' in formula:
                    assert formula['printed_J']-formula['J']==formula['printed_excess']
                    printed_different+=formula['printed_J']!=formula['J']
                models+=1;order_instances+=T
    return {'models':models,'order_instances':order_instances,'printed_expression_mismatches':printed_different}


def check_scalar_bounds():
    profiles=budgets=nonpositive=0
    for d in range(1,25):
        for a in range(d+1):
            f=Q(a,d)
            for b in range(max(0,2*a-d),a+1):
                B=Q(b,d);q=1-2*f+B;delta=f*f-B
                profiles+=1
                for r in range(1,13):
                    m,e=divmod(r,2)
                    x=budget(f,B,r); y=budget(f,B,r,both_outcomes=True)
                    assert 0<=x['pair']<=x['independent_pair_ceiling']<=x['uniform_marginal_ceiling']<=1
                    assert 0<=y['pair']<=y['independent_pair_ceiling']<=y['uniform_marginal_ceiling']<=1
                    if B<=f*f:
                        assert x['gain']>=0 and y['gain']>=0
                        if r>=2:
                            assert x['gain']<=m*delta*(1-f)**(r-2)<=m*f*f*(1-f)**(r-2)
                    budgets+=1
                if 0<f<1:
                    ts=hitting_times(f,B)
                    assert ts['both_pair']==2+q*ts['first_pair']+B*(1+f)/(1-B)
                    saving=ts['first_iid']-ts['first_pair']
                    assert saving==delta/(f*(2*f-B)) and saving<=Q(1,2)
                    if B<=f*f:
                        nonpositive+=1
                        assert 0<=saving<=Q(1,2)
                        assert 0<=ts['both_iid']-ts['both_pair']<=1
    # Sharp half-run family, exact one-run sharp example.
    for d in range(2,51):
        f=Q(1,d); ts=hitting_times(f,Q(0))
        assert ts['first_iid']-ts['first_pair']==Q(1,2)
    ts=hitting_times(Q(1,2),Q(0))
    assert ts['both_iid']-ts['both_pair']==1
    return {'rational_profiles':profiles,'budget_cases':budgets,
            'nonpositive_interior_profiles':nonpositive,'sharp_half_run_cases':49,
            'rare_example_20_runs':budget(Q(1,100),Q(0),20)}


def check_budget_enumeration():
    cases=0
    for f,B in [(Q(1,4),Q(0)),(Q(1,2),Q(1,4)),(Q(11,16),Q(1,2))]:
        pairtypes=[((0,0),1-2*f+B),((0,1),f-B),((1,0),f-B),((1,1),B)]
        for r in range(1,9):
            m,e=divmod(r,2); hit=both=Q(0)
            for seq in product(pairtypes,repeat=m):
                values=tuple(v for vv,_ in seq for v in vv)
                weight=Q(1)
                for _,p in seq:weight*=p
                ends=[((),Q(1))] if not e else [((0,),1-f),((1,),f)]
                for suffix,p in ends:
                    bits=values+suffix;w=weight*p
                    hit+=w*bool(sum(bits)); both+=w*(0 in bits and 1 in bits)
            assert hit==budget(f,B,r)['pair']
            assert both==budget(f,B,r,both_outcomes=True)['pair']
            cases+=1
    return {'exact_outcome_product_cases':cases}


def check_counterexamples():
    # Printed formula and cross-pair ceiling counterexample.
    f,B,orders,flags,R=joint_counts(((0,2),1),lambda o:common_failure(o,{1},{2}))
    assert (f,B)==(Q(1,4),Q(0))
    assert budget(f,B,4)['pair']==Q(3,4)
    orbits=sorted({tuple(sorted((i,R[i]))) for i in range(4)})
    schedules=[]
    for orb_order in permutations(orbits):
        for orientations in product((0,1),repeat=2):
            schedule=tuple(j for orbit,bit in zip(orb_order,orientations) for j in (orbit[bit],orbit[1-bit]))
            schedules.append(schedule)
    assert all(any(flags[i] for i in s) for s in schedules)
    assert all(sum(s[t]==i for s in schedules)==len(schedules)//4 for t in range(4) for i in range(4))
    assert pair_without_replacement(2,1,2)==1
    wor_checks=0
    for K in range(1,31):
        for H in range(K+1):
            for m in range(K+1):
                w=pair_without_replacement(K,H,m)
                iid=1-(1-Q(H,K))**m
                assert 0<=w-iid<=min(Q(1),Q(m*(m-1),2*K))
                wor_checks+=1
    # Adaptive gate: conditional second run is not uniform.
    rev=(1,0,3,2);gate=(Q(0),Q(1),Q(0),Q(0))
    dist=gate_law(rev,gate)
    assert dist==(Q(7,16),Q(3,16),Q(3,16),Q(3,16))
    F={0};hit=Q(0)
    for a in range(4):
        if a in F:hit+=Q(1,4)
        else:hit+=Q(1,4)*(gate[a]*(rev[a] in F)+(1-gate[a])*Q(1,4))
    assert hit==Q(5,8)>Q(1,2)
    # Same per-target f,B, different adaptive suite outcomes.
    same=[]
    for masks in ((1,2,0,0),(1,0,2,0)):
        for target in (1,2):
            assert sum(bool(mask&target) for mask in masks)==1
            assert not any(masks[i]&target and masks[rev[i]]&target for i in range(4))
        same.append({pol:two_run_suite(masks,rev,pol) for pol in ('iid','gate','pair')})
    assert same[0]['gate']['expected_count']==Q(5,8)
    assert same[1]['gate']['expected_count']==Q(9,8)
    # Existing physical two-target counterexample, not a JUnit integration claim.
    tr=((0,1),(2,3),(4,))
    oo=list(all_orders(tr)); rr=tuple(oo.index(o[::-1]) for o in oo)
    masks=[]
    for order in oo:
        A=Bbit=False; mask=0
        for test in order:
            if test==0 and A:mask|=1
            elif test==1:Bbit=True
            elif test==2 and Bbit:mask|=2
            elif test==3:A=True
            elif test==4:A=Bbit=False
        masks.append(mask)
    metrics={pol:two_run_suite(tuple(masks),rr,pol) for pol in ('iid','gate','pair')}
    assert metrics['iid']['expected_count']==Q(10,9)
    assert metrics['gate']['expected_count']==Q(8,9)
    assert metrics['pair']['expected_count']==Q(4,3)
    # The opposite ordering between the gate and unconditional pairing.
    tr4=((0,1,2),(3,));oo4=list(all_orders(tr4));rr4=tuple(oo4.index(o[::-1]) for o in oo4)
    masks4=[]
    for order in oo4:
        a=b=False;mask=0
        for test in order:
            if test==3:a=b=True
            elif test==2:b=False
            elif test==0 and a:mask|=1
            elif test==1 and b:mask|=2
        masks4.append(mask)
    metrics4={pol:two_run_suite(tuple(masks4),rr4,pol) for pol in ('iid','gate','pair')}
    assert metrics4['iid']['expected_count']==Q(19,16)
    assert metrics4['gate']['expected_count']==Q(25,16)
    assert metrics4['pair']['expected_count']==Q(3,2)
    # General Definition 1, nested (NOT a class-only counterexample).
    nested=(((0,(1,4)),(2,5)),3);cs={1:{4},2:{4},3:{5}}
    # Polluters and cleaners are disjoint, and the triple-based extraction
    # definition also recovers exactly these cleaner sets.
    for p in cs:
        for c in set(range(1,6))-{p}:
            assert (not bits_failure((p,c,0),cs)) == (c in cs[p])
    for o in all_orders(nested):
        assert definition1_failure(o,cs)==bits_failure(o,cs)
        pos={t:i for i,t in enumerate(o)}
        a=int(pos[4]<pos[1]);u=int(pos[4]<pos[0]);w=int(pos[2]<pos[0]);z=int(pos[3]<pos[0])
        formula=bool(z*(1-w) or (1-u)*w or u*a)
        mirror=bool((1-z)*w or u*(1-w) or (1-u)*(1-a))
        assert formula==definition1_failure(o,cs)
        assert mirror==definition1_failure(o[::-1],cs)
    f2,B2,oo2,ff2,rr2=joint_counts(nested,lambda o:definition1_failure(o,cs))
    assert (f2,B2)==(Q(11,16),Q(1,2))
    assert B2-f2*f2==Q(7,256)
    assert budget(f2,B2,2)['gain']==-Q(7,256)
    witness={'tree':nested,'cleaner_sets':{p:sorted(c) for p,c in cs.items()},'f':f2,'B':B2,
             'positive_covariance':B2-f2*f2,'orders':[{'order':o,'fail':ff2[i],'reverse_fail':ff2[rr2[i]]} for i,o in enumerate(oo2)]}
    (ROOT/'results/general_definition1_witness.json').write_text(json.dumps(safe_json(witness),indent=2))
    return {'three_test':{'f':f,'B':B,'J':f-B,'printed_J':Q(1,2),
                         'conditional':(f-B)/(1-f),'four_run_independent_pairs':Q(3,4),
                         'four_run_orbit_without_replacement':Q(1)},
            'without_replacement_checks':wor_checks,'nonuniform_second_marginal':dist,
            'nonuniform_gate_detection':hit,'same_profiles_different_gate':same,
            'five_test_suite':metrics,'four_test_gate_better':metrics4,'general_definition1':{k:v for k,v in witness.items() if k!='orders'}}


def main():
    started=time.perf_counter()
    result={'status':'PASS','kind':'synthetic exact rational checks; no real-project replication',
            'trees':check_trees(),'corrected_formula':check_corrected_formula(),'scalar_bounds':check_scalar_bounds(),
            'product_enumeration':check_budget_enumeration(),'counterexamples':check_counterexamples()}
    result['seconds']=round(time.perf_counter()-started,3)
    (ROOT/'results').mkdir(exist_ok=True)
    text=json.dumps(safe_json(result),indent=2)
    (ROOT/'results/theory_verification.json').write_text(text+'\n')
    print(text)
if __name__=='__main__':main()
