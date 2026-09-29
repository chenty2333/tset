# Provenance of the ISSTA'23 data

Source: public artifact of C. Li, M. M. Khosravi, W. Lam, A. Shi,
"Systematically Producing Test Orders to Detect Order-Dependent Flaky Tests",
ISSTA 2023, https://sites.google.com/view/systematically-detecting-od

| File(s) | Archive on the artifact page | Google Drive id |
|---|---|---|
| `all-polluter-cleaner-info-combined.csv`, `subjects.csv`, `original-orders/`, `README.md` | `data.tar.gz` ("Inputs to our techniques") | `1UYiJ2Ki2-oppV9VvRrmnOPEm5O6I2IL_` |
| `reference_simulator/simulator.py`, `reference_simulator/README.md` | `stats.tar.gz` ("Scripts to reproduce results") | `1y-x8db3rqW0HodOx5BAig8jNa5Tq42I9` |

Files are copied unmodified (macOS `._*` resource forks removed). `SHA256SUMS`
lists their hashes.  `reference_simulator/simulator.py` is used only to
cross-validate our outcome evaluator (`empirical/src/validate.py`); it is run
unmodified in a temporary directory that mimics its expected layout.

The files remain the work of their original authors; see the artifact page for
terms of use. `fetch.sh` restores them from the original source.
