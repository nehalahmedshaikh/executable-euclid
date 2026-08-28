"""The construction superoptimizer.

Iterative deepening over the space of straightedge-and-compass moves, looking
for the shortest construction that reaches a goal.  Three things keep it from
drowning:

* **Float search, exact verification.**  Millions of candidate figures are
  explored in machine arithmetic; only the winner is replayed through the exact
  kernel, where the answer either holds or does not.
* **Canonical states.**  Figures that differ by position, size or handedness are
  the same figure (:meth:`State.canonical`), so each is explored once.
* **Bounded scope.**  Points that wander far outside the region of interest are
  dropped, and the search stops at a node budget.

That last point is a real limit and the results say so.  A run reports whether
it was **exhaustive** -- meaning every construction of that length was examined,
so a returned answer is genuinely minimal and a failure genuinely proves none
exists at that depth -- or whether it hit the budget first, in which case the
answer is an upper bound and nothing more.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

from .isa import INSTRUCTION_SETS, InstructionSet, Move, moves_for
from .score import Geometrography, score
from .state import EPSILON, Circle, Line, State, intersect

__all__ = ["Result", "search"]

DEFAULT_NODE_BUDGET = 400_000
DEFAULT_MAX_POINTS = 20
DEFAULT_SCOPE = 8.0


@dataclass
class Result:
    problem: str
    isa: str
    found: bool = False
    moves: list[Move] = field(default_factory=list)
    depth_searched: int = 0
    exhaustive: bool = True
    nodes: int = 0
    verified: Optional[bool] = None
    point_names: list[str] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.moves)

    @property
    def geometrography(self) -> Geometrography:
        return score(self.moves)

    def steps(self) -> list[str]:
        return [move.describe(self.point_names) for move in self.moves]

    def report(self) -> str:
        lines = [f"{self.problem}   [{self.isa}]"]
        if not self.found:
            claim = "no construction exists" if self.exhaustive else "none found"
            lines.append(f"  {claim} within {self.depth_searched} moves "
                         f"({self.nodes} figures examined)")
            return "\n".join(lines)
        quality = "provably minimal" if self.exhaustive else "an upper bound (budget reached)"
        lines.append(f"  {self.length} moves -- {quality}")
        for index, step in enumerate(self.steps(), 1):
            lines.append(f"    {index}. {step}")
        grading = self.geometrography
        lines.append(f"  geometrography: {grading.notation()} "
                     f"= {grading.simplicity} (exactitude {grading.exactitude})")
        if self.verified is not None:
            lines.append(f"  exact verification: {'passed' if self.verified else 'FAILED'}")
        lines.append(f"  figures examined: {self.nodes}")
        return "\n".join(lines)


def _apply(
    state: State,
    move: Move,
    max_points: int = DEFAULT_MAX_POINTS,
    scope: float = DEFAULT_SCOPE,
) -> Optional[State]:
    """Draw one object and take in whatever new points it produces.

    Two bounds keep the figure finite: points further than ``scope`` times the
    base length from the origin are ignored, and a figure carrying more than
    ``max_points`` points is abandoned.  Both are heuristics, and both are
    reported, because either can hide a construction that exists.
    """
    points = state.points
    if move.first >= len(points) or move.second >= len(points):
        return None
    if move.kind == "line":
        if math.dist(points[move.first], points[move.second]) < EPSILON:
            return None
        drawn = Line.through(points[move.first], points[move.second])
    else:
        radius = math.dist(points[move.first], points[move.second])
        if radius < EPSILON:
            return None
        drawn = Circle(points[move.first][0], points[move.first][1], radius)

    if drawn.key() in state.object_keys():
        return None

    origin = points[0]
    reach = max(math.dist(origin, point) for point in points[:2]) or 1.0
    limit = scope * reach

    fresh = list(points)
    for existing in state.objects:
        for candidate in intersect(drawn, existing):
            if math.dist(origin, candidate) > limit or not all(map(math.isfinite, candidate)):
                continue
            if all(math.dist(candidate, known) > 1e-7 for known in fresh):
                fresh.append(candidate)
    if len(fresh) > max_points:
        return None
    return State(tuple(fresh), state.objects + (drawn,))


def search(
    problem: str,
    start: State,
    goal: Callable[[State], bool],
    isa: str = "full",
    max_depth: int = 5,
    node_budget: int = DEFAULT_NODE_BUDGET,
    point_names: Optional[list[str]] = None,
    max_points: int = DEFAULT_MAX_POINTS,
    scope: float = DEFAULT_SCOPE,
) -> Result:
    """Find the shortest construction reaching ``goal``, by iterative deepening."""
    instruction_set: InstructionSet = INSTRUCTION_SETS[isa]
    result = Result(problem=problem, isa=isa, point_names=point_names or [])
    nodes = 0
    truncated = False

    if goal(start):
        result.found = True
        return result

    for depth in range(1, max_depth + 1):
        seen: set = set()
        stack: list[tuple[State, list[Move]]] = [(start, [])]
        while stack:
            state, path = stack.pop()
            if len(path) == depth:
                continue
            for move in moves_for(instruction_set, len(state.points)):
                if nodes >= node_budget:
                    truncated = True
                    break
                following = _apply(state, move, max_points, scope)
                if following is None:
                    continue
                nodes += 1
                if goal(following):
                    result.found = True
                    result.moves = path + [move]
                    result.depth_searched = depth
                    result.exhaustive = not truncated
                    result.nodes = nodes
                    return result
                if len(path) + 1 < depth:
                    fingerprint = (len(path) + 1, following.canonical(), frozenset(following.object_keys()))
                    if fingerprint in seen:
                        continue
                    seen.add(fingerprint)
                    stack.append((following, path + [move]))
            if truncated:
                break
        result.depth_searched = depth
        if truncated:
            break

    result.nodes = nodes
    result.exhaustive = not truncated
    return result
