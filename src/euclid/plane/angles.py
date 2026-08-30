"""Exact angles.

Euclid adds and subtracts angles constantly -- "the three angles of a triangle
equal two right angles", "the exterior angle equals the sum of the two interior
and opposite" -- and none of that survives a predicate language that can only
say *equal* and *unequal*.  So angles get a real value type.

An angle is carried as the point ``(cos, sin)`` it cuts on the unit circle.
Both coordinates are constructible: ``cos = (u . v) / (|u| |v|)`` costs one
square root per side, which the kernel takes in its stride.  Addition is then
the ordinary rotation formula, and every classical angle-sum statement becomes
an exact identity rather than a numerical coincidence:

    angle(A,B,C) + angle(B,C,A) + angle(C,A,B) == STRAIGHT

holds with ``cos`` exactly ``-1`` and ``sin`` exactly ``0``.

Angles compare by their position in ``[0, 2*pi)``, so sums that overshoot a
straight angle still order correctly -- which is what I.17 and I.32 need.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import Constructible, is_zero, sign, sqrt
from .objects import Point, vector_between

__all__ = ["Angle", "RIGHT", "STRAIGHT", "angle_at", "length"]


def length(a: Point, b: Point) -> Constructible:
    """The exact distance ``|ab|``.  Costs one tower level unless it is rational."""
    dx, dy = vector_between(a, b)
    # The witness says this root is a hypotenuse, which is what a Pythagorean
    # field admits. Measuring a length is a different act from intersecting two
    # circles, and only the second needs continuity; carrying the pair here is
    # what lets euclid.measure.fields tell them apart.
    return sqrt(dx * dx + dy * dy, witness=(dx, dy))


class Angle:
    """A magnitude in ``[0, 2*pi)``, stored as ``(cos, sin)`` on the unit circle."""

    __slots__ = ("cos", "sin")

    def __init__(self, cosine: Constructible, sine: Constructible) -> None:
        self.cos = cosine
        self.sin = sine

    # -- construction -------------------------------------------------------
    @classmethod
    def between_rays(cls, vertex: Point, first: Point, second: Point) -> "Angle":
        """The unoriented angle ``first-vertex-second``, which lies in ``[0, pi]``."""
        ux, uy = vector_between(vertex, first)
        vx, vy = vector_between(vertex, second)
        scale = (sqrt(ux * ux + uy * uy, witness=(ux, uy))
                 * sqrt(vx * vx + vy * vy, witness=(vx, vy)))
        if is_zero(scale):
            raise ValueError("an angle needs two rays of positive length")
        cross = ux * vy - uy * vx
        if sign(cross) < 0:
            cross = -cross
        return cls((ux * vx + uy * vy) / scale, cross / scale)

    # -- arithmetic ---------------------------------------------------------
    def __add__(self, other: "Angle") -> "Angle":
        return Angle(
            self.cos * other.cos - self.sin * other.sin,
            self.sin * other.cos + self.cos * other.sin,
        )

    def __sub__(self, other: "Angle") -> "Angle":
        return Angle(
            self.cos * other.cos + self.sin * other.sin,
            self.sin * other.cos - self.cos * other.sin,
        )

    def doubled(self) -> "Angle":
        return self + self

    # -- ordering in [0, 2*pi) ---------------------------------------------
    def _sector(self) -> int:
        s = sign(self.sin)
        if s > 0:
            return 1
        if s < 0:
            return 3
        return 0 if sign(self.cos) > 0 else 2

    def _key(self):
        sector = self._sector()
        if sector == 1:
            return sector, -self.cos
        if sector == 3:
            return sector, self.cos
        return sector, Fraction(0)

    def _compare(self, other: "Angle") -> int:
        left, right = self._key(), other._key()
        if left[0] != right[0]:
            return -1 if left[0] < right[0] else 1
        difference = sign(left[1] - right[1])
        return difference

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Angle) and self.cos == other.cos and self.sin == other.sin

    def __hash__(self) -> int:
        return hash((self.cos, self.sin))

    def __lt__(self, other: "Angle") -> bool:
        return self._compare(other) < 0

    def __le__(self, other: "Angle") -> bool:
        return self._compare(other) <= 0

    def __gt__(self, other: "Angle") -> bool:
        return self._compare(other) > 0

    def __ge__(self, other: "Angle") -> bool:
        return self._compare(other) >= 0

    # -- reporting ----------------------------------------------------------
    def degrees(self) -> float:
        from math import atan2, degrees, pi

        from ..kernel.field import to_float

        value = atan2(to_float(self.sin), to_float(self.cos))
        return degrees(value if value >= 0 else value + 2 * pi)

    def __repr__(self) -> str:
        return f"Angle({self.degrees():.4f} deg)"


RIGHT = Angle(Fraction(0), Fraction(1))
STRAIGHT = Angle(Fraction(-1), Fraction(0))


def angle_at(first: Point, vertex: Point, second: Point) -> Angle:
    """``angle_at(A, B, C)`` is Euclid's angle ABC, with its vertex in the middle."""
    return Angle.between_rays(vertex, first, second)


