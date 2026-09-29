"""Exhaustive search: two-level (class-contiguous) orders, Definition-1
semantics with polluter-specific cleaners, roles disjoint (no test is both a
polluter and a cleaner).  All class shapes up to isomorphism, all role and
cleaner-set assignments.  Reports max(B - f^2)."""
import itertools, sys
from fractions import Fraction as Fr
import numpy as np

def partitions(n, maxpart=None):
    if maxpart is None: maxpart = n
    if n == 0: yield []; return
    for k in range(min(n, maxpart), 0, -1):
        for rest in partitions(n - k, k):
            yield [k] + rest

def orders_for(classes):
    blocks = {}
    for t, c in enumerate(classes): blocks.setdefault(c, []).append(t)
    blocks = list(blocks.values())
    out = []
    for border in itertools.permutations(range(len(blocks))):
        for parts in itertools.product(*(itertools.permutations(blocks[b]) for b in border)):
            out.append(tuple(x for p in parts for x in p))
    n = len(classes)
    pos = np.array([[o.index(t) for t in range(n)] for o in out])
    return pos

def fails(pos, P, C):
    v = pos[:, 0]; out = np.zeros(len(pos), bool)
    for p in P:
        pp = pos[:, p]; act = pp < v
        for c in C[p]:
            pc = pos[:, c]; act &= ~((pp < pc) & (pc < v))
        out |= act
    return out

def run(n):
    m = n - 1; best = (-1, None); count = 0
    for vs in range(1, n + 1):                       # size of v's class
        for rest in partitions(n - vs):
            classes = [0] * vs + [i + 1 for i, k in enumerate(rest) for _ in range(k)]
            pos = orders_for(classes); rpos = (n - 1) - pos; M = len(pos)
            for roles in itertools.product("PCN", repeat=m):
                P = [i + 1 for i, r in enumerate(roles) if r == "P"]
                Cs = [i + 1 for i, r in enumerate(roles) if r == "C"]
                if not P: continue
                for masks in itertools.product(range(1 << len(Cs)), repeat=len(P)):
                    C = {p: [Cs[b] for b in range(len(Cs)) if mk >> b & 1] for p, mk in zip(P, masks)}
                    if Cs and any(all(c not in C[p] for p in P) for c in Cs):
                        continue          # every declared cleaner cleans something
                    F = fails(pos, P, C); R = fails(rpos, P, C)
                    f = Fr(int(F.sum()), M); B = Fr(int((F & R).sum()), M)
                    count += 1
                    gap = B - f * f
                    if gap > best[0]: best = (gap, (classes, P, C, f, B))
    return count, best

if __name__ == "__main__":
    import json
    from pathlib import Path
    out = Path(__file__).with_name("exhaust2_disjoint.json")
    res = json.loads(out.read_text()) if out.exists() else {}
    for n in map(int, sys.argv[1:]):
        cnt, best = run(n)
        print(f"n={n}: configs={cnt} max(B-f^2)={float(best[0]):+.6f} at {best[1]}", flush=True)
        res[str(n)] = dict(configurations=cnt, max_B_minus_f2=str(best[0]), argmax=str(best[1]))
        out.write_text(json.dumps(res, indent=2))
