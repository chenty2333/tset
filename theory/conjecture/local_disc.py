"""Local model summaries (f,B,u,t,z) and the quadratic
H(x) = (u^2 - z) x^2 + 2(fu - t) x + (f^2 - B).
Check: (a) u^2 >= z, (b) discriminant (fu-t)^2 <= (u^2-z)(f^2-B)  [H >= 0 on R],
(c) H >= 0 on [0,1]."""
import itertools, random
from fractions import Fraction as Fr
rng = random.Random(4)
def summaries(m, P, G, E):
    tests = list(range(1, m + 1))
    def st(seq):
        seen = set()
        for t in seq:
            if t in G: return "K"
            if t in P and not (E[t] & seen): return "T"
            seen.add(t)
        return "U"
    n = m + 1; acc = {k: Fr(0) for k in ("f", "B", "u", "t", "z")}
    byj = {}
    for perm in itertools.permutations(tests + [0]):
        j = perm.index(0); byj.setdefault(j, []).append((st(list(reversed(perm[:j]))), st(list(perm[j + 1:]))))
    for j, L in byj.items():
        w = Fr(1, n * len(L))
        for a, b in L:
            acc["f"] += w * (a == "T"); acc["B"] += w * (a == "T" and b == "T")
            acc["u"] += w * (a == "U"); acc["t"] += w * (a == "U" and b == "T"); acc["z"] += w * (a == "U" and b == "U")
    return acc
bad = {"a": 0, "b": 0, "c": 0}; N = 0; ex = {}
for _ in range(2500):
    m = rng.randint(1, 5); tests = list(range(1, m + 1))
    roles = {t: rng.choice("PGEN") for t in tests}
    P = {t for t in tests if roles[t] == "P"}; G = {t for t in tests if roles[t] == "G"}
    ext = [t for t in tests if roles[t] == "E"]; E = {p: {e for e in ext if rng.random() < .6} for p in P}
    s = summaries(m, P, G, E); f, B, u, t, z = (s[k] for k in ("f", "B", "u", "t", "z"))
    A = u * u - z; Bc = f * u - t; Cc = f * f - B; N += 1
    if A < 0: bad["a"] += 1; ex.setdefault("a", (m, P, G, E, s))
    if Bc * Bc > A * Cc and A >= 0: bad["b"] += 1; ex.setdefault("b", (m, P, G, E, s))
    if min(A * x * x + 2 * Bc * x + Cc for x in [Fr(k, 100) for k in range(101)]) < 0: bad["c"] += 1
print("N", N, bad); [print(k, v) for k, v in ex.items()]
