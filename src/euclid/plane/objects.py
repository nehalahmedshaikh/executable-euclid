"""Points, lines and circles with exactly constructible coordinates.

Two representation choices matter:

* a line is stored as ``a*x + b*y = c`` with exact coefficients, normalised so
  that equality of lines is structural;
* a circle stores its **squared** radius.  Radii themselves are usually
  irrational, and carrying ``r^2`` keeps circles inside the current field
  instead of forcing a tower extension every time one is drawn.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Optional, Union

from ..kernel.field import Constructible, is_zero, sign, to_float

__all__ = ["Circle", "Line", "Point", "coerce", "midpoint_of", "vector_between"]

Scalar = Union[int, Fraction, "Constructible"]


def coerce(value: Scalar) -> Constructible:
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        raise TypeError("coordinates must be exact; pass a Fraction or int, not a float")
    return value


class Point:
    __slots__ = ("x", "y", "label", "_hash")

    def __init__(self, x: Scalar, y: Scalar, label: str = "") -> None:
        self.x = coerce(x)
        self.y = coerce(y)
        self.label = label
        self._hash: Optional[int] = None

    def named(self, label: str) -> "Point":
        return Point(self.x, self.y, label)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((self.x, self.y))
        return self._hash

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x - other.x, self.y - other.y)

    def scaled(self, factor: Scalar) -> "Point":
        factor = coerce(factor)
        return Point(self.x * factor, self.y * factor)

    def as_floats(self) -> tuple[float, float]:
        return to_float(self.x), to_float(self.y)

    def __repr__(self) -> str:
        name = f"{self.label}=" if self.label else ""
        fx, fy = self.as_floats()
        return f"{name}({fx:.6g}, {fy:.6g})"


def vector_between(start: Point, end: Point) -> tuple[Constructible, Constructible]:
    return end.x - start.x, end.y - start.y


def midpoint_of(p: Point, q: Point) -> Point:
    half = Fraction(1, 2)
    return Point((p.x + q.x) * half, (p.y + q.y) * half)


class Line:
    """The line ``a*x + b*y = c``, remembering the two points that defined it."""

    __slots__ = ("a", "b", "c", "p", "q", "label", "_hash")

    def __init__(self, a: Scalar, b: Scalar, c: Scalar, p: Point, q: Point, label: str = "") -> None:
        a, b, c = coerce(a), coerce(b), coerce(c)
        # Normalise so that structurally equal lines compare equal: scale the
        # first nonzero coefficient to 1.
        pivot = a if not is_zero(a) else b
        self.a, self.b, self.c = a / pivot, b / pivot, c / pivot
        self.p, self.q = p, q
        self.label = label
        self._hash: Optional[int] = None

    @classmethod
    def through(cls, p: Point, q: Point, label: str = "") -> "Line":
        if p == q:
            raise ValueError("Postulate 1 needs two distinct points")
        a = q.y - p.y
        b = p.x - q.x
        c = a * p.x + b * p.y
        return cls(a, b, c, p, q, label)

    def direction(self) -> tuple[Constructible, Constructible]:
        return vector_between(self.p, self.q)

    def evaluate(self, point: Point) -> Constructible:
        """``a*x + b*y - c``: zero on the line, and its sign names the side."""
        return self.a * point.x + self.b * point.y - self.c

    def side_of(self, point: Point) -> int:
        return sign(self.evaluate(point))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Line)
            and self.a == other.a
            and self.b == other.b
            and self.c == other.c
        )

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((self.a, self.b, self.c))
        return self._hash

    def __repr__(self) -> str:
        tag = f" [{self.label}]" if self.label else ""
        return f"Line({self.p.label or self.p}-{self.q.label or self.q}){tag}"


class Circle:
    """Circle of centre ``centre`` and squared radius ``r2``."""

    __slots__ = ("centre", "r2", "through", "label", "_hash")

    def __init__(self, centre: Point, r2: Scalar, through: Optional[Point] = None, label: str = "") -> None:
        self.centre = centre
        self.r2 = coerce(r2)
        if sign(self.r2) <= 0:
            raise ValueError("Postulate 3 needs a circle of positive radius")
        self.through = through
        self.label = label
        self._hash: Optional[int] = None

    @classmethod
    def centred(cls, centre: Point, through: Point, label: str = "") -> "Circle":
        dx, dy = vector_between(centre, through)
        return cls(centre, dx * dx + dy * dy, through, label)

    def evaluate(self, point: Point) -> Constructible:
        """Zero on the circle, negative inside, positive outside."""
        dx, dy = vector_between(self.centre, point)
        return dx * dx + dy * dy - self.r2

    def radius_float(self) -> float:
        return to_float(self.r2) ** 0.5

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Circle) and self.centre == other.centre and self.r2 == other.r2

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((self.centre, self.r2))
        return self._hash

    def __repr__(self) -> str:
        tag = f" [{self.label}]" if self.label else ""
        return f"Circle(centre={self.centre}, r^2={self.r2}){tag}"
