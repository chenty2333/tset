"""Independent cross-checks of the extension results (supplement, section "Extensions"), not reusing extensions/verify.py.
1. Cyclic-cut equivalence (flat, overlapping roles allowed), order by order.
2. S1 identity H(x) = d(1 - x/(g+1))^2 + q (x/(g+1))^2 on local models.
3. Extended Theorem 4 (no decisiveness condition) on two-level instances, up to 9 tests.
4. Flat S2 regions: <=2 polluters, or <=1 pure cleaner (overlap allowed): f^2-B >= 1/m^2.
5. Overlap pruning: pointwise preservation of the failure indicator.
6. The strict-extension example."""
import itertools, random, json
from fractions import Fraction as Fr
from pathlib import Path
import numpy as np
rng = random.Random(123)

def fails_order(order, P, C, v=0):
    pos = {t: i for i, t in enumerate(order)}
    return any(pos[p] < pos[v] and not any(pos[p] < pos[c] < pos[v] for c in C[p]) for p in P)

def flat_fB(n, P, C):
    nf = nb = T = 0
    for o in itertools.permutations(range(n)):
        a = fails_order(o, P, C); b = fails_order(o[::-1], P, C)
        nf += a; nb += a and b; T += 1
    return Fr(nf, T), Fr(nb, T)

out = {}
# 1. cyclic cut
cnt = 0
for _ in range(300):
    n = rng.randint(3, 6); others = list(range(1, n))
    P = [t for t in others if rng.random() < .5] or [1]
    C = {p: [t for t in others if t != p and rng.random() < .5] for p in P}
    for o in itertools.permutations(range(n)):
        i = o.index(0); A, Bw = o[:i], o[i + 1:]
        cut = Bw + (0,) + A
        rank = {t: k for k, t in enumerate(cut)}
        Mp = any(all(rank[p] > rank[t] for t in [0] + C[p]) for p in P)
        Mm = any(all(rank[p] < rank[t] for t in [0] + C[p]) for p in P)
        assert Mp == fails_order(o, P, C) and Mm == fails_order(o[::-1], P, C)
        cnt += 1
out["cyclic_cut_order_checks"] = cnt

# 2. S1 identity on local models (flat victim class with designated globals G)
def summaries(n, P, C, G):
    acc = dict(f=Fr(0), B=Fr(0), u=Fr(0), t=Fr(0), z=Fr(0)); N = 0
    def st(seq):
        seen = set()
        for x in seq:
            if x in G: return "C"
            if x in P and not (set(C[x]) & seen): return "F"
            seen.add(x)
        return "U"
    for o in itertools.permutations(range(n)):
        i = o.index(0); L = st(list(reversed(o[:i]))); R = st(list(o[i + 1:])); N += 1
        acc["f"] += L == "F"; acc["B"] += L == "F" and R == "F"; acc["u"] += L == "U"
        acc["t"] += L == "U" and R == "F"; acc["z"] += L == "U" and R == "U"
    return {k: v / N for k, v in acc.items()}
s1 = 0
for _ in range(400):
    n = rng.randint(2, 7); others = list(range(1, n))
    roles = {t: rng.choice("PGEN") for t in others}
    P = [t for t in others if roles[t] == "P"]; G = {t for t in others if roles[t] == "G"}
    if not P: continue
    E = [t for t in others if roles[t] == "E"]
    C = {p: sorted(G | {e for e in E if rng.random() < .6}) for p in P}
    s = summaries(n, P, C, G); f, B = s["f"], s["B"]; d = f * f - B; q = 1 - 2 * f + B; g = len(G)
    # coefficients of H(x) = (f+ux)^2 - B - 2tx - zx^2
    H = [f * f - B, 2 * (f * s["u"] - s["t"]), s["u"] ** 2 - s["z"]]
    if g == 0: W = [d, -2 * d, d]
    else:
        r = Fr(1, g + 1); W = [d, -2 * d * r, (d + q) * r * r]
    assert H == W, (n, P, C, G, H, W)
    s1 += 1
out["S1_identity_models"] = s1

# 3. extended Theorem 4 on two-level instances (transparent classes allowed)
def two_level_orders(classes):
    blocks = {}
    for t, c in enumerate(classes): blocks.setdefault(c, []).append(t)
    blocks = list(blocks.values())
    for border in itertools.permutations(range(len(blocks))):
        for parts in itertools.product(*(itertools.permutations(blocks[b]) for b in border)):
            yield tuple(x for p in parts for x in p)
t4 = 0; transparent_cases = 0; worst = None
while t4 < 250:
    n = rng.randint(4, 9); classes = [0] + [rng.randrange(4) for _ in range(n - 1)]
    if len(set(classes)) < 2: continue
    others = list(range(1, n)); roles = {t: rng.choice("PGEN") for t in others}
    P = [t for t in others if roles[t] == "P"]; G = [t for t in others if roles[t] == "G"]
    if not P: continue
    C = {p: sorted(set(G) | {e for e in others if roles[e] == "E" and classes[e] == classes[p] and rng.random() < .6}) for p in P}
    orders = list(two_level_orders(classes))
    if len(orders) > 50000: continue
    nf = nb = 0
    for o in orders:
        a = fails_order(o, P, C); b = fails_order(o[::-1], P, C); nf += a; nb += a and b
    f, B = Fr(nf, len(orders)), Fr(nb, len(orders))
    assert B <= f * f, (classes, P, C, f, B)
    # count instances outside the old Theorem 4 (a polluter class without a global cleaner whose polluters all have extras)
    old_ok = all(any(classes[g] == classes[p] for g in G) or any(set(C[q]) <= set(G) for q in P if classes[q] == classes[p]) for p in P if classes[p] != 0)
    transparent_cases += not old_ok
    t4 += 1
out["extended_theorem4_instances"] = t4; out["of_which_outside_old_theorem4"] = transparent_cases

# 4. flat S2 regions with overlap
s2 = 0
for _ in range(600):
    n = rng.randint(3, 7); others = list(range(1, n))
    kind = rng.choice(["two_polluters", "one_pure_cleaner"])
    if kind == "two_polluters":
        P = rng.sample(others, min(len(others), rng.randint(1, 2)))
    else:
        c = rng.choice(others); P = [t for t in others if t != c] or [c]
    C = {p: [t for t in others if t != p and rng.random() < .6] for p in P}
    if kind == "one_pure_cleaner":
        C = {p: [t for t in C[p] if t in P or t == c] for p in P}
    rel = set(P) | {x for p in P for x in C[p]}
    m = 1 + len(rel)
    f, B = flat_fB(n, P, C)
    assert f * f - B >= Fr(1, m * m), (kind, n, P, C, f, B, m)
    s2 += 1
out["S2_region_instances"] = s2

# 5. overlap pruning, pointwise
pr = 0
for _ in range(400):
    n = rng.randint(3, 6); others = list(range(1, n))
    P = [t for t in others if rng.random() < .5] or [1]
    C = {p: [t for t in others if t != p and rng.random() < .5] for p in P}
    D = {p: [c for c in C[p] if c not in P] for p in P}
    if not all(set(D[q]) <= set(D[p]) for p in P for q in C[p] if q in P):
        continue
    for o in itertools.permutations(range(n)):
        assert fails_order(o, P, C) == fails_order(o, P, D)
    pr += 1
out["pruning_instances_pointwise"] = pr

# 6. strict example: classes {v},{p1,g},{p2,e}
labels = {0: "v", 1: "p1", 2: "g", 3: "p2", 4: "e"}
classes = [0, 1, 1, 2, 2]; P = [1, 3]; C = {1: [2], 3: [2, 4]}
orders = list(two_level_orders(classes)); nf = nb = 0
for o in orders:
    a = fails_order(o, P, C); b = fails_order(o[::-1], P, C); nf += a; nb += a and b
out["strict_example"] = dict(f=str(Fr(nf, len(orders))), B=str(Fr(nb, len(orders))))
print(json.dumps(out, indent=2))
Path(__file__).with_name("crosscheck_appendix.json").write_text(json.dumps(out, indent=2))
