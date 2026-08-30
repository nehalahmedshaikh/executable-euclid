"""The dependency graph, and where each edge really comes from.

An edge arrives here by one of two routes, and they are not equally strong:

**Executed.**  One proposition calls another, and the call is recorded as it
happens.  I.44 genuinely runs I.42; nothing was declared, and the edge cannot be
wrong.

**Cited.**  A step names the result it appeals to -- ``claim(..., "I.4", ...)``
-- and that name is written by hand alongside the step, following Heath's
marginal references.  The *check* on the step is independent of the citation, so
a wrong name cannot smuggle a false statement through; but the edge itself is an
authored claim about the proof, not an observation of it.

The split is lopsided and should be stated rather than glossed: roughly one edge
in eight is executed and the rest are cited, and every postulate, definition and
common-notion edge is cited, because those are not callable objects.  So results
read off this graph -- what rests on I.1, where Postulate 5 first appears, the
minimal set behind I.47 -- report *Euclid's own cross-references, faithfully
transcribed*.  Useful, and not a discovery; this module used to claim it was.

:attr:`Graph.executed` holds only what actually ran; :attr:`Graph.cited` holds
the rest; :meth:`Graph.provenance` counts both.  :meth:`Graph.needs` and
everything built on it mix the two, which is usually what you want for
navigation and never what you want for a finding.

What it buys us -- all of it over the mixed edges, so read it as a tidy view of
Euclid's cross-references:

* **Tree-shaking.**  The minimal set of propositions needed for a given result,
  in dependency order -- a self-contained little book ending at, say, I.47.
* **Depth.**  How many layers of argument stand between a proposition and the
  postulates.
* **Load-bearing rank.**  How many propositions would fall if this one did.
  (I.4 has an alarming answer.)
* **First principles.**  Which postulates, definitions and common notions a
  result depends on.  That I.27 is neutral geometry and I.29 is not falls out of
  this -- but it falls out of the citations, which is to say out of Heath's
  margins, so it is not mechanical.

Two checks keep the cited edges honest, in :mod:`tests.test_corpus`: every
citation must name something that exists, and no proposition may cite a later
one.  Neither makes a citation into an observation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from ..elements.registry import Proposition, all_propositions, reference_kind

__all__ = ["Graph", "build"]


@dataclass
class Graph:
    nodes: dict[str, Proposition] = field(default_factory=dict)
    edges: dict[str, set[str]] = field(default_factory=dict)  # ref -> what it needs
    executed: dict[str, set[str]] = field(default_factory=dict)  # ...by calling it
    cited: dict[str, set[str]] = field(default_factory=dict)     # ...by naming it

    def provenance(self) -> tuple[int, int]:
        """How many edges were executed, and how many only cited."""
        return (sum(len(refs) for refs in self.executed.values()),
                sum(len(refs) for refs in self.cited.values()))

    # -- basic queries ------------------------------------------------------
    def needs(self, ref: str) -> set[str]:
        return self.edges.get(ref, set())

    def dependents(self, ref: str) -> set[str]:
        return {other for other, required in self.edges.items() if ref in required}

    def ancestors(self, ref: str) -> set[str]:
        """Everything ``ref`` rests on, transitively."""
        seen: set[str] = set()
        frontier = list(self.needs(ref))
        while frontier:
            current = frontier.pop()
            if current in seen or current not in self.nodes:
                continue
            seen.add(current)
            frontier.extend(self.needs(current))
        return seen

    def descendants(self, ref: str) -> set[str]:
        """Everything that would fall if ``ref`` did."""
        seen: set[str] = set()
        frontier = list(self.dependents(ref))
        while frontier:
            current = frontier.pop()
            if current in seen:
                continue
            seen.add(current)
            frontier.extend(self.dependents(current))
        return seen

    # -- ordering -----------------------------------------------------------
    def topological(self, refs: Optional[Iterable[str]] = None) -> list[str]:
        """Dependency order: nothing appears before what it needs.

        Ties are broken by the propositions' own numbering, so the output reads
        like Euclid rather than like a hash table.
        """
        chosen = set(refs) if refs is not None else set(self.nodes)
        remaining = dict((ref, self.needs(ref) & chosen) for ref in chosen)
        ordered: list[str] = []
        while remaining:
            ready = [ref for ref, pending in remaining.items() if not pending]
            if not ready:  # a cycle: emit the rest in book order and move on
                ready = sorted(remaining, key=lambda ref: self.nodes[ref].sort_key())
            ready.sort(key=lambda ref: self.nodes[ref].sort_key())
            for ref in ready:
                ordered.append(ref)
                del remaining[ref]
            for pending in remaining.values():
                pending.difference_update(ready)
        return ordered

    def tree_shake(self, ref: str) -> list[str]:
        """The minimal *Elements* for ``ref``: just what it needs, in order."""
        wanted = self.ancestors(ref) | {ref}
        return self.topological(wanted)

    def depth(self, ref: str) -> int:
        """Layers of argument between this proposition and the first principles."""
        memo: dict[str, int] = {}

        def measure(current: str, stack: frozenset) -> int:
            if current in memo:
                return memo[current]
            if current in stack:
                return 0
            required = [r for r in self.needs(current) if r in self.nodes]
            value = 0 if not required else 1 + max(
                measure(r, stack | {current}) for r in required
            )
            memo[current] = value
            return value

        return measure(ref, frozenset())

    # -- first principles ---------------------------------------------------
    def axioms(self, ref: str) -> set[str]:
        """Postulates, definitions and common notions used transitively."""
        collected: set[str] = set()
        for current in self.ancestors(ref) | {ref}:
            node = self.nodes.get(current)
            if node is not None:
                collected |= node.axioms_used
        return collected

    def uses_parallel_postulate(self, ref: str) -> bool:
        return any(axiom.startswith("Post.5") for axiom in self.axioms(ref))

    # -- metrics ------------------------------------------------------------
    def load_bearing(self) -> list[tuple[str, int]]:
        """Propositions ranked by how much of the corpus rests on them."""
        ranking = [(ref, len(self.descendants(ref))) for ref in self.nodes]
        ranking.sort(key=lambda pair: (-pair[1], self.nodes[pair[0]].sort_key()))
        return ranking

    def leaves(self) -> list[str]:
        """Propositions nothing else uses -- the ends of the branches."""
        return sorted(
            (ref for ref in self.nodes if not self.dependents(ref)),
            key=lambda ref: self.nodes[ref].sort_key(),
        )

    def roots(self) -> list[str]:
        """Propositions that need no other proposition."""
        return sorted(
            (ref for ref in self.nodes if not self.needs(ref)),
            key=lambda ref: self.nodes[ref].sort_key(),
        )

    # -- export -------------------------------------------------------------
    def to_dot(self, refs: Optional[Iterable[str]] = None) -> str:
        chosen = list(refs) if refs is not None else list(self.nodes)
        selected = set(chosen)
        lines = ["digraph Elements {", '  rankdir="BT";', '  node [shape=box, fontname="Georgia"];']
        for ref in self.topological(selected):
            lines.append(f'  "{ref}";')
        for ref in selected:
            for required in sorted(self.needs(ref) & selected):
                lines.append(f'  "{ref}" -> "{required}";')
        lines.append("}")
        return "\n".join(lines)

    def summary(self) -> str:
        rows = [f"{len(self.nodes)} propositions, {sum(len(e) for e in self.edges.values())} edges"]
        deepest = max(self.nodes, key=self.depth) if self.nodes else None
        if deepest:
            rows.append(f"deepest: {deepest} at depth {self.depth(deepest)}")
        ranking = self.load_bearing()[:3]
        if ranking:
            joined = ", ".join(f"{ref} ({count})" for ref, count in ranking)
            rows.append(f"most load-bearing: {joined}")
        return "\n".join(rows)


def build(propositions: Optional[Iterable[Proposition]] = None, warm: bool = True) -> Graph:
    """Assemble the graph, running the corpus first if it has not been run.

    Dependencies are discovered at run time, so a graph built before anything
    executes would be empty.  ``warm`` executes each proposition once.
    """
    if warm:
        from ..verify.fuzz import warm_up

        warm_up()
    entries = list(propositions) if propositions is not None else all_propositions()
    graph = Graph()
    for entry in entries:
        graph.nodes[entry.ref] = entry
    for entry in entries:
        def keep(refs):
            return {ref for ref in refs
                    if reference_kind(ref) == "proposition"
                    and ref in graph.nodes and ref != entry.ref}

        graph.edges[entry.ref] = keep(entry.depends_on)
        graph.executed[entry.ref] = keep(entry.calls)
        graph.cited[entry.ref] = keep(entry.cites) - keep(entry.calls)
    return graph
