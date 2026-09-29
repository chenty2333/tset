"""Search for B > f^2 under general Definition-1 semantics
(polluter-specific cleaner sets, roles may overlap) on flat and two-level
(class-contiguous) orders. Exact enumeration of all legal orders."""
import itertools, random, sys
from fractions import Fraction as Fr

def legal_orders(classes):
    labels = sorted(set(classes))
    blocks = [[i for i, c in enumerate(classes) if c == l] for l in labels]
    out = []
    for border in itertools.permutations(range(len(blocks))):
        for parts in itertools.product(*(itertools.permutations(blocks[b]) for b in border)):
            out.append(tuple(x for p in parts for x in p))
    return out

def fails(order, P, C):
    pos = {t: i for i, t in enumerate(order)}
    v = pos[0]
    for p in P:
        if pos[p] < v and not any(pos[p] < pos[c] < v for c in C[p]):
            return True
    return False

def fB(classes, P, C, orders):
    nf = nb = 0
    for o in orders:
        a = fails(o, P, C); b = fails(o[::-1], P, C)
        nf += a; nb += a and b
    T = len(orders)
    return Fr(nf, T), Fr(nb, T)

def run(n_other, samples, levels, seed=1, allow_overlap=True):
    rng = random.Random(seed)
    n = n_other + 1
    worst = None
    cache = {}
    for _ in range(samples):
        if levels == 1:
            classes = (0,) * n
        else:
            classes = tuple(rng.randrange(1, n) if i else rng.randrange(1, n) for i in range(n))
        if classes not in cache:
            cache[classes] = legal_orders(classes)
        orders = cache[classes]
        others = list(range(1, n))
        P = [t for t in others if rng.random() < 0.5] or [rng.choice(others)]
        C = {}
        for p in P:
            pool = [t for t in others if t != p and (allow_overlap or t not in P)]
            C[p] = [t for t in pool if rng.random() < 0.4]
        f, B = fB(classes, P, C, orders)
        gap = B - f * f
        if worst is None or gap > worst[0]:
            worst = (gap, classes, P, C, f, B)
    return worst

if __name__ == "__main__":
    for levels in (1, 2):
        for n_other in (3, 4, 5, 6):
            for ov in (False, True):
                w = run(n_other, 3000 if n_other < 6 else 800, levels, seed=n_other, allow_overlap=ov)
                print(f"levels={levels} n_other={n_other} overlap={ov}: max(B-f^2)={float(w[0]):+.5f}",
                      "" if w[0] <= 0 else f"COUNTEREXAMPLE classes={w[1]} P={w[2]} C={w[3]} f={w[4]} B={w[5]}", flush=True)
