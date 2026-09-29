"""Two-level orders, disjoint roles.  Decompose B - f^2 by the law of total
covariance over the victim's local time u and its class's time w:
   B - f^2 = E_{u,w}[Cov(g(A,D), g(A^c,D^c) | u,w)] + Cov(a(u,w), a(1-u,1-w)).
g(A,D) = P(left scan fails | local-left set A, left classes D)."""
import itertools, random
from functools import lru_cache
import numpy as np

def make(instance):
    local, classes, P, C = instance     # local: tests in v's class (excl v); classes: list of lists
    def scan_fails(seq):
        seen = set()
        for t in seq:
            if t in P and not (C[t] & seen): return True
            seen.add(t)
        return False
    @lru_cache(None)
    def g(A, D):
        A = list(A); D = [classes[i] for i in D]
        tot = cnt = 0
        for la in itertools.permutations(A):
            for co in itertools.permutations(range(len(D))):
                for inner in itertools.product(*(list(itertools.permutations(D[i])) for i in co)):
                    seq = list(la) + [t for blk in inner for t in reversed(blk)]
                    tot += 1; cnt += scan_fails(seq)
        return cnt / tot if tot else 0.0
    return g

def analyse(instance, grid=11):
    local, classes, P, C = instance
    g = make(instance)
    L = tuple(local); K = tuple(range(len(classes)))
    subsA = [tuple(s) for r in range(len(L) + 1) for s in itertools.combinations(L, r)]
    subsD = [tuple(s) for r in range(len(K) + 1) for s in itertools.combinations(K, r)]
    us = (np.arange(grid) + 0.5) / grid
    inner = np.zeros((grid, grid)); a = np.zeros((grid, grid)); b = np.zeros((grid, grid)); gg = np.zeros((grid, grid))
    for i, u in enumerate(us):
        for j, w in enumerate(us):
            E1 = E2 = E12 = 0.0
            for A in subsA:
                wa = u ** len(A) * (1 - u) ** (len(L) - len(A))
                Ac = tuple(x for x in L if x not in A)
                for D in subsD:
                    wd = w ** len(D) * (1 - w) ** (len(K) - len(D))
                    Dc = tuple(x for x in K if x not in D)
                    x1 = g(A, D); x2 = g(Ac, Dc)
                    E1 += wa * wd * x1; E2 += wa * wd * x2; E12 += wa * wd * x1 * x2
            inner[i, j] = E12 - E1 * E2; a[i, j] = E1; b[i, j] = E2; gg[i, j] = E12
    f = a.mean(); B = gg.mean()
    first = inner.mean(); second = (a * b).mean() - a.mean() * b.mean()
    return f, B, first, second, inner.max()

def random_instance(rng, n):
    others = list(range(1, n))
    rng.shuffle(others)
    nloc = rng.randint(0, min(3, n - 2))
    local = others[:nloc]; rest = others[nloc:]
    classes = []; i = 0
    while i < len(rest):
        k = rng.randint(1, min(3, len(rest) - i)); classes.append(rest[i:i + k]); i += k
    roles = {t: rng.choice("PCN") for t in others}
    P = [t for t in others if roles[t] == "P"] or [others[0]]
    for p in P: roles[p] = "P"
    Cs = [t for t in others if roles[t] == "C"]
    C = {p: frozenset(c for c in Cs if rng.random() < 0.6) for p in P}
    return (local, classes, frozenset(P), C)

if __name__ == "__main__":
    rng = random.Random(1)
    worst_first = worst_second = worst_total = -1
    pos_first = pos_second = 0; N = 0
    for _ in range(300):
        inst = random_instance(rng, rng.randint(4, 7))
        f, B, first, second, mx = analyse(inst)
        N += 1
        pos_first += first > 1e-12; pos_second += second > 1e-12
        worst_first = max(worst_first, first); worst_second = max(worst_second, second); worst_total = max(worst_total, first + second)
        if first + second > 1e-12: print("TOTAL POSITIVE", inst, first, second)
    print(f"instances={N} first>0: {pos_first} (max {worst_first:.2e}); second>0: {pos_second} (max {worst_second:.2e}); max total {worst_total:.2e}")
