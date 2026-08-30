"""The benchmark problems, and how the optimiser's answers are checked.

Each problem states its givens, a goal expressed in floating point (for the
search) and the exact predicate that the winning construction must satisfy when
replayed through the kernel.  Several also name the proposition where Euclid
solves the same problem, so his step count and the optimiser's can be put side
by side.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

from ..kernel.field import Context, is_zero
from ..plane.construct import circle_with_radius2, line as draw_line, meet
from ..plane.objects import Circle as ExactCircle, Line as ExactLine, Point
from ..plane.predicates import collinear, eq_len, len2, perpendicular, right_angle
from .isa import Move
from .optimizer import Result, search
from .state import EPSILON, Circle, Line, State

__all__ = ["PROBLEMS", "Problem", "replay_exactly", "solve"]

TOLERANCE = 1e-7


@dataclass
class Problem:
    name: str
    description: str
    points: tuple[tuple[float, float], ...]
    names: list[str]
    goal: Callable[[State], bool]
    exact_goal: Callable[[list, list], bool]
    euclid: Optional[str] = None
    given_circle: bool = False

    def start(self, isa: str) -> State:
        objects: tuple = ()
        if isa == "straightedge-only":
            # Poncelet-Steiner needs one circle, with its centre, to be given
            centre = self.points[0]
            objects = (Circle(centre[0], centre[1], math.dist(centre, self.points[1])),)
        return State(self.points, objects)


def _has_point(state: State, test: Callable[[tuple[float, float]], bool]) -> bool:
    return any(test(point) for point in state.points)


def _has_line(state: State, test) -> bool:
    return any(isinstance(item, Line) and test(item) for item in state.objects)


# ---------------------------------------------------------------------------
# the problems
# ---------------------------------------------------------------------------

A = (0.0, 0.0)
B = (1.0, 0.0)


def _equilateral_goal(state: State) -> bool:
    return _has_point(
        state,
        lambda p: abs(math.dist(p, A) - 1.0) < TOLERANCE
        and abs(math.dist(p, B) - 1.0) < TOLERANCE,
    )


def _equilateral_exact(points: list, drawn: list) -> bool:
    origin, unit = Point(0, 0), Point(1, 0)
    return any(
        eq_len(p, origin, origin, unit) and eq_len(p, unit, origin, unit)
        for p in points
    )


def _midpoint_goal(state: State) -> bool:
    return _has_point(state, lambda p: math.dist(p, (0.5, 0.0)) < TOLERANCE)


def _midpoint_exact(points: list, drawn: list) -> bool:
    from fractions import Fraction

    target = Point(Fraction(1, 2), 0)
    return any(p == target for p in points)


def _bisector_goal(state: State) -> bool:
    # the perpendicular bisector of AB is the line x = 1/2
    return _has_line(
        state,
        lambda l: abs(abs(l.a) - 1.0) < TOLERANCE
        and abs(l.b) < TOLERANCE
        and abs(abs(l.c) - 0.5) < TOLERANCE,
    )


def _bisector_exact(points: list, drawn: list) -> bool:
    """The line x = 1/2 must actually be drawn.

    This used to ask only for two points with x == 1/2, which is a strictly
    weaker condition than the one the search solves -- the two circles of the
    usual construction produce both points without drawing anything through
    them. So the "exact verification" was passing on a figure that does not
    contain the line, and exact enumeration found a two-move answer to a
    three-move problem. The goal has to be the same goal.
    """
    from fractions import Fraction

    return any(
        isinstance(shape, ExactLine)
        and shape.a == 1 and is_zero(shape.b) and shape.c == Fraction(1, 2)
        for shape in drawn
    )


def _perpendicular_at_a_goal(state: State) -> bool:
    return _has_line(
        state, lambda l: abs(l.b) < TOLERANCE and abs(l.c) < TOLERANCE
    )


def _perpendicular_at_a_exact(points: list, drawn: list) -> bool:
    """The y-axis must actually be drawn -- see :func:`_bisector_exact`.

    Points pinning a line down is not the same as the line being there.
    """
    return any(
        isinstance(shape, ExactLine)
        and shape.a == 1 and is_zero(shape.b) and is_zero(shape.c)
        for shape in drawn
    )


def _double_goal(state: State) -> bool:
    return _has_point(state, lambda p: math.dist(p, (2.0, 0.0)) < TOLERANCE)


def _double_exact(points: list, drawn: list) -> bool:
    return any(p == Point(2, 0) for p in points)


def _square_goal(state: State) -> bool:
    corners = [(0.0, 1.0), (1.0, 1.0)]
    return all(
        _has_point(state, lambda p, corner=corner: math.dist(p, corner) < TOLERANCE)
        for corner in corners
    ) or all(
        _has_point(state, lambda p, corner=corner: math.dist(p, corner) < TOLERANCE)
        for corner in [(0.0, -1.0), (1.0, -1.0)]
    )


def _square_exact(points: list, drawn: list) -> bool:
    wanted = [Point(0, 1), Point(1, 1)]
    mirrored = [Point(0, -1), Point(1, -1)]
    return all(p in points for p in wanted) or all(p in points for p in mirrored)


PROBLEMS: dict[str, Problem] = {
    "equilateral-triangle": Problem(
        "equilateral-triangle",
        "Given AB, find the apex of an equilateral triangle on it.",
        (A, B),
        ["A", "B"],
        _equilateral_goal,
        _equilateral_exact,
        euclid="I.1",
    ),
    "perpendicular-bisector": Problem(
        "perpendicular-bisector",
        "Given AB, draw the line that bisects it at right angles.",
        (A, B),
        ["A", "B"],
        _bisector_goal,
        _bisector_exact,
        euclid="I.10",
    ),
    "midpoint": Problem(
        "midpoint",
        "Given AB, find its midpoint.",
        (A, B),
        ["A", "B"],
        _midpoint_goal,
        _midpoint_exact,
        euclid="I.10",
    ),
    "perpendicular-at-a-point": Problem(
        "perpendicular-at-a-point",
        "Given AB, erect a perpendicular to it at A.",
        (A, B),
        ["A", "B"],
        _perpendicular_at_a_goal,
        _perpendicular_at_a_exact,
        euclid="I.11",
    ),
    "double-a-segment": Problem(
        "double-a-segment",
        "Given AB, find the point C with B between A and C and BC equal to AB.",
        (A, B),
        ["A", "B"],
        _double_goal,
        _double_exact,
        euclid="I.3",
    ),
    "square-on-a-segment": Problem(
        "square-on-a-segment",
        "Given AB, find the two far corners of the square described on it.",
        (A, B),
        ["A", "B"],
        _square_goal,
        _square_exact,
        euclid="I.46",
    ),
}


# ---------------------------------------------------------------------------
# exact replay
# ---------------------------------------------------------------------------


def replay_exactly(problem: Problem, moves: list[Move]) -> bool:
    """Re-run a discovered construction through the exact kernel.

    The float search and the exact primitives share their intersection ordering
    rules, so the move indices line up and the replay follows the same path.
    """
    from fractions import Fraction

    with Context(f"replay:{problem.name}"):
        points = [Point(Fraction(int(x)), Fraction(int(y)), name)
                  for (x, y), name in zip(problem.points, problem.names)]
        drawn: list = []
        if problem.given_circle:
            drawn.append(ExactCircle.centred(points[0], points[1]))
        for move in moves:
            if move.first >= len(points) or move.second >= len(points):
                return False
            first, second = points[move.first], points[move.second]
            if first == second:
                return False
            if move.kind == "line":
                shape = ExactLine.through(first, second)
            else:
                shape = ExactCircle.centred(first, second)
            for existing in drawn:
                for candidate in meet(shape, existing):
                    if candidate not in points:
                        points.append(candidate)
            drawn.append(shape)
        return problem.exact_goal(points, drawn)


def solve(
    name: str,
    isa: str = "full",
    max_depth: int = 5,
    node_budget: int = 400_000,
    max_points: int = 20,
) -> Result:
    """Search for the shortest construction, then verify it exactly."""
    problem = PROBLEMS[name]
    result = search(
        problem.name,
        problem.start(isa),
        problem.goal,
        isa=isa,
        max_depth=max_depth,
        node_budget=node_budget,
        point_names=list(problem.names),
        max_points=max_points,
    )
    if result.found and isa != "straightedge-only":
        result.verified = replay_exactly(problem, result.moves)
        # Then the other half of the claim: that nothing shorter exists. The
        # float search cannot establish that, so refute length - 1 exactly.
        from .exact import shortest_is_certified

        certified, exhaustion = shortest_is_certified(problem, isa, result.length)
        result.exact_minimal = certified
        result.exact_figures = exhaustion.figures
    return result
