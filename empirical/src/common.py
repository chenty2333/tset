"""Shared dataset loading, order sampling and outcome evaluation.

Dataset: ISSTA'23 artifact (Li, Khosravi, Lam, Shi), 289 known OD tests in
47 Maven modules, with polluters / cleaners (victims) and state-setters
(brittles).  See ../../data/issta23/README.md for provenance.

Outcome semantics
  S1 (primary, identical to the ISSTA'23 reference simulator
      data/issta23/reference_simulator/simulator.py): a victim v fails in an
      order iff some polluter p runs before v and no cleaner of the pair
      (v, p) runs strictly between p and v.  Cleaner groups "a|b" are split
      into individual cleaners.  A brittle fails iff no state-setter runs
      before it.
  S2 (sensitivity): as S1, but a cleaner group cleans only if *all* of its
      members run strictly between p and v.

Order distribution: iDFlakies' default detector type "random"
(random-class-method): uniform class order, uniform method order within
each class, independently.  Only relevant tests are materialised; deleting
irrelevant tests keeps the induced order uniform on the class-contiguous
orders of the relevant tests (pruning lemma), so outcomes are unchanged.
"""
from __future__ import annotations

import collections
import csv
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "issta23"
CSV = DATA / "all-polluter-cleaner-info-combined.csv"


def class_of(test: str) -> str:
    """Same rule as iDFlakies TestShuffler.className."""
    return test[: test.rindex(".")]


@dataclass
class Target:
    name: str
    kind: str                                   # "victim" | "brittle"
    # victim: polluter -> list of cleaner groups (each a tuple of tests)
    polluters: dict = field(default_factory=dict)
    setters: tuple = ()                         # brittle only

    def cleaners(self, p: str, semantics: str) -> list[tuple[str, ...]]:
        groups = self.polluters[p]
        if semantics == "S1":                   # split groups (ISSTA'23)
            return sorted({(c,) for g in groups for c in g})
        return sorted(set(groups))

    def relevant(self) -> set[str]:
        rel = {self.name, *self.setters, *self.polluters}
        for groups in self.polluters.values():
            for g in groups:
                rel.update(g)
        return rel


@dataclass
class Module:
    slug: str
    sha: str
    path: str
    targets: list[Target]
    original: list[str]

    @property
    def name(self) -> str:
        repo = self.slug.rstrip("/").split("/")[-1]
        return repo if self.path in (".", "./") else self.path.lstrip("./").split("/")[-1]

    def relevant_tests(self) -> list[str]:
        rel: set[str] = set()
        for t in self.targets:
            rel |= t.relevant()
        return sorted(rel)


def order_file(slug: str, sha: str, path: str) -> Path:
    owner, repo = slug.rstrip("/").split("/")[-2:]
    m = path[2:] if path.startswith("./") else path
    m = m.replace("/", "_") if m not in (".", "") else "."
    return DATA / "original-orders" / f"{owner}_{repo}-{m}-{sha[:7]}-original_order"


def load_modules() -> list[Module]:
    victims = collections.defaultdict(lambda: collections.defaultdict(set))
    setters = collections.defaultdict(set)
    kinds, where = {}, {}
    for r in csv.DictReader(open(CSV, newline="")):
        key = (r["github_slug"], r["sha"], r["module"])
        name = r["victim/brittle"]
        kinds[(key, name)] = r["type_victim_or_brittle"].strip()
        where.setdefault(key, []).append(name)
        other, cl = r["polluter/state-setter"].strip(), r["potential_cleaner"].strip()
        if kinds[(key, name)] == "victim":
            victims[(key, name)][other]
            if cl:
                victims[(key, name)][other].add(tuple(x for x in cl.split("|") if x))
        else:
            setters[(key, name)].add(other)
    mods = []
    for key in sorted(where):
        names = list(dict.fromkeys(where[key]))
        targets = []
        for n in names:
            if kinds[(key, n)] == "victim":
                pc = {p: sorted(g) for p, g in victims[(key, n)].items()}
                targets.append(Target(n, "victim", polluters=pc))
            else:
                targets.append(Target(n, "brittle", setters=tuple(sorted(setters[(key, n)]))))
        original = [l.strip() for l in open(order_file(*key)) if l.strip()]
        mods.append(Module(*key, targets=targets, original=original))
    return mods


# --------------------------------------------------------------------------
# Order sampling (vectorised) and outcome evaluation
# --------------------------------------------------------------------------
class Sampler:
    """Uniform class-contiguous orders of a fixed set of tests."""

    def __init__(self, tests: list[str]):
        self.tests = tests
        self.index = {t: i for i, t in enumerate(tests)}
        groups = collections.defaultdict(list)
        for t in tests:
            groups[class_of(t)].append(self.index[t])
        self.classes = [np.array(v) for v in groups.values()]
        self.sizes = np.array([len(v) for v in self.classes])
        self.n = len(tests)

    def positions(self, rng: np.random.Generator, count: int) -> np.ndarray:
        """Return (count, n) int32 positions of each test in sampled orders."""
        k = len(self.classes)
        corder = np.argsort(rng.random((count, k)), axis=1)
        csz = self.sizes[corder]
        starts = (np.cumsum(csz, axis=1) - csz).astype(np.int32)
        offset = np.empty((count, k), dtype=np.int32)
        np.put_along_axis(offset, corder, starts, axis=1)
        pos = np.empty((count, self.n), dtype=np.int32)
        for ci, members in enumerate(self.classes):
            if len(members) == 1:
                pos[:, members[0]] = offset[:, ci]
            else:
                within = np.argsort(np.argsort(rng.random((count, len(members))), axis=1), axis=1)
                pos[:, members] = offset[:, [ci]] + within
        return pos


class Evaluator:
    """Vectorised failure indicators for a module's targets."""

    def __init__(self, targets: list[Target], sampler: Sampler, semantics: str = "S1"):
        self.targets, self.s, self.sem = targets, sampler, semantics

    def fails(self, pos: np.ndarray) -> np.ndarray:
        """pos: (N, n) positions -> (N, len(targets)) bool failure matrix."""
        ix = self.s.index
        out = np.empty((pos.shape[0], len(self.targets)), dtype=bool)
        for j, t in enumerate(self.targets):
            pv = pos[:, ix[t.name]]
            if t.kind == "brittle":
                fail = np.ones(pos.shape[0], dtype=bool)
                for st in t.setters:
                    fail &= pos[:, ix[st]] > pv
            else:
                fail = np.zeros(pos.shape[0], dtype=bool)
                for p in t.polluters:
                    pp = pos[:, ix[p]]
                    active = pp < pv
                    for g in t.cleaners(p, self.sem):
                        cleaned = np.ones(pos.shape[0], dtype=bool)
                        for c in g:
                            pc = pos[:, ix[c]]
                            cleaned &= (pp < pc) & (pc < pv)
                        active &= ~cleaned
                    fail |= active
            out[:, j] = fail
        return out


def fails_single(order: list[str], t: Target, semantics: str = "S1") -> bool:
    """Scalar reference implementation of the same semantics."""
    pos = {x: i for i, x in enumerate(order)}
    v = pos[t.name]
    if t.kind == "brittle":
        return not any(pos[s] < v for s in t.setters)
    for p in t.polluters:
        if pos[p] < v and not any(all(pos[p] < pos[c] < v for c in g)
                                  for g in t.cleaners(p, semantics)):
            return True
    return False


def pack(bits: np.ndarray) -> np.ndarray:
    """(N, m<=64) bool -> (N,) uint64 bitmask."""
    w = (np.uint64(1) << np.arange(bits.shape[1], dtype=np.uint64))
    return (bits.astype(np.uint64) * w).sum(axis=1, dtype=np.uint64)
