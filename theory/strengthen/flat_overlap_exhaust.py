"""Exhaustive: interleaved (flat) orders, polluter-specific cleaners with
overlapping roles allowed (a test may be a polluter and a cleaner)."""
import itertools, json
import numpy as np
from pathlib import Path
import sys
res = json.loads(Path(__file__).with_name('flat_overlap_exhaust.json').read_text()) if Path(__file__).with_name('flat_overlap_exhaust.json').exists() else {}
for n in (map(int, sys.argv[1:]) if len(sys.argv) > 1 else (2, 3, 4, 5, 6)):
    m = n - 1; others = list(range(1, n))
    orders = list(itertools.permutations(range(n)))
    pos = np.array([[o.index(t) for t in range(n)] for o in orders]); rpos = (n - 1) - pos
    M = len(orders); worst = None; cnt = 0
    def fails(pz, P, C):
        v = pz[:, 0]; out = np.zeros(M, bool)
        for p in P:
            pp = pz[:, p]; act = pp < v
            for c in C[p]:
                pc = pz[:, c]; act &= ~((pp < pc) & (pc < v))
            out |= act
        return out
    for k in range(1, m + 1):
        for P in itertools.combinations(others, k):
            pools = [[t for t in others if t != p] for p in P]
            for choice in itertools.product(*[range(1 << (m - 1))] * k):
                C = {p: [pool[b] for b in range(m - 1) if ch >> b & 1] for p, pool, ch in zip(P, pools, choice)}
                F = fails(pos, P, C); R = fails(rpos, P, C)
                f = F.mean(); B = (F & R).mean(); cnt += 1
                g = B - f * f
                if worst is None or g > worst: worst = g
    res[str(n)] = dict(configurations=cnt, max_B_minus_f2=float(worst))
    print(n, res[str(n)], flush=True)
Path(__file__).with_name("flat_overlap_exhaust.json").write_text(json.dumps(res, indent=2))
