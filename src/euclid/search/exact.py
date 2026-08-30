"""Exhaustive enumeration in exact arithmetic, to certify that nothing is shorter.

The optimiser searches in floating point and replays only the winner exactly.
That is sound for the *positive* half of its answer -- a construction it returns
was re-run through the kernel and either works or does not.  It says nothing
about the *negative* half, which is the half that matters:
"fewest possible" means no shorter construction exists, and that claim was
resting on float arithmetic.

Three ways floats can lose a construction, each of which turns a real one
invisible and so makes a false negative:

* two distinct points collapse into one at the ``1e-7`` dedup;
* a tangency is discarded because its discriminant lands just below
  ``-EPSILON``;
* two genuinely different figures share a rounded :meth:`State.canonical`
  fingerprint, so one subtree is never opened.

None of the three can happen here.  Points are compared with the kernel's exact
equality, intersections either exist or do not, and nothing is deduplicated at
all.  The heuristics that bound the float search -- ``scope`` and
``max_points``, both documented there as able to hide a construction -- are
absent too, because a bound that can hide a construction cannot appear in a
proof that none exists.

The cost is that this only reaches shallow depths.  That is enough, because
certifying an answer of length ``L`` means refuting ``L - 1``, not enumerating
``L``: to know the two circles of I.1 cannot be beaten, only the one-move
figures have to be ruled out.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Optional

from ..kernel.field import Context
from ..plane.construct import meet
from ..plane.objects import Circle as ExactCircle, Line as ExactLine, Point
from .isa import INSTRUCTION_SETS, Move, moves_for

__all__ = ["Exhaustion", "shortest_is_certified", "enumerate_exactly"]

# A ceiling on the work, so a problem that is out of reach says so instead of
# hanging. Not a scope heuristic: hitting it makes the answer "unknown", never
# "none exists".
DEFAULT_EXACT_BUDGET = 60_000


class Exhaustion:
    """What an exact enumeration to some depth established."""

    __slots__ = ("depth", "found", "moves", "figures", "exhausted")

    def __init__(self, depth: int) -> None:
        self.depth = depth
        self.found = False
        self.moves: list[Move] = []
        self.figures = 0
        self.exhausted = False  # the whole space to `depth` was examined

    def __str__(self) -> str:
        if self.found:
            return f"a construction of {len(self.moves)} moves exists"
        if self.exhausted:
            return f"no construction of {self.depth} moves or fewer exists"
        return f"unknown: the budget ran out at depth {self.depth}"


def _replay(problem, moves: list[Move]) -> Optional[tuple[list[Point], list]]:
    """The exact figure a move sequence builds, or None if it is not drawable.

    The same walk as :func:`euclid.search.problems.replay_exactly`, but it hands
    back the figure rather than a verdict, so a prefix can be extended.
    """
    points = [Point(Fraction(int(x)), Fraction(int(y)), name)
              for (x, y), name in zip(problem.points, problem.names)]
    drawn: list = []
    if problem.given_circle:
        drawn.append(ExactCircle.centred(points[0], points[1]))
    for move in moves:
        if move.first >= len(points) or move.second >= len(points):
            return None
        first, second = points[move.first], points[move.second]
        if first == second:
            return None
        if move.kind == "line":
            shape = ExactLine.through(first, second)
        else:
            shape = ExactCircle.centred(first, second)
        for existing in drawn:
            for candidate in meet(shape, existing):
                if candidate not in points:
                    points.append(candidate)
        drawn.append(shape)
    return points, drawn


def enumerate_exactly(
    problem,
    isa: str = "full",
    depth: int = 2,
    budget: int = DEFAULT_EXACT_BUDGET,
) -> Exhaustion:
    """Try every construction of ``depth`` moves or fewer, in exact arithmetic.

    Each figure is rebuilt from the empty state in its own :class:`Context`, so
    one branch's square roots never pile up in another's tower.  Rebuilding a
    prefix costs a few exact intersections and buys that isolation, which at
    these depths is a good trade.
    """
    instruction_set = INSTRUCTION_SETS[isa]
    outcome = Exhaustion(depth)

    def walk(sequence: list[Move]) -> bool:
        """True if the goal was reached; sets outcome as a side effect."""
        if outcome.figures >= budget:
            return False
        outcome.figures += 1
        with Context(f"exact:{problem.name}:{len(sequence)}"):
            figure = _replay(problem, sequence)
            if figure is None:
                return False
            points, drawn = figure
            if sequence and problem.exact_goal(points, drawn):
                outcome.found = True
                outcome.moves = list(sequence)
                return True
            reach = len(points)
        if len(sequence) >= depth:
            return False
        for move in moves_for(instruction_set, reach):
            if walk(sequence + [move]):
                return True
            if outcome.figures >= budget:
                return False
        return False

    walk([])
    outcome.exhausted = outcome.figures < budget and not outcome.found
    return outcome


def shortest_is_certified(
    problem,
    isa: str,
    length: int,
    budget: int = DEFAULT_EXACT_BUDGET,
) -> tuple[bool, Exhaustion]:
    """Is a construction of ``length`` moves provably the shortest?

    Refutes ``length - 1`` exactly.  Three outcomes, and they are different:

    * the space to ``length - 1`` was exhausted with nothing found -- the answer
      is minimal, and that is a theorem;
    * the budget ran out -- unknown, so the answer stays an upper bound;
    * something *was* found -- the float search missed a shorter construction,
      which is a bug in the optimiser and not a fact about geometry.  The caller
      must not quietly treat this as "not certified".
    """
    if length <= 0:
        return False, Exhaustion(0)
    outcome = enumerate_exactly(problem, isa, depth=length - 1, budget=budget)
    if outcome.found:
        raise AssertionError(
            f"{problem.name} [{isa}]: the float search reported {length} moves, but "
            f"exact enumeration found one of {len(outcome.moves)}. The search is "
            f"losing constructions, not the arithmetic."
        )
    return outcome.exhausted, outcome
