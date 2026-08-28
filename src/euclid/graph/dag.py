"""The dependency graph, extracted by execution.

Nothing in this project maintains a cross-reference table.  The edges below are
whatever the propositions actually did when they ran: the calls they made and
the results they cited.  That has a pleasant consequence -- the graph cannot
drift out of step with the proofs, because it *is* the proofs.

What it buys us:

* **Tree-shaking.**  The minimal set of propositions needed for a given result,
  in dependency order -- a self-contained little book ending at, say, I.47.
* **Depth.**  How many layers of argument stand between a proposition and the
  postulates.
* **Load-bearing rank.**  How many propositions would fall if this one did.
  (I.4 has an alarming answer.)
* **First principles.**  Which postulates, definitions and common notions a
  result depends on -- which is how you see, mechanically, that I.27 is neutral
  geometry and I.29 is not.
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
        graph.edges[entry.ref] = {
            ref
            for ref in entry.depends_on
            if reference_kind(ref) == "proposition" and ref in graph.nodes
        }
    return graph
