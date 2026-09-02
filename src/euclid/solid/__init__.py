"""Solid geometry: a sibling of :mod:`euclid.plane`, not a generalisation of it.

Euclid has no postulates for space.  Postulates 1 to 5 are about the plane, and
Book XI opens with definitions and then argues.  So where the plane primitives
each carry a postulate tag, every primitive here carries none and says so, and
the assumption ledger counts what that costs.
"""

from .objects import Line3, Plane, Point3, Sphere, midpoint_of, vector_between
from .predicates import (
    collinear3,
    coplanar,
    cross3,
    dot3,
    eq_len3,
    inside_sphere,
    len2,
    on_line3,
    on_plane,
    on_sphere,
    parallel_planes,
    perpendicular_planes,
    same_side_of_plane,
    volume6,
)

__all__ = [
    "Line3",
    "Plane",
    "Point3",
    "Sphere",
    "collinear3",
    "coplanar",
    "cross3",
    "dot3",
    "eq_len3",
    "inside_sphere",
    "len2",
    "midpoint_of",
    "on_line3",
    "on_plane",
    "on_sphere",
    "parallel_planes",
    "perpendicular_planes",
    "same_side_of_plane",
    "vector_between",
    "volume6",
]
