"""Writes paper/generated/macros_execution_all.tex: totals over all executed modules
(the first check in results/ and the rare-failure check in results_rare/)."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
first = json.loads((HERE / 'results/summary.json').read_text())
rare = json.loads((HERE / 'results_rare/summary.json').read_text())
rare = rare if isinstance(rare, list) else [rare]
targets = sum(m['targets'] for m in first) + sum(m['targets'] for m in rare)
comps = sum(m['S1']['target_outcome_comparisons'] for m in first) + sum(
    m['S1']['target_outcome_comparisons'] if 'S1' in m else m['comparisons'] for m in rare)
fmt = lambda v: format(v, ',').replace(',', '{,}')
out = HERE.parents[1] / 'paper/generated/macros_execution_all.tex'
out.write_text(f"\\newcommand{{\\ExecAllModules}}{{{len(first) + len(rare)}}}\n"
               f"\\newcommand{{\\ExecAllTargets}}{{{targets}}}\n"
               f"\\newcommand{{\\ExecAllComparisons}}{{{fmt(comps)}}}\n")
print(out.read_text())
