"""Evaluation creation matrix: every option combination the UI allows.

Axes (mapped on prod 2026-11-05, see docs/app_bugs.md and tasks/todo.md):
  - method:    bulk | playground  (the method IS the mode; no automated/manual toggle)
  - evaluator: technical | domain | cultural
  - domain:    healthcare | agriculture | general   (modal step 2 "Evaluation Domain")
  - bulk only: modules = any non-empty subset of the 3 modules,
               source  = prompt library | custom (typed) prompts

`all_combos()` is the full 135-case space (9 playground + 126 bulk).
`PAIRWISE_IDS` is a 14-run subset in which every pair of
(evaluator, domain), (evaluator, module), (domain, module) and every
(evaluator|domain|module, source) pair appears at least once.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product

METHODS = ("bulk", "playground")
EVALUATORS = ("technical", "domain", "cultural")
DOMAINS = ("healthcare", "agriculture", "general")
MODULES = ("hallucination", "bias", "privacy")
SOURCES = ("library", "custom")


@dataclass(frozen=True)
class Combo:
    method: str
    evaluator: str
    domain: str
    modules: tuple[str, ...] = ()
    source: str = ""

    @property
    def id(self) -> str:
        if self.method == "playground":
            return f"playground-{self.evaluator}-{self.domain}"
        return f"bulk-{self.evaluator}-{self.domain}-{'+'.join(self.modules)}-{self.source}"


def _module_subsets() -> list[tuple[str, ...]]:
    return [c for n in range(1, len(MODULES) + 1) for c in combinations(MODULES, n)]


def all_combos() -> list[Combo]:
    out = [Combo("playground", e, d) for e, d in product(EVALUATORS, DOMAINS)]
    out += [
        Combo("bulk", e, d, m, s)
        for e, d, m, s in product(EVALUATORS, DOMAINS, _module_subsets(), SOURCES)
    ]
    return out


# Latin-square cover: (evaluator i, domain j, module (i+j)%3) over 9 bulk runs
# hits every pairwise pair; three playground runs cover each evaluator and
# domain once; two extra bulk runs close the (axis, source) gaps.
def _pairwise() -> list[Combo]:
    combos = [Combo("playground", EVALUATORS[i], DOMAINS[i]) for i in range(3)]
    for i, j in product(range(3), range(3)):
        source = SOURCES[(i + j) % 2]
        combos.append(Combo("bulk", EVALUATORS[i], DOMAINS[j], (MODULES[(i + j) % 3],), source))
    combos.append(Combo("bulk", "technical", "general", ("hallucination", "bias", "privacy"), "library"))
    combos.append(Combo("bulk", "cultural", "healthcare", ("privacy",), "custom"))
    return combos


PAIRWISE = _pairwise()
PAIRWISE_IDS = tuple(c.id for c in PAIRWISE)


def combos_for(selection: str) -> list[Combo]:
    """selection: 'pairwise' (14), 'all' (135); anything else -> empty (opt-in)."""
    return {"pairwise": PAIRWISE, "all": all_combos()}.get(selection.lower(), [])


def _selfcheck() -> None:
    assert len(all_combos()) == 135, len(all_combos())
    assert len({c.id for c in all_combos()}) == 135
    assert len(PAIRWISE) == 14 and len(set(PAIRWISE_IDS)) == 14
    bulk = [c for c in PAIRWISE if c.method == "bulk"]

    def pairs(f, g):
        return {(f(c), g(c)) for c in bulk if len(c.modules) == 1}

    for a, b in ((lambda c: c.evaluator, lambda c: c.domain),
                 (lambda c: c.evaluator, lambda c: c.modules[0]),
                 (lambda c: c.domain, lambda c: c.modules[0])):
        assert len(pairs(a, b)) == 9, "pairwise cover broken"
    for axis in (lambda c: c.evaluator, lambda c: c.domain, lambda c: c.modules[0]):
        got = {(axis(c), c.source) for c in bulk if len(c.modules) == 1}
        want = {(v, s) for v in {axis(c) for c in bulk if len(c.modules) == 1} for s in SOURCES}
        assert got >= want, f"source cover missing: {sorted(want - got)}"


if __name__ == "__main__":
    _selfcheck()
    print("ok", len(all_combos()), len(PAIRWISE))
    for c in PAIRWISE:
        print(c.id)
