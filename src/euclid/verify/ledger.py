"""The assumption ledger: what each proposition takes on trust.

Euclid's postulates let you draw lines and circles.  They do not tell you that
two circles meet, that a point falls between two others, or that a line enters
a triangle on the side the diagram shows.  Those gaps are the substance of the
Hilbert-Pasch critique, and the classical way to find them is to read the text
very carefully.  This module finds them by running the code instead.

Three kinds of debt are recorded.

**Continuity.**  Every line-circle and circle-circle intersection the
construction consumes.  No postulate asserts these points exist; Euclid names
them anyway, starting on the very first page with I.1.  This is read straight
off the trace, so it is exhaustive.

**Order.**  Betweenness and same-side facts the proposition relies on.  These
are recorded as they are evaluated, and flagged when they carry the argument.

**Case dependence.**  The interesting one, and the reason this is not just a
static scan.  The proposition is run over many configurations and the traces are
compared.  If a predicate's truth value flips, or an intersection returns a
different number of points, or the construction takes a different route, then
the proof depends on *which* diagram it was handed -- and Euclid, who drew one
diagram, could not have noticed.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from ..elements.registry import BadConfiguration, ProofFailure, get, run_sampled
from ..plane.construct import GeometryError
from ..plane.trace import Trace

__all__ = ["Assumption", "Ledger", "audit", "audit_all", "case_assumptions"]


@dataclass
class Assumption:
    kind: str  # "continuity" | "order" | "case"
    detail: str
    occurrences: int = 1


@dataclass
class Ledger:
    ref: str
    title: str
    configurations: int = 0
    assumptions: list[Assumption] = field(default_factory=list)
    distinct_routes: int = 0

    def of_kind(self, kind: str) -> list[Assumption]:
        return [item for item in self.assumptions if item.kind == kind]

    @property
    def continuity_debt(self) -> int:
        return sum(item.occurrences for item in self.of_kind("continuity"))

    @property
    def is_clean(self) -> bool:
        return not self.assumptions

    def report(self) -> str:
        lines = [f"{self.ref}  {self.title}", ""]
        if not self.assumptions:
            lines.append("  nothing taken on trust: no intersections, no order facts.")
            return "\n".join(lines)
        headings = {
            "continuity": "existence not granted by any postulate",
            "order": "betweenness and side facts read off the diagram",
            "case": "behaviour that changes with the configuration",
        }
        for kind, heading in headings.items():
            items = self.of_kind(kind)
            if not items:
                continue
            lines.append(f"  {kind.upper()} -- {heading}")
            for item in items:
                count = f" (x{item.occurrences})" if item.occurrences > 1 else ""
                lines.append(f"    - {item.detail}{count}")
            lines.append("")
        lines.append(f"  configurations examined: {self.configurations}")
        if self.distinct_routes > 1:
            lines.append(f"  distinct construction routes observed: {self.distinct_routes}")
        return "\n".join(lines).rstrip()


def _collect_traces(ref: str, trials: int, seed: int) -> list[Trace]:
    rng = random.Random(f"ledger:{ref}:{seed}")
    traces: list[Trace] = []
    attempts = 0
    while len(traces) < trials and attempts < trials * 6:
        attempts += 1
        try:
            traces.append(run_sampled(ref, rng).trace)
        except (BadConfiguration, GeometryError, ProofFailure):
            continue
    return traces


def audit(ref: str, trials: int = 12, seed: int = 0) -> Ledger:
    """Build the ledger for one proposition."""
    entry = get(ref)
    ledger = Ledger(ref=ref, title=entry.statement)
    if entry.sample is None:
        return ledger
    traces = _collect_traces(ref, trials, seed)
    ledger.configurations = len(traces)
    if not traces:
        return ledger

    # Across every configuration, not just the first. These tallies used to be
    # read off ``traces[0]``, which is only defensible if every configuration
    # takes the same route -- and four propositions demonstrably do not. For
    # those the reported debt was whichever route the first sample happened to
    # take. The debt of a proposition is the most it ever incurs, so each
    # distinct assumption is counted at its maximum over the configurations.
    def worst(counters: list[Counter]) -> Counter:
        combined: Counter = Counter()
        for counter in counters:
            for key, count in counter.items():
                combined[key] = max(combined[key], count)
        return combined

    # --- continuity ------------------------------------------------------
    per_trace: list[Counter] = []
    for trace in traces:
        tally: Counter = Counter()
        for event in trace.intersections:
            if not event.guaranteed_by_postulates:
                tally[(event.kind, event.detail)] += 1
        per_trace.append(tally)
    for (kind, detail), count in sorted(worst(per_trace).items()):
        ledger.assumptions.append(
            Assumption("continuity", f"a {kind} intersection is used, though {detail}", count)
        )

    # --- order -----------------------------------------------------------
    per_trace = []
    for trace in traces:
        order_tally: Counter = Counter()
        for event in trace.predicates:
            if event.order_sensitive:
                order_tally[event.name] += 1
        per_trace.append(order_tally)
    for name, count in sorted(worst(per_trace).items()):
        ledger.assumptions.append(
            Assumption("order", f"the argument reads a '{name}' fact off the figure", count)
        )

    # --- case dependence --------------------------------------------------
    ledger.distinct_routes = len({trace.signature() for trace in traces})
    ledger.assumptions.extend(case_assumptions(traces))
    return ledger


def case_assumptions(traces: list[Trace]) -> list[Assumption]:
    """Compare traces from different configurations and report what differs.

    A proof that is genuinely general behaves identically whatever legal figure
    it is handed.  Anything that varies -- the number of facts evaluated, the
    truth of one of them, the number of points an intersection returns -- means
    the argument is picking its way through a particular diagram.
    """
    found: list[Assumption] = []
    if len(traces) < 2:
        return found
    first = traces[0]

    lengths = {len(trace.predicates) for trace in traces}
    if len(lengths) > 1:
        found.append(
            Assumption(
                "case",
                "the proof evaluates a different number of facts on different "
                f"configurations (seen: {sorted(lengths)}), so it is following more "
                "than one route through the diagram",
            )
        )

    # Keyed by name and position-within-name, never by position in the list.
    # This check used to sit in the `else` of the branch above, so it never ran
    # on a proposition whose predicate count varies -- which is precisely where
    # a proof is branching and a flip is most likely. Three of the four
    # case-dependent propositions were in that blind spot.
    occurrences: dict[tuple[str, int], set[bool]] = {}
    for trace in traces:
        seen_of_name: Counter = Counter()
        for event in trace.predicates:
            index = seen_of_name[event.name]
            seen_of_name[event.name] += 1
            occurrences.setdefault((event.name, index), set()).add(bool(event.value))
    for (name, index), values in sorted(occurrences.items()):
        if len(values) > 1:
            found.append(
                Assumption(
                    "case",
                    f"the '{name}' fact (occurrence {index + 1}) is true in some "
                    "configurations and false in others",
                )
            )

    counts_by_position: dict[int, set[int]] = {}
    for trace in traces:
        for position, event in enumerate(trace.intersections):
            counts_by_position.setdefault(position, set()).add(event.count)
    for position, counts in sorted(counts_by_position.items()):
        if len(counts) > 1:
            found.append(
                Assumption(
                    "case",
                    f"intersection {position + 1} yields {sorted(counts)} points "
                    "depending on the configuration",
                )
            )
    return found


def audit_all(book: Optional[str] = None, trials: int = 12, seed: int = 0) -> list[Ledger]:
    from ..elements.registry import all_propositions

    chosen = all_propositions()
    if book is not None:
        chosen = [entry for entry in chosen if entry.book == book]
    return [audit(entry.ref, trials=trials, seed=seed) for entry in chosen]
