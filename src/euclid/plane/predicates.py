"""Exact geometric predicates.

Every test here is decided, not estimated.  Two tricks keep the whole predicate
language inside the current field, so testing a diagram never grows the tower:

* **Lengths are compared squared.**  ``AB = CD`` becomes ``|AB|^2 = |CD|^2``,
  which is a polynomial identity in the coordinates -- no square roots.
* **Angles are compared through cosines, cross-multiplied.**  With
  ``d = BA . BC`` and ``L = |BA|^2 |BC|^2`` we have ``cos = d / sqrt(L)``, so
  two angles compare by the sign of ``d1^2 L2 - d2^2 L1`` once the signs of the
  dot products agree.  Exact, and it handles obtuse angles correctly, which the
  naive squared comparison does not.

Predicates log themselves to the active trace.  That log is what the assumption
ledger later diffs across configurations to find facts that hold of Euclid's
diagram but not of every legal arrangement.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import Constructible, is_zero, sign
from .objects import Circle, Line, Point, vector_between
from .trace import record_predicate

__all__ = [
    "angle_cmp",
    "angle_less",
    "between",
    "collinear",
    "concurrent",
    "congruent_sss",
    "cross",
    "distinct",
    "dot",
    "eq_angle",
    "eq_area",
    "eq_len",
    "eq_polygon_area",
    "eq_ratio",
    "inside_circle",
    "len2",
    "on_circle",
    "on_line",
    "opposite_sides",
    "parallel",
    "perpendicular",
    "polygon_area2",
    "right_angle",
    "same_side",
    "signed_area2",
    "similar",
]


# ---------------------------------------------------------------------------
# raw exact quantities (not logged; they are ingredients, not assertions)
# ---------------------------------------------------------------------------


def len2(a: Point, b: Point) -> Constructible:
    """Squared length of the segment ``ab``."""
    dx, dy = vector_between(a, b)
    return dx * dx + dy * dy


def dot(vertex: Point, first: Point, second: Point) -> Constructible:
    """Dot product of the two rays leaving ``vertex``."""
    ux, uy = vector_between(vertex, first)
    vx, vy = vector_between(vertex, second)
    return ux * vx + uy * vy


def cross(vertex: Point, first: Point, second: Point) -> Constructible:
    ux, uy = vector_between(vertex, first)
    vx, vy = vector_between(vertex, second)
    return ux * vy - uy * vx


def signed_area2(a: Point, b: Point, c: Point) -> Constructible:
    """Twice the signed area of triangle ``abc``; sign gives the orientation."""
    return cross(a, b, c)


# ---------------------------------------------------------------------------
# incidence and equality
# ---------------------------------------------------------------------------


def distinct(a: Point, b: Point) -> bool:
    return record_predicate("distinct", a != b)


def eq_len(a: Point, b: Point, c: Point, d: Point) -> bool:
    """``ab = cd`` as magnitudes."""
    return record_predicate("eq_len", len2(a, b) == len2(c, d))


def collinear(a: Point, b: Point, c: Point) -> bool:
    return record_predicate("collinear", is_zero(signed_area2(a, b, c)))


def on_line(point: Point, l: Line) -> bool:
    return record_predicate("on_line", is_zero(l.evaluate(point)))


def on_circle(point: Point, k: Circle) -> bool:
    return record_predicate("on_circle", is_zero(k.evaluate(point)))


def inside_circle(point: Point, k: Circle) -> bool:
    return record_predicate("inside_circle", sign(k.evaluate(point)) < 0)


def parallel(u: Line, v: Line) -> bool:
    return record_predicate("parallel", is_zero(u.a * v.b - u.b * v.a))


def perpendicular(u: Line, v: Line) -> bool:
    return record_predicate("perpendicular", is_zero(u.a * v.a + u.b * v.b))


def concurrent(u: Line, v: Line, w: Line) -> bool:
    determinant = (
        u.a * (v.b * w.c - v.c * w.b)
        - u.b * (v.a * w.c - v.c * w.a)
        + u.c * (v.a * w.b - v.b * w.a)
    )
    return record_predicate("concurrent", is_zero(determinant))


# ---------------------------------------------------------------------------
# order and side -- the configuration-dependent facts, flagged as such
# ---------------------------------------------------------------------------


def between(a: Point, b: Point, c: Point) -> bool:
    """``b`` lies strictly between ``a`` and ``c``."""
    if not is_zero(signed_area2(a, b, c)):
        return record_predicate("between", False, order_sensitive=True)
    ux, uy = vector_between(a, b)
    vx, vy = vector_between(b, c)
    value = sign(ux * vx + uy * vy) > 0 and not (a == b or b == c)
    return record_predicate("between", value, order_sensitive=True)


def same_side(p: Point, q: Point, l: Line) -> bool:
    left, right = l.side_of(p), l.side_of(q)
    return record_predicate("same_side", left != 0 and left == right, order_sensitive=True)


def opposite_sides(p: Point, q: Point, l: Line) -> bool:
    left, right = l.side_of(p), l.side_of(q)
    return record_predicate("opposite_sides", left != 0 and right != 0 and left != right, order_sensitive=True)


# ---------------------------------------------------------------------------
# angles
# ---------------------------------------------------------------------------


def _angle_pair(a: Point, b: Point, c: Point) -> tuple[Constructible, Constructible]:
    """``(dot, |BA|^2 |BC|^2)`` for the angle ``abc`` at vertex ``b``."""
    return dot(b, a, c), len2(b, a) * len2(b, c)


def angle_cmp(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> int:
    """Compare angle ``abc`` with angle ``def``: ``-1``, ``0`` or ``1``.

    Cosine decreases on ``[0, pi]``, so the angle order is the reverse of the
    cosine order.  Comparing ``d1/sqrt(L1)`` with ``d2/sqrt(L2)`` needs the sign
    bookkeeping below; squaring alone would confuse an acute angle with its
    obtuse supplement.
    """
    d1, l1 = _angle_pair(a, b, c)
    d2, l2 = _angle_pair(d, e, f)
    s1, s2 = sign(d1), sign(d2)
    if s1 != s2:
        cosine_order = 1 if s1 > s2 else -1
    elif s1 == 0:
        cosine_order = 0
    else:
        difference = sign(d1 * d1 * l2 - d2 * d2 * l1)
        cosine_order = difference if s1 > 0 else -difference
    return -cosine_order


def eq_angle(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> bool:
    return record_predicate("eq_angle", angle_cmp(a, b, c, d, e, f) == 0)


def angle_less(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> bool:
    return record_predicate("angle_less", angle_cmp(a, b, c, d, e, f) < 0)


def right_angle(a: Point, b: Point, c: Point) -> bool:
    return record_predicate("right_angle", is_zero(dot(b, a, c)))


# ---------------------------------------------------------------------------
# areas, congruence, ratio
# ---------------------------------------------------------------------------


def eq_area(triangle_one: tuple[Point, Point, Point], triangle_two: tuple[Point, Point, Point]) -> bool:
    first = signed_area2(*triangle_one)
    second = signed_area2(*triangle_two)
    return record_predicate("eq_area", first == second or first == -second)


def polygon_area2(points: list[Point]) -> Constructible:
    """Twice the signed area of a simple polygon, by the shoelace formula."""
    total: Constructible = Fraction(0)
    count = len(points)
    for index in range(count):
        current, following = points[index], points[(index + 1) % count]
        total = total + (current.x * following.y - following.x * current.y)
    return total


def eq_polygon_area(first: list[Point], second: list[Point]) -> bool:
    a, b = polygon_area2(first), polygon_area2(second)
    return record_predicate("eq_polygon_area", a == b or a == -b)


def congruent_sss(
    triangle_one: tuple[Point, Point, Point], triangle_two: tuple[Point, Point, Point]
) -> bool:
    """Side-side-side congruence, the content of I.8."""
    a, b, c = triangle_one
    d, e, f = triangle_two
    value = len2(a, b) == len2(d, e) and len2(b, c) == len2(e, f) and len2(c, a) == len2(f, d)
    return record_predicate("congruent_sss", value)


def eq_ratio(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point, g: Point, h: Point) -> bool:
    """``ab : cd = ef : gh``, compared without ever taking a square root."""
    left = len2(a, b) * len2(g, h)
    right = len2(c, d) * len2(e, f)
    return record_predicate("eq_ratio", left == right)


def similar(
    triangle_one: tuple[Point, Point, Point], triangle_two: tuple[Point, Point, Point]
) -> bool:
    a, b, c = triangle_one
    d, e, f = triangle_two
    value = (
        len2(a, b) * len2(e, f) == len2(d, e) * len2(b, c)
        and len2(b, c) * len2(f, d) == len2(e, f) * len2(c, a)
    )
    return record_predicate("similar", value)
