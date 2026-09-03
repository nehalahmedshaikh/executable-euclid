"""The solid instruction set, and the fact that Euclid never licenses it.

Postulates 1 to 5 are postulates of the plane.  They let you draw a line between
two points, produce it, describe a circle, and they say what a right angle is
and when two lines meet.  Book XI opens with definitions and then argues: there
is no postulate that three points determine a plane, none that a sphere may be
described, and none that a line meets a plane it is not parallel to.

So every primitive here carries an empty postulate tag, and every intersection
is recorded with ``guaranteed_by_postulates=False``.  In the plane those flags
mark the places where the text leans on continuity it never states, and the
assumption ledger counts them; turned on Book XI the same machinery measures a
debt that is structural rather than incidental.  That is the finding, and it is
why the tags are empty rather than borrowed from the plane's.

Drawing this instruction set is a larger authorial act than anything in Books I
to X: in the plane Euclid names the moves and we transcribe them, and here we
choose them.  The mitigation is to refuse to hide it -- what is chosen is
recorded as unlicensed, so the choice becomes the ledger's subject instead of
its blind spot.
"""

from __future__ import annotations

from typing import Optional

from ..kernel.field import is_zero, sign, sqrt
from ..plane.construct import GeometryError
from ..plane.trace import IntersectionEvent, Move, broadcast_intersection, broadcast_move
from .objects import Line3, Plane, Point3, Sphere, vector_between
from .predicates import cross3, dot3

__all__ = [
    "line3",
    "meet_line_plane",
    "meet_line_sphere",
    "meet_planes",
    "plane_through",
    "posit3",
    "sphere_through",
]

# What licenses each move in the Elements. Empty means nothing does.
_UNLICENSED = ""


def posit3(point: Point3, label: str = "") -> Point3:
    named = point.named(label) if label else point
    broadcast_move(Move("free", named.label or "point", obj=named,
                        postulate=_UNLICENSED, note="posited in space"))
    return named


def line3(p: Point3, q: Point3, label: str = "") -> Line3:
    """Join two points in space.

    Postulate 1 is about the plane.  Reading it as if it were about space is the
    smallest of the liberties this module takes, and it is still a liberty.
    """
    drawn = Line3.through(p, q, label)
    broadcast_move(Move("line", label or "line", obj=drawn, inputs=(p, q),
                        postulate=_UNLICENSED,
                        note="Post. 1 read as if it spoke of space"))
    return drawn


def plane_through(p: Point3, q: Point3, r: Point3, label: str = "") -> Plane:
    """The plane through three points not in a straight line (XI Def. 1-2)."""
    try:
        drawn = Plane.through(p, q, r, label)
    except ValueError as problem:
        raise GeometryError(str(problem)) from None
    broadcast_move(Move("plane", label or "plane", obj=drawn, inputs=(p, q, r),
                        postulate=_UNLICENSED,
                        note="XI Def. 1-2; no postulate describes a plane"))
    return drawn


def sphere_through(centre: Point3, through: Point3, label: str = "") -> Sphere:
    """The sphere about a centre, through a point (XI Def. 14)."""
    try:
        drawn = Sphere.centred(centre, through, label)
    except ValueError as problem:
        raise GeometryError(str(problem)) from None
    broadcast_move(Move("sphere", label or "sphere", obj=drawn,
                        inputs=(centre, through), postulate=_UNLICENSED,
                        note="XI Def. 14; no postulate describes a sphere"))
    return drawn


def _record(kind: str, count: int, detail: str) -> None:
    broadcast_intersection(
        IntersectionEvent(kind, count, guaranteed_by_postulates=False, detail=detail))


def meet_planes(first: Plane, second: Plane) -> Line3:
    """Where two planes cut, they cut in a straight line.

    This is XI.3, which Euclid *proves*.  It is offered here because Books XI to
    XIII use it constantly, and calling it is recorded as an intersection like
    any other -- a step resting on a proposition, not a primitive resting on a
    postulate.
    """
    direction = cross3(first.normal(), second.normal())
    if all(is_zero(component) for component in direction):
        raise GeometryError("parallel planes have no common section")
    base = _common_point(first, second, direction)
    _record("plane-plane", 1, "no postulate asserts that two planes meet")
    onward = Point3(base.x + direction[0], base.y + direction[1], base.z + direction[2])
    return Line3(base, onward, "the common section")


def _common_point(first: Plane, second: Plane, direction: tuple) -> Point3:
    """One point of the common section, found exactly.

    Taking the point of the section nearest the origin keeps the arithmetic to
    the coefficients already in hand and needs no square root: it is a rational
    combination of the two normals.
    """
    n1, n2 = first.normal(), second.normal()
    across = dot3(direction, direction)
    # The order of each cross product is the whole of this: reversing one
    # negates the point, and a point through the origin is its own negative --
    # which is why two planes through the origin verified it and nothing else
    # would have.
    left = cross3(n2, direction)
    right = cross3(direction, n1)
    return Point3((first.d * left[0] + second.d * right[0]) / across,
                  (first.d * left[1] + second.d * right[1]) / across,
                  (first.d * left[2] + second.d * right[2]) / across)


def meet_line_plane(line: Line3, plane: Plane) -> Point3:
    """Where a line cuts a plane.  Nothing in the Elements says it does."""
    step = line.direction()
    along = dot3(plane.normal(), step)
    if is_zero(along):
        raise GeometryError("the line is parallel to the plane, or lies in it")
    parameter = -plane.evaluate(line.p) / along
    _record("line-plane", 1, "no postulate asserts that a line meets a plane")
    return line.at(parameter)


def meet_line_sphere(line: Line3, sphere: Sphere) -> list:
    """Where a line cuts a sphere: nought, one or two points.

    The same continuity the plane needs for a line and a circle, and with as
    little said about it -- less, since here not even a postulate about circles
    is in reach.
    """
    step = line.direction()
    from_centre = vector_between(sphere.centre, line.p)
    a = dot3(step, step)
    b = 2 * dot3(step, from_centre)
    c = dot3(from_centre, from_centre) - sphere.r2
    discriminant = b * b - 4 * a * c
    if sign(discriminant) < 0:
        raise GeometryError("the line does not reach the sphere")
    if is_zero(discriminant):
        _record("line-sphere", 1, "the line touches the sphere")
        return [line.at(-b / (2 * a))]
    root = sqrt(discriminant)
    _record("line-sphere", 2, "no postulate asserts that a line meets a sphere")
    return [line.at((-b - root) / (2 * a)), line.at((-b + root) / (2 * a))]
