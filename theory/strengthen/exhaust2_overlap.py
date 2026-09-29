"""Exhaustive: two-level orders, overlapping roles allowed (any test may be a
polluter and, independently, a member of any other polluter's cleaner set)."""
import itertools, json, sys
import numpy as np
from pathlib import Path
from exhaust2 import partitions, orders_for, fails
res = {}
for n in map(int, sys.argv[1:]):
    m = n - 1; others = list(range(1, n)); best = None; cnt = 0
    for vs in range(1, n + 1):
        for rest in partitions(n - vs):
            classes = [0] * vs + [i + 1 for i, k in enumerate(rest) for _ in range(k)]
            if len(set(classes)) == 1: continue          # flat case handled elsewhere
            pos = orders_for(classes); rpos = (n - 1) - pos; M = len(pos)
            for k in range(1, m + 1):
                for P in itertools.combinations(others, k):
                    pools = [[t for t in others if t != p] for p in P]
                    for choice in itertools.product(*[range(1 << (m - 1))] * k):
                        C = {p: [pool[b] for b in range(m - 1) if ch >> b & 1] for p, pool, ch in zip(P, pools, choice)}
                        F = fails(pos, P, C); R = fails(rpos, P, C)
                        g = (F & R).mean() - F.mean() ** 2; cnt += 1
                        if best is None or g > best[0]: best = (g, classes, P, C)
    res[n] = dict(configurations=cnt, max_B_minus_f2=float(best[0]), argmax=str(best[1:]))
    print(n, res[n], flush=True)
Path(__file__).with_name("exhaust2_overlap.json").write_text(json.dumps(res, indent=2))
