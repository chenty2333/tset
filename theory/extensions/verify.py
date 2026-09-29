#!/usr/bin/env python3
"""Independent, exact sanity checks for the extension results (supplement, section "Extensions").

Python 3.10+; standard library only. All reported probabilities use Fraction.
These finite checks supplement, rather than replace, the written proofs.
Run: python verify.py --output verification.json
"""
from __future__ import annotations
import argparse
import itertools as it
import json
import math
import random
from collections import Counter
from fractions import Fraction as Q
from functools import lru_cache
from pathlib import Path
from typing import Iterable

Tree = int | tuple
F, C, U = 0, 1, 2

@lru_cache(None)
def orders(tree: Tree) -> tuple[tuple[int, ...], ...]:
    if isinstance(tree, int):
        return ((tree,),)
    result = []
    for perm in it.permutations(range(len(tree))):
        for pieces in it.product(*(orders(tree[i]) for i in perm)):
            result.append(tuple(x for piece in pieces for x in piece))
    return tuple(result)

def scan(seq: Iterable[int], cleaners: dict[int, frozenset[int]],
         globals_: frozenset[int] = frozenset()) -> int:
    seen: set[int] = set()
    for t in seq:
        if t in globals_:
            return C
        if t in cleaners and not (cleaners[t] & seen):
            return F
        seen.add(t)
    return U

def state_pair(order: tuple[int, ...], cleaners: dict[int, frozenset[int]],
               globals_: frozenset[int] = frozenset()) -> tuple[int, int]:
    j = order.index(0)
    return scan(reversed(order[:j]), cleaners, globals_), scan(order[j+1:], cleaners, globals_)

def from_joint(joint: dict[tuple[int, int], int | Q]) -> tuple[Q, ...]:
    total = sum(joint.values())
    f = sum(v for (a,b),v in joint.items() if a == F)
    u = sum(v for (a,b),v in joint.items() if a == U)
    fR = sum(v for (a,b),v in joint.items() if b == F)
    uR = sum(v for (a,b),v in joint.items() if b == U)
    assert f == fR and u == uR
    t = joint.get((U,F),0)
    assert t == joint.get((F,U),0)
    return tuple(Q(x,total) for x in (f,joint.get((F,F),0),u,t,joint.get((U,U),0)))

def summaries(tree: Tree, cleaners: dict[int, frozenset[int]],
              globals_: frozenset[int] = frozenset()) -> tuple[Q, ...]:
    return from_joint(Counter(state_pair(o,cleaners,globals_) for o in orders(tree)))

def hcoeff(s: tuple[Q, ...]) -> tuple[Q, Q, Q]:
    f,b,u,t,z = s
    return f*f-b, 2*(f*u-t), u*u-z

def nonnegative(poly: tuple[Q, Q, Q]) -> bool:
    c,b,a = poly
    return a >= 0 and c >= 0 and b*b <= 4*a*c

def square(a: Q, b: Q) -> tuple[Q, Q, Q]:
    return a*a, 2*a*b, b*b

def combine(p, q, a=Q(1), b=Q(1)):
    return tuple(a*x+b*y for x,y in zip(p,q))

def subst(poly, a, b):
    c,l,q = poly
    return c+l*a+q*a*a, l*b+2*q*a*b, q*b*b

def subsets(xs):
    xs=tuple(xs)
    return tuple(frozenset(xs[i] for i in range(len(xs)) if mask>>i&1)
                 for mask in range(1<<len(xs)))

def family_configs(n, pcount, disjoint=False):
    P=tuple(range(1,pcount+1))
    choices=[subsets(t for t in range(1,n) if t != p and (not disjoint or t not in P)) for p in P]
    for sets in it.product(*choices):
        yield dict(zip(P,sets))

def extrema(order, cleaners, maximum):
    pos={t:i for i,t in enumerate(order)}
    return any(all(pos[p]>pos[t] if maximum else pos[p]<pos[t]
                   for t in ({0}|set(cs))) for p,cs in cleaners.items())

def check_cut_and_small_overlap():
    cases=checks=pruning=sharp=0
    for n in range(2,6):
        tree=tuple(range(n))
        for pcount in range(1,n):
            for cp in family_configs(n,pcount):
                cases+=1
                D={p:cs-cp.keys() for p,cs in cp.items()}
                eligible=all(D[q]<=D[p] for p,cs in cp.items() for q in cs if q in cp)
                counts=Counter()
                for o in orders(tree):
                    j=o.index(0); cut=o[j+1:]+(0,)+o[:j]
                    sl,sr=state_pair(o,cp)
                    assert (sl==F)==extrema(cut,cp,True)
                    assert (sr==F)==extrema(cut,cp,False)
                    assert (cut[cut.index(0)+1:]+(0,)+cut[:cut.index(0)])==o
                    ro=o[::-1]; rj=ro.index(0)
                    assert ro[rj+1:]+(0,)+ro[:rj] == cut[::-1]
                    if eligible:
                        dl,dr=state_pair(o,D)
                        assert (sl==F,sr==F)==(dl==F,dr==F)
                    counts[sl,sr]+=1; checks+=1
                if eligible: pruning+=1
                f,B,*_=from_joint(counts)
                relevant={0}|set(cp)|set().union(*cp.values())
                m=len(relevant)
                pure=set().union(*cp.values())-cp.keys()
                if pcount<=2 or len(pure)<=1:
                    assert f*f-B>=Q(1,m*m)
                    sharp+=1
    return dict(configurations=cases,order_checks=checks,pruning_configurations=pruning,
                sharp_gap_configurations=sharp)

def check_s1():
    cases=0; example=None
    for n in range(2,7):
        for pcount in range(1,n):
            for cp in family_configs(n,pcount,True):
                common=frozenset.intersection(*cp.values())
                for G in subsets(common):
                    s=summaries(tuple(range(n)),cp,G)
                    f,B,u,t,z=s; d=f*f-B; q=1-2*f+B; g=len(G)
                    assert d>=0 and q>=0
                    if g:
                        assert u==(1-f)/(g+1) and t==(f-B)/(g+1) and z==0
                        expected=combine(square(Q(1),-Q(1,g+1)),square(Q(0),Q(1,g+1)),d,q)
                    else:
                        assert u==1-f and t==f-B and z==q
                        expected=tuple(d*x for x in square(Q(1),Q(-1)))
                    assert hcoeff(s)==expected and nonnegative(expected)
                    cases+=1
    cp={1:frozenset((3,4)),2:frozenset((3,5))}
    example=summaries(tuple(range(6)),cp,frozenset((3,)))
    return dict(local_models=cases,example_summaries=list(map(str,example)))

def check_marked_items():
    rng=random.Random(72104); cases=0
    for _ in range(80):
        nd=rng.randrange(4); no=rng.randrange(min(4,6-nd))
        n=nd+no
        nums=[rng.randrange(4) for _ in range(n)] # probabilities / 3
        joint=Counter(); basejoint=Counter(); Tjoint=Counter(); fulljoint=Counter()
        denom=0
        for bits in it.product((0,1),repeat=n):
            weight=math.prod(nums[i] if bits[i] else 3-nums[i] for i in range(n))
            if not weight: continue
            labels={i+1:(F if bits[i] else (C if i<nd else U)) for i in range(n)}
            for o in it.permutations(range(n+1)):
                j=o.index(0); sides=(tuple(reversed(o[:j])),o[j+1:])
                outcomes=[]; baselines=[]; ts=[]
                for seq in sides:
                    actual=next((labels[t] for t in seq if labels[t]!=U),U)
                    base=next((labels[t] for t in seq if t<=nd),U)
                    quiet=1
                    for t in seq:
                        if t<=nd:break
                        if labels[t]==F:quiet=0
                    outcomes.append(actual);baselines.append(base);ts.append(quiet)
                a=tuple(outcomes); b=tuple(baselines); t=tuple(ts)
                joint[a]+=weight;basejoint[b]+=weight;Tjoint[t]+=weight;fulljoint[b,t]+=weight
                denom+=weight
        for b in basejoint:
            for t in Tjoint:
                assert fulljoint[b,t]*denom==basejoint[b]*Tjoint[t]
        ae=Q(sum(v for t,v in Tjoint.items() if t[0]),denom)
        be=Q(Tjoint[1,1],denom)
        assert be<=ae*ae
        s=from_joint(joint); base=from_joint(basejoint)
        fb,_,ub,_,_=base
        expected=combine(hcoeff(base),square(1-fb,-ub),be,ae*ae-be)
        assert hcoeff(s)==expected and nonnegative(expected)
        if nd:
            S=sum(Q(a,3) for a in nums[:nd]); Q2=sum(Q(a,3)**2 for a in nums[:nd])
            k=nd+1
            expectedbase=combine(square(-S/nd,Q(1)),(Q(1),Q(0),Q(0)),Q(1,k*k),(Q2-S*S/nd)/(k*nd))
            assert hcoeff(base)==expectedbase
        cases+=1
    return dict(marked_item_models=cases)

def check_composition():
    rng=random.Random(45012); cases=0; psd_pairs=0
    def randjoint():
        counts={}
        for a in range(3):
            for b in range(a,3):
                counts[a,b]=counts[b,a]=rng.randrange(6)
        if not sum(counts.values()): counts[U,U]=1
        total=sum(counts.values())
        return {k:Q(v,total) for k,v in counts.items()}
    for _ in range(300):
        A=randjoint();E=randjoint(); s=from_joint(A);e=from_joint(E)
        joint=Counter()
        for (l,r),p in A.items():
            for (le,re),q in E.items():
                joint[(le if l==U else l),(re if r==U else r)]+=p*q
        sp=from_joint(joint)
        f,B,u,t,z=s; h,b,a,tau,zeta=e
        assert sp==(f+u*h,B+2*t*h+z*b,u*a,t*a+z*tau,z*zeta)
        expected=combine(subst(hcoeff(s),h,a),hcoeff(e),Q(1),z)
        assert hcoeff(sp)==expected
        if nonnegative(hcoeff(s)) and nonnegative(hcoeff(e)):
            assert nonnegative(hcoeff(sp));psd_pairs+=1
        cases+=1
    return dict(compositions=cases,both_inputs_psd=psd_pairs)

def check_extended_theorem():
    rng=random.Random(21014); cases=0; deeper=0
    def model(regions):
        alltests=set().union(*(set(r) for r in regions))-{0}
        P={t for t in alltests if rng.random()<.45}
        if not P:P={min(alltests)}
        G=frozenset(t for t in alltests-P if rng.random()<.35)
        cp={}
        for reg in regions:
            extra=set(reg)-P-G-{0}
            for p in set(reg)&P:
                cp[p]=G|frozenset(c for c in extra if rng.random()<.55)
        return cp,G
    for _ in range(220):
        n=rng.randrange(3,9)
        parts=[[0]]
        for t in range(1,n):
            if rng.random()<.38 and len(parts)<4:parts.append([t])
            else:rng.choice(parts).append(t)
        tree=tuple(tuple(p) for p in parts)
        if math.factorial(len(parts))*math.prod(math.factorial(len(p)) for p in parts)>12000:continue
        cp,G=model(parts)
        s=summaries(tree,cp,G)
        assert nonnegative(hcoeff(s));cases+=1
    # Flat K, with arbitrarily nested off-spine regions at two successive ancestors.
    patterns=[((0,1),(2,(3,4)),(5,6)), ((0,1,2),((3,4),5),(6,)),
              ((0,),((1,2),(3,4)),(5,6,7))]
    for K,X,Y in patterns:
        def leaves(t):
            return (t,) if isinstance(t,int) else sum((leaves(c) for c in t),())
        regs=[leaves(K),leaves(X),leaves(Y)]
        tree=((K,X),Y)
        for _ in range(65):
            cp,G=model(regs);s=summaries(tree,cp,G)
            assert nonnegative(hcoeff(s));deeper+=1
    cp={1:frozenset((2,)),3:frozenset((2,4))}
    s=summaries(((0,),(1,2),(3,4)),cp,frozenset((2,)))
    assert s[0]==Q(3,8) and s[1]==Q(1,12)
    # Known counterexample: deliberately violates the region-locality assumption.
    old={1:frozenset((2,)),3:frozenset((2,)),5:frozenset((4,))}
    sx=summaries((((0,(1,2)),(3,4)),5),old)
    assert sx[0]==Q(11,16) and sx[1]==Q(1,2)
    # Known overlapping two-level counterexample, victim relabeled to zero.
    ov={1:frozenset((5,6)),6:frozenset((4,)),4:frozenset((2,3,5)),
        5:frozenset((1,3,6)),3:frozenset((5,6))}
    so=summaries(((6,4,0,2),(1,),(3,),(5,)),ov)
    assert so[0]==Q(83,96) and so[1]==Q(3,4)
    return dict(two_level_models=cases,deeper_models=deeper,
                strict_extension_example=dict(f=str(s[0]),B=str(s[1]),d=str(s[0]**2-s[1]),orders=24),
                guardrail_counterexamples=2)

def exact_two_B(a,b,g):
    m=a+b+g+3
    total=sum(Q(math.factorial(g+1+i+j),math.factorial(i)*math.factorial(j))
              for i in range(a+1) for j in range(b+1))
    return Q(2*math.factorial(a)*math.factorial(b),math.factorial(m))*total

def check_two_polluters():
    cases=paramcases=0
    for m in range(3,8):
        for a in range(m-2):
            for b in range(m-2-a):
                g=m-3-a-b
                if g<0:continue
                Ac=set(range(3,3+a));Bc=set(range(3+a,3+a+b));G=set(range(3+a+b,m))
                values=[]
                for pq,qp in it.product((0,1),repeat=2):
                    cp={1:frozenset(Ac|G|({2} if pq else set())),
                        2:frozenset(Bc|G|({1} if qp else set()))}
                    f,B,*_=summaries(tuple(range(m)),cp)
                    assert B==exact_two_B(a,b,g)
                    assert f*f-B>=Q(1,m*m)
                    if pq and qp:assert f==Q(1,a+g+3)+Q(1,b+g+3)
                    values.append(B);cases+=1
                assert len(set(values))==1
    for m in range(3,31):
        for a in range(m-2):
            for b in range(m-2-a):
                g=m-3-a-b
                if g<0:continue
                k=g+3;r=a+k;s=b+k
                B=exact_two_B(a,b,g);bound=Q(2*k,(k-1)*r*s)
                f=Q(1,r)+Q(1,s)
                assert B<=bound
                assert f*f-B>=Q(1,m*m)
                assert f*f-bound==(Q(1,r)-Q(1,s))**2+Q(2*(k-2),(k-1)*r*s)
                paramcases+=1
    return dict(enumerated_two_polluter_models=cases,exact_parameter_models=paramcases)

def check_one_pure_cleaner():
    rng=random.Random(62118);cases=0
    for n in (6,7):
        for _ in range(120):
            P=set(range(1,n-1));c=n-1
            cp={p:frozenset(t for t in range(1,n) if t!=p and rng.random()<.55) for p in P}
            # Ensure that the sole nonpolluter is relevant.
            p=min(P);cp[p]=cp[p]|{c}
            f,B,*_=summaries(tuple(range(n)),cp)
            assert f*f-B>=Q(1,n*n);cases+=1
    return dict(additional_one_pure_cleaner_models=cases)

def check_weak_bound():
    cases=0
    for n in range(2,7):
        for pcount in range(1,n):
            for cp in family_configs(n,pcount,True):
                relevant={0}|set(cp)|set().union(*cp.values());m=len(relevant)
                tree=tuple(sorted(relevant));f,B,*_=summaries(tree,cp)
                bound=Q(pcount*pcount,(m-1)**2)*(Q(1,m*m)-Q(math.factorial(m-1)**2,math.factorial(2*m-1)))
                assert bound>0 and f*f-B>=bound;cases+=1
    return dict(disjoint_models_for_weak_gap=cases)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('verification.json'))
    args=parser.parse_args()
    results={}
    checks=[check_cut_and_small_overlap,check_s1,check_marked_items,check_composition,
            check_extended_theorem,check_two_polluters,check_one_pure_cleaner,check_weak_bound]
    for check in checks:
        result=check();results[check.__name__]=result
        print(check.__name__,json.dumps(result),flush=True)
    results['status']='PASS'
    results['note']='Finite exact sanity checks, not a proof-assistant formalization or exhaustive search of the open conjectures.'
    args.output.write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print('Wrote',args.output,flush=True)
if __name__=='__main__':main()
