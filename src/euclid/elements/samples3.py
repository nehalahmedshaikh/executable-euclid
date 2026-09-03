"""Configurations in space for the solid books to be checked on.

Every one of these hands back a figure the proposition's hypotheses accept, and
every one is moved by :func:`euclid.elements.samples.frame3` before it is
returned.  The move matters: a proposition that holds only for the figure as it
was written down has not been tested, and the rotations of space used here are
exact, so moving it cannot introduce the rounding the whole project is built to
avoid.
"""

from __future__ import annotations

from fractions import Fraction

from ..solid.objects import Point3
from ..solid.predicates import collinear3, coplanar
from .samples import frame3, nonzero, scalar

__all__ = [
    "cutting_lines",
    "four_in_space",
    "parallel_lines3",
    "plane_and_point",
    "right_angled_at_origin",
    "tetrahedron",
    "three_in_space",
]


def three_in_space(rng) -> tuple:
    """Three points that are not in a straight line, so they describe a plane."""
    move = frame3(rng)
    while True:
        points = [Point3(scalar(rng, -4, 4), scalar(rng, -4, 4), scalar(rng, -4, 4))
                  for _ in range(3)]
        if not collinear3(*points):
            return tuple(move(point) for point in points)


def four_in_space(rng) -> tuple:
    """Four points not in one plane: a genuine solid figure."""
    move = frame3(rng)
    while True:
        points = [Point3(scalar(rng, -4, 4), scalar(rng, -4, 4), scalar(rng, -4, 4))
                  for _ in range(4)]
        if not coplanar(*points):
            return tuple(move(point) for point in points)


def tetrahedron(rng) -> tuple:
    """Four points with a vertex at the origin, for the solid-angle propositions."""
    move = frame3(rng)
    while True:
        corner = Point3(0, 0, 0)
        arms = [Point3(nonzero(rng, 1, 4) * rng.choice([1, -1]),
                       scalar(rng, -3, 3), scalar(rng, -3, 3)) for _ in range(3)]
        if not coplanar(corner, *arms):
            return tuple(move(point) for point in (corner, *arms))


def right_angled_at_origin(rng) -> tuple:
    """A line at right angles to two lines that cut one another (XI.4's figure).

    The upright is the common perpendicular of two directions in a plane, so it
    is built as their cross product: exact, and at right angles to both by
    construction rather than by search.
    """
    move = frame3(rng)
    first = (nonzero(rng, 1, 3), scalar(rng, -3, 3), Fraction(0))
    second = (scalar(rng, -3, 3), nonzero(rng, 1, 3), Fraction(0))
    upright = (first[1] * second[2] - first[2] * second[1],
               first[2] * second[0] - first[0] * second[2],
               first[0] * second[1] - first[1] * second[0])
    if all(component == 0 for component in upright):
        first, second = (Fraction(1), Fraction(0), Fraction(0)), (Fraction(0), Fraction(1), Fraction(0))
        upright = (Fraction(0), Fraction(0), Fraction(1))
    centre = Point3(0, 0, 0)
    return tuple(move(point) for point in (
        centre, Point3(*first), Point3(*second), Point3(*upright)))


def cutting_lines(rng) -> tuple:
    """Two lines through one point, which XI.2 says lie in one plane."""
    move = frame3(rng)
    corner = Point3(0, 0, 0)
    while True:
        first = Point3(scalar(rng, -4, 4), scalar(rng, -4, 4), scalar(rng, -4, 4))
        second = Point3(scalar(rng, -4, 4), scalar(rng, -4, 4), scalar(rng, -4, 4))
        if not collinear3(corner, first, second):
            return tuple(move(point) for point in (corner, first, second))


def parallel_lines3(rng) -> tuple:
    """Two parallel lines in space, given by an end of each and their direction."""
    move = frame3(rng)
    step = Point3(nonzero(rng, 1, 4), scalar(rng, -3, 3), scalar(rng, -3, 3))
    first = Point3(scalar(rng, -3, 3), scalar(rng, -3, 3), scalar(rng, -3, 3))
    while True:
        second = Point3(scalar(rng, -3, 3), scalar(rng, -3, 3), scalar(rng, -3, 3))
        if not collinear3(first, second, first + step):
            break
    return tuple(move(point) for point in
                 (first, first + step, second, second + step))


def plane_and_point(rng) -> tuple:
    """Three points describing a plane, and a fourth off it."""
    a, b, c = three_in_space(rng)
    move = frame3(rng)
    while True:
        away = Point3(scalar(rng, -4, 4), scalar(rng, -4, 4), scalar(rng, -4, 4))
        if not coplanar(a, b, c, away):
            return a, b, c, move(away)
