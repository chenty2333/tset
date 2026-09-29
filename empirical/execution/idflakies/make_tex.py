"""Writes paper/generated/{macros,table}_idflakies.tex from results/power.json."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
GEN = HERE.parents[2] / 'paper' / 'generated'
p = json.loads((HERE / 'results/power.json').read_text())
fmt = lambda v: format(v, ',').replace(',', '{,}')
S = lambda m, v, k: p[m]['structure'][v][k]
mods, vars_ = ('aismessages', 'http-request'), ('gate', 'iid', 'pair')
tot = lambda k: sum(S(m, v, k) for m in mods for v in vars_)
mac = {
    'IdfRunsAis': fmt(p['aismessages']['seeds_used']), 'IdfRunsHttp': fmt(p['http-request']['seeds_used']),
    'IdfDetectorRuns': fmt(sum(p[m]['seeds_used'] * 3 for m in mods)),
    'IdfOrders': fmt(tot('rounds')), 'IdfNonContig': fmt(tot('not_class_contiguous') + tot('not_full_permutation')),
    'IdfComparisons': fmt(tot('target_comparisons_S1')), 'IdfMismatches': fmt(tot('mismatches_S1')),
    'IdfGateTransitions': fmt(sum(S(m, 'gate', 'transitions') for m in mods)),
    'IdfGateRuleMatches': fmt(sum(S(m, 'gate', 'gate_rule_matches') for m in mods)),
}
(GEN / 'macros_idflakies.tex').write_text(''.join(f'\\newcommand{{\\{k}}}{{{v}}}\n' for k, v in mac.items()))
rows = []
for m, short in (('aismessages', 'aismessages'), ('http-request', 'http-request')):
    for key, lab in (('gate-iid', r'\GATEp$-$\IIDp'), ('pair-gate', r'\PAIRp$-$\GATEp')):
        cells = []
        for r in (2, 4, 10, 20):
            c = p[m]['contrasts'][f'KR:{key}:r{r}']
            cells.append(f"${c['mean_pp']:+.1f}$\\,{{\\scriptsize[{c['lo']:+.1f},{c['hi']:+.1f}]}}")
        rows.append(f"{short if key == 'gate-iid' else ''} & {lab} & " + ' & '.join(cells) + r'\\')
(GEN / 'table_idflakies.tex').write_text('\n'.join(rows) + '\n')
print((GEN / 'macros_idflakies.tex').read_text()); print((GEN / 'table_idflakies.tex').read_text())
