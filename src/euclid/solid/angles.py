"""Lengths and angles in space.

An angle in space has no orientation to speak of.  In the plane a rotation has a
sense, and :class:`euclid.plane.angles.Angle` carries ``(cos, sin)`` so that the
sense survives; in space the sense of an angle depends on which way you look at
it, so only the cosine is well defined and only unoriented angles are offered.
Comparing them compares cosines, which is exact and needs no arc.

The dihedral angle between two planes is the angle between their normals, taken
the same way.  XI Def. 6 defines it by drawing perpendiculars to the common
section, and the two agree: the perpendiculars span the same plane the normals
do.
"""

from __future__ import annotations

from ..kernel.field import Constructible, is_zero, sqrt
from .objects import Plane, Point3, vector_between
from .predicates import cross3, dot3

__all__ = ["SolidAngle", "angle_at3", "dihedral", "length3"]


def length3(a: Point3, b: Point3) -> Constructible:
    """The exact distance ``|ab|`` in space.

    The witness names the three components, so the root is admitted as a
    hypotenuse rather than as a general square root: measuring a length in space
    is the same act as measuring one in the plane, and the field ladder should
    say so.  See :class:`euclid.kernel.field.Pythagorean`.
    """
    dx, dy, dz = vector_between(a, b)
    return sqrt(dx * dx + dy * dy + dz * dz, witness=(dx, dy, dz))


class SolidAngle:
    """An unoriented angle in ``[0, pi]``, stored as its cosine.

    No sine, because in space there is no side to be on: a rotation through this
    angle can be taken either way round and nothing in the figure prefers one.
    Two such angles are equal when their cosines are, which is exact.
    """

    __slots__ = ("cos",)

    def __init__(self, cosine: Constructible) -> None:
        self.cos = cosine

    @classmethod
    def between_rays(cls, vertex: Point3, first: Point3, second: Point3) -> "SolidAngle":
        u = vector_between(vertex, first)
        v = vector_between(vertex, second)
        squared = dot3(u, u) * dot3(v, v)
        if is_zero(squared):
            raise ValueError("an angle needs two rays of positive length")
        # cos = u.v / (|u||v|), and the product of the two lengths is one root
        # rather than two: its radicand is a square times a square, so it is
        # admitted with the witness the product itself provides.
        scale = sqrt(squared, witness=_witness_for(u, v))
        return cls(dot3(u, v) / scale)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SolidAngle) and self.cos == other.cos

    def __hash__(self) -> int:
        return hash(("SolidAngle", self.cos))

    def __lt__(self, other: "SolidAngle") -> bool:
        # Cosine decreases as the angle grows, so the comparison reverses.
        return other.cos < self.cos

    def __repr__(self) -> str:
        return f"SolidAngle(cos={self.cos})"


def _witness_for(u: tuple, v: tuple) -> tuple:
    """Components whose squares sum to ``|u|^2 |v|^2``.

    Lagrange's identity: ``|u|^2 |v|^2 = (u.v)^2 + |u x v|^2``, so the dot
    product and the three components of the cross product are a witness, and the
    product of two lengths stays inside the Pythagorean field exactly as each
    length does.
    """
    across = cross3(u, v)
    return (dot3(u, v),) + across


def angle_at3(first: Point3, vertex: Point3, second: Point3) -> SolidAngle:
    return SolidAngle.between_rays(vertex, first, second)


def dihedral(first: Plane, second: Plane) -> SolidAngle:
    """The angle between two planes, by XI Def. 6.

    Taken between the normals, which span the same plane as the perpendiculars
    Euclid draws to the common section.
    """
    u, v = first.normal(), second.normal()
    squared = dot3(u, u) * dot3(v, v)
    if is_zero(squared):
        raise ValueError("a dihedral angle needs two genuine planes")
    return SolidAngle(dot3(u, v) / sqrt(squared, witness=_witness_for(u, v)))
