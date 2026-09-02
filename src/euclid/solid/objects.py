"""Points, planes, lines and spheres in space, with exact coordinates.

A sibling of :mod:`euclid.plane.objects` rather than a generalisation of it.
Widening ``Point`` to n coordinates would touch four hundred verified
propositions and every diagram; nothing here touches any of them.

Two of the three representations carry straight over, and it is worth saying
which way round:

* **A plane is a line promoted.**  ``Line`` is stored as ``a*x + b*y = c``,
  normalised so equality is structural, with ``evaluate`` giving the signed
  quantity whose sign names the side.  That is the codimension-1 trick, and in
  space it belongs to the *plane*, not the line: same normalisation, same
  equality, one more coefficient.
* **A sphere is a circle unchanged.**  ``Circle`` stores a *squared* radius and
  reaches coordinates only through ``vector_between``.  Give it three
  components and ``centred``, ``evaluate`` and the positive-radius guard all
  carry over as they stand.

``Line3`` cannot follow ``Line``.  A line in space has no sides and no implicit
equation, so it is stored as the two points that made it, and equality is
collinearity of both.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Optional, Union

from ..kernel.field import Constructible, is_zero, sign, to_float

__all__ = [
    "Line3",
    "Plane",
    "Point3",
    "Sphere",
    "coerce",
    "midpoint_of",
    "vector_between",
]

Scalar = Union[int, Fraction, "Constructible"]


def coerce(value: Scalar) -> Constructible:
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        raise TypeError("coordinates must be exact; pass a Fraction or int, not a float")
    return value


class Point3:
    __slots__ = ("x", "y", "z", "label", "_hash")

    def __init__(self, x: Scalar, y: Scalar, z: Scalar, label: str = "") -> None:
        self.x, self.y, self.z = coerce(x), coerce(y), coerce(z)
        self.label = label
        self._hash: Optional[int] = None

    def named(self, label: str) -> "Point3":
        return Point3(self.x, self.y, self.z, label)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Point3) and self.x == other.x
                and self.y == other.y and self.z == other.z)

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((self.x, self.y, self.z))
        return self._hash

    def __add__(self, other: "Point3") -> "Point3":
        return Point3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Point3") -> "Point3":
        return Point3(self.x - other.x, self.y - other.y, self.z - other.z)

    def scaled(self, factor: Scalar) -> "Point3":
        factor = coerce(factor)
        return Point3(self.x * factor, self.y * factor, self.z * factor)

    def as_floats(self) -> tuple[float, float, float]:
        return to_float(self.x), to_float(self.y), to_float(self.z)

    def __repr__(self) -> str:
        if self.label:
            return self.label
        return f"({self.x}, {self.y}, {self.z})"


def vector_between(start: Point3, end: Point3) -> tuple:
    return end.x - start.x, end.y - start.y, end.z - start.z


def midpoint_of(p: Point3, q: Point3) -> Point3:
    half = Fraction(1, 2)
    return Point3((p.x + q.x) * half, (p.y + q.y) * half, (p.z + q.z) * half)


class Plane:
    """The plane ``a*x + b*y + c*z = d``, remembering three points on it."""

    __slots__ = ("a", "b", "c", "d", "p", "q", "r", "label", "_hash")

    def __init__(self, a: Scalar, b: Scalar, c: Scalar, d: Scalar,
                 p: Point3, q: Point3, r: Point3, label: str = "") -> None:
        a, b, c, d = coerce(a), coerce(b), coerce(c), coerce(d)
        # Normalised exactly as a line is: the first nonzero coefficient goes to
        # one, so two planes that are the same plane compare equal.
        pivot = a if not is_zero(a) else (b if not is_zero(b) else c)
        if is_zero(pivot):
            raise ValueError("three collinear points determine no plane")
        self.a, self.b, self.c, self.d = a / pivot, b / pivot, c / pivot, d / pivot
        self.p, self.q, self.r = p, q, r
        self.label = label
        self._hash: Optional[int] = None

    @classmethod
    def through(cls, p: Point3, q: Point3, r: Point3, label: str = "") -> "Plane":
        """XI Def. 1-2 and no postulate: see :mod:`euclid.solid.construct`."""
        first, second = vector_between(p, q), vector_between(p, r)
        a = first[1] * second[2] - first[2] * second[1]
        b = first[2] * second[0] - first[0] * second[2]
        c = first[0] * second[1] - first[1] * second[0]
        if is_zero(a) and is_zero(b) and is_zero(c):
            raise ValueError("three collinear points determine no plane")
        d = a * p.x + b * p.y + c * p.z
        return cls(a, b, c, d, p, q, r, label)

    def normal(self) -> tuple:
        return self.a, self.b, self.c

    def evaluate(self, point: Point3) -> Constructible:
        """``a*x + b*y + c*z - d``: zero on the plane, its sign names the side."""
        return self.a * point.x + self.b * point.y + self.c * point.z - self.d

    def side_of(self, point: Point3) -> int:
        return sign(self.evaluate(point))

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Plane) and self.a == other.a and self.b == other.b
                and self.c == other.c and self.d == other.d)

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((self.a, self.b, self.c, self.d))
        return self._hash

    def __repr__(self) -> str:
        tag = f" [{self.label}]" if self.label else ""
        return f"Plane({self.p}-{self.q}-{self.r}){tag}"


class Line3:
    """A line in space, held as the two points that drew it.

    There is no implicit equation to normalise and no side to be on, so equality
    is not structural in the coefficients the way a plane's is: two lines are
    the same line when each holds both of the other's points.
    """

    __slots__ = ("p", "q", "label")

    def __init__(self, p: Point3, q: Point3, label: str = "") -> None:
        if p == q:
            raise ValueError("a line needs two distinct points")
        self.p, self.q = p, q
        self.label = label

    @classmethod
    def through(cls, p: Point3, q: Point3, label: str = "") -> "Line3":
        return cls(p, q, label)

    def direction(self) -> tuple:
        return vector_between(self.p, self.q)

    def holds(self, point: Point3) -> bool:
        """Whether the point lies on this line, by the vanishing of a cross product."""
        first, second = self.direction(), vector_between(self.p, point)
        return (is_zero(first[1] * second[2] - first[2] * second[1])
                and is_zero(first[2] * second[0] - first[0] * second[2])
                and is_zero(first[0] * second[1] - first[1] * second[0]))

    def at(self, parameter: Scalar) -> Point3:
        step = self.direction()
        parameter = coerce(parameter)
        return Point3(self.p.x + parameter * step[0],
                      self.p.y + parameter * step[1],
                      self.p.z + parameter * step[2])

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Line3)
                and self.holds(other.p) and self.holds(other.q))

    def __hash__(self) -> int:
        # Two equal lines must hash alike, and the points they were drawn from
        # differ, so nothing finer than a constant is available without a
        # canonical form this representation does not have.
        return hash("Line3")

    def __repr__(self) -> str:
        tag = f" [{self.label}]" if self.label else ""
        return f"Line3({self.p}-{self.q}){tag}"


class Sphere:
    """Sphere of centre ``centre`` and squared radius ``r2``."""

    __slots__ = ("centre", "r2", "through", "label", "_hash")

    def __init__(self, centre: Point3, r2: Scalar,
                 through: Optional[Point3] = None, label: str = "") -> None:
        self.centre = centre
        self.r2 = coerce(r2)
        if sign(self.r2) <= 0:
            raise ValueError("a sphere needs a positive radius")
        self.through = through
        self.label = label
        self._hash: Optional[int] = None

    @classmethod
    def centred(cls, centre: Point3, through: Point3, label: str = "") -> "Sphere":
        dx, dy, dz = vector_between(centre, through)
        return cls(centre, dx * dx + dy * dy + dz * dz, through, label)

    def evaluate(self, point: Point3) -> Constructible:
        """Zero on the surface, negative inside, positive outside."""
        dx, dy, dz = vector_between(self.centre, point)
        return dx * dx + dy * dy + dz * dz - self.r2

    def radius_float(self) -> float:
        return to_float(self.r2) ** 0.5

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Sphere) and self.centre == other.centre
                and self.r2 == other.r2)

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash((self.centre, self.r2))
        return self._hash

    def __repr__(self) -> str:
        tag = f" [{self.label}]" if self.label else ""
        return f"Sphere(centre={self.centre}, r^2={self.r2}){tag}"
