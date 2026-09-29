"""Flat (single-class) orders, general Definition-1 semantics.
g(A) = P(F | set A of tests left of v), left order uniform.
Checks: (i) conditional covariance given the Bernoulli(u) split,
(ii) monotonicity of a(u) = E_u g(A)."""
import itertools, random
from fractions import Fraction as Fr
import numpy as np

def g_of(A, P, C):
    A = list(A)
    if not A: return Fr(0)
    cnt = 0; tot = 0
    for scan in itertools.permutations(A):   # scan[0] is nearest to v
        tot += 1
        seen = set(); fail = False
        for t in scan:
            if t in P and not (set(C[t]) & seen):
                fail = True; break
            seen.add(t)
        cnt += fail
    return Fr(cnt, tot)

def analyse(m, P, C, grid=21):
    others = list(range(1, m + 1))
    g = {}
    for r in range(m + 1):
        for A in itertools.combinations(others, r):
            g[frozenset(A)] = g_of(A, P, C)
    full = frozenset(others)
    # exact f, B (v position uniform over m+1 slots)
    f = sum(sum(g[frozenset(A)] for A in itertools.combinations(others, j)) / len(list(itertools.combinations(others, j))) for j in range(m + 1)) / (m + 1)
    B = sum(sum(g[frozenset(A)] * g[full - frozenset(A)] for A in itertools.combinations(others, j)) / len(list(itertools.combinations(others, j))) for j in range(m + 1)) / (m + 1)
    worst_cond = -1; a = []
    for k in range(grid):
        u = k / (grid - 1)
        Eg = Egc = Eggc = 0.0
        for A, val in g.items():
            w = u ** len(A) * (1 - u) ** (m - len(A))
            Eg += w * float(val); Egc += w * float(g[full - A]); Eggc += w * float(val) * float(g[full - A])
        worst_cond = max(worst_cond, Eggc - Eg * Egc)
        a.append(Eg)
    mono = all(a[i] <= a[i + 1] + 1e-12 for i in range(len(a) - 1))
    return f, B, worst_cond, mono

if __name__ == "__main__":
    rng = random.Random(7)
    stats = {"cases": 0, "B>f2": 0, "cond_pos": 0, "nonmono": 0}
    ex = {}
    for trial in range(400):
        m = rng.randint(2, 6)
        others = list(range(1, m + 1))
        P = [t for t in others if rng.random() < 0.5] or [rng.choice(others)]
        overlap = rng.random() < 0.5
        C = {p: [t for t in others if t != p and (overlap or t not in P) and rng.random() < 0.5] for p in P}
        f, B, wc, mono = analyse(m, P, C)
        stats["cases"] += 1
        if B > f * f: stats["B>f2"] += 1
        if wc > 1e-12: stats["cond_pos"] += 1; ex.setdefault("cond", (m, P, C, wc))
        if not mono: stats["nonmono"] += 1; ex.setdefault("mono", (m, P, C))
    print(stats); print(ex)
