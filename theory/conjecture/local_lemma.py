"""Local lemma: victim's class = flat arrangement of local tests around v.
Polluters with cleaner sets (global cleaners kill everything incl. the tail;
extras kill only their own polluters).  Beyond the local tests, each side has
an independent tail that triggers with probability x, reached iff the side is
undecided (no active polluter, no global cleaner seen).
Check (1) H(x) = f''^2 - B'' >= 0; (2) a(u) = P(F''|u) monotone in u for each x."""
import itertools, random
from fractions import Fraction as Fr
rng = random.Random(2)

def analyse(m, P, G, E, xs=(Fr(0), Fr(1, 4), Fr(1, 2), Fr(3, 4), Fr(1))):
    tests = list(range(1, m + 1))
    def side_state(seq):              # 'T' trigger, 'K' killed by global, 'U' undecided
        seen = set()
        for t in seq:
            if t in G: return "K"
            if t in P and not (E[t] & seen): return "T"
            seen.add(t)
        return "U"
    # enumerate: v position j and left subset / orders -> (state_L, state_R) counts by j
    by_j = {}
    for perm in itertools.permutations(tests + [0]):
        j = perm.index(0)
        sL = side_state(list(reversed(perm[:j]))); sR = side_state(list(perm[j + 1:]))
        by_j.setdefault(j, []).append((sL, sR))
    res = []
    for x in xs:
        val = lambda s: Fr(1) if s == "T" else (x if s == "U" else Fr(0))
        n = m + 1
        f = sum(sum(val(a) for a, _ in L) / len(L) for L in by_j.values()) / n
        B = sum(sum((1 if a == "T" else (x if a == "U" else 0)) * (1 if b == "T" else (x if b == "U" else 0))
                    for a, b in L) / len(L) for L in by_j.values()) / n
        # note: when both sides undecided, tails independent -> x*x ; product form above is exact
        pj = [sum(val(a) for a, _ in by_j[j]) / len(by_j[j]) for j in range(n)]
        mono = all(pj[i] <= pj[i + 1] for i in range(n - 1)) or all(pj[i] >= pj[i + 1] for i in range(n - 1))
        res.append((x, f * f - B, mono))
    return res

bad_H = 0; nonmono = 0; N = 0; ex = None
for _ in range(1500):
    m = rng.randint(1, 5); tests = list(range(1, m + 1))
    roles = {t: rng.choice("PGEN") for t in tests}
    P = {t for t in tests if roles[t] == "P"}; G = {t for t in tests if roles[t] == "G"}
    extras = [t for t in tests if roles[t] == "E"]
    E = {p: {e for e in extras if rng.random() < .6} for p in P}
    for x, gap, mono in analyse(m, P, G, E):
        N += 1
        if gap < 0: bad_H += 1
        if not mono:
            nonmono += 1
            if ex is None: ex = (m, P, G, E, x)
print(f"cases={N}  H(x)<0: {bad_H}  position-profile not monotone: {nonmono}  example={ex}")
