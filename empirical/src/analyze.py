"""Aggregate per-target and suite-level results into numbers, LaTeX tables
and figures used in the paper.

Inputs : results/pertest_<SEM>.csv, results/suite_<SEM>.json
Outputs: results/summary_<SEM>.json, ../../paper/generated/*.tex,
         ../../paper/figures/*.pdf
"""
from __future__ import annotations

import csv
import json
import sys

import numpy as np

from common import ROOT

OUT = ROOT / "empirical" / "results"
GEN = ROOT / "paper" / "generated"
FIG = ROOT / "paper" / "figures"
BUDGETS = (2, 4, 10, 20, 40)
Z = 1.959964
BOOT = 2000


def load_pertest(sem):
    rows = list(csv.DictReader(open(OUT / f"pertest_{sem}.csv")))
    for r in rows:
        r["f"], r["B"] = float(r["f_float"]), float(r["B_float"])
    return rows


def bootstrap_fB(rows, rng):
    """Parametric bootstrap replicates of (f, B) for Monte Carlo targets."""
    f = np.array([r["f"] for r in rows]); B = np.array([r["B"] for r in rows])
    F = np.repeat(f[None], BOOT, 0); BB = np.repeat(B[None], BOOT, 0)
    for j, r in enumerate(rows):
        if r["method"] != "monte_carlo":
            continue
        cells = np.array([int(r[k]) for k in ("n11", "n10", "n01", "n00")])
        N = cells.sum()
        draw = rng.multinomial(N, cells / N, size=BOOT)
        F[:, j] = (2 * draw[:, 0] + draw[:, 1] + draw[:, 2]) / (2 * N)
        BB[:, j] = draw[:, 0] / N
    return F, BB


def D(f, B, r, proto, pol):
    m, e = divmod(r, 2)
    q = 1 - 2 * f + B
    if proto == "KR":
        return 1 - q ** m * (1 - f) ** e if pol == "PAIR" else 1 - (1 - f) ** r
    if pol == "PAIR":
        return 1 - q ** m * (1 - f) ** e - B ** m * f ** e
    return 1 - (1 - f) ** r - f ** r


def ET(f, B, proto, pol):
    """Expected runs until discovery (first failure, or both outcomes)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        t1_pair, t1_iid = (2 - f) / (2 * f - B), 1 / f
        if proto == "KR":
            return t1_pair if pol == "PAIR" else t1_iid
        q = 1 - 2 * f + B
        t0_pair, t0_iid = (2 - (1 - f)) / (2 * (1 - f) - q), 1 / (1 - f)
        return (t1_pair + t0_pair - 1) if pol == "PAIR" else (t1_iid + t0_iid - 1)


def ci(samples):
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return float(lo), float(hi)


def pertest_summary(rows, rng):
    n = len(rows)
    f = np.array([r["f"] for r in rows]); B = np.array([r["B"] for r in rows])
    Fb, Bb = bootstrap_fB(rows, rng)
    exact = np.array([r["method"] == "exact" for r in rows])
    d = f ** 2 - B
    mc = ~exact
    d_boot = Fb ** 2 - Bb
    d_lo = np.percentile(d_boot, 2.5, axis=0); d_hi = np.percentile(d_boot, 97.5, axis=0)
    s = dict(targets=n, victims=sum(r["kind"] == "victim" for r in rows),
             brittles=sum(r["kind"] == "brittle" for r in rows),
             exact=int(exact.sum()), monte_carlo=int(mc.sum()),
             exact_d_min=float(d[exact].min()),
             exact_zero_gap=int(np.sum(exact & (np.abs(d) < 1e-15))),
             B_zero=int(np.sum(B == 0)),
             mc_positive_cov_certified=int(np.sum(mc & (d_hi < 0))),
             mc_negative_cov_certified=int(np.sum(mc & (d_lo > 0))),
             mc_undetermined=int(np.sum(mc & (d_lo <= 0) & (d_hi >= 0))),
             f_mean=float(f.mean()), f_median=float(np.median(f)), f_min=float(f.min()),
             f_lt_0_1=int(np.sum(f < 0.1)),
             consistent_original=sum(r["original_outcome"] == "pass" for r in rows),
             multi_polluter_specific_cleaners=int(np.sum(mc)))
    for proto in ("KR", "NR"):
        sav = ET(f, B, proto, "IID") - ET(f, B, proto, "PAIR")
        savb = ET(Fb, Bb, proto, "IID") - ET(Fb, Bb, proto, "PAIR")
        rel = sav / ET(f, B, proto, "IID")
        limit = 0.5 if proto == "KR" else 1.0
        s[f"{proto}_saving_runs"] = dict(
            mean=float(sav.mean()), ci=ci(savb.mean(1)), median=float(np.median(sav)),
            max=float(sav.max()), min=float(sav.min()), limit=limit,
            at_limit=int(np.sum(np.abs(sav - limit) < 1e-9)),
            mean_relative=float(rel.mean()), median_relative=float(np.median(rel)),
            expected_runs_iid_mean=float(ET(f, B, proto, "IID").mean()),
            expected_runs_pair_mean=float(ET(f, B, proto, "PAIR").mean()))
        g = {}
        for r in BUDGETS:
            gain = D(f, B, r, proto, "PAIR") - D(f, B, r, proto, "IID")
            gainb = D(Fb, Bb, r, proto, "PAIR") - D(Fb, Bb, r, proto, "IID")
            iid_miss = 1 - D(f, B, r, proto, "IID")
            lo = f < 0.1
            g[r] = dict(iid=float(D(f, B, r, proto, "IID").mean()),
                        pair=float(D(f, B, r, proto, "PAIR").mean()),
                        gain_pp=float(100 * gain.mean()), gain_ci_pp=[100 * x for x in ci(gainb.mean(1))],
                        max_gain_pp=float(100 * gain.max()),
                        share_iid_miss_f_lt_0_1=float(iid_miss[lo].sum() / max(iid_miss.sum(), 1e-300)))
            if proto == "KR":
                m = r // 2
                g[r]["bound_pp"] = float(100 * np.mean(m * f ** 2 * (1 - f) ** (r - 2)))
        s[f"{proto}_gain"] = g
    return s, f, B


def suite_summary(sem, total_targets):
    data = json.load(open(OUT / f"suite_{sem}.json"))
    mods = data["modules"]
    out = dict(runs_per_module=data["runs_per_module"], modules=len(mods))
    for proto in ("NR", "KR"):
        P = {}
        for sub, denom in (("all", total_targets),
                           ("consistent", sum(m["consistent_targets"] for m in mods))):
            res = {}
            for key in ("IID", "PAIR", "GATE", "STRICT", "PAIR-IID", "GATE-IID", "STRICT-IID", "PAIR-GATE"):
                mean = sum(np.array(m["stats"][proto][sub][key]["mean"]) for m in mods)
                se = np.sqrt(sum(np.array(m["stats"][proto][sub][key]["se"]) ** 2 for m in mods))
                res[key] = dict(pct=(100 * mean / denom).tolist(), ci_pp=(100 * Z * se / denom).tolist())
            P[sub] = res
            P[sub]["denominator"] = denom
        # module-weighted: average over modules of within-module detected fraction
        mw = {}
        for key in ("IID", "PAIR", "GATE", "STRICT"):
            fr = [np.array(m["stats"][proto]["all"][key]["mean"]) / m["targets"] for m in mods]
            mw[key] = (100 * np.mean(fr, axis=0)).tolist()
        P["module_weighted"] = mw
        anyp = {k: (100 * np.mean([np.array(m["stats"][proto]["any"][k]["mean"]) for m in mods], axis=0)).tolist()
                for k in ("IID", "PAIR", "GATE", "STRICT")}
        P["module_any_detected"] = anyp
        # per-module significance of contrasts (Bonferroni over 47 modules)
        sig = {}
        zcrit = 3.07  # two-sided 0.05 / 47
        for key in ("PAIR-IID", "GATE-IID", "STRICT-IID", "PAIR-GATE"):
            sig[key] = {}
            for r in BUDGETS:
                pos = neg = 0
                for m in mods:
                    mu = m["stats"][proto]["all"][key]["mean"][r - 1]
                    se = m["stats"][proto]["all"][key]["se"][r - 1]
                    if se > 0 and mu / se > zcrit: pos += 1
                    if se > 0 and mu / se < -zcrit: neg += 1
                sig[key][r] = dict(better=pos, worse=neg)
        P["module_significance_bonferroni"] = sig
        out[proto] = P
    return out, mods


def fmt(x, nd=1):
    return f"{x:.{nd}f}"


def write_tables(sem, pt, st):
    GEN.mkdir(parents=True, exist_ok=True)
    b = BUDGETS
    # Table: suite-level detection
    lines = []
    for proto, label in (("NR", "No reference (ISSTA'23 definition)"), ("KR", "Known passing reference")):
        lines.append(r"\multicolumn{6}{l}{\emph{" + label + r"}}\\")
        for pol in ("IID", "PAIR", "GATE", "STRICT"):
            cells = [f"{st[proto]['all'][pol]['pct'][r-1]:.1f}" for r in b]
            lines.append(pol.replace("GATE", "Gate (iDFlakies)").replace("STRICT", "Strict gate")
                         .replace("PAIR", "Pair").replace("IID", "IID") + " & " + " & ".join(cells) + r"\\")
        for key, lab in (("PAIR-IID", r"$\Delta$ Pair$-$IID"), ("GATE-IID", r"$\Delta$ Gate$-$IID"),
                         ("PAIR-GATE", r"$\Delta$ Pair$-$Gate")):
            cells = [f"{st[proto]['all'][key]['pct'][r-1]:+.2f}{{\\scriptsize$\\pm${st[proto]['all'][key]['ci_pp'][r-1]:.2f}}}"
                     for r in b]
            lines.append(lab + " & " + " & ".join(cells) + r"\\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"
    (GEN / f"table_suite_{sem}.tex").write_text("\n".join(lines) + "\n")
    # Table: per-target gains (analytic)
    lines = []
    for proto in ("KR", "NR"):
        g = pt[f"{proto}_gain"]
        lab = "KR" if proto == "KR" else "NR"
        lines.append(f"{lab} IID & " + " & ".join(fmt(100 * g[r]['iid']) for r in b) + r"\\")
        lines.append(f"{lab} Pair & " + " & ".join(fmt(100 * g[r]['pair']) for r in b) + r"\\")
        lines.append(f"{lab} mean gain (pp) & " + " & ".join(f"{g[r]['gain_pp']:.2f}" for r in b) + r"\\")
        if proto == "KR":
            lines.append(r"KR bound $\overline{m f^2(1-f)^{r-2}}$ (pp) & " +
                         " & ".join(f"{g[r]['bound_pp']:.2f}" for r in b) + r"\\")
        lines.append(f"{lab} max gain, one test (pp) & " + " & ".join(f"{g[r]['max_gain_pp']:.2f}" for r in b) + r"\\")
        lines.append(r"\midrule")
    lines[-1] = r"\bottomrule"
    (GEN / f"table_pertest_{sem}.tex").write_text("\n".join(lines) + "\n")


def write_macros(sem, pt, st):
    """LaTeX macros so that every number in the text is generated."""
    M = {}
    M["NTargets"] = pt["targets"]; M["NVictims"] = pt["victims"]; M["NBrittles"] = pt["brittles"]
    M["NExact"] = pt["exact"]; M["NMC"] = pt["monte_carlo"]; M["NBzero"] = pt["B_zero"]
    M["NZeroGap"] = pt["exact_zero_gap"]; M["NMCneg"] = pt["mc_negative_cov_certified"]
    M["NMCpos"] = pt["mc_positive_cov_certified"]; M["NMCund"] = pt["mc_undetermined"]
    M["NConsistent"] = pt["consistent_original"]; M["NInconsistent"] = pt["targets"] - pt["consistent_original"]
    M["NflowTen"] = pt["f_lt_0_1"]
    M["FMean"] = f"{100 * pt['f_mean']:.1f}"; M["FMedian"] = f"{100 * pt['f_median']:.1f}"
    M["FMin"] = f"{100 * pt['f_min']:.1f}"
    for proto in ("KR", "NR"):
        sv = pt[f"{proto}_saving_runs"]
        M[f"{proto}SaveMean"] = f"{sv['mean']:.2f}"; M[f"{proto}SaveMax"] = f"{sv['max']:.2f}"
        M[f"{proto}SaveMedian"] = f"{sv['median']:.2f}"
        M[f"{proto}SaveCIlo"] = f"{sv['ci'][0]:.3f}"; M[f"{proto}SaveCIhi"] = f"{sv['ci'][1]:.3f}"
        M[f"{proto}SaveAtLimit"] = sv["at_limit"]
        M[f"{proto}SaveRelMean"] = f"{100 * sv['mean_relative']:.1f}"
        M[f"{proto}SaveRelMedian"] = f"{100 * sv['median_relative']:.1f}"
        M[f"{proto}RunsIID"] = f"{sv['expected_runs_iid_mean']:.2f}"
        M[f"{proto}RunsPair"] = f"{sv['expected_runs_pair_mean']:.2f}"
        for r in BUDGETS:
            g = pt[f"{proto}_gain"][r]
            M[f"{proto}Gain{r}"] = f"{g['gain_pp']:.2f}"; M[f"{proto}MaxGain{r}"] = f"{g['max_gain_pp']:.2f}"
            M[f"{proto}ShareLow{r}"] = f"{100 * g['share_iid_miss_f_lt_0_1']:.0f}"
            s = st[proto]["all"]
            for key in ("IID", "PAIR", "GATE", "STRICT"):
                M[f"{proto}{key.title()}{r}"] = f"{s[key]['pct'][r-1]:.1f}"
            for key in ("PAIR-IID", "GATE-IID", "PAIR-GATE", "STRICT-IID"):
                nm = key.replace("-", "Minus").replace("PAIR", "Pair").replace("GATE", "Gate").replace("IID", "Iid").replace("STRICT", "Strict")
                M[f"{proto}{nm}{r}"] = f"{s[key]['pct'][r-1]:+.2f}"
                M[f"{proto}{nm}CI{r}"] = f"{s[key]['ci_pp'][r-1]:.2f}"
            sig = st[proto]["module_significance_bonferroni"]
            M[f"{proto}GateWorse{r}"] = sig["GATE-IID"][r]["worse"]
            M[f"{proto}GateBetter{r}"] = sig["GATE-IID"][r]["better"]
            M[f"{proto}PairWorseGate{r}"] = sig["PAIR-GATE"][r]["worse"]
            M[f"{proto}PairBetterGate{r}"] = sig["PAIR-GATE"][r]["better"]
            M[f"{proto}PairWorseIid{r}"] = sig["PAIR-IID"][r]["worse"]
            c = st[proto]["consistent"]
            M[f"{proto}ConsPairMinusIid{r}"] = f"{c['PAIR-IID']['pct'][r-1]:+.2f}"
            M[f"{proto}ConsGateMinusIid{r}"] = f"{c['GATE-IID']['pct'][r-1]:+.2f}"
            mw = st[proto]["module_weighted"]
            M[f"{proto}MWPairMinusIid{r}"] = f"{mw['PAIR'][r-1] - mw['IID'][r-1]:+.2f}"
            M[f"{proto}MWGateMinusIid{r}"] = f"{mw['GATE'][r-1] - mw['IID'][r-1]:+.2f}"
    M["Runs"] = f"{st['runs_per_module']:,}".replace(",", "{,}")
    suffix = "" if sem == "S1" else "Alt"
    words = {"40": "Forty", "20": "Twenty", "10": "Ten", "4": "Four", "2": "Two"}
    def clean(k):
        import re
        return re.sub(r"\d+", lambda mt: words[mt.group(0)], k)
    M = {clean(k): v for k, v in M.items()}
    lines = [f"\\newcommand{{\\{k}{suffix}}}{{{v}}}" for k, v in M.items()]
    (GEN / f"macros_{sem}.tex").write_text("\n".join(lines) + "\n")


def figures(sem, f, B, st):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 8, "pdf.fonttype": 42, "ps.fonttype": 42,
                         "font.family": "serif", "axes.linewidth": 0.6})
    FIG.mkdir(parents=True, exist_ok=True)
    # Figure: per-target benefit vs flake rate against the proven limits.
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.3))
    sav = ET(f, B, "KR", "IID") - ET(f, B, "KR", "PAIR")
    xs = np.logspace(np.log10(0.005), np.log10(0.999), 300)
    ax[0].scatter(f, sav, s=7, c="#1f77b4", alpha=0.6, linewidths=0)
    ax[0].axhline(0.5, color="#d62728", lw=0.9, ls="--")
    ax[0].text(0.012, 0.53, "Half-run limit: saving $\\leq 1/2$ run", color="#d62728", fontsize=7)
    ax[0].set_xscale("log"); ax[0].set_ylim(-0.02, 0.62); ax[0].set_xlim(0.009, 1.1)
    ax[0].set_xlabel("flake rate $f$ (log scale)"); ax[0].set_ylabel("runs saved to first failure")
    ax[0].set_title("(a) expected runs saved per target (KR)", fontsize=8)
    r, m = 10, 5
    gain = D(f, B, r, "KR", "PAIR") - D(f, B, r, "KR", "IID")
    ax[1].scatter(f, 100 * gain, s=7, c="#1f77b4", alpha=0.6, linewidths=0)
    ax[1].plot(xs, 100 * m * xs ** 2 * (1 - xs) ** (r - 2), color="#d62728", lw=0.9, ls="--",
               label="bound $m f^2(1-f)^{r-2}$")
    ax[1].set_xscale("log"); ax[1].set_xlabel("flake rate $f$ (log scale)")
    ax[1].set_ylabel("discovery gain (pp)"); ax[1].legend(frameon=False, fontsize=7, loc="upper left")
    ax[1].set_title(f"(b) gain in discovery probability, $r={r}$ (KR)", fontsize=8)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=0.3)
    fig.savefig(FIG / f"pertest_{sem}.pdf")
    plt.close(fig)
    # Figure: suite-level contrasts with 95% CIs.
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.2), sharey=False)
    R = np.arange(1, len(st["NR"]["all"]["IID"]["pct"]) + 1)
    styles = {"PAIR-IID": ("Pair $-$ IID", "#2ca02c"), "GATE-IID": ("Gate (iDFlakies) $-$ IID", "#ff7f0e"),
              "STRICT-IID": ("Strict gate $-$ IID", "#9467bd")}
    for a, proto, title in ((ax[0], "NR", "(a) no reference (ISSTA'23 definition)"),
                            (ax[1], "KR", "(b) known passing reference")):
        for key, (lab, col) in styles.items():
            mu = np.array(st[proto]["all"][key]["pct"]); c = np.array(st[proto]["all"][key]["ci_pp"])
            a.plot(R, mu, color=col, lw=1.0, label=lab)
            a.fill_between(R, mu - c, mu + c, color=col, alpha=0.2, lw=0)
        a.axhline(0, color="k", lw=0.5)
        a.axvline(20, color="0.5", lw=0.6, ls=":")
        a.text(19, a.get_ylim()[1] * 0.95, "iDFlakies\ndefault ", fontsize=6.5, color="0.35", va="top", ha="right")
        a.set_xscale("log"); a.set_xticks([1, 2, 4, 10, 20, 40]); a.set_xticklabels(["1", "2", "4", "10", "20", "40"])
        a.set_xlabel("budget $r$ (complete suite runs)"); a.set_ylabel("difference (pp of 289 OD tests)")
        a.set_title(title, fontsize=8); a.spines[["top", "right"]].set_visible(False)
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], color=col, lw=1.2, label=lab) for lab, col in styles.values()]
    ax[0].legend(handles=handles, frameon=False, fontsize=7, loc="center right")
    fig.tight_layout(pad=0.3)
    fig.savefig(FIG / f"suite_{sem}.pdf")
    plt.close(fig)


def main(sem="S1"):
    rng = np.random.default_rng(99)
    rows = load_pertest(sem)
    pt, f, B = pertest_summary(rows, rng)
    st, mods = suite_summary(sem, len(rows))
    summary = dict(semantics=sem, pertest=pt, suite=st)
    (OUT / f"summary_{sem}.json").write_text(json.dumps(summary, indent=2))
    write_tables(sem, pt, st)
    write_macros(sem, pt, st)
    if sem == "S1":
        figures(sem, f, B, st)
    print(json.dumps(pt, indent=1)[:3000])



# --------------------------------------------------------------------------
# Additional views used in the paper (appended; see main()).
# --------------------------------------------------------------------------
def extra_views(sem="S1"):
    rows = load_pertest(sem)
    f = np.array([r["f"] for r in rows]); B = np.array([r["B"] for r in rows])
    groups = {
        "Brittles": [r["kind"] == "brittle" for r in rows],
        "Victims, one polluter": [r["kind"] == "victim" and int(r["n_polluters"]) == 1 for r in rows],
        "Victims, $\\ge$2 polluters, common cleaners": [r["kind"] == "victim" and int(r["n_polluters"]) > 1
                                                          and r["method"] == "exact" for r in rows],
        "Victims, polluter-specific cleaners": [r["method"] == "monte_carlo" for r in rows],
    }
    miss20 = (1 - f) ** 20
    lines, M = [], {}
    for name, mask in groups.items():
        m = np.array(mask)
        sav = ET(f[m], B[m], "KR", "IID") - ET(f[m], B[m], "KR", "PAIR")
        g10 = D(f[m], B[m], 10, "KR", "PAIR") - D(f[m], B[m], 10, "KR", "IID")
        lines.append(f"{name} & {m.sum()} & {100 * f[m].mean():.1f} & {100 * np.mean(B[m] == 0):.0f} & "
                     f"{sav.mean():.2f} & {100 * g10.mean():.2f} & {100 * miss20[m].sum() / miss20.sum():.0f}\\\\")
    GEN.mkdir(parents=True, exist_ok=True)
    (GEN / f"table_breakdown_{sem}.tex").write_text("\n".join(lines) + "\n\\bottomrule\n")
    # runs needed to reach a target detection level (per-test closed forms)
    for proto in ("KR", "NR"):
        for level in (80, 90, 95):
            for pol in ("IID", "PAIR"):
                r = 1
                while np.mean(D(f, B, r, proto, pol)) < level / 100 and r < 2000:
                    r += 1
                key = f"Runs{proto}{pol.title()}{ {80: 'Eighty', 90: 'Ninety', 95: 'NinetyFive'}[level] }".replace(" ", "")
                M[key] = r
    # per-module table for modules with >= 5 OD tests (suite simulation)
    suite = json.load(open(OUT / f"suite_{sem}.json"))
    lines = []
    for m in sorted(suite["modules"], key=lambda x: -x["targets"]):
        if m["targets"] < 5:
            continue
        cells = []
        for proto in ("KR", "NR"):
            st = m["stats"][proto]["all"]
            for pol in ("IID", "PAIR", "GATE"):
                cells.append(f"{100 * st[pol]['mean'][9] / m['targets']:.1f}")
        nm = m["module"].replace("_", "\\_")
        if len(nm) > 24:
            nm = nm[:22] + "\\ldots"
        lines.append(f"{nm} & {m['targets']} & " + " & ".join(cells) + "\\\\")
    (GEN / f"table_modules_{sem}.tex").write_text("\n".join(lines) + "\n\\bottomrule\n")
    M["NBigModules"] = len(lines)
    M["NBigModuleTests"] = sum(m["targets"] for m in suite["modules"] if m["targets"] >= 5)
    txt = "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items())
    (GEN / f"macros_extra_{sem}.tex").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    sem = sys.argv[1] if len(sys.argv) > 1 else "S1"
    main(sem)
    if sem == "S1":
        extra_views(sem)


def limits_map(sem="S1"):
    """Expected runs to first failure (KR) under the limits of Section IV-B."""
    rows = load_pertest(sem)
    f = np.array([r["f"] for r in rows]); B = np.array([r["B"] for r in rows])
    N = np.floor(1 / f)
    vals = {
        "Iid": 1 / f,
        "Pair": (2 - f) / (2 * f - B),
        # Theorem (block limit): 1/f-(k-1)/2 when kf <= 1, else the uniform-marginal limit
        "Blockfour": np.where(4 * f <= 1, 1 / f - 1.5, (N + 1) * (1 - N * f / 2)),
        "Oracle": (1 + f - B) / (2 * f - B),
        "Uniform": (N + 1) * (1 - N * f / 2),
    }
    rare = f < 0.1
    M = {}
    for k, x in vals.items():
        M[f"ET{k}"] = f"{x.mean():.2f}"
        M[f"ET{k}Rare"] = f"{x[rare].mean():.2f}"
    M["HeadroomShare"] = f"{100 * (vals['Iid'] - vals['Pair']).sum() / (vals['Iid'] - vals['Uniform']).sum():.1f}"
    M["HeadroomUniformPct"] = f"{100 * (1 - vals['Uniform'].mean() / vals['Iid'].mean()):.0f}"
    M.update(rare_tail_concentration(rows, f, rare))
    txt = "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items())
    (GEN / f"macros_limits_{sem}.tex").write_text(txt + "\n")
    print(txt)


def rare_tail_concentration(rows, f, rare):
    """Numbers behind the RQ1 sentence on how concentrated the rare tail is (KR protocol).

    The two modules with the most rare targets are found from the data.  The structural
    claims that the text makes about them are asserted, so the sentence cannot go stale.
    """
    import collections
    from common import class_of, load_modules
    mod = np.array([r["module"] for r in rows])
    (m1, _), (m2, _) = collections.Counter(mod[rare]).most_common(2)
    assert {m1, m2} == {"dubbo-config-api", "marine-api"}, (m1, m2)
    by_name = collections.defaultdict(list)
    for m in load_modules():
        by_name[m.name].append(m)
    (dubbo,), (marine,) = by_name["dubbo-config-api"], by_name["marine-api"]
    assert all(t.kind == "brittle" for t in dubbo.targets)          # "brittles of one test class"
    assert len({class_of(t.name) for t in dubbo.targets}) == 1
    assert all(t.kind == "victim" for t in marine.targets)          # "victims of one polluter"
    assert len({tuple(sorted(t.polluters)) for t in marine.targets}) == 1
    two = np.isin(mod, [m1, m2])
    M = {
        "NRareDubbo": int((rare & (mod == "dubbo-config-api")).sum()),
        "NRareMarine": int((rare & (mod == "marine-api")).sum()),
        "NRareTwoMods": int((rare & two).sum()),
        "NRareOther": int((rare & ~two).sum()),
        "NOtherTargets": int((~two).sum()),
    }
    for r, word in ((10, "Ten"), (20, "Twenty")):
        miss = (1 - f) ** r                                          # KR miss probability of IID
        M[f"ShareMissTwo{word}"] = f"{100 * miss[two].sum() / miss.sum():.0f}"
        M[f"KRShareLow{word}Excl"] = f"{100 * miss[rare & ~two].sum() / miss[~two].sum():.0f}"
    return M


if __name__ == "__main__" and (len(sys.argv) < 2 or sys.argv[1] == "S1"):
    limits_map("S1")


def reference_sensitivity_table():
    """Score original joint simulations on all/reference-consistent targets.

    This does NOT rerun a gate with inconsistent targets removed from its state.
    CIs describe Monte Carlo uncertainty, not model error or generalisation.
    """
    lines = []
    for sem in ("S1", "S2"):
        rows = load_pertest(sem)
        stats, _ = suite_summary(sem, len(rows))
        for sub, label in (("all", "All"), ("consistent", "Consistent")):
            n = stats["KR"][sub]["denominator"]
            cells = []
            for contrast in ("PAIR-IID", "GATE-IID"):
                for proto in ("KR", "NR"):
                    x = stats[proto][sub][contrast]
                    cells.append(f"${x['pct'][19]:.2f}\\pm{x['ci_pp'][19]:.2f}$")
            lines.append(f"{sem}, {label} & {n} & " + " & ".join(cells) + " " + chr(92) * 2)
    (GEN / "table_reference_sensitivity.tex").write_text("\n".join(lines) + "\n")


if __name__ == "__main__" and (len(sys.argv) < 2 or sys.argv[1] == "S1"):
    reference_sensitivity_table()
