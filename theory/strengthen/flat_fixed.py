import itertools, random
from fractions import Fraction as Fr
from flat_structure import g_of
rng = random.Random(11)
viol = 0; cases = 0; worst = None
for trial in range(500):
    m = rng.randint(2, 7)
    others = list(range(1, m + 1))
    P = [t for t in others if rng.random() < 0.5] or [rng.choice(others)]
    overlap = rng.random() < 0.5
    C = {p: [t for t in others if t != p and (overlap or t not in P) and rng.random() < 0.5] for p in P}
    g = {}
    for r in range(m + 1):
        for A in itertools.combinations(others, r):
            g[frozenset(A)] = g_of(A, P, C)
    full = frozenset(others)
    for j in range(m + 1):
        subs = [frozenset(A) for A in itertools.combinations(others, j)]
        n = len(subs)
        e1 = sum(g[A] for A in subs) / n; e2 = sum(g[full - A] for A in subs) / n
        e12 = sum(g[A] * g[full - A] for A in subs) / n
        cov = e12 - e1 * e2
        cases += 1
        if cov > 0:
            viol += 1
            if worst is None or cov > worst[0]: worst = (cov, m, j, P, C)
print("cases", cases, "fixed-position covariance > 0:", viol, "worst", worst)
