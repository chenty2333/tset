import random, sys
from climb import Shape, climb, random_tree
import climb as CL

def random_config_noov(n, rng):
    others = list(range(1, n))
    P = [t for t in others if rng.random() < 0.5] or [rng.choice(others)]
    rest = [t for t in others if t not in P]
    C = {p: [t for t in rest if rng.random() < 0.5] for p in P}
    return P, C

def mutate_noov(P, C, n, rng):
    others = list(range(1, n))
    for _ in range(20):
        P2 = list(P); C2 = {k: list(v) for k, v in C.items()}
        if rng.random() < 0.3:
            t = rng.choice(others)
            if t in P2 and len(P2) > 1:
                P2.remove(t); C2.pop(t)
            elif t not in P2:
                P2.append(t); C2[t] = []
                for k in C2:
                    if t in C2[k]: C2[k].remove(t)
        else:
            p = rng.choice(P2); rest = [x for x in others if x not in P2]
            if not rest: continue
            t = rng.choice(rest)
            if t in C2[p]: C2[p].remove(t)
            else: C2[p].append(t)
        return P2, C2
    return P, C

mode = sys.argv[1]
rng = random.Random(int(sys.argv[2]))
if mode == "noov":
    CL.random_config, CL.mutate = random_config_noov, mutate_noov
    depths = (2, 3)
else:
    depths = (1,)
for depth in depths:
    for n in (5, 6, 7, 8):
        best = None
        for _ in range(16 if n < 8 else 8):
            tree = tuple(range(n)) if depth == 1 else random_tree(n, depth, rng)
            sh = Shape(tree, n)
            if len(sh.pos) > 50000: continue
            b = climb(sh, 300, rng, 3)
            if best is None or b[0] > best[0]:
                best = (b[0], tree, b[1], b[2], b[3], b[4])
        print(f"{mode} depth={depth} n={n}: max(B-f^2)={float(best[0]):+.5f} tree={best[1]} P={best[2]} C={best[3]} f={best[4]} B={best[5]}", flush=True)
