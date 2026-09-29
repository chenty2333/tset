"""Which theorem covers each OD test under class-contiguous orders (S1)?
Thm 1: brittle, or victim with a common cleaner set disjoint from polluters.
Thm 3: disjoint roles; every class other than the victim's either has no
       polluter or its cleaners clean only polluters of that class; the
       victim's class has no polluter or its cleaners clean only its polluters.
Thm 4: disjoint roles; with G = intersection of all cleaner sets (global
       cleaners), every other cleaner of p lies in p's class (no further
       condition on outside classes; extended form, see supplement).
Self-cleaner entries (p listed in C_p) are removed first: they are vacuous.
Output: results/coverage_S1.json and paper/generated/macros_coverage_S1.tex"""
import collections, json
from common import ROOT, class_of, load_modules

OUT = ROOT / "empirical" / "results"; GEN = ROOT / "paper" / "generated"

def covered(t):
    if t.kind == "brittle":
        return "Thm1"
    P = set(t.polluters)
    # normalise: a polluter listed as its own cleaner is vacuous (never strictly between itself and v)
    Cp = {p: {c for g in t.cleaners(p, "S1") for c in g} - {p} for p in P}
    C = set().union(*Cp.values()) if Cp else set()
    if (C & P) or t.name in C:
        return "overlapping roles"
    if len({frozenset(s) for s in Cp.values()}) <= 1:
        return "Thm1"
    cv = class_of(t.name)
    cleans = {c: {p for p in P if c in Cp[p]} for c in C}
    classes = {class_of(x) for x in P | C}
    ok3 = True
    for X in classes:
        PX = {p for p in P if class_of(p) == X}
        CX = {c for c in C if class_of(c) == X}
        if PX and any(class_of(p) != X for c in CX for p in cleans[c]):
            ok3 = False
    if ok3:
        return "Thm3"
    # Theorem 4 (extended): with G the common cleaners, every other cleaner of p lies in p's class
    G = set.intersection(*Cp.values())
    if all(class_of(e) == class_of(p) for p in P for e in Cp[p] - G):
        return "Thm4"
    return "Conjecture1"


res = collections.Counter(); detail = []
for m in load_modules():
    for t in m.targets:
        c = covered(t); res[c] += 1
        selfc = t.kind == "victim" and any(p in {x for g in t.cleaners(p, "S1") for x in g} for p in t.polluters)
        detail.append(dict(module=m.name, test=t.name, covered_by=c, self_cleaner=selfc))
(OUT / "coverage_S1.json").write_text(json.dumps(dict(counts=res, tests=detail), indent=2))
M = {"CovThmOne": res["Thm1"], "CovThmThree": res["Thm3"], "CovThmFour": res["Thm4"],
     "CovConj": res["Conjecture1"], "CovOverlap": res["overlapping roles"],
     "CovTheorems": res["Thm1"] + res["Thm3"] + res["Thm4"],
     "CovSelfCleaner": sum(1 for d in detail if d["self_cleaner"])}
(GEN / "macros_coverage_S1.tex").write_text("\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items()) + "\n")
print(dict(res)); print(M)
