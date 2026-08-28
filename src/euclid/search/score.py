"""Lemoine's geometrography: counting what a construction actually costs.

Emile Lemoine's *Geometrographie* (1888) proposed grading constructions by the
physical operations they demand, rather than by how elegant the write-up looks:

======  ==========================================================
``S1``  place the edge of the straightedge against a given point
``S2``  draw a line
``C1``  place a compass point on a given point
``C2``  open the compass to a given point
``C3``  describe a circle
======  ==========================================================

The *simplicity* of a construction is the total count; the *exactitude* is the
count of the placement operations (``S1``, ``C1``, ``C2``), the ones where a
draughtsman's hand can slip.

A caveat worth stating rather than hiding: with both primitives costing three
operations apiece, simplicity is three times the move count for the problems
here.  The breakdown still distinguishes a straightedge-heavy construction from
a compass-heavy one, which is the comparison that matters when retargeting
between instruction sets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .isa import Move

__all__ = ["Geometrography", "score"]


@dataclass
class Geometrography:
    s1: int = 0
    s2: int = 0
    c1: int = 0
    c2: int = 0
    c3: int = 0

    @property
    def simplicity(self) -> int:
        return self.s1 + self.s2 + self.c1 + self.c2 + self.c3

    @property
    def exactitude(self) -> int:
        return self.s1 + self.c1 + self.c2

    def notation(self) -> str:
        parts = []
        for count, symbol in (
            (self.s1, "S1"),
            (self.s2, "S2"),
            (self.c1, "C1"),
            (self.c2, "C2"),
            (self.c3, "C3"),
        ):
            if count:
                parts.append(f"{count}{symbol}")
        return " + ".join(parts) if parts else "0"

    def __repr__(self) -> str:
        return f"<{self.notation()} = {self.simplicity}>"


def score(moves: Iterable[Move]) -> Geometrography:
    """Grade a construction by Lemoine's scheme."""
    total = Geometrography()
    for move in moves:
        if move.kind == "line":
            total.s1 += 2  # the edge is laid against each of the two points
            total.s2 += 1
        else:
            total.c1 += 1  # the compass point goes on the centre
            total.c2 += 1  # and the pencil is opened to the second point
            total.c3 += 1
    return total
