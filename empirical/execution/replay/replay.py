"""Replay detector policies on recorded real executions (no new runs).

Each recorded pair is an independent uniform anchor order and its reversal, with
the real target outcomes of both. IID, PAIR, GATE, and STRICT only ever run a fresh
order or the reverse of the previous fresh order, so every policy can be replayed
exactly on the recorded outcomes. A detector run draws pairs with replacement; all
policies share the same pair sequence (common random numbers). Uncertainty: outer
bootstrap over the recorded pairs, inner Monte Carlo over detector runs.

Detection is over the module's published OD targets, as in the simulation.
KR: a target is detected at its first failing run. NR: both outcomes must occur.
GATE reverses iff the previous round was fresh and detected no new target (KR or
NR sense, matching the protocol). STRICT reverses iff the previous fresh round had
no target failure.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
POLICIES = ("IID", "PAIR", "GATE", "STRICT")


def load_pairs(subject, results):
    rows = [json.loads(l) for l in (results / subject / "formal.jsonl").read_text().splitlines()]
    by = {}
    for r in rows:
        by.setdefault(r["pair"], {})[r["direction"]] = r
    pairs = [(d["anchor"]["observed"], d["reverse"]["observed"]) for _, d in sorted(by.items())
             if set(d) == {"anchor", "reverse"} and d["anchor"]["valid"] and d["reverse"]["valid"]]
    return np.array(pairs, dtype=bool)  # [n_pairs, 2, n_targets]


def run_policies(P, seq, rounds):
    """P: [n,2,T] outcomes; seq: [runs, rounds] pair indices. Returns detected
    counts [policy, protocol(KR,NR), runs, rounds]."""
    runs, T = seq.shape[0], P.shape[2]
    out = np.zeros((len(POLICIES), 2, runs, rounds))
    for pi, pol in enumerate(POLICIES):
        for proto in (0, 1):
            fail = np.zeros((runs, T), bool); ok = np.zeros((runs, T), bool)
            nxt = np.zeros(runs, int)          # next fresh pair position in seq
            prev_fresh = np.full(runs, -1)     # pair index of previous round if it was fresh, else -1
            gate_flag = np.zeros(runs, bool)
            for r in range(rounds):
                if pol == "IID":
                    rev = np.zeros(runs, bool)
                elif pol == "PAIR":
                    rev = prev_fresh >= 0
                else:
                    rev = (prev_fresh >= 0) & gate_flag
                idx = np.where(rev, prev_fresh, seq[np.arange(runs), np.minimum(nxt, rounds - 1)])
                outc = P[idx, rev.astype(int)]                  # [runs, T]
                before = fail.copy() if proto == 0 else (fail & ok)
                fail |= outc; ok |= ~outc
                det = fail if proto == 0 else (fail & ok)
                new = (det & ~before).any(1)
                if pol == "GATE":
                    gate_flag = ~new
                elif pol == "STRICT":
                    gate_flag = ~outc.any(1)
                nxt = np.where(rev, nxt, nxt + 1)
                prev_fresh = np.where(rev, -1, idx)
                out[pi, proto, :, r] = det.sum(1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("subjects", nargs="+")
    ap.add_argument("--results", type=Path, default=HERE.parent / "results")
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--outer", type=int, default=400)
    ap.add_argument("--inner", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=2026092930)
    ap.add_argument("--out", type=Path, default=HERE / "replay_summary.json")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    budgets = [b for b in (1, 2, 4, 10, 20, 40) if b <= a.rounds]
    summary = {"seed": a.seed, "outer": a.outer, "inner": a.inner, "rounds": a.rounds, "modules": {}}
    tot_targets = 0; tot = None
    for s in a.subjects:
        P = load_pairs(s, a.results); n, _, T = P.shape; tot_targets += T
        est = np.zeros((a.outer, len(POLICIES), 2, a.rounds))
        for b in range(a.outer):
            boot = rng.integers(0, n, n)                      # resample the recorded pairs
            seq = boot[rng.integers(0, n, (a.inner, a.rounds))]
            est[b] = run_policies(P, seq, a.rounds).mean(2)   # expected detected targets
        point_seq = rng.integers(0, n, (a.inner * 10, a.rounds))
        point = run_policies(P, point_seq, a.rounds).mean(2)
        summary["modules"][s] = {"pairs": int(n), "targets": int(T)}
        tot = est if tot is None else tot + est
        for key, e, p, TT in [(s, est, point, T)]:
            summary["modules"][key]["results"] = describe(e, p, TT, budgets)
    summary["combined"] = describe(tot, None, tot_targets, budgets)
    a.out.write_text(json.dumps(summary, indent=2) + "\n")
    for k, v in list(summary["modules"].items()) + [("combined", {"results": summary["combined"]})]:
        print("==", k)
        for proto in ("KR", "NR"):
            for b in budgets:
                r = v["results"][proto][str(b)]
                print(f"  {proto} r={b:2d} " + "  ".join(f"{p}={r['pct'][p]:.2f}" for p in POLICIES)
                      + "   " + "  ".join(f"{d}={r['diff'][d]['est']:+.2f}[{r['diff'][d]['lo']:+.2f},{r['diff'][d]['hi']:+.2f}]" for d in r['diff']))


def describe(est, point, T, budgets):
    res = {}
    for pr, proto in enumerate(("KR", "NR")):
        res[proto] = {}
        for b in budgets:
            pct = {p: float(100 * (point if point is not None else est.mean(0))[i, pr, b - 1] / T) for i, p in enumerate(POLICIES)}
            diff = {}
            for name, i, j in [("PAIR-IID", 1, 0), ("GATE-IID", 2, 0), ("PAIR-GATE", 1, 2), ("STRICT-IID", 3, 0)]:
                d = 100 * (est[:, i, pr, b - 1] - est[:, j, pr, b - 1]) / T
                diff[name] = {"est": float(d.mean()), "lo": float(np.percentile(d, 2.5)), "hi": float(np.percentile(d, 97.5))}
            res[proto][str(b)] = {"pct": pct, "diff": diff}
    return res


if __name__ == "__main__":
    main()
