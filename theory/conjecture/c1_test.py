"""(C1): class level only.  Classes (lists of tests) get i.i.d. sides
Bernoulli(w); left classes in uniform order, uniform internal orders, scanned
from the near end; same on the right.  Left event: some polluter not in dead
set DL is met before all of its cleaners; right event likewise with DR.
Test Cov(Gamma_L(D), Gamma_R(D^c)) <= 0 for fixed w (grid)."""
import itertools, random
from functools import lru_cache
rng = random.Random(9)

def run(trials=600):
    worst = -1; ex = None
    for _ in range(trials):
        n = rng.randint(2, 6)
        tests = list(range(1, n + 1)); rng.shuffle(tests)
        classes = []; i = 0
        while i < n:
            k = rng.randint(1, min(3, n - i)); classes.append(tuple(tests[i:i + k])); i += k
        roles = {t: rng.choice("PCN") for t in tests}
        P = [t for t in tests if roles[t] == "P"] or [tests[0]]
        for p in P: roles[p] = "P"
        Cl = [t for t in tests if roles[t] == "C"]
        C = {p: frozenset(c for c in Cl if rng.random() < .6) for p in P}
        DL = frozenset(p for p in P if rng.random() < .3); DR = frozenset(p for p in P if rng.random() < .3)
        @lru_cache(None)
        def gamma(D, dead):
            blocks = [classes[j] for j in D]
            tot = cnt = 0
            for co in itertools.permutations(range(len(blocks))):
                for inner in itertools.product(*(list(itertools.permutations(blocks[j])) for j in co)):
                    seq = [t for b in inner for t in b]     # near end first
                    seen = set(); hit = False
                    for t in seq:
                        if t in C and t not in dead and not (C[t] & seen): hit = True; break
                        seen.add(t)
                    tot += 1; cnt += hit
            return cnt / tot if tot else 0.0
        K = range(len(classes))
        for w in (0.1, 0.3, 0.5, 0.7, 0.9):
            E1 = E2 = E12 = 0.0
            for r in range(len(classes) + 1):
                for D in itertools.combinations(K, r):
                    Dc = tuple(j for j in K if j not in D)
                    pw = w ** len(D) * (1 - w) ** len(Dc)
                    a = gamma(D, DL); b = gamma(Dc, DR)
                    E1 += pw * a; E2 += pw * b; E12 += pw * a * b
            cov = E12 - E1 * E2
            if cov > worst: worst = cov; ex = (classes, P, dict(C), DL, DR, w)
    return worst, ex

w, ex = run()
print("max Cov =", w); print(ex if w > 1e-12 else "")
