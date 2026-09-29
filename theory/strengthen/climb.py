"""Hill-climbing search maximising B - f^2 over Definition-1 configurations
on a given tree shape family.  Trees: nested tuples of leaf ids (0 = victim)."""
import itertools, random, sys
from fractions import Fraction as Fr
import numpy as np

def all_orders(tree):
    if isinstance(tree, int):
        yield (tree,); return
    for p in itertools.permutations(tree):
        for parts in itertools.product(*(list(all_orders(c)) for c in p)):
            yield tuple(x for part in parts for x in part)

class Shape:
    def __init__(self, tree, n):
        self.tree, self.n = tree, n
        orders = list(all_orders(tree))
        self.pos = np.array([[o.index(t) for t in range(n)] for o in orders])  # (M, n)
        self.rpos = (n - 1) - self.pos
    def fB(self, P, C):
        def fails(pos):
            v = pos[:, 0]
            out = np.zeros(len(pos), bool)
            for p in P:
                pp = pos[:, p]; act = pp < v
                for c in C[p]:
                    pc = pos[:, c]; act &= ~((pp < pc) & (pc < v))
                out |= act
            return out
        F = fails(self.pos); R = fails(self.rpos)
        M = len(F)
        return Fr(int(F.sum()), M), Fr(int((F & R).sum()), M)

def random_config(n, rng):
    others = list(range(1, n))
    P = [t for t in others if rng.random() < 0.5] or [rng.choice(others)]
    C = {p: [t for t in others if t != p and rng.random() < 0.4] for p in P}
    return P, C

def mutate(P, C, n, rng):
    P = list(P); C = {k: list(v) for k, v in C.items()}
    others = list(range(1, n))
    r = rng.random()
    if r < 0.3:
        t = rng.choice(others)
        if t in P and len(P) > 1:
            P.remove(t); C.pop(t)
        elif t not in P:
            P.append(t); C[t] = []
    else:
        p = rng.choice(P); t = rng.choice([x for x in others if x != p])
        if t in C[p]: C[p].remove(t)
        else: C[p].append(t)
    return P, C

def climb(shape, iters, rng, restarts):
    best = None
    for _ in range(restarts):
        P, C = random_config(shape.n, rng)
        f, B = shape.fB(P, C); cur = B - f * f
        for _ in range(iters):
            P2, C2 = mutate(P, C, shape.n, rng)
            f2, B2 = shape.fB(P2, C2); val = B2 - f2 * f2
            if val >= cur or rng.random() < 0.02:
                P, C, cur, f, B = P2, C2, val, f2, B2
                if best is None or cur > best[0]:
                    best = (cur, P, C, f, B)
    return best

def random_tree(n, depth, rng):
    """random tree with leaves 0..n-1 and at most `depth` internal levels"""
    leaves = list(range(n)); rng.shuffle(leaves)
    def build(items, d):
        if len(items) == 1: return items[0]
        if d == 1: return tuple(items)
        k = rng.randint(2, min(4, len(items)))
        cuts = sorted(rng.sample(range(1, len(items)), k - 1))
        groups = [items[a:b] for a, b in zip([0] + cuts, cuts + [len(items)])]
        return tuple(build(g, d - 1) for g in groups)
    return build(leaves, depth)

if __name__ == "__main__":
    rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    for depth in (2, 3):
        for n in (5, 6, 7, 8):
            best = None
            trials = 12 if n < 8 else 6
            for _ in range(trials):
                tree = random_tree(n, depth, rng)
                sh = Shape(tree, n)
                if len(sh.pos) > 50000: continue
                b = climb(sh, 250, rng, 3)
                if best is None or b[0] > best[0]:
                    best = (b[0], tree, b[1], b[2], b[3], b[4])
            print(f"depth={depth} n={n}: max(B-f^2)={float(best[0]):+.5f}  tree={best[1]} P={best[2]} C={best[3]} f={best[4]} B={best[5]}", flush=True)
