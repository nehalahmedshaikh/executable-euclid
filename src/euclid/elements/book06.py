"""Book VI: similar figures, where Book V's proportion theory meets geometry."""

from __future__ import annotations

from fractions import Fraction

from ..plane.angles import length
from ..plane.construct import circle_with_radius2, line, meet, meet_one, posit
from ..plane.objects import Line, Point
from ..plane.predicates import (
    collinear,
    eq_angle,
    len2,
    on_line,
    parallel,
    polygon_area2,
    right_angle,
    signed_area2,
    similar,
)
from . import samples
from .book01_foundations import prop_I_10, prop_I_11
from .registry import CONSTRUCTION, THEOREM, Out, claim, hypothesis, proposition


def _area(*points: Point):
    value = polygon_area2(list(points))
    return (value if value >= 0 else -value) / 2


def _cut_base(rng):
    """A triangle whose base is divided, for the ratio theorems."""
    move = samples.frame(rng)
    left, right = samples.nonzero(rng, 1, 5), samples.nonzero(rng, 1, 5)
    return (
        move(Point(samples.scalar(rng, -2, 4), samples.nonzero(rng, 2, 6))),
        move(Point(0, 0)),
        move(Point(left, 0)),
        move(Point(left + right, 0)),
    )


@proposition(
    "VI.1",
    "Triangles and parallelograms which are under the same height are to one another as "
    "their bases.",
    THEOREM,
    sample=_cut_base,
)
def prop_VI_1(a: Point, b: Point, c: Point, d: Point) -> Out:
    hypothesis("B, C and D lie in a straight line", collinear(b, c, d))
    hypothesis("A is off that line", not collinear(a, b, c))
    line(a, b)
    line(a, c)
    line(a, d)
    claim("the triangles ABC and ACD are as the bases BC and CD", ["I.38", "V.Def.5"],
          _area(a, b, c) * length(c, d) == _area(a, c, d) * length(b, c))
    return Out()


def _triangle_with_parallel(rng):
    """A triangle ABC with DE parallel to BC cutting the other two sides."""
    move = samples.frame(rng)
    base = samples.nonzero(rng, 3, 7)
    apex_x, apex_y = samples.scalar(rng, -2, 5), samples.nonzero(rng, 2, 6)
    ratio = Fraction(rng.randint(1, 3), 4)
    a = Point(apex_x, apex_y)
    b, c = Point(0, 0), Point(base, 0)
    d = Point(a.x + ratio * (b.x - a.x), a.y + ratio * (b.y - a.y))
    e = Point(a.x + ratio * (c.x - a.x), a.y + ratio * (c.y - a.y))
    return move(a), move(b), move(c), move(d), move(e)


@proposition(
    "VI.2",
    "If a straight line is drawn parallel to one of the sides of a triangle, then it cuts "
    "the sides of the triangle proportionally.",
    THEOREM,
    sample=_triangle_with_parallel,
    note="The intercept theorem, and the workhorse of the rest of Book VI.",
)
def prop_VI_2(a: Point, b: Point, c: Point, d: Point, e: Point) -> Out:
    hypothesis("D lies on AB and E on AC",
               on_line(d, Line.through(a, b)) and on_line(e, Line.through(a, c)))
    hypothesis("DE is parallel to BC", parallel(Line.through(d, e), Line.through(b, c)))
    line(d, e, "DE")
    claim("the triangles BDE and CDE are equal, being on the same base and in the "
          "same parallels", "I.38", _area(b, d, e) == _area(c, d, e))
    claim("so AD is to DB as AE is to EC", ["I.38", "V.Def.5"],
          length(a, d) * length(e, c) == length(d, b) * length(a, e))
    return Out()


def _equiangular_triangles(rng):
    a, b, c = samples.triangle(rng)
    move = samples.frame(rng)  # a similarity: same angles, different size
    return a, b, c, move(a), move(b), move(c)


@proposition(
    "VI.4",
    "In equiangular triangles the sides about the equal angles are proportional, and "
    "those are corresponding sides which subtend the equal angles.",
    THEOREM,
    sample=_equiangular_triangles,
)
def prop_VI_4(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("the triangles are equiangular",
               eq_angle(a, b, c, d, e, f) and eq_angle(b, c, a, e, f, d))
    claim("the sides about the equal angles are proportional", ["VI.2", "I.32"],
          similar((a, b, c), (d, e, f)))
    claim("in particular AB is to BC as DE is to EF", "VI.2",
          len2(a, b) * len2(e, f) == len2(d, e) * len2(b, c))
    return Out()


def _mean_proportional_setup(rng):
    move = samples.frame(rng)
    first, second = samples.nonzero(rng, 1, 6), samples.nonzero(rng, 1, 6)
    return move(Point(0, 0)), move(Point(first, 0)), move(Point(first + second, 0))


@proposition(
    "VI.13",
    "To find a mean proportional to two given straight lines.",
    CONSTRUCTION,
    sample=_mean_proportional_setup,
    note="The geometric mean, raised as the height of a semicircle. This is the "
    "construction that makes every rational length's square root constructible.",
)
def prop_VI_13(a: Point, b: Point, c: Point) -> Out:
    hypothesis("B lies between A and C", on_line(b, Line.through(a, c)) and b != a and b != c)
    middle = posit(prop_I_10(a, c).midpoint, "M")
    semicircle = circle_with_radius2(middle, len2(middle, a), "the semicircle on AC")
    upright = prop_I_11(a, c, b).perpendicular
    d = posit(meet(upright, semicircle)[1], "D")

    claim("the angle in the semicircle is right", "III.31", right_angle(a, d, c))
    claim("BD is the mean proportional: AB is to BD as BD is to BC", "VI.8",
          length(a, b) * length(b, c) == length(b, d) * length(b, d))
    return Out(mean=d)


@proposition(
    "VI.31",
    "In right-angled triangles the figure on the side subtending the right angle equals "
    "the sum of the similar and similarly described figures on the sides containing the "
    "right angle.",
    THEOREM,
    sample=samples.right_triangle,
    note="Pythagoras generalised: the figures need not be squares, only similar. "
    "Here they are similar triangles, so I.47 is a special case.",
)
def prop_VI_31(a: Point, b: Point, c: Point) -> Out:
    """The right angle is at B; similar triangles are erected on the three sides."""
    hypothesis("the angle ABC is right", right_angle(a, b, c))
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))

    def similar_on(first: Point, second: Point) -> tuple[Point, Point, Point]:
        """Erect on the segment a triangle similar to ABC, on a fixed side."""
        dx, dy = second.x - first.x, second.y - first.y
        # the shape of ABC expressed in the frame of its own hypotenuse
        hx, hy = c.x - a.x, c.y - a.y
        scale = len2(a, c)
        px, py = b.x - a.x, b.y - a.y
        u = (px * hx + py * hy) / scale
        v = (px * hy - py * hx) / scale
        apex = Point(first.x + u * dx - v * dy, first.y + u * dy + v * dx)
        return first, apex, second

    on_hypotenuse = similar_on(a, c)
    on_first = similar_on(a, b)
    on_second = similar_on(b, c)
    for triangle in (on_hypotenuse, on_first, on_second):
        line(triangle[0], triangle[1])
        line(triangle[1], triangle[2])

    claim("the three figures are similar to one another", "VI.4",
          similar(on_first, on_hypotenuse) and similar(on_second, on_hypotenuse))
    claim("similar figures are to one another as the squares on their sides", "VI.20",
          _area(*on_first) * len2(a, c) == _area(*on_hypotenuse) * len2(a, b))
    claim("so the figure on the hypotenuse equals the two on the legs", ["I.47", "VI.20"],
          _area(*on_hypotenuse) == _area(*on_first) + _area(*on_second))
    return Out(figures=(on_hypotenuse, on_first, on_second))
