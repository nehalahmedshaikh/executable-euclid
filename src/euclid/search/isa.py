"""Instruction sets: what counts as a legal move.

Euclid's postulates are one instruction set among several, and the classical
restriction theorems say the others are surprisingly capable:

``full``
    straightedge and compass, Postulates 1 and 3.
``compass-only``
    circles alone.  Mohr (1672) and Mascheroni (1797) proved that every point
    constructible with both tools is constructible with the compass alone --
    lines cannot be drawn, but their intersections can still be found.
``straightedge-only``
    lines alone.  Poncelet and Steiner proved this suffices *provided* one
    circle with its centre is given, which is why this ISA starts with one.
``rusty-compass``
    a compass stuck at one opening.  Enough for most of Book I, and a favourite
    of the medieval Arabic geometers.

Retargeting the same problem across these is the point: a construction is a
program, and these are its back ends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator

from .state import Circle, Line

__all__ = ["INSTRUCTION_SETS", "InstructionSet", "Move", "moves_for"]


@dataclass(frozen=True)
class Move:
    """Draw one object, naming the points that determined it."""

    kind: str  # "line" | "circle"
    first: int
    second: int

    def describe(self, names: list[str]) -> str:
        one = names[self.first] if self.first < len(names) else f"P{self.first}"
        two = names[self.second] if self.second < len(names) else f"P{self.second}"
        if self.kind == "line":
            return f"draw the line {one}{two}"
        return f"draw the circle with centre {one} through {two}"


@dataclass(frozen=True)
class InstructionSet:
    name: str
    lines: bool
    circles: bool
    description: str
    fixed_radius: bool = False
    needs_given_circle: bool = False


INSTRUCTION_SETS = {
    "full": InstructionSet(
        "full", True, True,
        "straightedge and compass: Euclid's Postulates 1 and 3",
    ),
    "compass-only": InstructionSet(
        "compass-only", False, True,
        "the compass alone (Mohr-Mascheroni): every constructible point is still "
        "reachable, though no line can be drawn",
    ),
    "straightedge-only": InstructionSet(
        "straightedge-only", True, False,
        "the straightedge alone (Poncelet-Steiner), given one circle with its centre",
        needs_given_circle=True,
    ),
    "rusty-compass": InstructionSet(
        "rusty-compass", True, True,
        "straightedge and a compass fixed at a single opening",
        fixed_radius=True,
    ),
}


def moves_for(isa: InstructionSet, point_count: int) -> Iterator[Move]:
    """Every legal move on a figure with the given number of points."""
    if isa.lines:
        for first in range(point_count):
            for second in range(first + 1, point_count):
                yield Move("line", first, second)
    if isa.circles:
        if isa.fixed_radius:
            # the opening never changes: the second point only names the radius
            # once, so a circle is determined by its centre alone
            for centre in range(point_count):
                yield Move("circle", centre, 0 if centre != 0 else 1)
        else:
            for centre in range(point_count):
                for through in range(point_count):
                    if centre != through:
                        yield Move("circle", centre, through)
