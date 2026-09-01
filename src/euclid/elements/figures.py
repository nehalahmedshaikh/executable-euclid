"""Figures Books II to IV share.

Five constructions are wanted by more than one of the three books: the square
raised on a segment, the centre found from three points, the tangent at a point,
a rotation about a centre, and the foot of a perpendicular. They sat in a module
holding all three books, and splitting the books apart is what named them.
"""

from __future__ import annotations

from ..plane.construct import circle, line
from ..plane.objects import Line, Point


def _across(p: Point, q: Point) -> tuple:
    """The step from P to Q, turned through a right angle."""
    return -(q.y - p.y), q.x - p.x


def _foot_of_the_perpendicular(apex: Point, first: Point, second: Point) -> Point:
    """Where the perpendicular from the apex meets the line through the base.

    Projection is a ratio of dot products, so the foot is rational whenever the
    three given points are -- no square root, and no new level on the tower.
    """
    ux, uy = second.x - first.x, second.y - first.y
    vx, vy = apex.x - first.x, apex.y - first.y
    along = (ux * vx + uy * vy) / (ux * ux + uy * uy)
    return Point(first.x + along * ux, first.y + along * uy)


def _centre_of(a: Point, b: Point, c: Point) -> Point:
    """The point equidistant from three, found where two bisectors cross.

    Rational whenever the three are: the perpendicular bisectors are linear
    conditions, so no square root is taken and the tower does not grow.
    """
    ax, ay = b.x - a.x, b.y - a.y
    bx, by = c.x - a.x, c.y - a.y
    d = 2 * (ax * by - ay * bx)
    first = ax * ax + ay * ay
    second = bx * bx + by * by
    return Point(a.x + (by * first - ay * second) / d, a.y + (ax * second - bx * first) / d)


def _turn(centre: Point, point: Point, angle) -> Point:
    """Carry a point round a centre through an exact angle.

    An ``Angle`` is kept as its cosine and sine, both exact, so turning is a
    multiplication and nothing is approximated or rounded.
    """
    dx, dy = point.x - centre.x, point.y - centre.y
    return Point(
        centre.x + dx * angle.cos - dy * angle.sin,
        centre.y + dx * angle.sin + dy * angle.cos,
    )


def _tangent_at(centre: Point, touch: Point, label: str = "") -> Line:
    """The tangent where a radius meets the circle, at right angles to it (III.16)."""
    across = _across(centre, touch)
    return line(touch, Point(touch.x + across[0], touch.y + across[1]), label)
