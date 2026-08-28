"""The instruction set: Euclid's postulates as executable primitives.

Three operations generate everything in the *Elements*:

======================  =====================================================
``line(P, Q)``          Postulate 1 -- draw the straight line through P and Q
``circle(O, A)``        Postulate 3 -- draw the circle with centre O through A
``meet(u, v)``          not a postulate at all
======================  =====================================================

That third row is the interesting one.  Euclid draws two circles and then
*names* their intersection point, but no postulate says two circles ever meet.
Rather than paper over the gap we make it visible: every intersection is
recorded as an event, tagged with whether the postulates actually license it,
and the assumption ledger reads those tags back out.

Intersections come back in a deterministic, geometrically meaningful order --
along the line's own direction for line-circle, and left-then-right of the
directed centre line for circle-circle -- so propositions can say "the apex
above AB" without hidden coin flips.
"""

from __future__ import annotations

from typing import Union

from ..kernel.field import Constructible, is_zero, sign, sqrt
from .objects import Circle, Line, Point
from .trace import IntersectionEvent, Move, broadcast_intersection, broadcast_move

__all__ = [
    "Figure",
    "GeometryError",
    "circle",
    "circle_with_radius2",
    "free_point",
    "line",
    "meet",
    "meet_one",
    "on_side",
    "posit",
]

Shape = Union[Line, Circle]


def _record(move: Move) -> Move:
    return broadcast_move(move)


def free_point(x, y, label: str = "") -> Point:
    """Posit a point.  Euclid's givens enter the machine here."""
    point = Point(x, y, label)
    _record(Move("free", label or repr(point), obj=point, note="given"))
    return point


def posit(point: Point, label: str) -> Point:
    """Name a point that was derived rather than drawn (midpoints, feet, ...)."""
    named = point.named(label)
    _record(Move("derived", label, obj=named))
    return named


def line(p: Point, q: Point, label: str = "") -> Line:
    """Postulate 1: to draw a straight line from any point to any point."""
    drawn = Line.through(p, q, label or f"{p.label}{q.label}")
    _record(Move("line", drawn.label, obj=drawn, inputs=(p, q), postulate="Post.1"))
    return drawn


def circle(centre: Point, through: Point, label: str = "") -> Circle:
    """Postulate 3: to describe a circle with any centre and radius."""
    drawn = Circle.centred(centre, through, label or f"({centre.label}{through.label})")
    _record(Move("circle", drawn.label, obj=drawn, inputs=(centre, through), postulate="Post.3"))
    return drawn


def circle_with_radius2(centre: Point, r2: Constructible, label: str = "") -> Circle:
    drawn = Circle(centre, r2, None, label or f"({centre.label})")
    _record(Move("circle", drawn.label, obj=drawn, inputs=(centre,), postulate="Post.3"))
    return drawn


# ---------------------------------------------------------------------------
# intersections
# ---------------------------------------------------------------------------


def _line_line(u: Line, v: Line) -> list[Point]:
    determinant = u.a * v.b - u.b * v.a
    if is_zero(determinant):
        return []
    x = (u.c * v.b - u.b * v.c) / determinant
    y = (u.a * v.c - u.c * v.a) / determinant
    return [Point(x, y)]


def _line_circle(u: Line, k: Circle) -> list[Point]:
    denominator = u.a * u.a + u.b * u.b
    offset = u.a * k.centre.x + u.b * k.centre.y - u.c
    foot = Point(
        k.centre.x - u.a * offset / denominator,
        k.centre.y - u.b * offset / denominator,
    )
    discriminant = k.r2 - offset * offset / denominator
    status = sign(discriminant)
    if status < 0:
        return []
    if status == 0:
        return [foot]
    half_chord = sqrt(discriminant / denominator)
    first = Point(foot.x - u.b * half_chord, foot.y + u.a * half_chord)
    second = Point(foot.x + u.b * half_chord, foot.y - u.a * half_chord)
    # order along the line's own direction, so the answer does not depend on
    # which way the coefficients happened to be normalised
    dx, dy = u.direction()
    ordering = (second.x - first.x) * dx + (second.y - first.y) * dy
    return [first, second] if sign(ordering) > 0 else [second, first]


def _circle_circle(j: Circle, k: Circle) -> list[Point]:
    if j.centre == k.centre:
        return []
    # Subtracting the two circle equations leaves the radical axis, a line.
    a = 2 * (k.centre.x - j.centre.x)
    b = 2 * (k.centre.y - j.centre.y)
    c = (
        j.r2
        - k.r2
        + (k.centre.x * k.centre.x + k.centre.y * k.centre.y)
        - (j.centre.x * j.centre.x + j.centre.y * j.centre.y)
    )
    radical = Line(a, b, c, j.centre, k.centre, "radical")
    points = _line_circle(radical, j)
    if len(points) < 2:
        return points
    # order: the point to the left of the directed centre line comes first
    dx, dy = k.centre.x - j.centre.x, k.centre.y - j.centre.y
    first = points[0]
    cross = dx * (first.y - j.centre.y) - dy * (first.x - j.centre.x)
    return points if sign(cross) > 0 else [points[1], points[0]]


def meet(u: Shape, v: Shape, labels: str = "") -> list[Point]:
    """Intersect two drawn objects, recording the continuity debt incurred."""
    if isinstance(u, Line) and isinstance(v, Line):
        kind, guaranteed, detail = "line-line", True, "Postulate 5 licenses non-parallel lines to meet"
        points = _line_line(u, v)
    elif isinstance(u, Circle) and isinstance(v, Circle):
        kind, guaranteed = "circle-circle", False
        detail = "no postulate asserts that two circles meet"
        points = _circle_circle(u, v)
    else:
        if isinstance(u, Circle):
            u, v = v, u
        kind, guaranteed = "line-circle", False
        detail = "no postulate asserts that a line meets a circle"
        points = _line_circle(u, v)

    broadcast_intersection(IntersectionEvent(kind, len(points), guaranteed, detail))
    for index, point in enumerate(points):
        if index < len(labels):
            points[index] = point.named(labels[index])
    return points


def meet_one(u: Shape, v: Shape, label: str = "") -> Point:
    """Intersect where exactly one point is expected."""
    points = meet(u, v, label)
    if len(points) != 1:
        raise GeometryError(f"expected a single intersection, found {len(points)}")
    return points[0]


class GeometryError(Exception):
    """A construction could not be carried out on this configuration."""


def on_side(points: list[Point], reference: Line, same_as: Point) -> Point:
    """Select the intersection lying on the same side of ``reference`` as ``same_as``."""
    wanted = reference.side_of(same_as)
    for point in points:
        if reference.side_of(point) == wanted:
            return point
    raise GeometryError("no intersection on the requested side")


class Figure:
    """A bag of drawn objects, used by the renderer and the search engine."""

    def __init__(self) -> None:
        self.points: list[Point] = []
        self.lines: list[Line] = []
        self.circles: list[Circle] = []

    def add(self, item) -> None:
        if isinstance(item, Point) and item not in self.points:
            self.points.append(item)
        elif isinstance(item, Line) and item not in self.lines:
            self.lines.append(item)
        elif isinstance(item, Circle) and item not in self.circles:
            self.circles.append(item)
