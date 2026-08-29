"""Book VI, complete: similar figures, where Book V's proportion meets geometry.

Everything here rests on VI.2, the intercept theorem, and on the Definition 5
machinery of Book V -- which is why the two books were written in that order.
The application-of-areas propositions at the end (VI.27-29) are the geometric
solution of a quadratic: VI.27 is the maximum, and Euclid's proviso in VI.28 is
exactly the condition for the discriminant not to be negative.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import sign, sqrt
from ..plane.angles import RIGHT, STRAIGHT, angle_at, length
from ..plane.construct import circle_with_radius2, line, meet, meet_one, outline, posit
from ..plane.objects import Line, Point
from ..plane.predicates import (
    collinear,
    eq_angle,
    eq_len,
    len2,
    on_line,
    parallel,
    polygon_area2,
    right_angle,
    signed_area2,
    similar,
)
from . import samples
from .book05 import separating_witness
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
    THEOREM,
    sample=_triangle_with_parallel,
    note="The intercept theorem, and the workhorse of the rest of Book VI.",
)
def prop_VI_2(a: Point, b: Point, c: Point, d: Point, e: Point) -> Out:
    hypothesis("D lies on AB and E on AC",
               on_line(d, Line.through(a, b)) and on_line(e, Line.through(a, c)))
    hypothesis("DE is parallel to BC", parallel(Line.through(d, e), Line.through(b, c)))
    outline(a, b, c)
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
    THEOREM,
    sample=_equiangular_triangles,
)
def prop_VI_4(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("the triangles are equiangular",
               eq_angle(a, b, c, d, e, f) and eq_angle(b, c, a, e, f, d))
    outline(a, b, c)
    outline(d, e, f)
    claim("the sides about the equal angles are proportional", ["VI.2", "I.32"],
          similar((a, b, c), (d, e, f)))
    claim("in particular AB is to BC as DE is to EF", "VI.2",
          len2(a, b) * len2(e, f) == len2(d, e) * len2(b, c))
    return Out()


def _mean_proportional_setup(rng):
    move = samples.frame(rng)
    first, second = samples.nonzero(rng, 1, 6), samples.nonzero(rng, 1, 6)
    return move(Point(0, 0)), move(Point(first, 0)), move(Point(first + second, 0))


def _standing_on(start: Point, end: Point, height) -> tuple:
    """The rectangle raised on a segment to a given height, at right angles."""
    across = (-(end.y - start.y), end.x - start.x)
    scale = height / length(start, end)
    step = (across[0] * scale, across[1] * scale)
    return (start, end, Point(end.x + step[0], end.y + step[1]),
            Point(start.x + step[0], start.y + step[1]))


def _along(origin: Point, towards: Point, part) -> Point:
    """The point a given fraction of the way from one point towards another."""
    return Point(origin.x + part * (towards.x - origin.x),
                 origin.y + part * (towards.y - origin.y))


def _bisected_angle(rng):
    """A triangle with the bisector of the angle at A meeting the base."""
    a, b, c = samples.triangle(rng)
    # The bisector cuts the base in the ratio of the adjacent sides, which is
    # where it meets BC; handing that point over keeps the figure exact.
    ab, ac = length(a, b), length(a, c)
    d = Point((ac * b.x + ab * c.x) / (ab + ac), (ac * b.y + ab * c.y) / (ab + ac))
    return a, b, c, d


@proposition(
    "VI.3",
    THEOREM,
    sample=_bisected_angle,
    note="The angle bisector cuts the base in the ratio of the adjacent sides -- "
    "and the converse holds too, so the ratio identifies the bisector.",
)
def prop_VI_3(a: Point, b: Point, c: Point, d: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
    hypothesis("D lies on the base BC", on_line(d, Line.through(b, c)) and d != b and d != c)
    outline(a, b, c)
    line(a, d, "the line AD")

    claim("AD bisects the angle at A", "I.9", eq_angle(b, a, d, d, a, c))
    claim("so the segments of the base are as the remaining sides", "VI.2",
          length(b, d) * length(a, c) == length(d, c) * length(a, b))
    claim("and conversely, that ratio makes AD the bisector", "VI.2",
          (length(b, d) * length(a, c) == length(d, c) * length(a, b))
          == eq_angle(b, a, d, d, a, c))
    return Out(section=d)


def _similar_triangles(rng):
    a, b, c = samples.triangle(rng)
    move = samples.frame(rng)
    return a, b, c, move(a), move(b), move(c)


@proposition(
    "VI.5",
    THEOREM,
    sample=_similar_triangles,
    note="The converse of VI.4: proportional sides force equal angles. Together "
    "they make similarity a single notion rather than two.",
)
def prop_VI_5(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("neither triangle is degenerate",
               not collinear(a, b, c) and not collinear(d, e, f))
    hypothesis("the sides are proportional", similar((a, b, c), (d, e, f)))
    outline(a, b, c)
    outline(d, e, f)

    claim("the triangles are equiangular", "I.8",
          eq_angle(b, a, c, e, d, f) and eq_angle(a, b, c, d, e, f)
          and eq_angle(a, c, b, d, f, e))
    claim("and the equal angles are those the corresponding sides subtend", "I.8",
          eq_angle(a, c, b, d, f, e))
    return Out()


@proposition(
    "VI.6",
    THEOREM,
    sample=_similar_triangles,
)
def prop_VI_6(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("neither triangle is degenerate",
               not collinear(a, b, c) and not collinear(d, e, f))
    hypothesis("one angle equals one angle", eq_angle(b, a, c, e, d, f))
    hypothesis("the sides about those angles are proportional",
               len2(a, b) * len2(d, f) == len2(d, e) * len2(a, c))
    outline(a, b, c)
    outline(d, e, f)

    claim("the triangles are equiangular", ["VI.4", "I.4"],
          eq_angle(a, b, c, d, e, f) and eq_angle(a, c, b, d, f, e))
    claim("and so similar throughout", "VI.4", similar((a, b, c), (d, e, f)))
    return Out()


@proposition(
    "VI.7",
    THEOREM,
    sample=_similar_triangles,
    note="The ambiguous case, made unambiguous by Euclid's proviso that the "
    "remaining angles are both acute or both not acute.",
)
def prop_VI_7(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("neither triangle is degenerate",
               not collinear(a, b, c) and not collinear(d, e, f))
    hypothesis("one angle equals one angle", eq_angle(a, b, c, d, e, f))
    hypothesis("the sides about other angles are proportional",
               len2(b, a) * len2(e, f) == len2(e, d) * len2(b, c))
    remaining = (angle_at(b, c, a), angle_at(e, f, d))
    hypothesis("the remaining angles are both less, or both not less, than a right angle",
               (remaining[0] < RIGHT) == (remaining[1] < RIGHT))
    outline(a, b, c)
    outline(d, e, f)

    claim("the triangles are equiangular", "VI.5", eq_angle(b, c, a, e, f, d))
    claim("and the sides about the proportional angles correspond", "VI.5",
          similar((a, b, c), (d, e, f)))
    return Out()


@proposition(
    "VI.8",
    THEOREM,
    sample=samples.right_triangle,
    note="Dropping the perpendicular from the right angle splits the triangle "
    "into two copies of itself -- and gives VI.13's mean proportional at once.",
)
def prop_VI_8(a: Point, b: Point, c: Point) -> Out:
    """The right angle is at B; the perpendicular falls from B to AC."""
    hypothesis("the angle at B is right", right_angle(a, b, c))
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
    outline(a, b, c)

    ux, uy = c.x - a.x, c.y - a.y
    along = ((b.x - a.x) * ux + (b.y - a.y) * uy) / (ux * ux + uy * uy)
    foot = posit(Point(a.x + along * ux, a.y + along * uy), "D")
    line(b, foot, "the perpendicular BD")

    claim("BD is perpendicular to the base", "I.12", right_angle(b, foot, a))
    claim("each adjoining triangle is similar to the whole", "VI.4",
          similar((a, foot, b), (a, b, c)) and similar((b, foot, c), (a, b, c)))
    claim("and so to one another", "VI.4", similar((a, foot, b), (b, foot, c)))
    claim("whence BD is the mean proportional between the segments", "VI.4",
          len2(b, foot) == length(a, foot) * length(foot, c))
    return Out(foot=foot)


@proposition(
    "VI.9",
    CONSTRUCTION,
    sample=lambda rng: samples.segment(rng) + (rng.randint(2, 6),),
)
def prop_VI_9(a: Point, b: Point, parts: int) -> Out:
    """Cut off from AB the prescribed part -- one of `parts` equal pieces."""
    hypothesis("A and B are distinct", a != b)
    hypothesis("a genuine part is asked for", parts >= 2)
    line(a, b, "the given line AB")

    # Euclid lays off equal lengths on a second line through A and joins the
    # last to B; the parallels through the divisions cut AB proportionally.
    aside = posit(Point(a.x + (b.y - a.y), a.y - (b.x - a.x)), "C")
    marks = [posit(_along(a, aside, Fraction(k, parts)), f"M{k}") for k in range(1, parts + 1)]
    line(a, aside, "the line laid off from A")
    line(marks[-1], b, "the join CB")
    cut = posit(_along(a, b, Fraction(1, parts)), "D")
    line(marks[0], cut, "the parallel through the first division")

    claim("the divisions of the second line are equal", "I.3",
          all(eq_len(marks[k], marks[k + 1], a, marks[0]) for k in range(len(marks) - 1)))
    claim("the line through the first division is parallel to CB", "I.31",
          parallel(Line.through(marks[0], cut), Line.through(marks[-1], b)))
    claim("so AD is the part asked for", "VI.2", parts * length(a, cut) == length(a, b))
    return Out(part=cut)


@proposition(
    "VI.10",
    CONSTRUCTION,
    sample=lambda rng: samples.segment(rng)
    + (Fraction(rng.randint(1, 3), 8), Fraction(rng.randint(5, 7), 8)),
)
def prop_VI_10(a: Point, b: Point, first, second) -> Out:
    """Cut AB in the same ratios as a given cut line."""
    hypothesis("A and B are distinct", a != b)
    hypothesis("the given line is cut in order", sign(second - first) > 0
               and sign(first) > 0 and sign(1 - second) > 0)
    line(a, b, "the line to be cut")

    aside = posit(Point(a.x + (b.y - a.y), a.y - (b.x - a.x)), "C")
    line(a, aside, "the given cut line, laid alongside")
    given = [posit(_along(a, aside, part), name)
             for part, name in ((first, "D"), (second, "E"))]
    line(aside, b, "the join CB")
    cuts = [posit(_along(a, b, part), name)
            for part, name in ((first, "F"), (second, "G"))]
    for mark, cut in zip(given, cuts):
        line(mark, cut)

    claim("the joining lines are parallel to CB", "I.31",
          all(parallel(Line.through(mark, cut), Line.through(aside, b))
              for mark, cut in zip(given, cuts)))
    claim("so AB is cut in the same ratios as the given line", "VI.2",
          length(a, cuts[0]) * length(a, aside) == length(a, given[0]) * length(a, b)
          and length(a, cuts[1]) * length(a, aside) == length(a, given[1]) * length(a, b))
    return Out(sections=tuple(cuts))


@proposition(
    "VI.11",
    CONSTRUCTION,
    sample=lambda rng: samples.segment(rng) + (Fraction(rng.randint(2, 7), 4),),
)
def prop_VI_11(a: Point, b: Point, ratio) -> Out:
    """To AB and AC, find the third proportional: AB : AC = AC : x."""
    hypothesis("A and B are distinct", a != b)
    hypothesis("the second line is a genuine magnitude", sign(ratio) > 0)
    line(a, b, "the first given line AB")
    c = posit(_along(a, b, ratio), "C")

    aside = posit(Point(a.x + (b.y - a.y), a.y - (b.x - a.x)), "D")
    line(a, aside, "a line through A")
    e = posit(_along(a, aside, ratio), "E")
    line(b, e, "the join BE")
    third = posit(_along(a, aside, ratio * ratio), "F")
    line(c, third, "the parallel through C")

    claim("CF is parallel to BE", "I.31",
          parallel(Line.through(c, third), Line.through(b, e)))
    claim("so AB is to AC as AC is to AF", "VI.2",
          length(a, b) * length(a, third) == length(a, c) * length(a, c))
    return Out(third=third)


@proposition(
    "VI.12",
    CONSTRUCTION,
    sample=lambda rng: samples.segment(rng)
    + (Fraction(rng.randint(2, 7), 4), Fraction(rng.randint(2, 7), 4)),
)
def prop_VI_12(a: Point, b: Point, second, third) -> Out:
    """To three given lines, find the fourth proportional."""
    hypothesis("A and B are distinct", a != b)
    hypothesis("the given lines are genuine magnitudes",
               sign(second) > 0 and sign(third) > 0)
    line(a, b, "the first given line AB")
    c = posit(_along(a, b, second), "C")

    aside = posit(Point(a.x + (b.y - a.y), a.y - (b.x - a.x)), "D")
    line(a, aside, "a line through A")
    e = posit(_along(a, aside, third), "E")
    line(b, e, "the join BE")
    fourth = posit(_along(a, aside, third * second), "F")
    line(c, fourth, "the parallel through C")

    claim("CF is parallel to BE", "I.31",
          parallel(Line.through(c, fourth), Line.through(b, e)))
    claim("so AB is to AC as AE is to AF", "VI.2",
          length(a, b) * length(a, fourth) == length(a, c) * length(a, e))
    return Out(fourth=fourth)


@proposition(
    "VI.13",
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


def _similar_polygons(rng):
    """A quadrilateral and its image under a similarity of the plane."""
    a, b, c, d = samples.quadrilateral(rng)
    move = samples.frame(rng)
    return a, b, c, d, move(a), move(b), move(c), move(d)


def _parallelogram_on(corner: Point, first: Point, second: Point) -> tuple:
    """The parallelogram with the two given sides drawn from one corner."""
    far = Point(first.x + second.x - corner.x, first.y + second.y - corner.y)
    return corner, first, far, second


def _two_parallelograms(rng, equal: bool):
    """Two equiangular parallelograms, equal in area or not."""
    move = samples.frame(rng, scaled=False)
    cosine, sine = samples.rational_rotation(rng)
    while sine == 0:
        cosine, sine = samples.rational_rotation(rng)
    first, second = samples.nonzero(rng, 2, 6), samples.nonzero(rng, 2, 6)
    third = samples.nonzero(rng, 1, 5)
    fourth = (first * second / third) if equal else samples.nonzero(rng, 1, 5)
    apart = first + third + 4
    return (
        move(Point(0, 0)), move(Point(first, 0)),
        move(Point(second * cosine, second * sine)),
        move(Point(apart, 0)), move(Point(apart + third, 0)),
        move(Point(apart + fourth * cosine, fourth * sine)),
    )


@proposition(
    "VI.14",
    THEOREM,
    sample=lambda rng: _two_parallelograms(rng, equal=True),
    note="'Reciprocally proportional' is Euclid's way of saying the product of "
    "the sides is fixed -- an area law written entirely in ratios.",
)
def prop_VI_14(a: Point, b: Point, d: Point, p: Point, q: Point, s: Point) -> Out:
    """Two equiangular parallelograms, on sides AB, AD and PQ, PS."""
    hypothesis("neither parallelogram is degenerate",
               not collinear(a, b, d) and not collinear(p, q, s))
    hypothesis("they are equiangular", eq_angle(b, a, d, q, p, s))
    first = _parallelogram_on(a, b, d)
    second = _parallelogram_on(p, q, s)
    outline(*first)
    outline(*second)
    hypothesis("the parallelograms are equal", _area(*first) == _area(*second))

    claim("the sides about the equal angles are reciprocally proportional -- "
          "AB is to PQ as PS is to AD", "VI.1",
          length(a, b) * length(a, d) == length(p, q) * length(p, s))
    claim("and the reciprocal proportion in turn makes them equal", "VI.1",
          (length(a, b) * length(a, d) == length(p, q) * length(p, s))
          == (_area(*first) == _area(*second)))
    return Out(parallelograms=(first, second))


@proposition(
    "VI.15",
    THEOREM,
    sample=lambda rng: _two_parallelograms(rng, equal=True),
)
def prop_VI_15(a: Point, b: Point, d: Point, p: Point, q: Point, s: Point) -> Out:
    """The same for triangles, which are the halves of those parallelograms."""
    hypothesis("neither triangle is degenerate",
               not collinear(a, b, d) and not collinear(p, q, s))
    hypothesis("one angle equals one angle", eq_angle(b, a, d, q, p, s))
    outline(a, b, d)
    outline(p, q, s)
    hypothesis("the triangles are equal", _area(a, b, d) == _area(p, q, s))

    claim("the sides about the equal angles are reciprocally proportional", "VI.14",
          length(a, b) * length(a, d) == length(p, q) * length(p, s))
    claim("and the reciprocal proportion makes them equal", "VI.14",
          (length(a, b) * length(a, d) == length(p, q) * length(p, s))
          == (_area(a, b, d) == _area(p, q, s)))
    return Out()


def _four_proportional_lines(rng):
    """Four lengths in proportion, laid out as segments to be drawn."""
    move = samples.frame(rng, scaled=False)
    first, second = samples.nonzero(rng, 2, 6), samples.nonzero(rng, 2, 6)
    scale = Fraction(rng.randint(1, 5), rng.randint(1, 4))
    lengths = (first, second, first * scale, second * scale)
    points = []
    for index, reach in enumerate(lengths):
        base = Point(0, -index * 2)
        points += [move(base), move(Point(reach, -index * 2))]
    return tuple(points)


@proposition(
    "VI.16",
    THEOREM,
    sample=_four_proportional_lines,
    note="The rule of three, stated about rectangles: the product of the extremes "
    "equals the product of the means.",
)
def prop_VI_16(a: Point, b: Point, c: Point, d: Point,
               e: Point, f: Point, g: Point, h: Point) -> Out:
    """The four lines are AB, CD, EF and GH, drawn one under another."""
    for pair in ((a, b), (c, d), (e, f), (g, h)):
        line(*pair)
    first, second = length(a, b), length(c, d)
    third, fourth = length(e, f), length(g, h)
    hypothesis("the four lines are genuine magnitudes",
               all(sign(x) > 0 for x in (first, second, third, fourth)))
    # Proportion for magnitudes is Eudoxus' Definition 5, which is decided by
    # looking for equimultiples that separate the ratios. Stating the hypothesis
    # that way keeps the two halves of this proposition from collapsing into one
    # rewriting of the same product.
    hypothesis("the four are proportional",
               separating_witness(first, second, third, fourth) is None)

    # The two rectangles, built and drawn, so the claim is about figures.
    by_extremes = _standing_on(a, b, fourth)
    by_means = _standing_on(c, d, third)
    outline(*by_extremes)
    outline(*by_means)

    claim("the rectangle contained by the extremes equals that by the means",
          "VI.14", _area(*by_extremes) == _area(*by_means))
    claim("and conversely, equal rectangles leave no equimultiples that separate "
          "the ratios", "VI.14",
          (_area(*by_extremes) == _area(*by_means))
          == (separating_witness(first, second, third, fourth) is None))
    return Out(rectangles=(by_extremes, by_means))


def _three_proportional_lines(rng):
    """Three lengths in proportion, laid out as separate segments to be drawn."""
    move = samples.frame(rng, scaled=False)
    first = samples.nonzero(rng, 2, 6)
    ratio = Fraction(rng.randint(2, 7), 4)
    points = []
    for index, reach in enumerate((first, first * ratio, first * ratio * ratio)):
        points += [move(Point(0, -index * 2)), move(Point(reach, -index * 2))]
    return tuple(points)


@proposition(
    "VI.17",
    THEOREM,
    sample=_three_proportional_lines,
    note="The special case of VI.16 where the means coincide, and the one that "
    "makes a mean proportional the side of an equal square.",
)
def prop_VI_17(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    """The three lines are AB, CD and EF, laid out one under another."""
    for pair in ((a, b), (c, d), (e, f)):
        line(*pair)
    first, mean, last = length(a, b), length(c, d), length(e, f)
    hypothesis("the three lines are genuine magnitudes",
               all(sign(x) > 0 for x in (first, mean, last)))
    hypothesis("they are proportional", first * last == mean * mean)

    # The rectangle contained by the extremes, and the square on the mean, both
    # built and drawn: the claim is then about figures rather than products.
    rectangle = _standing_on(a, b, last)
    square = _standing_on(c, d, mean)
    outline(*rectangle)
    outline(*square)

    claim("the drawn figures really are the rectangle and the square", "Def.22",
          _area(*rectangle) == first * last and _area(*square) == mean * mean)
    claim("so the rectangle contained by the extremes equals the square on the mean",
          "VI.16", _area(*rectangle) == _area(*square))
    claim("and conversely the equality makes the three proportional", "VI.16",
          (_area(*rectangle) == _area(*square)) == (first * last == mean * mean))
    return Out(rectangle=rectangle, square=square)


@proposition(
    "VI.18",
    CONSTRUCTION,
    sample=lambda rng: samples.quadrilateral(rng) + samples.segment(rng),
)
def prop_VI_18(a: Point, b: Point, c: Point, d: Point, p: Point, q: Point) -> Out:
    """On PQ, describe a figure similar to the given quadrilateral ABCD."""
    hypothesis("the given figure is genuine",
               not collinear(a, b, c) and not collinear(a, c, d))
    hypothesis("P and Q are distinct", p != q)
    outline(a, b, c, d)
    line(p, q, "the given line PQ")

    # The similarity carrying AB onto PQ, expressed in the frame of AB itself.
    ux, uy = b.x - a.x, b.y - a.y
    scale = len2(a, b)
    vx, vy = q.x - p.x, q.y - p.y

    def carried(point: Point) -> Point:
        px, py = point.x - a.x, point.y - a.y
        along = (px * ux + py * uy) / scale
        across = (px * uy - py * ux) / scale
        return Point(p.x + along * vx + across * vy, p.y + along * vy - across * vx)

    built = [p, q] + [posit(carried(point), name) for point, name in ((c, "R"), (d, "S"))]
    outline(*built)

    claim("the figure described is similar to the given one", "VI.Def.1",
          all(len2(built[i], built[j]) * len2(a, b) == len2((a, b, c, d)[i], (a, b, c, d)[j])
              * len2(p, q) for i in range(4) for j in range(i + 1, 4)))
    claim("and it stands on the given straight line", "Post.1",
          built[0] == p and built[1] == q)
    return Out(figure=tuple(built))


@proposition(
    "VI.19",
    THEOREM,
    sample=_similar_triangles,
    note="Areas of similar triangles go as the squares on their sides. VI.20 "
    "generalises it to any figure, and VI.31 turns it into Pythagoras.",
)
def prop_VI_19(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("neither triangle is degenerate",
               not collinear(a, b, c) and not collinear(d, e, f))
    hypothesis("the triangles are similar", similar((a, b, c), (d, e, f)))
    outline(a, b, c)
    outline(d, e, f)

    claim("the triangles are to one another in the duplicate ratio of BC to EF",
          ["VI.11", "VI.15"],
          _area(a, b, c) * len2(e, f) == _area(d, e, f) * len2(b, c))
    return Out()


@proposition(
    "VI.21",
    THEOREM,
    sample=_similar_triangles,
)
def prop_VI_21(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    """Two figures similar to the same figure are similar to one another."""
    hypothesis("neither triangle is degenerate",
               not collinear(a, b, c) and not collinear(d, e, f))
    hypothesis("the second is similar to the first", similar((a, b, c), (d, e, f)))
    outline(a, b, c)
    outline(d, e, f)

    # A third figure, similar to the first; similarity should carry across.
    third = [posit(Point(a.x + 2 * (point.x - a.x), a.y + 2 * (point.y - a.y)), name)
             for point, name in ((a, "G"), (b, "H"), (c, "K"))]
    outline(*third)

    claim("the third is similar to the first", "VI.Def.1", similar((a, b, c), tuple(third)))
    claim("so the second and third are similar to one another", "VI.Def.1",
          similar((d, e, f), tuple(third)))
    return Out()


@proposition(
    "VI.22",
    THEOREM,
    sample=_four_proportional_lines,
)
def prop_VI_22(a: Point, b: Point, c: Point, d: Point,
               e: Point, f: Point, g: Point, h: Point) -> Out:
    """Similar figures described on four proportional lines are proportional."""
    first, second = length(a, b), length(c, d)
    third, fourth = length(e, f), length(g, h)
    hypothesis("the four lines are genuine magnitudes",
               all(sign(x) > 0 for x in (first, second, third, fourth)))
    hypothesis("they are proportional", first * fourth == second * third)
    for pair in ((a, b), (c, d), (e, f), (g, h)):
        line(*pair)

    # Squares are the simplest similar figures to describe on them.
    squares = []
    for start, end in ((a, b), (c, d), (e, f), (g, h)):
        across = (-(end.y - start.y), end.x - start.x)
        squares.append(_area(start, end, Point(end.x + across[0], end.y + across[1]),
                             Point(start.x + across[0], start.y + across[1])))

    claim("the similar figures on them are proportional", "VI.20",
          squares[0] * squares[3] == squares[1] * squares[2])
    claim("and conversely, proportional figures make the lines proportional", "VI.20",
          (squares[0] * squares[3] == squares[1] * squares[2])
          == (first * fourth == second * third))
    return Out()


@proposition(
    "VI.23",
    THEOREM,
    sample=lambda rng: _two_parallelograms(rng, equal=False),
    note="'Compounded ratio' is the product of two ratios, which Euclid has no "
    "notation for and states by naming a mean.",
)
def prop_VI_23(a: Point, b: Point, d: Point, p: Point, q: Point, s: Point) -> Out:
    hypothesis("neither parallelogram is degenerate",
               not collinear(a, b, d) and not collinear(p, q, s))
    hypothesis("they are equiangular", eq_angle(b, a, d, q, p, s))
    first = _parallelogram_on(a, b, d)
    second = _parallelogram_on(p, q, s)
    outline(*first)
    outline(*second)

    claim("the ratio of the parallelograms is that of the sides compounded",
          ["VI.1", "V.Def.5"],
          _area(*first) * (length(p, q) * length(p, s))
          == _area(*second) * (length(a, b) * length(a, d)))
    return Out()


def _parallelogram_with_similar_corner(rng):
    """A parallelogram and the similar one cut from it at a common corner."""
    move = samples.frame(rng, scaled=False)
    cosine, sine = samples.rational_rotation(rng)
    while sine == 0:
        cosine, sine = samples.rational_rotation(rng)
    first, second = samples.nonzero(rng, 3, 7), samples.nonzero(rng, 3, 7)
    part = Fraction(rng.randint(1, 3), 4)
    return (
        move(Point(0, 0)),
        move(Point(first, 0)),
        move(Point(second * cosine, second * sine)),
        part,
    )


@proposition(
    "VI.24",
    THEOREM,
    sample=_parallelogram_with_similar_corner,
)
def prop_VI_24(a: Point, b: Point, d: Point, part) -> Out:
    """The parallelograms about the diameter of ABCD."""
    hypothesis("the parallelogram is genuine", not collinear(a, b, d))
    hypothesis("the division is a proper one", sign(part) > 0 and sign(1 - part) > 0)
    whole = _parallelogram_on(a, b, d)
    outline(*whole)
    diameter = line(a, whole[2], "the diameter AC")

    corner = posit(_along(a, whole[2], part), "K")
    inner = _parallelogram_on(a, posit(_along(a, b, part), "E"),
                              posit(_along(a, d, part), "G"))
    outline(*inner)

    claim("the lesser parallelogram stands about the same diameter", "I.43",
          on_line(corner, diameter) and inner[2] == corner)
    claim("and it is similar to the whole", "VI.Def.1",
          similar((inner[0], inner[1], inner[2]), (whole[0], whole[1], whole[2])))
    return Out(inner=inner, whole=whole)


@proposition(
    "VI.25",
    CONSTRUCTION,
    sample=lambda rng: samples.triangle(rng) + (Fraction(rng.randint(1, 6), 4),),
    note="Similar in shape to one figure, equal in size to another. The scale "
    "wanted is a square root, which is why VI.13's mean proportional is needed.",
)
def prop_VI_25(a: Point, b: Point, c: Point, wanted) -> Out:
    """Build a triangle similar to ABC and equal to a given area."""
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
    hypothesis("a positive area is asked for", sign(wanted) > 0)
    outline(a, b, c)
    target = _area(a, b, c) * wanted

    # Similar figures go as the squares on their sides (VI.19), so the side must
    # be scaled by the square root of the ratio of the areas.
    scale = sqrt(target / _area(a, b, c))
    built = (a,
             posit(_along(a, b, scale), "D"),
             posit(_along(a, c, scale), "E"))
    outline(*built)

    claim("the figure built is similar to the given one", "VI.Def.1",
          similar((a, b, c), built))
    claim("and equal to the area asked for", "VI.19", _area(*built) == target)
    return Out(figure=built)


def _deficient_application(rng):
    """A line to apply to, and how far along the half the parallelogram reaches."""
    a, b = samples.segment(rng)
    return a, b, Fraction(rng.randint(1, 7), 8)


@proposition(
    "VI.27",
    THEOREM,
    sample=_deficient_application,
    note="A maximum, proved without calculus: of all the deficient parallelograms "
    "on a line, the one on the half is the greatest.",
)
def prop_VI_27(a: Point, b: Point, part) -> Out:
    """Parallelograms on AB deficient by a figure similar to that on the half."""
    hypothesis("A and B are distinct", a != b)
    hypothesis("the application is a proper one", sign(part) > 0 and sign(1 - part) > 0)
    line(a, b, "the given line AB")
    middle = posit(prop_I_10(a, b).midpoint, "C")

    # Applying to AD leaves a defect similar to the one on the half, so the
    # parallelogram is as AD by DB -- greatest when the two are equal.
    d = posit(_along(a, b, part), "D")
    across = (-(b.y - a.y), b.x - a.x)
    applied = _parallelogram_on(a, d, Point(a.x + across[0] / 2, a.y + across[1] / 2))
    on_half = _parallelogram_on(a, middle, Point(a.x + across[0] / 2, a.y + across[1] / 2))
    outline(*applied)
    outline(*on_half)

    claim("each applied parallelogram is as the rectangle contained by the "
          "segments it leaves", "VI.23",
          _area(*applied) == length(a, d) * length(a, b) / 2
          and _area(*on_half) == length(a, middle) * length(a, b) / 2)
    # The maximum is the whole content, so it is tested against the whole line
    # rather than against the one position that happened to be sampled.
    elsewhere = [_along(a, b, Fraction(k, 12)) for k in range(1, 12)]
    claim("and that on the half is not less than any other applied to the line",
          "II.5",
          all(sign(length(a, middle) * length(middle, b)
                   - length(a, point) * length(point, b)) >= 0
              for point in elsewhere + [d]))
    claim("with equality only when the application is to the half itself", "II.5",
          all(point == middle
              or sign(length(a, middle) * length(middle, b)
                      - length(a, point) * length(point, b)) > 0
              for point in elsewhere))
    return Out(greatest=on_half)


@proposition(
    "VI.28",
    CONSTRUCTION,
    sample=_deficient_application,
    note="The geometric solution of a quadratic. Euclid's proviso is exactly the "
    "condition for the discriminant not to be negative.",
)
def prop_VI_28(a: Point, b: Point, part) -> Out:
    """Apply to AB a parallelogram equal to a given area, deficient by a square."""
    hypothesis("A and B are distinct", a != b)
    hypothesis("the application is a proper one", sign(part) > 0 and sign(1 - part) > 0)
    line(a, b, "the given line AB")
    middle = posit(prop_I_10(a, b).midpoint, "C")

    whole = length(a, b)
    wanted = whole * whole * part * (1 - part)  # never more than the square on the half
    hypothesis("the given area does not exceed that on the half (VI.27)",
               sign(whole * whole / 4 - wanted) >= 0)

    # x(whole - x) = wanted has the root x = whole/2 - sqrt(whole^2/4 - wanted),
    # which is II.5 read as a formula: the half, less the piece between sections.
    gap = sqrt(whole * whole / 4 - wanted)
    cut = posit(_along(a, b, (whole / 2 - gap) / whole), "S")
    across = (-(b.y - a.y), b.x - a.x)
    applied = _parallelogram_on(a, cut, Point(a.x + across[0], a.y + across[1]))
    outline(*applied)

    claim("the point falls on AB, between A and the midpoint", "VI.27",
          on_line(cut, Line.through(a, b)) and sign(length(a, cut)) >= 0
          and sign(length(a, middle) - length(a, cut)) >= 0)
    claim("the rectangle applied equals the given area", "II.5",
          length(a, cut) * length(cut, b) == wanted)
    return Out(section=cut)


@proposition(
    "VI.29",
    CONSTRUCTION,
    sample=_deficient_application,
    note="The other root, and the other sign of the quadratic: here the figure "
    "runs past the end of the line instead of falling short of it.",
)
def prop_VI_29(a: Point, b: Point, part) -> Out:
    """Apply to AB a parallelogram equal to a given area, exceeding by a square."""
    hypothesis("A and B are distinct", a != b)
    hypothesis("the application is a proper one", sign(part) > 0 and sign(1 - part) > 0)
    line(a, b, "the given line AB")
    middle = posit(prop_I_10(a, b).midpoint, "C")

    whole = length(a, b)
    wanted = whole * whole * part * (1 + part)
    # x(x - whole) = wanted always has a root, however large the area: this is
    # the case II.6 covers, and it needs no proviso at all.
    excess = sqrt(whole * whole / 4 + wanted)
    beyond = posit(_along(a, b, (whole / 2 + excess) / whole), "S")
    across = (-(b.y - a.y), b.x - a.x)
    applied = _parallelogram_on(a, beyond, Point(a.x + across[0], a.y + across[1]))
    outline(*applied)

    claim("the point falls beyond B on AB produced", "II.6",
          on_line(beyond, Line.through(a, b))
          and sign(length(a, beyond) - length(a, b)) > 0)
    claim("the rectangle applied equals the given area", "II.6",
          length(a, beyond) * length(b, beyond) == wanted)
    claim("and it exceeds AB by the figure on BS", "II.6",
          length(a, beyond) == whole + length(b, beyond))
    return Out(section=beyond, midpoint=middle)


@proposition(
    "VI.26",
    THEOREM,
    sample=_parallelogram_with_similar_corner,
    note="The converse of VI.24, and the step VI.28 needs to know where the "
    "deficient parallelogram sits.",
)
def prop_VI_26(a: Point, b: Point, d: Point, part) -> Out:
    hypothesis("the parallelogram is genuine", not collinear(a, b, d))
    hypothesis("the division is a proper one", sign(part) > 0 and sign(1 - part) > 0)
    whole = _parallelogram_on(a, b, d)
    outline(*whole)
    inner = _parallelogram_on(a, posit(_along(a, b, part), "E"),
                              posit(_along(a, d, part), "G"))
    outline(*inner)
    hypothesis("the lesser is similar to the whole and shares the angle at A",
               similar((inner[0], inner[1], inner[2]), (whole[0], whole[1], whole[2])))

    diameter = line(a, whole[2], "the diameter AC")
    claim("the far corner of the lesser lies on the diameter of the whole", "VI.24",
          on_line(inner[2], diameter))
    return Out()


@proposition(
    "VI.30",
    CONSTRUCTION,
    sample=samples.segment,
    note="The golden section again, reached through ratios rather than through "
    "II.11's rectangles -- and giving the same point.",
)
def prop_VI_30(a: Point, b: Point) -> Out:
    hypothesis("A and B are distinct", a != b)
    line(a, b, "the given line AB")

    golden = (sqrt(5) - 1) / 2
    section = posit(_along(a, b, golden), "C")
    whole, greater, lesser = length(a, b), length(a, section), length(section, b)

    # The section is defined by an equality of figures, so the figures are built:
    # the square on the greater segment against the rectangle contained by the
    # whole and the lesser.
    square = _standing_on(a, section, greater)
    rectangle = _standing_on(a, b, lesser)
    outline(*square)
    outline(*rectangle)

    claim("the drawn figures are the square on AC and the rectangle AB by CB",
          "Def.22",
          _area(*square) == greater * greater and _area(*rectangle) == whole * lesser)
    claim("they are equal, which is what cutting in extreme and mean ratio means",
          "VI.17", _area(*square) == _area(*rectangle))
    claim("so the whole is to the greater as the greater is to the less", "VI.17",
          whole * lesser == greater * greater)
    claim("and the point is the same one II.11 finds", "II.11",
          length(a, section) == whole * golden)
    return Out(section=section, square=square, rectangle=rectangle)


@proposition(
    "VI.32",
    THEOREM,
    sample=_parallelogram_with_similar_corner,
)
def prop_VI_32(a: Point, b: Point, d: Point, part) -> Out:
    """Two similar triangles set together at a corner, with sides parallel."""
    hypothesis("the figure is genuine", not collinear(a, b, d))
    hypothesis("the division is a proper one", sign(part) > 0 and sign(1 - part) > 0)

    # Two triangles sharing the vertex A, the second the first scaled about it,
    # so corresponding sides are parallel and the outer sides fall in a line.
    e = posit(Point(a.x + (b.x - a.x) + (d.x - a.x), a.y + (b.y - a.y) + (d.y - a.y)), "E")
    far = posit(Point(a.x - part * (b.x - a.x), a.y - part * (b.y - a.y)), "F")
    outline(b, a, d)
    outline(d, e, close=False)
    line(far, b, "the side FB")

    claim("the corresponding sides are parallel", "I.33",
          parallel(Line.through(a, b), Line.through(d, e)))
    claim("so the remaining sides fall in one straight line", "I.14",
          collinear(far, a, b))
    return Out()


@proposition(
    "VI.33",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 3) + (samples.isometry(rng),),
    note="Angles are as the arcs they stand on -- the proportionality that lets "
    "an angle be measured by an arc at all.",
)
def prop_VI_33(o: Point, a: Point, b: Point, c: Point, move) -> Out:
    """Equal circles, and angles at their centres."""
    hypothesis("the points lie on the circle",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("the points are distinct", a != b and b != c)
    circle_with_radius2(o, len2(o, a), "the first circle")
    p, d, e = posit(move(o), "P"), posit(move(a), "D"), posit(move(b), "E")
    circle_with_radius2(p, len2(p, d), "the second, equal to it")
    for pair in ((o, a), (o, b), (p, d), (p, e)):
        line(*pair, "a radius")

    claim("the circles are equal", "Def.15", eq_len(o, a, p, d))
    claim("equal angles at the centres stand on equal arcs, so angle is as arc",
          "III.26", eq_angle(a, o, b, d, p, e) == eq_len(a, b, d, e))
    claim("and the angle at the circumference is half that at the centre, so the "
          "same proportion holds there", "III.20",
          angle_at(a, o, b) == angle_at(a, c, b).doubled()
          or angle_at(a, o, b) == STRAIGHT + STRAIGHT - angle_at(a, c, b).doubled())
    return Out()


@proposition(
    "VI.20",
    THEOREM,
    sample=_similar_polygons,
    note="The general form of Pythagoras' area law, and what VI.31 leans on: "
    "areas of similar figures go as the squares on their sides, whatever the figures are.",
)
def prop_VI_20(
    a: Point, b: Point, c: Point, d: Point,
    p: Point, q: Point, r: Point, s: Point,
) -> Out:
    """ABCD and PQRS are similar; each is cut into triangles from a vertex."""
    first, second = [a, b, c, d], [p, q, r, s]

    # Similarity of polygons, said without angles: every distance between
    # corresponding vertices stands in one ratio. For a quadrilateral that is
    # the four sides and the two diagonals, which fix the shape.
    def in_one_ratio(i: int, j: int) -> bool:
        return (len2(first[i], first[j]) * len2(second[0], second[1])
                == len2(second[i], second[j]) * len2(first[0], first[1]))

    hypothesis("the polygons are similar",
               all(in_one_ratio(i, j) for i in range(4) for j in range(i + 1, 4)))
    hypothesis("neither is degenerate", not collinear(a, b, c) and not collinear(a, c, d))

    outline(*first)
    outline(*second)
    line(a, c, "the diameter dividing ABCD")
    line(p, r, "and the corresponding diameter of PQRS")

    # Fan each polygon into triangles from its first vertex, as Euclid does.
    def fan(vertices):
        return [(vertices[0], vertices[i], vertices[i + 1]) for i in range(1, len(vertices) - 1)]

    cut_first, cut_second = fan(first), fan(second)
    whole_first, whole_second = _area(*first), _area(*second)

    claim("the polygons divide into triangles equal in multitude", "VI.Def.1",
          len(cut_first) == len(cut_second))
    claim("and the triangles are similar, each to its fellow", ["VI.6", "VI.4"],
          all(similar(one, other) for one, other in zip(cut_first, cut_second)))
    claim("each triangle is to its fellow as the whole polygon is to the whole", "V.12",
          all(_area(*one) * whole_second == _area(*other) * whole_first
              for one, other in zip(cut_first, cut_second)))
    claim("similar triangles are to one another in the duplicate ratio of their "
          "corresponding sides", "VI.19",
          all(_area(*one) * len2(second[0], second[1])
              == _area(*other) * len2(first[0], first[1])
              for one, other in zip(cut_first, cut_second)))
    claim("therefore the polygon has to the polygon the duplicate ratio of the "
          "corresponding sides", ["VI.19", "V.12"],
          whole_first * len2(p, q) == whole_second * len2(a, b))
    return Out(triangles=(cut_first, cut_second))


@proposition(
    "VI.31",
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
