"""RQ3: suite-level detection under four scheduling policies.

All OD targets of a module are simulated jointly on the same orders.  Every
simulated detector run draws a private sequence of fresh uniform orders;
all policies consume the SAME sequence (common random numbers), so policy
differences are estimated from paired per-run differences.

Policies (budget = number of complete suite runs)
  IID    fresh order every run.
  PAIR   sigma_1, R sigma_1, sigma_2, R sigma_2, ...  (unconditional pairs).
  GATE   iDFlakies RandomDetector @ f54b3f0: run R(previous) iff the
         previous round discovered no NEW OD test and the previous order was
         not itself a reversal (its reversal was already issued); otherwise
         a fresh order.  Fresh orders are not de-duplicated (as in the tool).
  STRICT like GATE, but reverse iff the previous run had no failing target
         (the alternative left commented out in RandomDetector).

Protocols
  NR (ISSTA'23 definition) a target is detected once a passing AND a
     failing order have both been observed within the budget.
  KR (known passing reference, iDFlakies/TACAS'21 setting) the original
     order passed; a target is detected at its first failing run.
  For GATE, "new" means newly detected under the protocol in force.

Estimates: mean detected targets per budget with standard errors over T
independent detector runs; paired differences for policy contrasts.
Output: results/suite_<SEM>.json
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

from common import ROOT, Evaluator, Sampler, load_modules, pack

OUT = ROOT / "empirical" / "results"
POLICIES = ("IID", "PAIR", "GATE", "STRICT")
CONTRASTS = (("PAIR", "IID"), ("GATE", "IID"), ("STRICT", "IID"), ("PAIR", "GATE"))
SEED = 20261102


def popcount(x):
    return np.bitwise_count(x).astype(np.int64)


def simulate_chunk(Fm, Rm, allbits, consistent):
    """Fm, Rm: (T, R) uint64 masks of failing targets for fresh order j and
    its reversal.  Returns dict[(protocol, policy, subset)] -> (T, R) counts
    and 'any' indicators for the NR protocol."""
    T, R = Fm.shape
    rows = np.arange(T)
    out = {}
    for proto in ("NR", "KR"):
        for pol in POLICIES:
            fresh = np.zeros(T, dtype=np.int64)       # next fresh index
            last = np.zeros(T, dtype=np.int64)        # fresh index of last anchor
            last_rev = np.zeros(T, dtype=bool)
            last_new = np.zeros(T, dtype=np.uint64)
            last_mask = np.zeros(T, dtype=np.uint64)
            seenF = np.zeros(T, dtype=np.uint64)
            seenP = np.zeros(T, dtype=np.uint64)
            det = np.zeros(T, dtype=np.uint64)
            cnt_all = np.empty((T, R), dtype=np.int16)
            cnt_con = np.empty((T, R), dtype=np.int16)
            anyd = np.empty((T, R), dtype=bool)
            for t in range(R):
                if pol == "IID" or t == 0:
                    rev = np.zeros(T, dtype=bool)
                elif pol == "PAIR":
                    rev = np.full(T, t % 2 == 1)
                elif pol == "GATE":
                    rev = (last_new == 0) & ~last_rev
                else:
                    rev = (last_mask == 0) & ~last_rev
                idx = np.where(rev, last, fresh)
                mask = np.where(rev, Rm[rows, np.minimum(idx, R - 1)], Fm[rows, np.minimum(idx, R - 1)])
                last = np.where(rev, last, fresh)
                fresh = np.where(rev, fresh, fresh + 1)
                seenF |= mask
                seenP |= (~mask) & allbits
                newdet = (seenF & seenP) if proto == "NR" else seenF
                last_new = newdet & ~det
                det = newdet
                last_rev, last_mask = rev, mask
                cnt_all[:, t] = popcount(det)
                cnt_con[:, t] = popcount(det & consistent)
                anyd[:, t] = det != 0
            out[(proto, pol, "all")] = cnt_all
            out[(proto, pol, "consistent")] = cnt_con
            out[(proto, pol, "any")] = anyd
    return out


def run(sem="S1", T=20_000, R=40, chunk=2_000):
    rng = np.random.default_rng(SEED)
    t0 = time.time()
    import csv
    per = {(r["slug"], r["path"], r["test"]): r for r in csv.DictReader(open(OUT / f"pertest_{sem}.csv"))}
    result = dict(semantics=sem, runs_per_module=T, budget_max=R, seed=SEED, modules=[])
    for mod in load_modules():
        tests = mod.relevant_tests()
        s = Sampler(tests)
        ev = Evaluator(mod.targets, s, sem)
        m = len(mod.targets)
        allbits = np.uint64((1 << m) - 1)
        consistent = np.uint64(sum(1 << j for j, t in enumerate(mod.targets)
                                   if per[(mod.slug, mod.path, t.name)]["original_outcome"] == "pass"))
        acc = {}
        for c0 in range(0, T, chunk):
            Tc = min(chunk, T - c0)
            pos = s.positions(rng, Tc * R)
            Fm = pack(ev.fails(pos)).reshape(Tc, R)
            Rm = pack(ev.fails(s.n - 1 - pos)).reshape(Tc, R)
            sims = simulate_chunk(Fm, Rm, allbits, consistent)
            for proto in ("NR", "KR"):
                for sub in ("all", "consistent", "any"):
                    for pol in POLICIES:
                        x = sims[(proto, pol, sub)].astype(np.float64)
                        a = acc.setdefault((proto, sub, pol), [np.zeros(R), np.zeros(R)])
                        a[0] += x.sum(0); a[1] += (x * x).sum(0)
                    for p1, p2 in CONTRASTS:
                        d = (sims[(proto, p1, sub)].astype(np.float64)
                             - sims[(proto, p2, sub)].astype(np.float64))
                        a = acc.setdefault((proto, sub, f"{p1}-{p2}"), [np.zeros(R), np.zeros(R)])
                        a[0] += d.sum(0); a[1] += (d * d).sum(0)
        entry = dict(module=mod.name, path=mod.path, slug=mod.slug, targets=m,
                     consistent_targets=int(bin(int(consistent)).count("1")), stats={})
        for (proto, sub, key), (s1, s2) in acc.items():
            mean = s1 / T
            var = np.maximum(s2 / T - mean ** 2, 0) * T / (T - 1)
            entry["stats"].setdefault(proto, {}).setdefault(sub, {})[key] = dict(
                mean=mean.round(6).tolist(), se=np.sqrt(var / T).round(6).tolist())
        result["modules"].append(entry)
        print(f"{mod.name[:40]:40s} targets={m:3d} rel={s.n:4d} {time.time() - t0:7.1f}s", flush=True)
    result["seconds"] = round(time.time() - t0, 1)
    (OUT / f"suite_{sem}.json").write_text(json.dumps(result))


if __name__ == "__main__":
    sem = sys.argv[1] if len(sys.argv) > 1 else "S1"
    T = int(sys.argv[2]) if len(sys.argv) > 2 else 20_000
    run(sem, T=T)
