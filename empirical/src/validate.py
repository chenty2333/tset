"""Internal validity checks.

(1) Suite simulation vs closed-form per-target predictions: for IID and PAIR
    the expected number of detected targets equals the sum over targets of
    D(f, B), independent of cross-target dependence (linearity).  Compare
    simulated means with these predictions (z-scores).
(2) Our vectorised evaluator vs the unmodified ISSTA'23 reference simulator
    (data/issta23/reference_simulator/simulator.py) on random orders.
Output: results/validation_<SEM>.json
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

from common import DATA, ROOT, Evaluator, Sampler, load_modules

OUT = ROOT / "empirical" / "results"


def D_known(f, B, r):
    m, e = divmod(r, 2)
    return 1 - (1 - 2 * f + B) ** m * (1 - f) ** e, 1 - (1 - f) ** r


def D_none(f, B, r):
    m, e = divmod(r, 2)
    q = 1 - 2 * f + B
    return (1 - q ** m * (1 - f) ** e - B ** m * f ** e,
            1 - (1 - f) ** r - f ** r)


def check_suite(sem):
    per = {(r["slug"], r["path"], r["test"]): r for r in csv.DictReader(open(OUT / f"pertest_{sem}.csv"))}
    suite = json.load(open(OUT / f"suite_{sem}.json"))
    zs = []
    for mod in suite["modules"]:
        tests = [r for (sl, p, _), r in per.items() if (sl, p) == (mod["slug"], mod["path"])]
        for proto, fn in (("KR", D_known), ("NR", D_none)):
            st = mod["stats"][proto]["all"]
            for r in range(1, suite["budget_max"] + 1):
                d = [fn(float(x["f_float"]), float(x["B_float"]), r) for x in tests]
                for pol, k in (("PAIR", 0), ("IID", 1)):
                    pred = sum(x[k] for x in d)
                    # The sample SE underestimates the spread when misses are
                    # rare, so floor it with the largest possible SD of a sum
                    # of Bernoulli indicators (perfect positive correlation).
                    sd_max = sum(np.sqrt(max(x[k] * (1 - x[k]), 0.0)) for x in d)
                    mean, se = st[pol]["mean"][r - 1], st[pol]["se"][r - 1]
                    se = max(se, sd_max / np.sqrt(suite["runs_per_module"]))
                    if se > 0:
                        zs.append((mean - pred) / se)
                    elif abs(mean - pred) > 1e-9:
                        zs.append(float("inf"))
    zs = np.array(zs)
    return dict(comparisons=int(len(zs)), max_abs_z=float(np.max(np.abs(zs))),
                share_abs_z_gt_3=float(np.mean(np.abs(zs) > 3)),
                note="z uses max(sample SE, conservative Bernoulli-sum SE)")


def check_reference_simulator(sem, orders_per_module=150, seed=7):
    """Run the unmodified ISSTA'23 simulator on our sampled orders and
    compare the reported first passing / first failing order index."""
    if sem != "S1":
        return None
    rng = np.random.default_rng(seed)
    tmp = tempfile.mkdtemp()
    sim_dir = os.path.join(tmp, "stats", "simulation")
    os.makedirs(sim_dir)
    shutil.copy(DATA / "reference_simulator" / "simulator.py", sim_dir)
    shutil.copytree(DATA / "original-orders", os.path.join(tmp, "data", "original-orders"))
    ours = {}
    for mod in load_modules():
        s = Sampler(mod.relevant_tests())
        ev = Evaluator(mod.targets, s, sem)
        pos = s.positions(rng, orders_per_module)
        fails = ev.fails(pos)
        slug = mod.slug[19:].replace("/", "_")
        m = mod.path.replace("./", "").replace("/", "_")
        d = os.path.join(tmp, "orders", "intra-orders", f"{slug}-{m}-{mod.sha[:7]}-intra-orders")
        os.makedirs(d)
        for i in range(orders_per_module):
            order = [None] * s.n
            for tname, j in s.index.items():
                order[pos[i, j]] = tname
            with open(os.path.join(d, f"order-{i}"), "w") as fh:
                fh.write("\n".join(order) + "\n")
        for j, t in enumerate(mod.targets):
            f_idx = np.flatnonzero(fails[:, j]); p_idx = np.flatnonzero(~fails[:, j])
            ours[t.name] = (len(p_idx) > 0, int(p_idx[0]) if len(p_idx) else 0,
                            len(f_idx) > 0, int(f_idx[0]) if len(f_idx) else 0)
    res = subprocess.run([sys.executable, os.path.join(sim_dir, "simulator.py"), str(DATA /
                          "all-polluter-cleaner-info-combined.csv"), "intra"],
                         capture_output=True, text=True, check=True)
    theirs = {}
    for line in res.stdout.strip().splitlines():
        parts = line.split(",")
        theirs[parts[3]] = (parts[4] == "True", int(parts[5]), parts[6] == "True", int(parts[7]))
    shutil.rmtree(tmp)
    agree = sum(ours[k] == theirs.get(k) for k in ours)
    return dict(orders_per_module=orders_per_module, targets=len(ours),
                targets_reported_by_reference=len(theirs), agreeing_targets=agree,
                disagreements=[k for k in ours if ours[k] != theirs.get(k)][:10])


if __name__ == "__main__":
    sem = sys.argv[1] if len(sys.argv) > 1 else "S1"
    out = dict(semantics=sem, suite_vs_closed_form=check_suite(sem),
               evaluator_vs_issta23_reference_simulator=check_reference_simulator(sem))
    (OUT / f"validation_{sem}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
