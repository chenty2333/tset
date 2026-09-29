#!/usr/bin/env python3
"""Exact, dependency-free theory utilities; not a production test detector.
A tree is an integer test ID or a nonempty tuple of child trees. Victim ID is 0.
Every internal node has an independent, uniform child permutation.
All probabilities use fractions.Fraction. Cost claims count arithmetic operations.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from functools import lru_cache
from itertools import permutations, product
from math import comb
from typing import Iterator

Tree = int | tuple['Tree', ...]

@dataclass(frozen=True)
class Summary:
    f: Q
    B: Q
    u: Q
    t: Q
    base: tuple[int, Q, Q] | None
    ancestors: tuple[tuple[int, Q], ...] = ()

    def certificate(self) -> dict:
        if self.base is None:
            return {'gap': Q(0), 'square': Q(0), 'variance': Q(0), 'x': Q(0)}
        k, S, V2 = self.base
        x = Q(0)
        for parent_k, h in reversed(self.ancestors):
            x = h + x / parent_k
        square = (x - S/(k-1))**2 / k**2
        variance = (V2 - S*S/(k-1))/(k*(k-1))
        return {'gap': square + variance, 'square': square,
                'variance': variance, 'x': x, 'base_k': k}


def leaves(tree: Tree) -> tuple[int, ...]:
    if isinstance(tree, int):
        return (tree,)
    if not isinstance(tree, tuple) or not tree:
        raise ValueError('An internal node must be a nonempty tuple')
    return tuple(t for c in tree for t in leaves(c))


def validate_tree(tree: Tree) -> set[int]:
    ids = leaves(tree)
    if ids.count(0) != 1 or len(ids) != len(set(ids)):
        raise ValueError('Unique leaf IDs and exactly one victim 0 are required')
    return set(ids)


def tree_summary(tree: Tree, polluters: set[int], cleaners: set[int]) -> Summary:
    ids = validate_tree(tree)
    if polluters & cleaners or 0 in polluters | cleaners:
        raise ValueError('Victim, polluters and common cleaners must be disjoint')
    if not (polluters | cleaners) <= ids:
        raise ValueError('Unknown action ID')

    def walk(node: Tree) -> Summary | Q | None:
        if isinstance(node, int):
            if node == 0:
                return Summary(Q(0), Q(0), Q(1), Q(0), None)
            if node in polluters:
                return Q(1)
            if node in cleaners:
                return Q(0)
            return None
        v = [x for child in node if (x := walk(child)) is not None]
        if not v:
            return None
        distinguished = [x for x in v if isinstance(x, Summary)]
        if not distinguished:
            return sum(v, Q(0)) / len(v)
        if len(distinguished) != 1:
            raise ValueError('Multiple victim-containing subtrees')
        s = distinguished[0]
        k = len(v)
        if k == 1:
            return s
        alphas = [x for x in v if isinstance(x, Q)]
        S = sum(alphas, Q(0)); V2 = sum((a*a for a in alphas), Q(0)); h = S/k
        if s.base is None:
            return Summary(h, (S*S-V2)/(k*(k-1)), Q(1,k), S/(k*(k-1)), (k,S,V2))
        return Summary(s.f+s.u*h, s.B+2*s.t*h, s.u/k, s.t/k,
                       s.base, s.ancestors+((k,h),))
    answer = walk(tree)
    if not isinstance(answer, Summary):
        raise ValueError('No victim in tree')
    return answer


def all_orders(tree: Tree) -> Iterator[tuple[int, ...]]:
    if isinstance(tree, int):
        yield (tree,)
        return
    for children in permutations(tree):
        for parts in product(*(all_orders(c) for c in children)):
            yield tuple(t for part in parts for t in part)


def common_failure(order: tuple[int, ...], polluters: set[int], cleaners: set[int]) -> bool:
    state = False
    for test in order:
        if test == 0:
            return state
        if test in polluters:
            state = True
        if test in cleaners:
            state = False
    raise ValueError('Victim 0 missing')


def definition1_failure(order: tuple[int, ...], cleaner_sets: dict[int, set[int]]) -> bool:
    """Direct quantified predicate, deliberately independent of bit execution."""
    pos = {t:i for i,t in enumerate(order)}
    v = pos[0]
    return any(pos[p] < v and not any(pos[p] < pos[c] < v for c in cs)
               for p,cs in cleaner_sets.items())


def bits_failure(order: tuple[int, ...], cleaner_sets: dict[int, set[int]]) -> bool:
    """Executable semantics for general per-polluter cleaners (not shared bit)."""
    bits = {p:False for p in cleaner_sets}
    for test in order:
        if test == 0:
            return any(bits.values())
        for p,cs in cleaner_sets.items():
            if test in cs:
                bits[p] = False
        if test in bits:
            bits[test] = True
    raise ValueError('Victim missing')


def validate_profile(f: Q, B: Q) -> None:
    if not 0 <= f <= 1 or not max(Q(0), 2*f-1) <= B <= f:
        raise ValueError(f'Invalid equal-marginal Bernoulli pair: f={f}, B={B}')


def budget(f: Q, B: Q, runs: int, *, both_outcomes: bool=False) -> dict[str,Q]:
    validate_profile(f,B)
    if runs < 0:
        raise ValueError('Run budget must be nonnegative')
    if runs == 0:
        return {k:Q(0) for k in ('iid','pair','independent_pair_ceiling','uniform_marginal_ceiling','gain')}
    m,e = divmod(runs,2)
    q = 1-2*f+B; L = max(Q(0),2*f-1)
    iid = 1-(1-f)**runs
    paired = 1-q**m*(1-f)**e
    upper = 1-(1-2*f+L)**m*(1-f)**e
    union = min(Q(1),runs*f)
    if both_outcomes:
        iid -= f**runs
        paired -= B**m*f**e
        upper -= L**m*f**e
        union = Q(0) if runs < 2 else min(Q(1),runs*f,runs*(1-f))
    return {'iid':iid, 'pair':paired, 'independent_pair_ceiling':upper,
            'uniform_marginal_ceiling':union, 'gain':paired-iid}


def hitting_times(f: Q, B: Q) -> dict[str,Q | None]:
    validate_profile(f,B)
    first_iid = None if f == 0 else 1/f
    first_pair = None if f == 0 else (2-f)/(2*f-B)
    both_iid = None if f in (0,1) else 1/f+1/(1-f)-1
    both_pair = None if f in (0,1) else (2-f)/(2*f-B)+(1+f)/(1-B)-1
    return {'first_iid':first_iid,'first_pair':first_pair,
            'both_iid':both_iid,'both_pair':both_pair}


def pair_without_replacement(K: int, H: int, pairs: int) -> Q:
    if not 0 <= H <= K or K < 1 or not 0 <= pairs <= K:
        raise ValueError('Require K>=1, 0<=H<=K and 0<=pairs<=K')
    return 1-Q(comb(K-H,pairs),comb(K,pairs))


def gate_law(reverse: tuple[int,...], gate: tuple[Q,...]) -> tuple[Q,...]:
    """Second-order marginal law on a finite uniform sample space."""
    n = len(reverse)
    if n == 0 or len(gate) != n or sorted(reverse) != list(range(n)):
        raise ValueError('Invalid finite involution/gate')
    if any(reverse[reverse[i]] != i for i in range(n)) or any(not 0<=g<=1 for g in gate):
        raise ValueError('Require an involution and probabilities in [0,1]')
    mean = sum(gate,Q(0))/n
    return tuple((1+gate[reverse[t]]-mean)/n for t in range(n))


def two_run_suite(masks: tuple[int,...], reverse: tuple[int,...], policy: str) -> dict[str,Q]:
    """Exact initial two-run comparison, known reference passing all targets.
    gate = reverse iff first run's failure mask is empty; no confirmation cost.
    Not a full iDFlakies implementation.
    """
    if len(masks) != len(reverse) or not masks:
        raise ValueError('Inconsistent sample space')
    n=len(masks); mass={}
    for a,ma in enumerate(masks):
        if policy=='pair' or (policy=='gate' and ma==0):
            choices=[(reverse[a],Q(1))]
        elif policy in ('iid','gate'):
            choices=[(b,Q(1,n)) for b in range(n)]
        else:
            raise ValueError('policy must be iid, gate, or pair')
        for b,p in choices:
            mask=ma|masks[b]
            mass[mask]=mass.get(mask,Q(0))+p/n
    allmask=0
    for mask in masks: allmask |= mask
    return {'expected_count':sum((mask.bit_count()*p for mask,p in mass.items()),Q(0)),
            'any':sum((p for mask,p in mass.items() if mask),Q(0)),
            'all':mass.get(allmask,Q(0))}


def set_partitions(labels: tuple[int,...]):
    if not labels:
        yield ()
        return
    first,*tail=labels
    for blocks in set_partitions(tuple(tail)):
        yield ((first,),)+blocks
        for i in range(len(blocks)):
            yield blocks[:i]+((first,)+blocks[i],)+blocks[i+1:]


@lru_cache(None)
def all_trees(labels: tuple[int,...]) -> tuple[Tree,...]:
    if len(labels)==1: return (labels[0],)
    answer=[]
    for blocks in set_partitions(labels):
        if len(blocks)==1: continue
        for children in product(*(all_trees(b) for b in blocks)):
            answer.append(children)
    return tuple(answer)


def two_level_formula(a: int, b: int, others: list[tuple[int,int]]) -> dict[str,Q]:
    """Corrected rates; irrelevant (0,0) outside classes are pruned first."""
    if min(a,b)<0 or any(min(p,c)<0 for p,c in others):
        raise ValueError('Counts must be nonnegative')
    nonempty=[(p,c) for p,c in others if p+c]
    k=1+len(nonempty);r=a+b
    S=sum((Q(p,p+c) for p,c in nonempty),Q(0));h=S/k
    if r==0:
        sq=sum((Q(p,p+c)**2 for p,c in nonempty),Q(0))
        f=h;B=Q(0) if k==1 else (S*S-sq)/(k*(k-1))
        return {'f':f,'B':B,'J':f-B}
    f=(a+h)/(r+1);B=Q(a,r*(r+1))*(a-1+2*h)
    J=(a*(b+1)+(b-a)*h)/(r*(r+1))
    printed=Q(1,k*r*(r+1))*(a+k*a*b+a*(k-1-S)+b*(r+1)*S)
    return {'f':f,'B':B,'J':J,'printed_J':printed,'printed_excess':b*S/(k*(r+1))}
