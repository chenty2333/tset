"""Exact checks for the strengthened theory (added 2026-09-28).
1. Theorem (interleaved orders, polluter-specific cleaners, disjoint roles):
   B <= f^2 -- exhaustive over all configurations with up to 6 tests.
2. Lemma (position monotonicity): P(F | j tests left of v) nondecreasing in j,
   also with overlapping roles.
3. Boundary instances: two-level with overlapping roles, three-level with
   disjoint roles (B > f^2).
4. Block limit: E[T] >= 1/f - (k-1)/2 for independent k-blocks with uniform
   marginals, equality iff within-block failures are disjoint (random
   rational instances).
Writes results/verify_new.json."""
import itertools, json, random, time
from fractions import Fraction as Fr
from pathlib import Path

def fails(order, P, C):
    pos = {t: i for i, t in enumerate(order)}; v = pos[0]
    return any(pos[p] < v and not any(pos[p] < pos[c] < v for c in C[p]) for p in P)

def all_orders(tree):
    if isinstance(tree, int):
        yield (tree,); return
    for p in itertools.permutations(tree):
        for parts in itertools.product(*(list(all_orders(c)) for c in p)):
            yield tuple(x for part in parts for x in part)

def fB(orders, P, C):
    nf = nb = 0
    for o in orders:
        a = fails(o, P, C)
        nf += a; nb += a and fails(o[::-1], P, C)
    return Fr(nf, len(orders)), Fr(nb, len(orders))

def flat_exhaustive(nmax=6):
    out = {}
    for n in range(2, nmax + 1):
        m = n - 1; others = list(range(1, n))
        orders = list(itertools.permutations(range(n)))
        checked = 0; worst = None; mono_fail = 0
        for roles in itertools.product("PCN", repeat=m):
            P = [i + 1 for i, r in enumerate(roles) if r == "P"]
            Cs = [i + 1 for i, r in enumerate(roles) if r == "C"]
            if not P: continue
            for masks in itertools.product(range(1 << len(Cs)), repeat=len(P)):
                C = {p: [Cs[b] for b in range(len(Cs)) if mk >> b & 1] for p, mk in zip(P, masks)}
                f, B = fB(orders, P, C)
                assert B <= f * f, (n, P, C, f, B)
                checked += 1
                gap = f * f - B
                if worst is None or gap < worst: worst = gap
                # position monotonicity
                byj = [[0, 0] for _ in range(n)]
                for o in orders:
                    j = o.index(0); byj[j][0] += fails(o, P, C); byj[j][1] += 1
                pj = [Fr(a, b) for a, b in byj]
                mono_fail += any(pj[i] > pj[i + 1] for i in range(n - 1))
        out[n] = dict(configurations=checked, min_gap=str(worst), monotonicity_violations=mono_fail)
    return out

def overlap_monotonicity(samples=300, seed=3):
    rng = random.Random(seed); viol = 0
    for _ in range(samples):
        n = rng.randint(3, 7); others = list(range(1, n))
        P = [t for t in others if rng.random() < .5] or [others[0]]
        C = {p: [t for t in others if t != p and rng.random() < .5] for p in P}
        orders = list(itertools.permutations(range(n)))
        byj = [[0, 0] for _ in range(n)]
        for o in orders:
            j = o.index(0); byj[j][0] += fails(o, P, C); byj[j][1] += 1
        pj = [Fr(a, b) for a, b in byj]
        viol += any(pj[i] > pj[i + 1] for i in range(n - 1))
    return dict(samples=samples, violations=viol)

def boundary():
    res = {}
    two = ((6, 4, 0, 2), 1, 3, 5)
    P = [1, 6, 4, 5, 3]; C = {1: [6, 5], 6: [4], 4: [3, 2, 5], 5: [6, 3, 1], 3: [5, 6]}
    f, B = fB(list(all_orders(two)), P, C)
    res["two_level_overlapping_roles"] = dict(tree=str(two), P=P, C=C, f=str(f), B=str(B), B_minus_f2=str(B - f * f))
    three = (((0, (1, 4)), (2, 5)), 3)
    P = [1, 2, 3]; C = {1: [4], 2: [4], 3: [5]}
    f, B = fB(list(all_orders(three)), P, C)
    res["three_level_disjoint_roles"] = dict(tree=str(three), P=P, C=C, f=str(f), B=str(B), B_minus_f2=str(B - f * f))
    return res

def block_limit(samples=2000, seed=5):
    rng = random.Random(seed); ok = 0; eq_ok = 0
    for _ in range(samples):
        k = rng.randint(2, 5); N = rng.randint(k, 12)          # f = 1/N, kf <= 1
        f = Fr(1, N)
        # random within-block joint law of k failure indicators with marginals f:
        # choose a random coupling on a finite sample space of size N*L
        L = rng.randint(1, 4); S = N * L
        fail_sets = [set(rng.sample(range(S), L)) for _ in range(k)]
        # first-failure distribution within block
        d = []; seen = set()
        for i in range(k):
            new = fail_sets[i] - seen; d.append(Fr(len(new), S)); seen |= fail_sets[i]
        h = sum(d); s = [Fr(1)]
        for i in range(k): s.append(s[-1] - d[i])
        ET = sum(s[:k]) / h
        bound = 1 / f - Fr(k - 1, 2)
        assert ET >= bound, (k, N, ET, bound)
        ok += 1
        disjoint = all(not (fail_sets[a] & fail_sets[b]) for a in range(k) for b in range(a + 1, k))
        if disjoint:
            assert ET == bound; eq_ok += 1
        else:
            assert ET > bound
    return dict(instances=ok, disjoint_equality_instances=eq_ok)

if __name__ == "__main__":
    t = time.time()
    out = dict(flat_disjoint_exhaustive=flat_exhaustive(6), flat_overlap_position_monotonicity=overlap_monotonicity(),
               boundary_instances=boundary(), block_limit=block_limit())
    out["seconds"] = round(time.time() - t, 1)
    Path(__file__).with_name("verify_new.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
