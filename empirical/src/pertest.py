"""RQ1/RQ2 inputs: per-target failure rate f and reversal joint failure B.

f = P(target fails in a uniform class-contiguous order),
B = P(target fails in the order AND in its reversal).

Exact rational values for every target covered by the common-cleaner
theorem (all polluters share one cleaner set of single tests, disjoint
from polluters and the victim) and for every brittle; Monte Carlo with
recorded cell counts for the remaining targets.  Exact values are also
cross-checked by Monte Carlo (z-scores recorded).

Output: results/pertest_<SEM>.csv and results/pertest_<SEM>_validation.json
"""
from __future__ import annotations

import csv
import json
import sys
import time
from fractions import Fraction as Fr

import numpy as np

from common import ROOT, Evaluator, Sampler, Target, class_of, fails_single, load_modules

OUT = ROOT / "empirical" / "results"
N_MC = 2_000_000          # samples for targets without a closed form
N_CHECK = 200_000         # samples used to cross-check closed forms
SEED = 20261102


def exact_fB(t: Target, sem: str):
    """Closed-form (f, B) or None if the target is outside the theorem."""
    if t.kind == "brittle":
        if not t.setters:
            return Fr(1), Fr(1)
        rel_classes = {class_of(s) for s in t.setters} | {class_of(t.name)}
        s_b = sum(class_of(s) == class_of(t.name) for s in t.setters)
        return Fr(1, len(rel_classes) * (s_b + 1)), Fr(0)
    sets = {tuple(t.cleaners(p, sem)) for p in t.polluters}
    if len(sets) != 1:
        return None
    groups = next(iter(sets))
    if any(len(g) != 1 for g in groups):
        return None
    P, C = set(t.polluters), {g[0] for g in groups}
    if P & C or t.name in P | C:
        return None
    cv = class_of(t.name)
    a = sum(class_of(p) == cv for p in P)
    b = sum(class_of(c) == cv for c in C)
    other = sorted({class_of(x) for x in P | C} - {cv})
    alphas = []
    for c in other:
        pc = sum(class_of(p) == c for p in P)
        cc = sum(class_of(x) == c for x in C)
        alphas.append(Fr(pc, pc + cc))
    k = 1 + len(other)
    S, Q = sum(alphas, Fr(0)), sum((x * x for x in alphas), Fr(0))
    r = a + b
    if r > 0:
        h = S / k
        return (a + h) / (r + 1), Fr(a) * (a - 1 + 2 * h) / (r * (r + 1))
    if k > 1:
        return S / k, (S * S - Q) / (k * (k - 1))
    return Fr(0), Fr(0)


def mc_cells(t: Target, sem: str, n: int, rng) -> tuple[int, int, int, int]:
    """Counts (both fail, fwd only, rev only, neither) over n sampled orders."""
    s = Sampler(sorted(t.relevant()))
    ev = Evaluator([t], s, sem)
    n11 = n10 = n01 = n00 = 0
    chunk = 250_000
    done = 0
    while done < n:
        m = min(chunk, n - done)
        pos = s.positions(rng, m)
        fwd = ev.fails(pos)[:, 0]
        rev = ev.fails(s.n - 1 - pos)[:, 0]
        n11 += int(np.sum(fwd & rev)); n10 += int(np.sum(fwd & ~rev))
        n01 += int(np.sum(~fwd & rev)); n00 += int(np.sum(~fwd & ~rev))
        done += m
    return n11, n10, n01, n00


def main(sem: str = "S1"):
    rng = np.random.default_rng(SEED)
    rows, zs, t0 = [], [], time.time()
    for mod in load_modules():
        opos = {x: i for i, x in enumerate(mod.original)}
        for t in mod.targets:
            rel = t.relevant()
            missing = sorted(x for x in rel if x not in opos)
            orig = "" if missing else ("fail" if fails_single(mod.original, t, sem) else "pass")
            ex = exact_fB(t, sem)
            row = dict(module=mod.name, slug=mod.slug, path=mod.path, test=t.name, kind=t.kind,
                       n_polluters=len(t.polluters) if t.kind == "victim" else len(t.setters),
                       n_cleaners=len({c for p in t.polluters for g in t.cleaners(p, sem) for c in g}),
                       n_rel_tests=len(rel), n_rel_classes=len({class_of(x) for x in rel}),
                       cleaner_groups=int(any(len(g) > 1 for p in t.polluters for g in t.polluters[p])),
                       original_outcome=orig, missing_in_original=len(missing))
            if ex is not None:
                f, B = ex
                n11, n10, n01, n00 = mc_cells(t, sem, N_CHECK, rng)
                N = n11 + n10 + n01 + n00
                fh, Bh = (2 * n11 + n10 + n01) / (2 * N), n11 / N
                for est, true in ((fh, float(f)), (Bh, float(B))):
                    se = max(np.sqrt(max(true * (1 - true), 1e-12) / N), 1e-12)
                    zs.append((est - true) / se)
                row.update(method="exact", f=f"{f.numerator}/{f.denominator}",
                           B=f"{B.numerator}/{B.denominator}", f_float=float(f), B_float=float(B),
                           n11="", n10="", n01="", n00="")
            else:
                n11, n10, n01, n00 = mc_cells(t, sem, N_MC, rng)
                N = n11 + n10 + n01 + n00
                row.update(method="monte_carlo", f="", B="",
                           f_float=(2 * n11 + n10 + n01) / (2 * N), B_float=n11 / N,
                           n11=n11, n10=n10, n01=n01, n00=n00)
            rows.append(row)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"pertest_{sem}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    zs = np.array(zs)
    val = dict(semantics=sem, targets=len(rows), exact=sum(r["method"] == "exact" for r in rows),
               monte_carlo=sum(r["method"] == "monte_carlo" for r in rows),
               mc_samples_for_non_closed_form=N_MC, mc_samples_for_closed_form_check=N_CHECK,
               closed_form_check_max_abs_z=float(np.max(np.abs(zs))),
               closed_form_check_count=int(len(zs)), seed=SEED, seconds=round(time.time() - t0, 1))
    (OUT / f"pertest_{sem}_validation.json").write_text(json.dumps(val, indent=2))
    print(json.dumps(val, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "S1")
