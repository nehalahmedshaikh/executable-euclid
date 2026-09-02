"""Exact tests on points, lines, planes and spheres in space.

Every one of these is a polynomial in the coordinates, so it decides rather than
estimates: two points are the same point or they are not, four points are
coplanar or they are not.  Nothing here takes a square root, which is what keeps
a solid figure inside the field its coordinates were built in -- distances are
compared as squares, exactly as they are in the plane.
"""

from __future__ import annotations

from ..kernel.field import Constructible, is_zero, sign
from ..plane.trace import record_predicate
from .objects import Line3, Plane, Point3, Sphere, vector_between

__all__ = [
    "collinear3",
    "coplanar",
    "cross3",
    "dot3",
    "eq_len3",
    "inside_sphere",
    "len2",
    "on_line3",
    "on_plane",
    "on_sphere",
    "parallel_planes",
    "perpendicular_planes",
    "same_side_of_plane",
    "volume6",
]


def dot3(first: tuple, second: tuple) -> Constructible:
    return first[0] * second[0] + first[1] * second[1] + first[2] * second[2]


def cross3(first: tuple, second: tuple) -> tuple:
    return (first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0])


def len2(p: Point3, q: Point3) -> Constructible:
    """The square of the distance.  The square, because the distance itself is
    usually irrational and carrying it would extend the field for every join."""
    step = vector_between(p, q)
    return dot3(step, step)


def eq_len3(a: Point3, b: Point3, c: Point3, d: Point3) -> bool:
    return record_predicate("eq_len3", len2(a, b) == len2(c, d))


def volume6(a: Point3, b: Point3, c: Point3, d: Point3) -> Constructible:
    """Six times the signed volume of the tetrahedron: the scalar triple product.

    Zero exactly when the four points are coplanar, and its sign says which side
    of the plane *abc* the point *d* falls on.  It is to space what the signed
    area of a triangle is to the plane, and it does the same work.
    """
    return dot3(cross3(vector_between(a, b), vector_between(a, c)),
                vector_between(a, d))


def collinear3(a: Point3, b: Point3, c: Point3) -> bool:
    first, second = vector_between(a, b), vector_between(a, c)
    across = cross3(first, second)
    return record_predicate(
        "collinear3", all(is_zero(component) for component in across))


def coplanar(a: Point3, b: Point3, c: Point3, d: Point3) -> bool:
    return record_predicate("coplanar", is_zero(volume6(a, b, c, d)))


def on_plane(point: Point3, plane: Plane) -> bool:
    return record_predicate("on_plane", is_zero(plane.evaluate(point)))


def on_line3(point: Point3, line: Line3) -> bool:
    return record_predicate("on_line3", line.holds(point))


def on_sphere(point: Point3, sphere: Sphere) -> bool:
    return record_predicate("on_sphere", is_zero(sphere.evaluate(point)))


def inside_sphere(point: Point3, sphere: Sphere) -> bool:
    return record_predicate("inside_sphere", sign(sphere.evaluate(point)) < 0)


def same_side_of_plane(first: Point3, second: Point3, plane: Plane) -> bool:
    """Both strictly on one side.  A point *on* the plane is on neither side,
    which is the reading that makes this the plane's ``same_side``."""
    here, there = plane.side_of(first), plane.side_of(second)
    return record_predicate("same_side_of_plane",
                            here != 0 and here == there,
                            order_sensitive=False)


def parallel_planes(first: Plane, second: Plane) -> bool:
    """Normals in one direction.  Two planes so placed never meet, unless they
    are the same plane -- which is why XI.3 has something to prove."""
    return record_predicate(
        "parallel_planes",
        all(is_zero(component) for component in cross3(first.normal(), second.normal())))


def perpendicular_planes(first: Plane, second: Plane) -> bool:
    return record_predicate("perpendicular_planes",
                            is_zero(dot3(first.normal(), second.normal())))
