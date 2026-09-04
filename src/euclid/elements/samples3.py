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
from .samples import frame3, nonzero, rational_rotation, rational_rotation3, scalar

__all__ = [
    "circle_in_space",
    "cone_figure",
    "corner_and_arms",
    "cube_corner",
    "cutting_lines",
    "four_in_space",
    "parallel_lines3",
    "plane_and_point",
    "polygon_base",
    "right_angled_at_origin",
    "sphere_about",
    "tetrahedron",
    "three_in_space",
    "two_corners",
    "two_radii",
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


def corner_and_arms(rng) -> tuple:
    """A corner and the three vertices next to it: a parallelepiped's givens.

    The arms are kept well clear of one plane rather than merely out of it, so
    the solids the parallelepipedal propositions build have content that does
    not come near vanishing and the ratios between them stay legible.
    """
    move = frame3(rng)
    while True:
        corner = Point3(scalar(rng, -2, 2), scalar(rng, -2, 2), scalar(rng, -2, 2))
        arms = [Point3(corner.x + nonzero(rng, 1, 4), corner.y + scalar(rng, -2, 2),
                       corner.z + scalar(rng, -2, 2)),
                Point3(corner.x + scalar(rng, -2, 2), corner.y + nonzero(rng, 1, 4),
                       corner.z + scalar(rng, -2, 2)),
                Point3(corner.x + scalar(rng, -2, 2), corner.y + scalar(rng, -2, 2),
                       corner.z + nonzero(rng, 1, 4))]
        if not coplanar(corner, *arms):
            return tuple(move(point) for point in (corner, *arms))


def two_corners(rng) -> tuple:
    """Two parallelepipeds' worth of givens: a corner and three arms, twice."""
    return corner_and_arms(rng) + corner_and_arms(rng)


def cube_corner(rng) -> tuple:
    """A corner of a cube and the three vertices next to it.

    Built square to the axes and then moved, which keeps it a cube: the move is
    a rotation with rational entries followed by one scaling, so every edge is
    carried to an edge of the same length exactly.
    """
    move = frame3(rng)
    edge = nonzero(rng, 1, 4)
    corner = Point3(scalar(rng, -3, 3), scalar(rng, -3, 3), scalar(rng, -3, 3))
    arms = (Point3(corner.x + edge, corner.y, corner.z),
            Point3(corner.x, corner.y + edge, corner.z),
            Point3(corner.x, corner.y, corner.z + edge))
    return tuple(move(point) for point in (corner, *arms))


def polygon_base(rng) -> tuple:
    """A triangle in space and a point off its plane, for prisms and pyramids."""
    a, b, c = three_in_space(rng)
    move = frame3(rng)
    while True:
        apex = Point3(scalar(rng, -4, 4), scalar(rng, -4, 4), scalar(rng, -4, 4))
        moved = move(apex)
        if not coplanar(a, b, c, moved):
            return a, b, c, moved


def _circle_frame(rng) -> tuple:
    """A centre, a radius, and two directions of unit length in the circle's plane.

    The frame is a rotation of space with rational entries, so its rows are
    already at right angles and already of length one: a point set out on the
    circle by a rational cosine and sine lands on it exactly, with no root taken
    anywhere.
    """
    rows = rational_rotation3(rng)
    centre = Point3(scalar(rng, -3, 3), scalar(rng, -3, 3), scalar(rng, -3, 3))
    return centre, nonzero(rng, 1, 4), rows[0], rows[1], rows[2]


def circle_in_space(rng) -> tuple:
    """A centre and four points on one circle in space.

    XII.1 is about any similar polygons inscribed in circles, not the regular
    ones the exhaustion needs, so the vertices are taken at random angles round
    the circle rather than at the divisions of a right angle.
    """
    centre, radius, first, second, _ = _circle_frame(rng)
    seen: list = []
    while len(seen) < 4:
        cosine, sine = rational_rotation(rng)
        along = tuple(radius * (cosine * first[i] + sine * second[i]) for i in range(3))
        point = Point3(centre.x + along[0], centre.y + along[1], centre.z + along[2])
        if point not in seen:
            seen.append(point)
    return (centre,) + tuple(seen)


def cone_figure(rng) -> tuple:
    """A circle in space and a point on the axis through its centre.

    Euclid's cones and cylinders are right ones -- got by carrying a right
    triangle round one of its sides -- so the point is set on the perpendicular
    through the centre, and the same figure serves for both.
    """
    centre, radius, first, _, normal = _circle_frame(rng)
    height = nonzero(rng, 1, 4)
    edge = Point3(centre.x + radius * first[0], centre.y + radius * first[1],
                  centre.z + radius * first[2])
    apex = Point3(centre.x + height * normal[0], centre.y + height * normal[1],
                  centre.z + height * normal[2])
    return centre, edge, apex


def two_radii(rng) -> tuple:
    """One centre, a point on the greater circle, and one on the lesser.

    The lesser is kept well inside the greater, because XII.16 and XII.17 ask
    for a figure that clears it and the stage at which one does is what the
    proposition reports.
    """
    centre, radius, first, second, _ = _circle_frame(rng)
    inner = radius * Fraction(rng.choice([1, 2, 3]), 5)
    greater = Point3(centre.x + radius * first[0], centre.y + radius * first[1],
                     centre.z + radius * first[2])
    lesser = Point3(centre.x + inner * second[0], centre.y + inner * second[1],
                    centre.z + inner * second[2])
    return centre, greater, lesser


def sphere_about(rng) -> tuple:
    """A centre and a point on the sphere about it.

    The radius is rational, so the diameter is rational too -- which is what
    XIII.16 and XIII.17 need before they can call a side minor or apotome, since
    Book X names an irrational line only against an assigned rational one.
    """
    centre, radius, first, _, _ = _circle_frame(rng)
    return centre, Point3(centre.x + radius * first[0],
                          centre.y + radius * first[1],
                          centre.z + radius * first[2])
