import random, numpy as np
from decompose import analyse, random_instance, make
import decompose as Dm

def a_grid(instance, grid=9):
    import itertools
    local, classes, P, C = instance
    g = make(instance)
    L = tuple(local); K = tuple(range(len(classes)))
    subsA = [tuple(s) for r in range(len(L) + 1) for s in itertools.combinations(L, r)]
    subsD = [tuple(s) for r in range(len(K) + 1) for s in itertools.combinations(K, r)]
    us = np.linspace(0, 1, grid)
    a = np.zeros((grid, grid)); inner = np.zeros((grid, grid))
    for i, u in enumerate(us):
        for j, w in enumerate(us):
            E1 = E2 = E12 = 0.0
            for A in subsA:
                wa = u ** len(A) * (1 - u) ** (len(L) - len(A))
                Ac = tuple(x for x in L if x not in A)
                for D in subsD:
                    wd = w ** len(D) * (1 - w) ** (len(K) - len(D))
                    Dc = tuple(x for x in K if x not in D)
                    x1, x2 = g(A, D), g(Ac, Dc)
                    E1 += wa * wd * x1; E2 += wa * wd * x2; E12 += wa * wd * x1 * x2
            a[i, j] = E1; inner[i, j] = E12 - E1 * E2
    return a, inner

rng = random.Random(5)
pw_pos = 0; mixed_dir = 0; N = 0; ex = {}
for _ in range(400):
    inst = random_instance(rng, rng.randint(4, 7))
    a, inner = a_grid(inst)
    N += 1
    if inner.max() > 1e-12:
        pw_pos += 1; ex.setdefault("pointwise", (inst, inner.max()))
    du = np.diff(a, axis=0)            # change in u for each w
    inc = (du >= -1e-12).all(); dec = (du <= 1e-12).all()
    if not (inc or dec):
        mixed_dir += 1; ex.setdefault("nonmono_u", inst)
print(f"N={N} pointwise conditional covariance > 0 somewhere: {pw_pos}; a not monotone in u (single direction): {mixed_dir}")
for k, v in ex.items(): print(k, v)
