"""(C2): local class = uniform permutation of local tests around v.
score(side) = 1 if a local polluter is active on that side, else phi(Z), with
Z = local cleaners on that side (tail polluters killed by them), phi decreasing.
Test Cov(score_L, score_R) <= 0 for (a) arbitrary decreasing phi and
(b) phi arising from a tail of independent 'tail polluters' q_k each killed by
a subset K_k of local cleaners: phi(Z) = 1 - prod_{k: K_k ∩ Z = ∅}(1 - beta_k)."""
import itertools, random
rng = random.Random(3)

def run(mode, trials=3000):
    worst = -1; bad = None
    for _ in range(trials):
        m = rng.randint(1, 6)
        tests = list(range(1, m + 1))
        roles = {t: rng.choice("PC") for t in tests}
        P = [t for t in tests if roles[t] == "P"]; Cl = [t for t in tests if roles[t] == "C"]
        C = {p: {c for c in Cl if rng.random() < .5} for p in P}
        subsets = [frozenset(s) for r in range(len(Cl) + 1) for s in itertools.combinations(Cl, r)]
        if mode == "arbitrary":
            # random decreasing set function: phi(Z) = min over supersets ... build via random values then enforce monotone
            val = {Z: rng.random() for Z in subsets}
            for Z in sorted(subsets, key=len):
                for c in Cl:
                    if c not in Z:
                        Z2 = Z | {c}
                        val[Z2] = min(val[Z2], val[Z])
            phi = val
        else:
            K = [(frozenset(c for c in Cl if rng.random() < .5), rng.random()) for _ in range(rng.randint(1, 3))]
            phi = {}
            for Z in subsets:
                pr = 1.0
                for Kk, bk in K:
                    if not (Kk & Z): pr *= (1 - bk)
                phi[Z] = 1 - pr
        E1 = E2 = E12 = 0.0; N = 0
        for perm in itertools.permutations(tests + [0]):
            i = perm.index(0)
            left = list(reversed(perm[:i])); right = list(perm[i + 1:])
            def score(seq):
                seen = set()
                for t in seq:
                    if t in P and not (C[t] & seen): return 1.0
                    seen.add(t)
                return phi[frozenset(x for x in seq if x in Cl)]
            a, b = score(left), score(right)
            E1 += a; E2 += b; E12 += a * b; N += 1
        cov = E12 / N - (E1 / N) * (E2 / N)
        if cov > worst: worst = cov; bad = (P, C, phi if mode != "arbitrary" else "arb")
    return worst, bad

for mode in ("tail", "arbitrary"):
    w, bad = run(mode)
    print(mode, "max Cov =", w, "" if w <= 1e-12 else bad)
