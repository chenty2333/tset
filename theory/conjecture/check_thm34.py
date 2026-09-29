"""Random exact checks of Theorems 3 and 4 on two-level instances with up to 9
tests (beyond the exhaustive range), generated to satisfy each theorem's
hypotheses.  Exact enumeration of all class-contiguous orders."""
import itertools, random, json
from fractions import Fraction as Fr
import numpy as np
from pathlib import Path
rng = random.Random(17)

def orders(classes):
    blocks = {}
    for t, c in enumerate(classes): blocks.setdefault(c, []).append(t)
    blocks = list(blocks.values())
    out = []
    for border in itertools.permutations(range(len(blocks))):
        for parts in itertools.product(*(itertools.permutations(blocks[b]) for b in border)):
            out.append(tuple(x for p in parts for x in p))
    return np.array([[o.index(t) for t in range(len(classes))] for o in out])

def fB(pos, P, C):
    n = pos.shape[1]
    def fails(pz):
        v = pz[:, 0]; out = np.zeros(len(pz), bool)
        for p in P:
            pp = pz[:, p]; act = pp < v
            for c in C[p]:
                pc = pz[:, c]; act &= ~((pp < pc) & (pc < v))
            out |= act
        return out
    F = fails(pos); R = fails(n - 1 - pos)
    return Fr(int(F.sum()), len(F)), Fr(int((F & R).sum()), len(F))

def gen_thm3(n):
    while True:
        k = rng.randint(2, 4); classes = [0] + [rng.randrange(k) for _ in range(n - 1)]
        if len(set(classes)) < 2: continue
        # choose per class a type: P-type or C-type (victim class: 'nopoll' or 'internal')
        types = {c: rng.choice("PC") for c in set(classes)}
        roles = {}
        for t in range(1, n):
            c = classes[t]
            roles[t] = rng.choice("PCN") if (c != 0 and types[c] == "P") or c == 0 else rng.choice("CN")
        P = [t for t in range(1, n) if roles[t] == "P"]
        if not P: continue
        Cs = [t for t in range(1, n) if roles[t] == "C"]
        vic_mode = rng.choice(["nopoll", "internal"])
        if vic_mode == "nopoll":
            P = [p for p in P if classes[p] != 0]
            if not P: continue
        C = {}
        for p in P:
            cand = []
            for c in Cs:
                X = classes[c]
                # cleaner in a class with polluters may clean only polluters of that class
                has_p = any(classes[q] == X for q in P)
                if has_p and X != classes[p]: continue
                if X == 0 and vic_mode == "internal" and classes[p] != 0: continue
                cand.append(c)
            C[p] = [c for c in cand if rng.random() < .6]
        return classes, P, C

def gen_thm4(n):
    while True:
        k = rng.randint(2, 4); classes = [0] + [rng.randrange(k) for _ in range(n - 1)]
        if len(set(classes)) < 2: continue
        roles = {t: rng.choice("PGEN") for t in range(1, n)}
        P = [t for t in range(1, n) if roles[t] == "P"]; G = [t for t in range(1, n) if roles[t] == "G"]
        if not P: continue
        # decisiveness: every non-victim class with a polluter has a global cleaner
        if any(classes[p] != 0 and not any(classes[g] == classes[p] for g in G) for p in P): continue
        C = {p: list(G) + [e for e in range(1, n) if roles[e] == "E" and classes[e] == classes[p] and rng.random() < .6] for p in P}
        return classes, P, C

res = {}
for name, gen in (("theorem3", gen_thm3), ("theorem4", gen_thm4)):
    worst = None; cnt = 0
    for _ in range(250):
        n = rng.randint(4, 9)
        classes, P, C = gen(n)
        pos = orders(classes)
        if len(pos) > 60000: continue
        f, B = fB(pos, P, C); cnt += 1
        assert B <= f * f, (name, classes, P, C, f, B)
        g = f * f - B
        if worst is None or g < worst: worst = g
    res[name] = dict(instances=cnt, min_gap=str(worst))
print(res)
Path(__file__).with_name("check_thm34.json").write_text(json.dumps(res, indent=2))
