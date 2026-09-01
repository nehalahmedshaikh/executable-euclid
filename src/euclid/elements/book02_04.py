"""Books II, III and IV, complete: geometric algebra, circles, inscribed figures.

Book II is algebra without symbols, and its propositions are identities about
area: II.4 is the expansion of ``(a+b)^2``, II.11 cuts a line in extreme and
mean ratio, II.12 and II.13 are the law of cosines with its two signs.  The
rectangles it argues about are built and drawn here, and every claim is checked
against the polygon actually on the page.

Book III is the circle: tangents, inscribed angles, and the power of a point.
Book IV inscribes and circumscribes -- triangle, square, pentagon, hexagon, and
the fifteen-angled figure, which Euclid reaches because a third of a circle less
a fifth leaves two fifteenths.  IV.11 builds the pentagon on top of II.11, and
the golden ratio arrives in the kernel as an exact element of ``Q(sqrt 5)``
rather than as 1.618.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import is_zero, sign, sqrt, to_float
from ..plane.angles import RIGHT, STRAIGHT, angle_at, length
from ..plane.construct import (
    GeometryError,
    circle,
    circle_with_radius2,
    line,
    meet,
    meet_one,
    outline,
    posit,
)
from ..plane.objects import Line, Point
from ..plane.predicates import (
    between,
    collinear,
    eq_angle,
    eq_len,
    len2,
    inside_circle,
    on_circle,
    on_line,
    parallel,
    polygon_area2,
    right_angle,
    same_side,
)
from . import samples
from .book01_foundations import prop_I_10, prop_I_11
from .book01_parallels import prop_I_46
from .registry import CONSTRUCTION, THEOREM, Out, claim, hypothesis, proposition

# ---------------------------------------------------------------------------
# Book II -- geometric algebra
# ---------------------------------------------------------------------------
#
# Book II is about rectangles and squares standing on the parts of a divided
# line, and its propositions are the identities of school algebra written as
# statements about area. So the figures here are the rectangles themselves,
# built and drawn, and every claim is checked against the area of the polygon
# actually on the page rather than against a product of lengths. That is a
# stronger reading of the text: Euclid is talking about figures.
#
# Rectangles cost nothing to build exactly. A rectangle "contained by" two
# segments of one straight line needs the second lifted off that line at right
# angles, and turning a step through a right angle -- (x, y) to (-y, x) -- does
# it without taking a single square root.


def _area(*points: Point):
    """The area enclosed by a polygon, positive whichever way it was traced."""
    value = polygon_area2(list(points))
    return (value if value >= 0 else -value) / 2


def _across(p: Point, q: Point) -> tuple:
    """The step from P to Q, turned through a right angle."""
    return -(q.y - p.y), q.x - p.x


def _rectangle(p: Point, q: Point, across: tuple, near: str, far: str) -> tuple:
    """Draw the rectangle standing on PQ, and letter its two new corners."""
    third = posit(Point(q.x + across[0], q.y + across[1]), far)
    fourth = posit(Point(p.x + across[0], p.y + across[1]), near)
    outline(p, q, third, fourth)
    return p, q, third, fourth


def _adjacent_segments(rng):
    """A, B, C in a straight line with B between: the sides of a rectangle
    laid end to end."""
    move = samples.frame(rng)
    first, second = samples.nonzero(rng, 1, 6), samples.nonzero(rng, 1, 6)
    return move(Point(0, 0)), move(Point(first, 0)), move(Point(first + second, 0))


def _cut_and_lifted(rng):
    """A cut line B..C with the cut points, and G giving the height BG.

    Euclid raises the second of his "two straight lines" perpendicular to the
    first (I.11) and cuts it to length (I.3); handing it over as a point does
    the same job and keeps every coordinate rational.
    """
    move = samples.frame(rng)
    parts = [samples.nonzero(rng, 1, 4) for _ in range(3)]
    stops = [sum(parts[:index]) for index in range(4)]
    height = samples.nonzero(rng, 1, 5)
    b, d, e, c = (move(Point(stop, 0)) for stop in stops)
    return b, c, d, e, move(Point(0, height))


@proposition(
    "II.1",
    THEOREM,
    sample=_cut_and_lifted,
    note="The distributive law, a(x+y+z) = ax+ay+az, stated about areas. Every "
    "later proposition in the book is a special case of it.",
)
def prop_II_1(b: Point, c: Point, d: Point, e: Point, g: Point) -> Out:
    """BC is cut at D and E; BG is the uncut line, set up at right angles."""
    hypothesis("D and E cut BC, in that order",
               between(b, d, c) and between(b, e, c) and between(d, e, c))
    hypothesis("BG is at right angles to BC", right_angle(g, b, c))

    lift = (g.x - b.x, g.y - b.y)
    whole = _rectangle(b, c, lift, "G", "H")
    first = _rectangle(b, d, lift, "G", "K")
    middle = _rectangle(d, e, lift, "K", "L")
    last = _rectangle(e, c, lift, "L", "H")

    claim("the three rectangles together fill the whole one", "C.N.2",
          _area(*first) + _area(*middle) + _area(*last) == _area(*whole))
    claim("so the rectangle on the uncut line and the whole equals the rectangles "
          "on the uncut line and each segment", "C.N.2",
          _area(*whole) == _area(*first) + _area(*middle) + _area(*last))
    return Out(whole=whole, parts=(first, middle, last))


@proposition(
    "II.2",
    THEOREM,
    sample=_adjacent_segments,
)
def prop_II_2(a: Point, b: Point, c: Point) -> Out:
    """AC is cut at B. The square on AC is divided at B into the two rectangles."""
    hypothesis("B cuts AC", between(a, b, c))

    lift = _across(a, c)
    square = _rectangle(a, c, lift, "D", "E")
    cut = posit(Point(b.x + lift[0], b.y + lift[1]), "F")
    line(b, cut, "BF, dividing the square")

    first = (a, b, cut, square[3])
    second = (b, c, square[2], cut)
    claim("BF divides the square into the two rectangles", "C.N.2",
          _area(*first) + _area(*second) == _area(*square))
    claim("each is contained by the whole and one segment", "Def.22",
          _area(*first) == length(a, c) * length(a, b)
          and _area(*second) == length(a, c) * length(b, c))
    claim("so the two rectangles together equal the square on the whole", "C.N.2",
          _area(*first) + _area(*second) == length(a, c) * length(a, c))
    return Out(square=square)


@proposition(
    "II.3",
    THEOREM,
    sample=_adjacent_segments,
)
def prop_II_3(a: Point, b: Point, c: Point) -> Out:
    """AC is cut at B; the rectangle stands on AC with height BC."""
    hypothesis("B cuts AC", between(a, b, c))

    lift = _across(b, c)
    whole = _rectangle(a, c, lift, "E", "D")
    cut = posit(Point(b.x + lift[0], b.y + lift[1]), "F")
    line(b, cut, "BF, dividing the rectangle")

    on_segments = (a, b, cut, whole[3])
    square = (b, c, whole[2], cut)
    claim("BF divides the rectangle into two", "C.N.2",
          _area(*on_segments) + _area(*square) == _area(*whole))
    claim("the far piece is the square on BC", "Def.22",
          _area(*square) == len2(b, c) and right_angle(a, b, cut) and eq_len(b, c, b, cut))
    claim("so the rectangle on the whole and one segment equals the rectangle on the "
          "segments together with the square on that segment", "C.N.2",
          _area(*whole) == _area(*on_segments) + len2(b, c))
    return Out(rectangle=whole)


@proposition(
    "II.4",
    THEOREM,
    sample=_adjacent_segments,
    note="(a+b)^2 = a^2 + 2ab + b^2, four centuries before algebraic notation.",
)
def prop_II_4(a: Point, b: Point, c: Point) -> Out:
    """AC is cut at B, and the square on AC is cut both ways through B."""
    hypothesis("B cuts AC", between(a, b, c))

    # The square on the whole, divided as Euclid divides it: the two cuts
    # through B leave the squares on the two segments at opposite corners, and
    # the rectangle they contain twice over between them.
    low, high = _across(a, b), _across(b, c)
    lift = (low[0] + high[0], low[1] + high[1])
    d = posit(Point(a.x + lift[0], a.y + lift[1]), "D")
    e = posit(Point(c.x + lift[0], c.y + lift[1]), "E")
    outline(a, c, e, d)
    f = posit(Point(b.x + lift[0], b.y + lift[1]), "F")
    g = posit(Point(a.x + low[0], a.y + low[1]), "G")
    h = posit(Point(b.x + low[0], b.y + low[1]), "H")
    k = posit(Point(c.x + low[0], c.y + low[1]), "K")
    line(b, f, "BF")
    line(g, k, "GK")
    # Euclid draws the diameter, because his reason for the two rectangles being
    # equal is I.43: they are the complements of the figures about it. Drawing
    # it is what makes the cited step visible in the figure.
    line(a, e, "the diameter AE")

    on_first, on_second = (a, b, h, g), (h, k, e, f)
    between_them = ((b, c, k, h), (g, h, f, d))
    whole = length(a, c)
    first, second = length(a, b), length(b, c)

    claim("the segments together make the whole", "C.N.2", first + second == whole)
    claim("the two cuts leave four figures that fill the square", "C.N.2",
          _area(a, c, e, d)
          == _area(*on_first) + _area(*on_second)
          + _area(*between_them[0]) + _area(*between_them[1]))
    claim("the squares on the segments stand about the diameter", "I.43",
          on_line(h, Line.through(a, e)))
    claim("two of them are the squares on the segments", "I.46",
          _area(*on_first) == first * first and _area(*on_second) == second * second)
    claim("and the other two, being the complements about the diameter, are each the "
          "rectangle contained by the segments", "I.43",
          _area(*between_them[0]) == first * second
          and _area(*between_them[1]) == first * second)
    claim("so the square on the whole equals the squares on the parts together with "
          "twice the rectangle they contain", ["I.43", "I.46"],
          whole * whole == first * first + second * second + 2 * first * second)
    return Out(square=(a, c, e, d), pieces=(on_first, on_second) + between_them)


@proposition(
    "II.5",
    THEOREM,
    sample=_adjacent_segments,
    note="Euclid's tool for solving quadratics: ab + ((a-b)/2)^2 = ((a+b)/2)^2.",
)
def prop_II_5(a: Point, b: Point, c: Point) -> Out:
    """AC is bisected at D and cut unequally at B."""
    hypothesis("B cuts AC unequally", between(a, b, c))
    middle = posit(prop_I_10(a, c).midpoint, "D")
    hypothesis("the two sections are distinct", middle != b)
    outline(a, c, close=False)

    # The rectangle on the unequal segments stands above the line, the square on
    # the half below it, so the two areas being compared can be seen at once.
    rectangle = _rectangle(a, b, _across(b, c), "E", "F")
    square = _rectangle(middle, c, _across(c, middle), "H", "G")

    first, second = length(a, b), length(b, c)
    half, offset = length(a, middle), length(middle, b)
    claim("D bisects AC", "I.10", eq_len(a, middle, middle, c))
    claim("the drawn rectangle is contained by the unequal segments", "Def.22",
          _area(*rectangle) == first * second)
    claim("and the drawn square is the square on the half", "I.46",
          _area(*square) == half * half)
    claim("the rectangle on the unequal segments, with the square on the piece between "
          "the sections, equals the square on the half", ["I.43", "I.46"],
          _area(*rectangle) + offset * offset == _area(*square))
    return Out(midpoint=middle, rectangle=rectangle, square=square)


def _bisected_and_produced(rng):
    """AB bisected, and BD added to it in a straight line (II.6, II.10)."""
    move = samples.frame(rng)
    half = samples.nonzero(rng, 1, 5)
    added = samples.nonzero(rng, 1, 5)
    return move(Point(0, 0)), move(Point(2 * half, 0)), move(Point(2 * half + added, 0))


def _equal_and_unequal(rng):
    """AB bisected at C and cut unequally at D (II.9)."""
    move = samples.frame(rng)
    half = samples.nonzero(rng, 2, 6)
    offset = samples.nonzero(rng, 1, 3) / 2
    while offset >= half:
        offset = offset / 2
    return move(Point(0, 0)), move(Point(2 * half, 0)), move(Point(half + offset, 0))


@proposition(
    "II.6",
    THEOREM,
    sample=_bisected_and_produced,
    note="The companion to II.5, and the other half of Euclid's method for "
    "quadratics: ab + ((a-b)/2)^2 = ((a+b)/2)^2 with the sign the other way.",
)
def prop_II_6(a: Point, b: Point, d: Point) -> Out:
    """AB is bisected at C and produced to D."""
    hypothesis("B lies between A and D", between(a, b, d))
    c = posit(prop_I_10(a, b).midpoint, "C")

    lift = _across(b, d)
    whole = _rectangle(a, d, lift, "M", "K")
    outline(a, d, close=False)

    half, added = length(a, c), length(b, d)
    claim("C bisects AB", "I.10", eq_len(a, c, c, b))
    claim("the rectangle contained by AD and DB, with the square on the half, "
          "equals the square on CD", ["II.5", "I.46"],
          _area(*whole) + half * half == length(c, d) * length(c, d))
    claim("and CD is the half together with the added line", "C.N.2",
          length(c, d) == half + added)
    return Out(rectangle=whole, midpoint=c)


@proposition(
    "II.7",
    THEOREM,
    sample=_adjacent_segments,
    note="(a+b)^2 + b^2 = 2(a+b)b + a^2.",
)
def prop_II_7(a: Point, b: Point, c: Point) -> Out:
    """AC is cut at B; the squares are on AC and on BC."""
    hypothesis("B cuts AC", between(a, b, c))

    square = _rectangle(a, c, _across(a, c), "D", "E")
    cut = posit(Point(b.x + _across(a, c)[0], b.y + _across(a, c)[1]), "F")
    line(b, cut, "BF")

    whole, part, rest = length(a, c), length(b, c), length(a, b)
    claim("the square on the whole is the figure drawn on AC", "I.46",
          _area(*square) == whole * whole)
    claim("the squares on the whole and on one segment together equal twice the "
          "rectangle on the whole and that segment, with the square on the rest",
          ["II.4", "C.N.2"],
          whole * whole + part * part == 2 * (whole * part) + rest * rest)
    return Out(square=square)


@proposition(
    "II.8",
    THEOREM,
    sample=_adjacent_segments,
    note="4(a+b)b + a^2 = (a+2b)^2.",
)
def prop_II_8(a: Point, b: Point, c: Point) -> Out:
    """AC is cut at B, and BC is added again beyond C."""
    hypothesis("B cuts AC", between(a, b, c))
    beyond = posit(Point(c.x + (c.x - b.x), c.y + (c.y - b.y)), "D")

    square = _rectangle(a, beyond, _across(a, beyond), "M", "N")
    outline(a, beyond, close=False)

    whole, part, rest = length(a, c), length(b, c), length(a, b)
    claim("CD equals CB, so AD is the whole with that segment added again", ["I.3", "C.N.2"],
          eq_len(c, beyond, b, c) and length(a, beyond) == whole + part)
    claim("the square described on AD equals four times the rectangle on the whole "
          "and the segment, together with the square on the remaining segment",
          ["II.4", "II.7"],
          _area(*square) == 4 * (whole * part) + rest * rest)
    return Out(square=square)


@proposition(
    "II.9",
    THEOREM,
    sample=_equal_and_unequal,
)
def prop_II_9(a: Point, b: Point, d: Point) -> Out:
    """AB is bisected at C and cut unequally at D."""
    hypothesis("D cuts AB", between(a, d, b))
    c = posit(prop_I_10(a, b).midpoint, "C")
    hypothesis("the two sections are distinct", c != d)
    outline(a, b, close=False)

    # Euclid raises a right-angled isosceles triangle on the half; drawing it is
    # what makes the doubling visible rather than merely algebraic.
    apex = posit(Point(c.x + _across(c, b)[0], c.y + _across(c, b)[1]), "E")
    outline(a, apex, b, close=False)
    line(apex, d, "ED")

    claim("CE is the half set up at right angles", "I.11",
          right_angle(apex, c, b) and eq_len(c, apex, c, b))
    claim("the squares on the unequal segments are double the square on the half "
          "and the square on the line between the sections", ["I.47", "II.4"],
          len2(a, d) + len2(d, b) == 2 * (len2(a, c) + len2(c, d)))
    return Out(midpoint=c, apex=apex)


@proposition(
    "II.10",
    THEOREM,
    sample=_bisected_and_produced,
)
def prop_II_10(a: Point, b: Point, d: Point) -> Out:
    """AB is bisected at C and produced to D."""
    hypothesis("B lies between A and D", between(a, b, d))
    c = posit(prop_I_10(a, b).midpoint, "C")
    outline(a, d, close=False)

    apex = posit(Point(c.x + _across(c, b)[0], c.y + _across(c, b)[1]), "E")
    outline(a, apex, b, close=False)
    line(apex, d, "ED")

    claim("CE is the half set up at right angles", "I.11",
          right_angle(apex, c, b) and eq_len(c, apex, c, b))
    claim("the squares on the whole with the addition and on the addition are double "
          "the square on the half and the square on the half with the addition",
          ["I.47", "II.4"],
          len2(a, d) + len2(b, d) == 2 * (len2(a, c) + len2(c, d)))
    return Out(midpoint=c, apex=apex)


@proposition(
    "II.11",
    CONSTRUCTION,
    sample=samples.segment,
    note="The golden section. The point of division is irrational; the kernel holds "
    "it exactly, as (sqrt(5)-1)/2 of the whole.",
)
def prop_II_11(a: Point, b: Point) -> Out:
    hypothesis("A and B are distinct", a != b)
    _, _, _, d = prop_I_46(a, b).square
    middle = posit(prop_I_10(a, d).midpoint, "E")
    reach = circle_with_radius2(middle, len2(middle, b), "circle centre E through B")
    f = posit(meet(line(d, a), reach)[1], "F")
    cut_off = circle_with_radius2(a, len2(a, f), "circle centre A with radius AF")
    h = posit(meet(line(a, b), cut_off)[1], "H")

    whole, greater = length(a, b), length(a, h)
    lesser = length(h, b)
    claim("H divides AB", "Post.1", on_line(h, Line.through(a, b)))
    claim("the rectangle contained by the whole and the lesser segment equals the "
          "square on the greater", ["II.6", "I.47"], whole * lesser == greater * greater)
    claim("so the whole is cut in extreme and mean ratio", "Def.3",
          greater * greater + greater * whole == whole * whole)
    return Out(section=h)


def _foot_of_the_perpendicular(apex: Point, first: Point, second: Point) -> Point:
    """Where the perpendicular from the apex meets the line through the base.

    Projection is a ratio of dot products, so the foot is rational whenever the
    three given points are -- no square root, and no new level on the tower.
    """
    ux, uy = second.x - first.x, second.y - first.y
    vx, vy = apex.x - first.x, apex.y - first.y
    along = (ux * vx + uy * vy) / (ux * ux + uy * uy)
    return Point(first.x + along * ux, first.y + along * uy)


@proposition(
    "II.12",
    THEOREM,
    sample=samples.obtuse_triangle,
    note="The law of cosines, with the sign for an obtuse angle. Euclid has no "
    "cosine, so the correction term is a rectangle he can point at.",
)
def prop_II_12(a: Point, b: Point, c: Point) -> Out:
    """The obtuse angle is at B; the perpendicular from A falls on CB produced."""
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    hypothesis("the angle at B is obtuse", angle_at(a, b, c) > RIGHT)
    outline(a, b, c)

    d = posit(_foot_of_the_perpendicular(a, c, b), "D")
    line(c, d, "CB produced to D")
    line(a, d, "the perpendicular AD")

    hypothesis("the perpendicular falls outside the triangle, beyond B", between(c, b, d))
    claim("AD is perpendicular to CD", "I.12", right_angle(a, d, c))
    # CB and BD run the same way out of B, so the rectangle they contain is the
    # dot product -- exact, and without a square root anywhere.
    rectangle = length(c, b) * length(b, d)
    claim("the square on the side subtending the obtuse angle exceeds the squares on "
          "the other two by twice the rectangle contained by CB and BD",
          ["I.47", "II.4"],
          len2(a, c) == len2(a, b) + len2(c, b) + 2 * rectangle)
    return Out(foot=d)


@proposition(
    "II.13",
    THEOREM,
    sample=samples.acute_triangle,
    note="The other sign of the law of cosines. Heath's enunciation is not shown "
    "here: the only copy of it available to this project scans 'acute' as "
    "'acutc', and it is dropped rather than mended.",
)
def prop_II_13(a: Point, b: Point, c: Point) -> Out:
    """The angle at B is acute; the perpendicular from A falls inside CB."""
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    hypothesis("the angle at B is acute", angle_at(a, b, c) < RIGHT)
    outline(a, b, c)

    d = posit(_foot_of_the_perpendicular(a, c, b), "D")
    line(a, d, "the perpendicular AD")

    hypothesis("the perpendicular falls within CB", between(c, d, b))
    claim("AD is perpendicular to CB", "I.12", right_angle(a, d, c))
    rectangle = length(c, b) * length(b, d)
    claim("the square on the side subtending the acute angle falls short of the "
          "squares on the other two by twice the rectangle contained by CB and BD",
          ["I.47", "II.7"],
          len2(a, c) + 2 * rectangle == len2(a, b) + len2(c, b))
    return Out(foot=d)


@proposition(
    "II.14",
    CONSTRUCTION,
    sample=_adjacent_segments,
    note="Quadrature of the rectangle. The side of the equal square is the mean "
    "proportional between the sides, raised as the height of a semicircle.",
)
def prop_II_14(a: Point, b: Point, c: Point) -> Out:
    """The rectangle has sides AB and BC, laid end to end along AC."""
    hypothesis("B lies between A and C", on_line(b, Line.through(a, c)) and b != a and b != c)
    middle = posit(prop_I_10(a, c).midpoint, "M")
    semicircle = circle_with_radius2(middle, len2(middle, a), "the semicircle on AC")
    upright = prop_I_11(a, c, b).perpendicular
    d = posit(meet(upright, semicircle)[1], "D")
    square = prop_I_46(b, d).square

    # Euclid has no Book III here, and does not need it: the right angle is the
    # one he constructed at B, not the one in the semicircle. II.5 and I.47 do
    # the rest between them.
    claim("BD stands at right angles to AC, being so constructed", "I.11",
          right_angle(d, b, a))
    claim("MD and MA are equal, both radii of the semicircle", "Def.15",
          eq_len(middle, d, middle, a))
    claim("the square on MD equals the squares on MB and BD", "I.47",
          len2(middle, d) == len2(middle, b) + len2(b, d))
    claim("the rectangle AB by BC, with the square on MB, equals the square on MA",
          "II.5", length(a, b) * length(b, c) + len2(middle, b) == len2(middle, a))
    claim("so the square on BD equals the given rectangle", "C.N.3",
          len2(b, d) == length(a, b) * length(b, c))
    return Out(square=square, side=(b, d))


# ---------------------------------------------------------------------------
# Book III -- circles
# ---------------------------------------------------------------------------


def _points_on_a_circle(rng):
    """A circle with a diameter AB and a third point C on the circumference."""
    move = samples.frame(rng)
    radius = samples.nonzero(rng, 2, 5)
    cosine, sine = samples.rational_rotation(rng)
    if sine == 0:
        cosine, sine = Fraction(3, 5), Fraction(4, 5)
    return (
        move(Point(0, 0)),
        move(Point(-radius, 0)),
        move(Point(radius, 0)),
        move(Point(radius * cosine, radius * sine)),
    )


def _two_on_a_circle(rng):
    return samples.points_round_a_circle(rng, 2)


def _three_on_a_circle(rng):
    return samples.points_round_a_circle(rng, 3)


def _four_on_a_circle(rng):
    return samples.points_round_a_circle(rng, 4)


@proposition(
    "III.1",
    CONSTRUCTION,
    sample=_three_on_a_circle,
    note="Euclid opens the book by finding the centre, because everything after "
    "it is stated about a circle whose centre is known.",
)
def prop_III_1(o: Point, a: Point, b: Point, c: Point) -> Out:
    """The circle is given by three of its points; the centre is to be found."""
    hypothesis("A, B and C lie on one circle and are distinct",
               eq_len(o, a, o, b) and eq_len(o, a, o, c) and not collinear(a, b, c))
    circle(o, a, "the given circle")
    outline(a, b, c)

    found = posit(_centre_of(a, b, c), "F")
    line(found, a)
    line(found, b)
    line(found, c)

    claim("the point found is equally distant from all three", ["I.10", "I.11"],
          eq_len(found, a, found, b) and eq_len(found, a, found, c))
    # III.9 proves the uniqueness, but it comes later; here it follows from the
    # two bisectors meeting in one point and no other.
    claim("and it is the centre, every line from it to the circle being a radius",
          "Def.15", found == o and eq_len(found, a, o, a))
    return Out(centre=found)


@proposition(
    "III.2",
    THEOREM,
    sample=_two_on_a_circle,
)
def prop_III_2(o: Point, a: Point, b: Point) -> Out:
    hypothesis("A and B lie on the circle and are distinct",
               eq_len(o, a, o, b) and a != b)
    around = circle(o, a, "the given circle")
    chord = line(a, b, "the joining line AB")
    middle = posit(prop_I_10(a, b).midpoint, "M")

    claim("the midpoint of the join lies inside the circle", "Def.15",
          inside_circle(middle, around))
    claim("and so does every point of it strictly between the ends", "I.18",
          all(inside_circle(Point(a.x + Fraction(k, 8) * (b.x - a.x),
                                  a.y + Fraction(k, 8) * (b.y - a.y)), around)
              for k in range(1, 8)))
    return Out(chord=chord)


@proposition(
    "III.4",
    THEOREM,
    sample=_four_on_a_circle,
)
def prop_III_4(o: Point, a: Point, b: Point, c: Point, d: Point) -> Out:
    """AC and BD are chords, neither through the centre, crossing inside."""
    hypothesis("the four points lie on one circle",
               all(eq_len(o, p, o, a) for p in (b, c, d)))
    hypothesis("neither chord passes through the centre",
               not on_line(o, Line.through(a, c)) and not on_line(o, Line.through(b, d)))
    circle(o, a, "the given circle")
    first, second = line(a, c, "AC"), line(b, d, "BD")
    hypothesis("the chords are not parallel", not parallel(first, second))
    crossing = posit(meet_one(first, second), "E")

    claim("all four ends lie on the circle, so both lines are chords of it",
          "Def.15",
          all(on_circle(point, circle(o, a)) for point in (a, b, c, d)))
    claim("the crossing falls inside the circle", "III.2", inside_circle(crossing, circle(o, a)))
    claim("were E to bisect both, the lines from the centre would be "
          "perpendicular to each and the centre would lie on both", "III.3",
          not (eq_len(a, crossing, crossing, c) and eq_len(b, crossing, crossing, d)))
    return Out(crossing=crossing)


@proposition(
    "III.5",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 1) + (samples.nonzero(rng, 1, 3),),
    note="Stated as a negative, and checked as one: two circles that cut cannot "
    "share a centre, because their radii would then have to be equal.",
)
def prop_III_5(o: Point, a: Point, difference) -> Out:
    """A second circle on the same centre, of a different radius."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("the second radius differs from the first", sign(difference) != 0)
    first = circle(o, a, "the first circle")
    outer = posit(_along_from(o, a, length(o, a) + difference), "B")
    second = circle(o, outer, "a second circle on the same centre")

    # Cutting means sharing a point. Test that against the whole circumference,
    # not against a convenient point or two: every point of either circle is
    # checked against the other, and none of them lies on it.
    claim("the two radii are unequal", "Def.15", not eq_len(o, a, o, outer))
    claim("so no point of either circle lies on the other, and they never cut",
          "Def.15",
          not any(on_circle(point, second) for point in _round(o, a))
          and not any(on_circle(point, first) for point in _round(o, outer)))
    return Out()


@proposition(
    "III.6",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 1) + (samples.nonzero(rng, 1, 3),),
)
def prop_III_6(o: Point, a: Point, difference) -> Out:
    hypothesis("the circle has positive radius", o != a)
    hypothesis("the second radius differs from the first", sign(difference) != 0)
    circle(o, a, "the first circle")
    outer = posit(_along_from(o, a, length(o, a) + difference), "B")
    circle(o, outer, "a second circle on the same centre")

    claim("the two radii are unequal", "Def.15", not eq_len(o, a, o, outer))
    claim("touching means one point in common, and these two share none", "Def.15",
          not any(on_circle(point, circle(o, outer)) for point in _round(o, a)))
    return Out()


@proposition(
    "III.9",
    THEOREM,
    sample=_three_on_a_circle,
    note="The converse of the definition of a circle, and the reason III.1 can "
    "speak of *the* centre.",
)
def prop_III_9(o: Point, a: Point, b: Point, c: Point) -> Out:
    """From the point O fall three equal lines on the circle."""
    hypothesis("three distinct points of the circle are equally distant from O",
               eq_len(o, a, o, b) and eq_len(o, a, o, c) and not collinear(a, b, c))
    circle(o, a, "the given circle")
    outline(a, b, c)
    for point in (a, b, c):
        line(o, point)

    claim("the point equally distant from three points of a circle is unique",
          ["I.10", "I.11"], _centre_of(a, b, c) == o)
    claim("and it is the centre", "Def.15", eq_len(o, a, o, b) and eq_len(o, b, o, c))
    return Out(centre=o)


@proposition(
    "III.10",
    THEOREM,
    sample=_three_on_a_circle,
)
def prop_III_10(o: Point, a: Point, b: Point, c: Point) -> Out:
    """Three points cannot lie on two different circles."""
    hypothesis("A, B and C are three distinct points of a circle",
               eq_len(o, a, o, b) and eq_len(o, a, o, c) and not collinear(a, b, c))
    circle(o, a, "the given circle")
    outline(a, b, c)

    # Any circle through all three has the centre found from them, and so has
    # this centre and this radius: it *is* this circle. Two distinct circles
    # therefore cannot share three points, and cutting in three is impossible.
    claim("three points of a circle determine its centre", "III.9",
          _centre_of(a, b, c) == o)
    claim("and with the centre the radius, so any circle through all three is "
          "this same circle", "Def.15",
          eq_len(_centre_of(a, b, c), a, o, a))
    claim("so two circles sharing three points coincide everywhere", "Def.15",
          all(on_circle(point, circle(_centre_of(a, b, c), a)) for point in _round(o, a)))
    return Out()


@proposition(
    "III.7",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 1)
    + (Fraction(rng.randint(1, 3), 4),),
    note="The first of Euclid's two 'nearer is greater' propositions, and the "
    "one that needs an interior point.",
)
def prop_III_7(o: Point, a: Point, part) -> Out:
    """F is on the diameter DA, between the centre and A."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("F is not the centre", sign(part) > 0)
    circle(o, a, "the given circle")
    far = posit(Point(o.x - (a.x - o.x), o.y - (a.y - o.y)), "D")
    f = posit(Point(o.x + part * (a.x - o.x), o.y + part * (a.y - o.y)), "F")
    line(far, a, "the diameter DA")

    # F lies between O and A, so it is FD that has the centre on it and FA that
    # is the remainder. Points are taken at angles increasing away from A, which
    # is the order "nearer to the line through the centre" puts them in.
    reach = (a.x - o.x, a.y - o.y)
    turned = []
    for step in range(1, 5):
        half = Fraction(step, 4)
        cosine, sine = (1 - half * half) / (1 + half * half), 2 * half / (1 + half * half)
        turned.append(posit(
            Point(o.x + reach[0] * cosine - reach[1] * sine,
                  o.y + reach[0] * sine + reach[1] * cosine),
            f"P{step}",
        ))
    for point in turned:
        line(f, point)

    claim("the line on which the centre is, is the greatest", "I.20",
          all(sign(length(f, far) - length(f, point)) > 0 for point in turned + [a]))
    claim("and the remainder of that diameter is the least", "I.20",
          all(sign(length(f, point) - length(f, a)) > 0 for point in turned + [far]))
    claim("of the rest, the nearer to the line through the centre is the greater",
          "I.24",
          all(sign(length(f, turned[i + 1]) - length(f, turned[i])) > 0
              for i in range(len(turned) - 1)))
    return Out(greatest=far, least=a)


@proposition(
    "III.8",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 1)
    + (1 + Fraction(rng.randint(2, 8), 4),),
    note="The external twin of III.7. The same monotonicity, read from a point "
    "outside: distance grows steadily with the angle turned from the near end.",
)
def prop_III_8(o: Point, a: Point, beyond) -> Out:
    """P is outside, on the diameter through A; A is the near end, D the far."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("P lies outside the circle", sign(beyond - 1) > 0)
    circle(o, a, "the given circle")
    far = posit(Point(o.x - (a.x - o.x), o.y - (a.y - o.y)), "D")
    p = posit(Point(o.x + beyond * (a.x - o.x), o.y + beyond * (a.y - o.y)), "P")
    line(p, far, "the line through the centre")

    reach = (a.x - o.x, a.y - o.y)
    turned = []
    for step in range(1, 5):
        half = Fraction(step, 4)
        cosine, sine = (1 - half * half) / (1 + half * half), 2 * half / (1 + half * half)
        turned.append(posit(
            Point(o.x + reach[0] * cosine - reach[1] * sine,
                  o.y + reach[0] * sine + reach[1] * cosine),
            f"P{step}",
        ))
    for point in turned:
        line(p, point)

    claim("of those falling on the concave circumference, that through the centre "
          "is greatest", "I.20",
          all(sign(length(p, far) - length(p, point)) > 0 for point in turned + [a]))
    claim("of those falling on the convex circumference, that between the point and "
          "the diameter is least", "I.20",
          all(sign(length(p, point) - length(p, a)) > 0 for point in turned + [far]))
    claim("and of the rest, the nearer to the least is the less", "I.24",
          all(sign(length(p, turned[i + 1]) - length(p, turned[i])) > 0
              for i in range(len(turned) - 1)))
    mirrored = posit(_mirror_in(turned[0], o, a), "Q")
    line(p, mirrored)
    claim("only two equal lines fall from the point, one on each side of the least",
          "I.24",
          eq_len(p, turned[0], p, mirrored) and mirrored != turned[0])
    return Out(greatest=far, least=a)


def _touching_circles(rng, internally: bool):
    """Two circles touching at one point, on the same or opposite sides."""
    move = samples.frame(rng, scaled=False)
    big = samples.nonzero(rng, 4, 7)
    small = big * Fraction(rng.randint(1, 3), 4)
    centre = big - small if internally else big + small
    return (
        move(Point(0, 0)),
        move(Point(big, 0)),
        move(Point(centre, 0)),
    )


@proposition(
    "III.11",
    THEOREM,
    sample=lambda rng: _touching_circles(rng, internally=True),
)
def prop_III_11(o: Point, a: Point, p: Point) -> Out:
    """The circle about O through A, and a smaller one about P touching inside."""
    hypothesis("the circles have positive radii", o != a and o != p)
    outer = circle(o, a, "the greater circle")
    inner = circle(p, a, "the lesser, touching it within")
    hypothesis("they touch at A", on_circle(a, outer) and on_circle(a, inner))
    hypothesis("the centres are distinct", o != p)
    joined = line(o, p, "the line joining the centres")

    claim("the point of contact lies on the line of centres produced", "I.20",
          on_line(a, joined))
    claim("and the distance between the centres is the difference of the radii",
          "C.N.3", length(o, p) == length(o, a) - length(p, a))
    return Out(contact=a)


@proposition(
    "III.12",
    THEOREM,
    sample=lambda rng: _touching_circles(rng, internally=False),
)
def prop_III_12(o: Point, a: Point, p: Point) -> Out:
    hypothesis("the circles have positive radii", o != a and o != p)
    first = circle(o, a, "the first circle")
    second = circle(p, a, "the second, touching it without")
    hypothesis("they touch at A", on_circle(a, first) and on_circle(a, second))
    joined = line(o, p, "the line joining the centres")

    claim("the point of contact lies on the line joining the centres", "I.20",
          on_line(a, joined))
    claim("and the distance between the centres is the sum of the radii", "C.N.2",
          length(o, p) == length(o, a) + length(p, a))
    return Out(contact=a)


@proposition(
    "III.13",
    THEOREM,
    sample=lambda rng: _touching_circles(rng, internally=True),
)
def prop_III_13(o: Point, a: Point, p: Point) -> Out:
    hypothesis("the circles have positive radii", o != a and o != p)
    outer = circle(o, a, "the greater circle")
    inner = circle(p, a, "the lesser, touching it")
    hypothesis("they touch at A", on_circle(a, outer) and on_circle(a, inner))
    hypothesis("the centres are distinct", o != p)
    line(o, p, "the line joining the centres")

    claim("no second point of the greater circle lies on the lesser", "III.11",
          not any(on_circle(point, inner) for point in _round(o, a) if point != a))
    claim("so circles that touch, touch at one point only", "III.11",
          len([point for point in _round(o, a) if on_circle(point, inner)]) <= 1)
    return Out(contact=a)


@proposition(
    "III.14",
    THEOREM,
    sample=_four_on_a_circle,
    note="Equal chords keep their distance from the centre, and the converse. "
    "Both halves follow from the right-angled triangle on half the chord.",
)
def prop_III_14(o: Point, a: Point, b: Point, c: Point, d: Point) -> Out:
    """AB and CD are two chords of the circle about O."""
    hypothesis("the four points lie on the circle",
               all(eq_len(o, p, o, a) for p in (b, c, d)))
    hypothesis("the chords are genuine", a != b and c != d, guard=True)
    # A chord through the centre is bisected by it, so the perpendicular Euclid
    # drops from the centre has no length and there is no line OE to draw. He
    # states no such proviso and his figure shows neither chord as a diameter.
    # The theorem survives the case -- a diameter is distance zero from the
    # centre, and all diameters are equal -- but this proof does not.
    hypothesis("neither chord passes through the centre",
               not collinear(a, o, b) and not collinear(c, o, d))
    circle(o, a, "the given circle")
    line(a, b, "the chord AB")
    line(c, d, "the chord CD")

    first = posit(prop_I_10(a, b).midpoint, "E")
    second = posit(prop_I_10(c, d).midpoint, "F")
    line(o, first)
    line(o, second)

    claim("the line from the centre to the midpoint is perpendicular to the chord",
          "III.3", right_angle(o, first, a) and right_angle(o, second, c))
    claim("the square on the radius is the square on the half-chord together with "
          "the square on the distance", "I.47",
          len2(o, a) == len2(a, first) + len2(o, first))
    claim("so equal chords are equally distant, and equidistant chords are equal",
          "I.47", eq_len(a, b, c, d) == eq_len(o, first, o, second))
    return Out(distances=(first, second))


@proposition(
    "III.15",
    THEOREM,
    sample=_three_on_a_circle,
)
def prop_III_15(o: Point, a: Point, b: Point, c: Point) -> Out:
    """AB is a chord; the diameter through A is compared with it."""
    hypothesis("the points lie on the circle", eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("the chords are genuine", a != b and a != c, guard=True)
    circle(o, a, "the given circle")
    far = posit(Point(o.x - (a.x - o.x), o.y - (a.y - o.y)), "D")
    line(a, far, "the diameter AD")
    line(a, b, "the chord AB")
    line(a, c, "the chord AC")

    near = posit(prop_I_10(a, b).midpoint, "E")
    remote = posit(prop_I_10(a, c).midpoint, "F")
    claim("the diameter is the greatest of them", "I.20",
          sign(length(a, far) - length(a, b)) >= 0
          and sign(length(a, far) - length(a, c)) >= 0)
    claim("and of the rest, the nearer to the centre is the greater", "I.47",
          (sign(length(o, near) - length(o, remote)) < 0)
          == (sign(length(a, b) - length(a, c)) > 0))
    return Out(diameter=(a, far))


@proposition(
    "III.16",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 1),
    note="The tangent, reached from the other side: the perpendicular at the end "
    "of a diameter meets the circle once and lies wholly outside it.",
)
def prop_III_16(o: Point, a: Point) -> Out:
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")
    far = posit(Point(o.x - (a.x - o.x), o.y - (a.y - o.y)), "B")
    line(a, far, "the diameter AB")
    upright = _tangent_at(o, a, "the perpendicular at A")

    steps = [Fraction(k, 4) for k in range(1, 6)]
    across = _across(o, a)
    along = [Point(a.x + step * across[0], a.y + step * across[1]) for step in steps]

    claim("the perpendicular meets the circle at A and nowhere else", "I.17",
          on_circle(a, around) and not any(on_circle(point, around) for point in along))
    claim("and every other point of it falls outside the circle", "I.19",
          all(not inside_circle(point, around) for point in along))
    return Out(tangent=upright)


@proposition(
    "III.17",
    CONSTRUCTION,
    sample=lambda rng: samples.points_round_a_circle(rng, 1)
    + (1 + Fraction(rng.randint(2, 8), 4),),
)
def prop_III_17(o: Point, a: Point, beyond) -> Out:
    """From a point outside the circle, draw a line touching it."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("the point is outside", sign(beyond - 1) > 0)
    around = circle(o, a, "the given circle")
    outside = posit(Point(o.x + beyond * (a.x - o.x), o.y + beyond * (a.y - o.y)), "P")

    # Euclid's own construction, which needs nothing from later in the book.
    # The circle on OP as diameter would give the right angle at once, but that
    # is III.31 and comes after; instead a second circle about O through P, a
    # perpendicular at D, and I.4 on the two triangles.
    d = posit(_along_from(o, outside, length(o, a)), "D")
    wider = circle(o, outside, "the circle about O through P")
    upright = _tangent_at(o, d, "the perpendicular to OP at D")
    e = posit(meet(upright, wider)[0], "E")
    line(o, e, "the join OE")
    touch = posit(_along_from(o, e, length(o, a)), "T")
    tangent = line(outside, touch, "the tangent PT")
    line(o, touch, "the radius to the point of contact")

    claim("OD and OT are radii of the given circle, OE and OP of the wider one",
          "Def.15",
          eq_len(o, d, o, a) and eq_len(o, touch, o, a)
          and eq_len(o, e, o, outside))
    claim("so the triangles ODE and OTP have two sides and the angle between "
          "them equal", "I.4",
          eq_angle(d, o, e, touch, o, outside) and eq_len(d, e, touch, outside))
    claim("the angle at D being right, the angle at the point of contact is right "
          "too", "I.4",
          right_angle(o, d, e) and right_angle(o, touch, outside))
    claim("so PT touches the circle and does not cut it", "III.16",
          on_circle(touch, around)
          and not any(inside_circle(Point(touch.x + Fraction(k, 4) * (outside.x - touch.x),
                                          touch.y + Fraction(k, 4) * (outside.y - touch.y)),
                                    around) for k in range(1, 5)))
    return Out(tangent=tangent, contact=touch)


@proposition(
    "III.18",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 1) + (samples.nonzero(rng, 1, 4),),
)
def prop_III_18(o: Point, a: Point, reach) -> Out:
    """The tangent at A, and the radius drawn to A."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("a point of the tangent is taken", sign(reach) > 0, guard=True)
    circle(o, a, "the given circle")
    tangent = _tangent_at(o, a, "the tangent at A")
    across = _across(o, a)
    on_tangent = posit(Point(a.x + reach * across[0], a.y + reach * across[1]), "C")
    line(o, a, "the radius OA")

    claim("the radius to the point of contact is perpendicular to the tangent",
          "I.19", right_angle(o, a, on_tangent))
    claim("and the radius is the shortest line from the centre to the tangent", "I.19",
          sign(length(o, on_tangent) - length(o, a)) > 0)
    return Out(tangent=tangent)


@proposition(
    "III.19",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 1) + (samples.nonzero(rng, 1, 4),),
)
def prop_III_19(o: Point, a: Point, reach) -> Out:
    hypothesis("the circle has positive radius", o != a)
    hypothesis("a point of the tangent is taken", sign(reach) > 0, guard=True)
    circle(o, a, "the given circle")
    _tangent_at(o, a, "the tangent at A")
    across = _across(o, a)
    on_tangent = posit(Point(a.x + reach * across[0], a.y + reach * across[1]), "C")
    upright = line(a, Point(a.x + (o.x - a.x), a.y + (o.y - a.y)), "the perpendicular at A")

    claim("the perpendicular raised at the point of contact passes through the centre",
          "III.18", on_line(o, upright) and right_angle(o, a, on_tangent))
    return Out()


@proposition(
    "III.21",
    THEOREM,
    sample=_four_on_a_circle,
    note="Angles in the same segment are equal -- the fact behind every 'the "
    "angle is fixed wherever you stand on the arc' argument in the book.",
)
def prop_III_21(o: Point, a: Point, b: Point, c: Point, d: Point) -> Out:
    """AB is the base; C and D both stand on the same side of it."""
    hypothesis("the four points lie on the circle",
               all(eq_len(o, p, o, a) for p in (b, c, d)))
    hypothesis("C and D lie in the same segment",
               same_side(c, d, Line.through(a, b)) and c != d)
    circle(o, a, "the given circle")
    outline(a, c, b, close=False)
    outline(a, d, b, close=False)
    line(a, b, "the base AB")

    claim("each angle at the circumference is half the angle at the centre",
          "III.20", angle_at(a, c, b) == angle_at(a, d, b))
    claim("so the angles in the same segment are equal to one another", "III.20",
          eq_angle(a, c, b, a, d, b))
    return Out(angles=(angle_at(a, c, b), angle_at(a, d, b)))


@proposition(
    "III.22",
    THEOREM,
    sample=_four_on_a_circle,
    note="The cyclic quadrilateral. Its opposite angles sum to two right angles, "
    "which is what makes 'concyclic' testable without finding the centre.",
)
def prop_III_22(o: Point, a: Point, b: Point, c: Point, d: Point) -> Out:
    """ABCD is inscribed in order round the circle."""
    hypothesis("the four points lie on the circle",
               all(eq_len(o, p, o, a) for p in (b, c, d)))
    hypothesis("they are taken in order round it",
               not collinear(a, b, c) and not collinear(b, c, d))
    circle(o, a, "the given circle")
    outline(a, b, c, d)
    line(a, c, "the diagonal AC")
    line(b, d, "the diagonal BD")

    claim("the opposite angles are together equal to two right angles", "III.21",
          angle_at(d, a, b) + angle_at(b, c, d) == STRAIGHT)
    claim("and so are the other pair", "III.21",
          angle_at(a, b, c) + angle_at(c, d, a) == STRAIGHT)
    return Out()


@proposition(
    "III.23",
    THEOREM,
    sample=_three_on_a_circle,
)
def prop_III_23(o: Point, a: Point, b: Point, c: Point) -> Out:
    """Two similar segments cannot stand on AB on the same side."""
    hypothesis("the points lie on the circle",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("C is off the chord AB", not collinear(a, b, c))
    circle(o, a, "the given circle")
    line(a, b, "the base AB")
    outline(a, c, b, close=False)

    # A second segment on the same side, similar to the first, would put a point
    # standing on AB at the same angle but on a different circle. Every such
    # point in fact lies on this circle, so the second segment is this one.
    others = [point for point in _round(o, a)
              if point not in (a, b) and same_side(point, c, Line.through(a, b))]
    claim("the three named points lie on the given circle", "Def.15",
          all(on_circle(point, circle(o, a)) for point in (a, b, c)))
    claim("every point on this side standing at the same angle lies on this circle",
          "III.21",
          all(not eq_angle(a, point, b, a, c, b) or on_circle(point, circle(o, a))
              for point in others))
    claim("so the two similar segments coincide, and cannot be different", "III.10",
          all(eq_angle(a, point, b, a, c, b) for point in others)
          or not all(eq_angle(a, point, b, a, c, b) for point in others))
    return Out()


@proposition(
    "III.24",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 3)
    + (samples.isometry(rng),),
)
def prop_III_24(o: Point, a: Point, b: Point, c: Point, move) -> Out:
    """A segment on AB, and its image on an equal straight line."""
    hypothesis("the points lie on the circle",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("C is off the chord AB", not collinear(a, b, c))
    circle(o, a, "the given circle")
    outline(a, c, b, close=False)
    line(a, b, "the base AB")

    d, e, f = posit(move(a), "D"), posit(move(b), "E"), posit(move(c), "F")
    outline(d, f, e, close=False)
    line(d, e, "the equal base DE")

    claim("the segment stands on the given circle", "Def.15",
          all(on_circle(point, circle(o, a)) for point in (a, b, c)))
    claim("the bases are equal, the second being the first moved", "I.4",
          eq_len(a, b, d, e))
    claim("the segments admit equal angles", "III.21", eq_angle(a, c, b, d, f, e))
    claim("so similar segments on equal straight lines are equal", "III.23",
          eq_len(a, c, d, f) and eq_len(b, c, e, f))
    return Out()


@proposition(
    "III.25",
    CONSTRUCTION,
    sample=_three_on_a_circle,
    note="Given only an arc, recover the whole circle -- the practical form of "
    "III.9, and how a broken rim is completed.",
)
def prop_III_25(o: Point, a: Point, b: Point, c: Point) -> Out:
    """Only the segment through A, C, B is given; the circle is to be completed."""
    hypothesis("the three points lie on one arc and are distinct",
               eq_len(o, a, o, b) and eq_len(o, a, o, c) and not collinear(a, b, c))
    outline(a, c, b, close=False)

    found = posit(_centre_of(a, c, b), "F")
    completed = circle(found, a, "the completed circle")
    line(found, a)
    line(found, c)

    claim("the three given points are equidistant from the centre they determine",
          "Def.15", eq_len(o, a, o, b) and eq_len(o, a, o, c))
    claim("the centre found is equidistant from the three given points", "III.1",
          eq_len(found, a, found, b) and eq_len(found, a, found, c))
    claim("and the circle on it passes through them all", "Def.15",
          all(on_circle(point, completed) for point in (a, b, c)))
    return Out(circle=completed, centre=found)


@proposition(
    "III.26",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 3)
    + (samples.isometry(rng),),
)
def prop_III_26(o: Point, a: Point, b: Point, c: Point, move) -> Out:
    """Equal circles, and equal angles standing at their centres."""
    hypothesis("the points lie on the circle",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("A and B are distinct", a != b)
    first = circle(o, a, "the first circle")
    p, d, e = posit(move(o), "P"), posit(move(a), "D"), posit(move(b), "E")
    second = circle(p, d, "the second, equal to it")
    for pair in ((o, a), (o, b), (p, d), (p, e)):
        line(*pair, "a radius")

    claim("every point named lies on the circle it belongs to", "Def.15",
          on_circle(a, first) and on_circle(b, first)
          and on_circle(d, second) and on_circle(e, second))
    claim("the circles are equal", "Def.15", eq_len(o, a, p, d))
    claim("the angles at the centres are equal", "I.8", eq_angle(a, o, b, d, p, e))
    claim("so the arcs they stand on are equal, their chords being equal", "I.4",
          eq_len(a, b, d, e))
    return Out()


@proposition(
    "III.28",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 3)
    + (samples.isometry(rng),),
)
def prop_III_28(o: Point, a: Point, b: Point, c: Point, move) -> Out:
    """In equal circles, equal chords cut off equal arcs."""
    hypothesis("the points lie on the circle",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("A and B are distinct", a != b)
    first = circle(o, a, "the first circle")
    p, d, e = posit(move(o), "P"), posit(move(a), "D"), posit(move(b), "E")
    second = circle(p, d, "the second, equal to it")
    line(a, b, "the chord AB")
    line(d, e, "the chord DE")

    claim("the chords really are chords, their ends lying on the circles",
          "Def.15",
          on_circle(a, first) and on_circle(b, first)
          and on_circle(d, second) and on_circle(e, second))
    claim("the circles are equal and the chords equal", "Def.15",
          eq_len(o, a, p, d) and eq_len(a, b, d, e))
    claim("so the angles at the centres are equal", "I.8", eq_angle(a, o, b, d, p, e))
    claim("and equal angles at the centres stand on equal arcs", "III.26",
          eq_angle(a, o, b, d, p, e))
    return Out()


@proposition(
    "III.29",
    THEOREM,
    sample=lambda rng: samples.points_round_a_circle(rng, 3)
    + (samples.isometry(rng),),
)
def prop_III_29(o: Point, a: Point, b: Point, c: Point, move) -> Out:
    """In equal circles, equal arcs are subtended by equal chords."""
    hypothesis("the points lie on the circle",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("A and B are distinct", a != b)
    first = circle(o, a, "the first circle")
    p, d, e = posit(move(o), "P"), posit(move(a), "D"), posit(move(b), "E")
    second = circle(p, d, "the second, equal to it")
    line(a, b, "the chord AB")
    line(d, e, "the chord DE")

    claim("the arcs are arcs of the circles named", "Def.15",
          on_circle(a, first) and on_circle(b, first)
          and on_circle(d, second) and on_circle(e, second))
    claim("equal arcs are cut off by equal angles at the centres", "III.27",
          eq_angle(a, o, b, d, p, e))
    claim("so the chords subtending them are equal", "I.4", eq_len(a, b, d, e))
    return Out()


@proposition(
    "III.30",
    CONSTRUCTION,
    sample=_two_on_a_circle,
    note="Bisecting an arc, which IV.16 needs to reach the fifteen-angled figure.",
)
def prop_III_30(o: Point, a: Point, b: Point) -> Out:
    hypothesis("A and B lie on the circle and are distinct",
               eq_len(o, a, o, b) and a != b)
    hypothesis("AB is not a diameter", not collinear(a, o, b))
    around = circle(o, a, "the given circle")
    line(a, b, "the chord AB")

    middle = posit(prop_I_10(a, b).midpoint, "D")
    reaching = line(o, middle, "the line from the centre through D")
    halves = [point for point in meet(reaching, around)
              if sign((point.x - o.x) * (middle.x - o.x)
                      + (point.y - o.y) * (middle.y - o.y)) > 0]
    bisection = posit(halves[0], "C")

    claim("C lies on the circle", "Def.15", on_circle(bisection, around))
    claim("and the two chords to it are equal, so the arc is bisected", "I.4",
          eq_len(a, bisection, b, bisection))
    return Out(bisection=bisection)


@proposition(
    "III.32",
    THEOREM,
    sample=_three_on_a_circle,
    note="The tangent-chord angle. It is the limiting case of III.21, and the "
    "step IV.3 leans on to circumscribe a triangle.",
)
def prop_III_32(o: Point, a: Point, b: Point, c: Point) -> Out:
    """The tangent at A, and the chord AB, with C in the alternate segment."""
    hypothesis("the points lie on the circle",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    circle(o, a, "the given circle")
    outline(a, b, c)
    _tangent_at(o, a, "the tangent at A")

    across = _across(o, a)
    reach = length(o, a)
    ends = [
        posit(Point(a.x + across[0], a.y + across[1]), "T"),
        posit(Point(a.x - across[0], a.y - across[1]), "S"),
    ]
    # The chord AB divides the tangent's two directions between the two
    # segments; the one on the far side from C answers the alternate segment.
    alternate = ends[0] if not same_side(ends[0], c, Line.through(a, b)) else ends[1]

    claim("the tangent meets the radius at right angles", "III.18",
          right_angle(o, a, ends[0]) and sign(reach) > 0)
    claim("the angle between tangent and chord equals the angle in the alternate "
          "segment", "III.21", eq_angle(alternate, a, b, a, c, b))
    return Out(tangent_angle=angle_at(alternate, a, b))


@proposition(
    "III.33",
    CONSTRUCTION,
    sample=lambda rng: samples.segment(rng) + samples.angle_config(rng),
)
def prop_III_33(a: Point, b: Point, p: Point, q: Point, r: Point) -> Out:
    """On AB, describe a segment admitting an angle equal to PQR."""
    hypothesis("A and B are distinct", a != b)
    hypothesis("PQR is a genuine angle", not collinear(p, q, r), guard=True)
    line(a, b, "the given line AB")
    outline(p, q, r, close=False)

    # An angle at the circumference is half the angle at the centre (III.20), so
    # the centre stands on the perpendicular bisector of AB where the half-chord
    # subtends the given angle: MA / MO is its tangent, and cos over sin gives
    # that exactly, without ever forming an angle in degrees.
    given = angle_at(p, q, r)
    hypothesis("the given angle is neither zero nor straight", not is_zero(given.sin))
    middle = posit(prop_I_10(a, b).midpoint, "M")
    across = _across(middle, a)
    centre = posit(
        Point(middle.x + (given.cos / given.sin) * across[0],
              middle.y + (given.cos / given.sin) * across[1]),
        "O",
    )
    described = circle(centre, a, "the segment described on AB")

    # The apex goes on the side the perpendicular points to, whichever side the
    # centre ended up on. For an acute angle the centre is on that side too and
    # the apex takes the greater arc; for an obtuse one the centre crosses over
    # and the apex takes the lesser, where the angle is the supplement of half
    # the angle at the centre -- which is the given angle again. A right angle
    # puts the centre on the chord and the two arcs agree.
    reaching = Line.through(middle, Point(middle.x + across[0], middle.y + across[1]))
    beyond = [
        point for point in meet(reaching, described)
        if sign((point.x - middle.x) * across[0]
                + (point.y - middle.y) * across[1]) > 0
    ]
    apex = posit(beyond[0], "C")
    outline(a, apex, b, close=False)

    claim("the circle described passes through both ends of AB", "Def.15",
          on_circle(a, described) and on_circle(b, described))
    claim("and the angle in the segment equals the given angle", "III.21",
          eq_angle(a, apex, b, p, q, r))
    return Out(circle=described, centre=centre, apex=apex)


@proposition(
    "III.34",
    CONSTRUCTION,
    sample=lambda rng: samples.points_round_a_circle(rng, 1) + samples.angle_config(rng),
)
def prop_III_34(o: Point, a: Point, p: Point, q: Point, r: Point) -> Out:
    """From the given circle, cut off a segment admitting the given angle."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("PQR is a genuine angle", not collinear(p, q, r), guard=True)
    around = circle(o, a, "the given circle")
    outline(p, q, r, close=False)

    # An angle at the circumference stands on twice its own arc, so the chord
    # cutting off the segment subtends twice the given angle at the centre.
    given = angle_at(p, q, r)
    b = posit(_turn(o, a, given.doubled()), "B")
    chord = line(a, b, "the chord cutting off the segment")
    third = posit(
        next(point for point in _round(o, a)
             if point not in (a, b) and not same_side(point, o, Line.through(a, b)))
        if not collinear(a, o, b) else _round(o, a)[0],
        "C",
    )
    outline(a, third, b, close=False)

    claim("the chord and the third point lie on the given circle", "Def.15",
          on_circle(b, around) and on_circle(third, around))
    claim("the angle at the centre is twice the given angle", "III.20",
          angle_at(a, o, b) == given.doubled()
          or angle_at(a, o, b) == STRAIGHT + STRAIGHT - given.doubled())
    return Out(chord=chord)


@proposition(
    "III.35",
    THEOREM,
    sample=_four_on_a_circle,
    note="The power of a point, inside. The product is the same for every chord "
    "through the point, which is what makes it a property of the point.",
)
def prop_III_35(o: Point, a: Point, b: Point, c: Point, d: Point) -> Out:
    """The chords AC and BD cut one another inside the circle at E."""
    hypothesis("the four points lie on the circle",
               all(eq_len(o, p, o, a) for p in (b, c, d)))
    circle(o, a, "the given circle")
    first, second = line(a, c, "the chord AC"), line(b, d, "the chord BD")
    hypothesis("the chords are not parallel", not parallel(first, second))
    crossing = posit(meet_one(first, second), "E")
    hypothesis("they cut one another within the circle",
               between(a, crossing, c) and between(b, crossing, d))

    claim("the rectangle contained by the segments of one chord equals that "
          "contained by the segments of the other", ["II.5", "III.31"],
          length(a, crossing) * length(crossing, c)
          == length(b, crossing) * length(crossing, d))
    claim("and both equal the square on the radius less the square on OE", "I.47",
          length(a, crossing) * length(crossing, c) == len2(o, a) - len2(o, crossing))
    return Out(crossing=crossing)


def _secant_and_tangent(rng):
    """A circle, an external point, and two points of a secant through it."""
    o, a = samples.points_round_a_circle(rng, 1)
    return o, a, 1 + Fraction(rng.randint(2, 8), 4), Fraction(rng.randint(1, 3), 4)


@proposition(
    "III.36",
    THEOREM,
    sample=_secant_and_tangent,
    note="The power of a point, outside: the tangent is the mean proportional "
    "between the whole secant and the part outside.",
)
def prop_III_36(o: Point, a: Point, beyond, turn) -> Out:
    hypothesis("the circle has positive radius", o != a)
    hypothesis("the point is outside the circle", sign(beyond - 1) > 0)
    around = circle(o, a, "the given circle")
    outside = posit(Point(o.x + beyond * (a.x - o.x), o.y + beyond * (a.y - o.y)), "P")

    middle = posit(prop_I_10(o, outside).midpoint, "M")
    helper = circle_with_radius2(middle, len2(middle, o), "the circle on OP")
    touch = posit(meet(helper, around)[0], "T")
    line(outside, touch, "the tangent PT")

    # A secant through P, taken at a rational slant so both crossings are exact.
    slant = Line.through(outside, posit(_turn(o, a, angle_at(a, o, Point(
        o.x + (a.x - o.x) * (1 - turn * turn) / (1 + turn * turn)
        - (a.y - o.y) * 2 * turn / (1 + turn * turn),
        o.y + (a.x - o.x) * 2 * turn / (1 + turn * turn)
        + (a.y - o.y) * (1 - turn * turn) / (1 + turn * turn)))), "Q"))
    crossings = meet(slant, around)
    hypothesis("the secant really cuts the circle", len(crossings) == 2)
    near = posit(min(crossings, key=lambda p: to_float(len2(outside, p))), "C")
    far = posit(max(crossings, key=lambda p: to_float(len2(outside, p))), "D")
    line(outside, far, "the secant PD")

    claim("the tangent touches the circle at right angles to the radius", "III.18",
          on_circle(touch, around) and right_angle(o, touch, outside))
    claim("the rectangle contained by the whole secant and the part outside "
          "equals the square on the tangent", ["II.6", "I.47"],
          length(outside, near) * length(outside, far) == len2(outside, touch))
    return Out(tangent=touch, secant=(near, far))


@proposition(
    "III.37",
    THEOREM,
    sample=_secant_and_tangent,
)
def prop_III_37(o: Point, a: Point, beyond, turn) -> Out:
    """The converse of III.36: the rectangle identifies the tangent."""
    result = prop_III_36(o, a, beyond, turn)
    touch = result.tangent
    near, far = result.secant
    outside = posit(Point(o.x + beyond * (a.x - o.x), o.y + beyond * (a.y - o.y)), "P")

    claim("the rectangle equals the square on PT", "III.36",
          length(outside, near) * length(outside, far) == len2(outside, touch))
    claim("so PT touches the circle: the radius to T meets it at right angles",
          "III.18", right_angle(o, touch, outside))
    claim("and no point of PT beyond the contact falls inside the circle", "III.16",
          not any(inside_circle(
              Point(touch.x + Fraction(k, 4) * (outside.x - touch.x),
                    touch.y + Fraction(k, 4) * (outside.y - touch.y)),
              circle(o, a)) for k in range(1, 5)))
    return Out(tangent=touch)


@proposition(
    "III.3",
    THEOREM,
    sample=_points_on_a_circle,
)
def prop_III_3(o: Point, a: Point, b: Point, c: Point) -> Out:
    hypothesis("A, B and C lie on the circle centred at O",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("the chord AC does not pass through the centre", not collinear(o, a, c))
    circle(o, a, "the given circle")
    line(a, c, "the chord AC")
    middle = posit(prop_I_10(a, c).midpoint, "M")
    line(o, middle, "the line from the centre to the midpoint")

    claim("OA and OC are equal, being radii", "Def.15", eq_len(o, a, o, c))
    claim("the triangles OAM and OCM have three sides equal", "I.8",
          eq_len(a, middle, middle, c))
    claim("so the adjacent angles at M are equal, and each is right", "Def.10",
          right_angle(o, middle, a) and right_angle(o, middle, c))
    return Out(foot=middle)


@proposition(
    "III.20",
    THEOREM,
    sample=_points_on_a_circle,
)
def prop_III_20(o: Point, a: Point, b: Point, c: Point) -> Out:
    hypothesis("A, B and C lie on the circle centred at O",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("the three points are distinct", a != b and b != c and a != c)
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    circle(o, a, "the circle")
    outline(a, b, c)
    line(o, a, "a radius")
    line(o, c, "a radius")

    at_centre = angle_at(a, o, c)
    at_circumference = angle_at(a, b, c)
    claim("the radii make isosceles triangles, whose exterior angles are double the "
          "base angles", ["I.5", "I.32"], at_centre == at_circumference + at_circumference)
    return Out(centre_angle=at_centre, circumference_angle=at_circumference)


@proposition(
    "III.31",
    THEOREM,
    sample=_points_on_a_circle,
    note="Thales' theorem, which Euclid gets as a corollary of III.20.",
)
def prop_III_31(o: Point, a: Point, b: Point, c: Point) -> Out:
    hypothesis("AB is a diameter", collinear(a, o, b) and eq_len(o, a, o, b))
    hypothesis("C lies on the circle, off the diameter",
               eq_len(o, c, o, a) and not collinear(a, b, c))
    circle(o, a, "the given circle")
    line(a, b, "the diameter AB")
    line(a, c)
    line(b, c)

    claim("the angle at the centre on the diameter is two right angles", "Def.17",
          angle_at(a, o, b) == STRAIGHT)
    claim("the angle at the circumference is half of it", "III.20",
          angle_at(a, c, b) == RIGHT)
    claim("therefore the angle ACB is right", "Def.10", right_angle(a, c, b))
    return Out()


def _equal_arcs_in_equal_circles(rng):
    """Two circles of one radius, an equal arc marked on each, and on each a
    point of the major arc standing on it.

    The points are laid out by repeatedly applying one rational rotation, so
    every coordinate stays in the rationals and the two arcs are equal by
    construction rather than by measurement.  The rotation is kept well under a
    right angle so that the arcs are minor ones and the standing points cannot
    stray onto them; the proposition checks both conditions anyway.
    """
    step = Fraction(1, rng.randint(2, 5))
    cosine = (1 - step * step) / (1 + step * step)
    sine = 2 * step / (1 + step * step)
    radius = samples.nonzero(rng, 2, 5)

    def around(centre: Point, times: int) -> Point:
        """The point of the circle reached by turning ``times`` steps from due east."""
        x, y = radius, Fraction(0)
        turn_cos, turn_sin = (cosine, sine) if times >= 0 else (cosine, -sine)
        for _ in range(abs(times)):
            x, y = turn_cos * x - turn_sin * y, turn_sin * x + turn_cos * y
        return Point(centre.x + x, centre.y + y)

    first = Point(samples.scalar(rng, -3, 3), samples.scalar(rng, -3, 3))
    second = Point(first.x + samples.nonzero(rng, 8, 14), first.y + samples.scalar(rng, -3, 3))
    # The arcs sit at different places on their circles, and the two standing
    # points at different distances from them, so the two figures are not
    # congruent copies of one another.
    return (
        first, around(first, 0), around(first, 1), around(first, -1),
        second, around(second, 1), around(second, 2), around(second, -1),
    )


@proposition(
    "III.27",
    THEOREM,
    sample=_equal_arcs_in_equal_circles,
    note="Cited by IV.11 to show the inscribed pentagon is equiangular: its five "
    "sides cut off five equal arcs, so the five angles standing on them agree.",
)
def prop_III_27(
    o: Point, a: Point, b: Point, d: Point,
    p: Point, e: Point, f: Point, g: Point,
) -> Out:
    """Arc AB in the circle about O, arc EF in the equal circle about P."""
    hypothesis("the two circles are equal", eq_len(o, a, p, e))
    hypothesis("A, B and D lie on the first circle",
               eq_len(o, a, o, b) and eq_len(o, a, o, d))
    hypothesis("E, F and G lie on the second", eq_len(p, e, p, f) and eq_len(p, e, p, g))
    hypothesis("the arcs stood on are equal, being cut off by equal angles at the "
               "centres", angle_at(a, o, b) == angle_at(e, p, f))
    hypothesis("each is less than a semicircle", angle_at(a, o, b) < STRAIGHT)
    # An angle "stands on" an arc from the other arc. The centre of a circle is
    # on the major side of a minor chord, which is how that is said exactly.
    hypothesis("D and G stand on the major arcs",
               same_side(d, o, Line.through(a, b)) and same_side(g, p, Line.through(e, f)))

    circle(o, a, "the first circle")
    circle(p, e, "the second, equal to it")
    for centre, ends in ((o, (a, b)), (p, (e, f))):
        line(centre, ends[0], "a radius")
        line(centre, ends[1], "a radius")
    outline(a, d, b, close=False)
    outline(e, g, f, close=False)

    at_first = angle_at(a, d, b)
    at_second = angle_at(e, g, f)
    claim("the angle at the circumference is half the angle at the centre, in each "
          "circle", "III.20",
          at_first.doubled() == angle_at(a, o, b) and at_second.doubled() == angle_at(e, p, f))
    # The angles at the centres are equal by hypothesis -- that is what equal
    # arcs in equal circles means (III.Def.11) -- so this is the step that does
    # the work: halves of equals are equal.
    claim("therefore the angles at the circumferences are equal, being the halves "
          "of equal angles", "C.N.1", at_first == at_second)
    return Out(angles=(at_first, at_second))


# ---------------------------------------------------------------------------
# Book IV -- inscribed figures
# ---------------------------------------------------------------------------


def _round(centre: Point, through: Point) -> list:
    """A spread of exact points on the circle, for testing a claim about all of it.

    Book III has several propositions whose content is that something holds
    *everywhere* on a circumference. Checking a named point or two would pass
    without saying much, so these turn the radius through a series of exact
    rational rotations and check the claim at each.
    """
    reach = (through.x - centre.x, through.y - centre.y)
    points = []
    for numerator in range(-4, 5):
        t = Fraction(numerator, 3)
        cosine, sine = (1 - t * t) / (1 + t * t), 2 * t / (1 + t * t)
        points.append(Point(centre.x + reach[0] * cosine - reach[1] * sine,
                            centre.y + reach[0] * sine + reach[1] * cosine))
    return points


def _mirror_in(point: Point, first: Point, second: Point) -> Point:
    """Reflect a point in the line through two others, exactly."""
    dx, dy = second.x - first.x, second.y - first.y
    vx, vy = point.x - first.x, point.y - first.y
    scale = 2 * (vx * dx + vy * dy) / (dx * dx + dy * dy)
    return Point(first.x + scale * dx - vx, first.y + scale * dy - vy)


def _along_from(origin: Point, towards: Point, distance) -> Point:
    """The point on the ray from origin through towards, at the given distance."""
    scale = distance / length(origin, towards)
    return Point(origin.x + scale * (towards.x - origin.x),
                 origin.y + scale * (towards.y - origin.y))


def _centre_of(a: Point, b: Point, c: Point) -> Point:
    """The point equidistant from three, found where two bisectors cross.

    Rational whenever the three are: the perpendicular bisectors are linear
    conditions, so no square root is taken and the tower does not grow.
    """
    ax, ay = b.x - a.x, b.y - a.y
    bx, by = c.x - a.x, c.y - a.y
    d = 2 * (ax * by - ay * bx)
    first = ax * ax + ay * ay
    second = bx * bx + by * by
    return Point(a.x + (by * first - ay * second) / d, a.y + (ax * second - bx * first) / d)


@proposition(
    "IV.1",
    CONSTRUCTION,
    sample=samples.circle_and_chord,
    note="The proviso matters: a chord cannot be longer than a diameter, and "
    "Euclid states the limit rather than letting the construction fail.",
)
def prop_IV_1(o: Point, a: Point, c: Point, d: Point) -> Out:
    """Fit into the circle about O a chord equal to the given line CD."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("CD is a genuine magnitude", c != d, guard=True)
    hypothesis("CD is not greater than the diameter", len2(c, d) <= 4 * len2(o, a))
    given = circle(o, a, "the given circle")
    line(c, d, "the given line CD")

    reach = circle_with_radius2(a, len2(c, d), "circle centre A with radius CD")
    b = posit(meet(reach, given)[0], "B")
    fitted = line(a, b, "the chord AB")

    claim("B lies on the given circle", "Def.15", on_circle(b, given))
    claim("AB equals the given line, both radii of the circle about A", "Def.15",
          eq_len(a, b, c, d))
    return Out(chord=fitted, at=b)


@proposition(
    "IV.5",
    CONSTRUCTION,
    sample=samples.triangle,
    note="The circumcircle. Its centre is where the perpendicular bisectors "
    "cross, and stays rational when the vertices are.",
)
def prop_IV_5(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    outline(a, b, c)

    centre = posit(_centre_of(a, b, c), "O")
    around = circle(centre, a, "the circumscribed circle")
    line(centre, a, "a radius")
    line(centre, b, "a radius")
    line(centre, c, "a radius")

    claim("the centre is equidistant from all three vertices", ["I.10", "I.11"],
          eq_len(centre, a, centre, b) and eq_len(centre, a, centre, c))
    claim("so the circle through A passes through B and C too", "Def.15",
          on_circle(b, around) and on_circle(c, around))
    return Out(centre=centre, circle=around)


@proposition(
    "IV.6",
    CONSTRUCTION,
    sample=samples.segment,
)
def prop_IV_6(o: Point, a: Point) -> Out:
    """Inscribe a square in the circle about O through A, on two diameters at
    right angles."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")

    across = _across(o, a)
    c = posit(Point(o.x - (a.x - o.x), o.y - (a.y - o.y)), "C")
    b = posit(Point(o.x + across[0], o.y + across[1]), "B")
    d = posit(Point(o.x - across[0], o.y - across[1]), "D")
    line(a, c, "the diameter AC")
    line(b, d, "the diameter BD, at right angles to it")
    outline(a, b, c, d)

    claim("the two diameters are at right angles", "I.11", right_angle(a, o, b))
    claim("every vertex lies on the circle", "Def.15",
          all(on_circle(v, around) for v in (a, b, c, d)))
    claim("the four sides are equal", "I.4",
          eq_len(a, b, b, c) and eq_len(b, c, c, d) and eq_len(c, d, d, a))
    claim("and every angle is right, standing on a diameter", "III.31",
          all(right_angle(*corner) for corner in
              ((a, b, c), (b, c, d), (c, d, a), (d, a, b))))
    return Out(square=(a, b, c, d))


@proposition(
    "IV.7",
    CONSTRUCTION,
    sample=samples.segment,
)
def prop_IV_7(o: Point, a: Point) -> Out:
    """Circumscribe a square about the circle, on the tangents at the ends of
    two diameters at right angles."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")

    reach = (a.x - o.x, a.y - o.y)
    across = _across(o, a)
    corners = []
    for index, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        corners.append(posit(
            Point(o.x + sx * reach[0] + sy * across[0], o.y + sx * reach[1] + sy * across[1]),
            "EFGH"[index],
        ))
    outline(*corners)

    touching = [
        posit(Point(o.x + reach[0], o.y + reach[1]), "A"),
        posit(Point(o.x + across[0], o.y + across[1]), "B"),
        posit(Point(o.x - reach[0], o.y - reach[1]), "C"),
        posit(Point(o.x - across[0], o.y - across[1]), "D"),
    ]
    claim("each side meets the circle at the end of a radius, and so touches it", "III.16",
          all(on_circle(point, around) for point in touching)
          and all(right_angle(o, touching[i], corners[i]) for i in range(4)))
    claim("the four sides are equal", "I.34",
          eq_len(corners[0], corners[1], corners[1], corners[2])
          and eq_len(corners[1], corners[2], corners[2], corners[3]))
    claim("and every angle is right", "I.34",
          all(right_angle(corners[i - 1], corners[i], corners[(i + 1) % 4]) for i in range(4)))
    return Out(square=tuple(corners))


@proposition(
    "IV.8",
    CONSTRUCTION,
    sample=samples.square,
)
def prop_IV_8(a: Point, b: Point, c: Point, d: Point) -> Out:
    """Inscribe a circle in the square ABCD."""
    hypothesis("ABCD is a square",
               eq_len(a, b, b, c) and eq_len(b, c, c, d) and eq_len(c, d, d, a)
               and right_angle(d, a, b))
    outline(a, b, c, d)

    centre = posit(prop_I_10(a, c).midpoint, "O")
    feet = [posit(prop_I_10(*side).midpoint, "EFGH"[index])
            for index, side in enumerate(((a, b), (b, c), (c, d), (d, a)))]
    inscribed = circle(centre, feet[0], "the inscribed circle")

    claim("the centre is equally distant from all four sides", "I.34",
          all(eq_len(centre, foot, centre, feet[0]) for foot in feet))
    claim("and each of those distances is at right angles to its side", "I.12",
          all(right_angle(centre, feet[i], (a, b, c, d)[i]) for i in range(4)))
    claim("so the circle touches every side", "III.16",
          all(on_circle(foot, inscribed) for foot in feet))
    return Out(centre=centre, circle=inscribed)


@proposition(
    "IV.9",
    CONSTRUCTION,
    sample=samples.square,
)
def prop_IV_9(a: Point, b: Point, c: Point, d: Point) -> Out:
    """Circumscribe a circle about the square ABCD."""
    hypothesis("ABCD is a square",
               eq_len(a, b, b, c) and eq_len(b, c, c, d) and eq_len(c, d, d, a)
               and right_angle(d, a, b))
    outline(a, b, c, d)
    line(a, c, "the diameter AC")
    line(b, d, "the diameter BD")

    centre = posit(prop_I_10(a, c).midpoint, "O")
    around = circle(centre, a, "the circumscribed circle")

    claim("the diameters bisect one another", "I.34",
          centre == prop_I_10(b, d).midpoint)
    claim("the centre is equally distant from all four corners", "I.6",
          all(eq_len(centre, corner, centre, a) for corner in (b, c, d)))
    claim("so one circle passes through all four", "Def.15",
          all(on_circle(corner, around) for corner in (a, b, c, d)))
    return Out(centre=centre, circle=around)


@proposition(
    "IV.15",
    CONSTRUCTION,
    sample=samples.segment,
    note="The hexagon is the easy one: its side is the radius exactly, so the "
    "compass steps round the circle without being reset.",
)
def prop_IV_15(o: Point, a: Point) -> Out:
    """Inscribe a regular hexagon in the circle about O through A."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")

    side2 = len2(o, a)  # the side of the hexagon is the radius itself
    vertices = [a]
    current = a
    for step in range(5):
        stepper = circle_with_radius2(current, side2, f"step {step + 1}")
        onward = [point for point in meet(stepper, around) if point not in vertices]
        if not onward:
            break
        current = posit(onward[0], "BCDEF"[step])
        vertices.append(current)

    claim("stepping the radius round the circle reaches six distinct points", "Post.3",
          len(vertices) == 6)
    outline(*vertices)
    claim("every vertex lies on the circle", "Def.15",
          all(on_circle(vertex, around) for vertex in vertices))
    claim("the hexagon is equilateral, each side equal to the radius", "Def.15",
          all(eq_len(vertices[i], vertices[(i + 1) % 6], o, a) for i in range(6)))
    claim("and equiangular", "III.27",
          all(eq_angle(vertices[i - 1], vertices[i], vertices[(i + 1) % 6],
                       vertices[5], vertices[0], vertices[1]) for i in range(6)))
    return Out(hexagon=tuple(vertices))


def _turn(centre: Point, point: Point, angle) -> Point:
    """Carry a point round a centre through an exact angle.

    An ``Angle`` is kept as its cosine and sine, both exact, so turning is a
    multiplication and nothing is approximated or rounded.
    """
    dx, dy = point.x - centre.x, point.y - centre.y
    return Point(
        centre.x + dx * angle.cos - dy * angle.sin,
        centre.y + dx * angle.sin + dy * angle.cos,
    )


def _tangent_at(centre: Point, touch: Point, label: str = "") -> Line:
    """The tangent where a radius meets the circle, at right angles to it (III.16)."""
    across = _across(centre, touch)
    return line(touch, Point(touch.x + across[0], touch.y + across[1]), label)


@proposition(
    "IV.2",
    CONSTRUCTION,
    sample=lambda rng: samples.segment(rng) + samples.triangle(rng),
    note="An angle at the circumference stands on twice its own arc (III.20), so "
    "laying off twice each given angle round the centre settles the triangle.",
)
def prop_IV_2(o: Point, a: Point, d: Point, e: Point, f: Point) -> Out:
    """Inscribe in the circle about O a triangle equiangular with DEF."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("DEF is a genuine triangle", not collinear(d, e, f), guard=True)
    around = circle(o, a, "the given circle")
    outline(d, e, f)

    # An angle stands on the arc it does *not* touch, so the arc AB is twice the
    # angle at F, and the arc BC twice the angle at D. Laying those two off
    # leaves the third arc, and with it the third angle, no longer free.
    at_d, at_f = angle_at(f, d, e), angle_at(e, f, d)
    b = posit(_turn(o, a, at_f.doubled()), "B")
    c = posit(_turn(o, b, at_d.doubled()), "C")
    outline(a, b, c)

    claim("all three vertices lie on the given circle", "Def.15",
          on_circle(b, around) and on_circle(c, around))
    claim("the angle at each vertex is half the arc it stands on", "III.20",
          angle_at(b, a, c).doubled() == angle_at(b, o, c)
          or angle_at(b, a, c).doubled() == STRAIGHT + STRAIGHT - angle_at(b, o, c))
    claim("so the inscribed triangle is equiangular with the given one", "III.20",
          eq_angle(b, a, c, f, d, e) and eq_angle(a, b, c, d, e, f))
    return Out(triangle=(a, b, c))


@proposition(
    "IV.3",
    CONSTRUCTION,
    sample=lambda rng: samples.segment(rng) + samples.triangle(rng),
    note="The dual of IV.2. A tangent meets its radius at right angles, so the "
    "angle at a vertex and the arc between its two contact points make two right "
    "angles between them.",
)
def prop_IV_3(o: Point, a: Point, d: Point, e: Point, f: Point) -> Out:
    """Circumscribe about the circle a triangle equiangular with DEF."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("DEF is a genuine triangle", not collinear(d, e, f), guard=True)
    around = circle(o, a, "the given circle")
    outline(d, e, f)

    at_d, at_e = angle_at(f, d, e), angle_at(d, e, f)
    # The arc between two contact points is the supplement of the angle between
    # the tangents there, so lay the contact points off by those supplements.
    touch_b = posit(_turn(o, a, STRAIGHT - at_d), "P")
    touch_c = posit(_turn(o, touch_b, STRAIGHT - at_e), "Q")
    touches = (a, touch_b, touch_c)
    tangents = [_tangent_at(o, point, f"the tangent at {point.label}") for point in touches]
    for point in touches:
        line(o, point, "a radius")

    corners = [
        posit(meet_one(tangents[index], tangents[(index + 1) % 3]), "GHK"[index])
        for index in range(3)
    ]
    outline(*corners)

    claim("each side touches the circle, meeting a radius at right angles", "III.16",
          all(on_circle(point, around) for point in touches)
          and all(right_angle(o, touches[i], corners[i]) for i in range(3)))
    claim("so the circumscribed triangle is equiangular with the given one", "III.32",
          eq_angle(corners[2], corners[0], corners[1], f, d, e)
          and eq_angle(corners[0], corners[1], corners[2], d, e, f))
    return Out(triangle=tuple(corners), touching=touches)


@proposition(
    "IV.12",
    CONSTRUCTION,
    sample=samples.segment,
    note="The pentagon of IV.11 turned outside in: its vertices become the points "
    "where the circumscribed pentagon touches.",
)
def prop_IV_12(o: Point, a: Point) -> Out:
    """Circumscribe a regular pentagon about the circle about O through A."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")
    touches = prop_IV_11(o, a).pentagon

    tangents = [_tangent_at(o, point) for point in touches]
    corners = [
        posit(meet_one(tangents[index], tangents[(index + 1) % 5]), "GHKLM"[index])
        for index in range(5)
    ]
    outline(*corners)

    claim("each side touches the circle at a vertex of the inscribed pentagon", "III.16",
          all(on_circle(point, around) for point in touches)
          and all(right_angle(o, touches[i], corners[i]) for i in range(5)))
    claim("the circumscribed pentagon is equilateral", "I.47",
          all(eq_len(corners[i], corners[(i + 1) % 5], corners[0], corners[1])
              for i in range(5)))
    claim("and equiangular", "I.8",
          all(eq_angle(corners[i - 1], corners[i], corners[(i + 1) % 5],
                       corners[4], corners[0], corners[1]) for i in range(5)))
    return Out(pentagon=tuple(corners), touching=touches)


@proposition(
    "IV.4",
    CONSTRUCTION,
    sample=samples.triangle,
    note="The incircle. Its centre is where the angle bisectors meet, and unlike "
    "the circumcentre it is irrational in general -- the kernel carries it exactly.",
)
def prop_IV_4(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    outline(a, b, c)

    # Where two angle bisectors cross. Weighting each vertex by the opposite
    # side is the same point Euclid reaches with I.9, and reaches it without
    # intersecting two constructed rays.
    opposite = (length(b, c), length(c, a), length(a, b))
    total = opposite[0] + opposite[1] + opposite[2]
    centre = posit(
        Point(
            (opposite[0] * a.x + opposite[1] * b.x + opposite[2] * c.x) / total,
            (opposite[0] * a.y + opposite[1] * b.y + opposite[2] * c.y) / total,
        ),
        "O",
    )
    feet = [
        posit(_foot_of_the_perpendicular(centre, *side), "DEF"[index])
        for index, side in enumerate(((b, c), (c, a), (a, b)))
    ]
    for foot in feet:
        line(centre, foot)
    inscribed = circle(centre, feet[0], "the inscribed circle")

    claim("the centre lies on the bisector of each angle", "I.9",
          all(eq_angle(*pair) for pair in (
              (b, a, centre, centre, a, c),
              (a, b, centre, centre, b, c),
              (a, c, centre, centre, c, b))))
    claim("the perpendiculars from it to the three sides are equal", "I.26",
          eq_len(centre, feet[0], centre, feet[1])
          and eq_len(centre, feet[0], centre, feet[2]))
    claim("each perpendicular meets its side at right angles", "I.12",
          all(right_angle(centre, feet[index], vertex)
              for index, vertex in enumerate((b, c, a))))
    claim("so the circle on that radius touches all three sides", "III.16",
          all(on_circle(foot, inscribed) for foot in feet))
    return Out(centre=centre, circle=inscribed)


@proposition(
    "IV.10",
    CONSTRUCTION,
    sample=samples.segment,
    note="The triangle that makes the pentagon possible: its base angles are "
    "double the apex, which puts 36 degrees within reach of the compass.",
)
def prop_IV_10(a: Point, b: Point) -> Out:
    """Cut AB in extreme and mean ratio, and step the greater segment off the
    circle about A."""
    hypothesis("A and B are distinct", a != b)
    section = prop_II_11(a, b).section
    around = circle(a, b, "circle centre A through B")
    reach = circle_with_radius2(b, len2(a, section), "circle centre B with radius AC")
    d = posit(meet(reach, around)[0], "D")
    outline(a, b, d)
    line(section, d, "CD")

    claim("BD equals the greater segment AC", "I.3", eq_len(b, d, a, section))
    claim("the triangle is isosceles, AB and AD both radii", "Def.15", eq_len(a, b, a, d))
    claim("each angle at the base is double the angle at the apex", ["II.11", "III.32"],
          angle_at(a, b, d) == angle_at(b, a, d).doubled()
          and angle_at(a, d, b) == angle_at(b, a, d).doubled())
    return Out(triangle=(a, b, d), section=section)


@proposition(
    "IV.13",
    CONSTRUCTION,
    sample=samples.segment,
    note="Every regular polygon has an inscribed circle for the same reason: the "
    "centre is as far from every side as from every other.",
)
def prop_IV_13(o: Point, a: Point) -> Out:
    """The pentagon is the one IV.11 inscribes; inscribe a circle in it."""
    hypothesis("the circle has positive radius", o != a)
    vertices = prop_IV_11(o, a).pentagon
    outline(*vertices)

    feet = [posit(prop_I_10(vertices[i], vertices[(i + 1) % 5]).midpoint, "FGHKL"[i])
            for i in range(5)]
    for foot in feet:
        line(o, foot)
    inscribed = circle(o, feet[0], "the inscribed circle")

    claim("the centre is equally distant from every side", "I.4",
          all(eq_len(o, foot, o, feet[0]) for foot in feet))
    claim("and meets each at right angles", "I.12",
          all(right_angle(o, feet[i], vertices[i]) for i in range(5)))
    claim("so the circle touches all five sides", "III.16",
          all(on_circle(foot, inscribed) for foot in feet))
    return Out(centre=o, circle=inscribed, pentagon=vertices)


@proposition(
    "IV.14",
    CONSTRUCTION,
    sample=samples.segment,
)
def prop_IV_14(o: Point, a: Point) -> Out:
    """Circumscribe a circle about the regular pentagon of IV.11."""
    hypothesis("the circle has positive radius", o != a)
    vertices = prop_IV_11(o, a).pentagon
    outline(*vertices)
    for vertex in vertices:
        line(o, vertex)
    around = circle(o, vertices[0], "the circumscribed circle")

    claim("the centre is equally distant from every vertex", "I.6",
          all(eq_len(o, vertex, o, vertices[0]) for vertex in vertices))
    claim("so one circle passes through all five", "Def.15",
          all(on_circle(vertex, around) for vertex in vertices))
    return Out(centre=o, circle=around)


@proposition(
    "IV.16",
    CONSTRUCTION,
    sample=samples.segment,
    note="Fifteen because three and five are prime to one another: a third of the "
    "circumference less a fifth leaves two fifteenths, and bisecting that gives one.",
)
def prop_IV_16(o: Point, a: Point) -> Out:
    """Inscribe a regular fifteen-angled figure, from the hexagon and the pentagon."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")

    # Euclid's own route. From A, a vertex of the inscribed equilateral triangle
    # stands a third of the way round and a vertex of the pentagon a fifth, so
    # the arc between them is 1/3 - 1/5 = 2/15. Bisecting it gives a fifteenth,
    # and its chord is the side wanted. Nothing here is a formula for the side:
    # it is measured off the figure, as he measures it.
    pentagon = prop_IV_11(o, a).pentagon
    a_fifth = pentagon[1]
    third = circle_with_radius2(a, 3 * len2(o, a), "the chord subtending a third")
    a_third = posit(
        next(point for point in meet(third, around)
             if same_side(point, a_fifth, Line.through(o, a))),
        "T",
    )
    middle = posit(prop_I_10(a_fifth, a_third).midpoint, "M")
    bisected = posit(
        next(point for point in meet(Line.through(o, middle), around)
             if sign((point.x - o.x) * (middle.x - o.x)
                     + (point.y - o.y) * (middle.y - o.y)) > 0),
        "N",
    )
    claim("the arc between the two vertices is two fifteenths of the circle", "IV.11",
          on_circle(a_third, around) and on_circle(a_fifth, around))
    claim("and N bisects it, so AN cuts off one fifteenth", "III.30",
          eq_len(bisected, a_fifth, bisected, a_third))

    side2 = len2(a_fifth, bisected)
    vertices = [a]
    current = a
    for step in range(14):
        stepper = circle_with_radius2(current, side2, f"step {step + 1}")
        onward = [point for point in meet(stepper, around) if point not in vertices]
        if not onward:
            break
        current = posit(onward[0], f"V{step + 2}")
        vertices.append(current)

    claim("stepping the chord round the circle reaches fifteen distinct points", "Post.3",
          len(vertices) == 15)
    outline(*vertices)
    claim("every vertex lies on the circle", "Def.15",
          all(on_circle(vertex, around) for vertex in vertices))
    claim("the figure is equilateral", "Def.19",
          all(eq_len(vertices[i], vertices[(i + 1) % 15], vertices[0], vertices[1])
              for i in range(15)))
    claim("and equiangular", "III.27",
          all(eq_angle(vertices[i - 1], vertices[i], vertices[(i + 1) % 15],
                       vertices[14], vertices[0], vertices[1]) for i in range(15)))
    return Out(polygon=tuple(vertices))


@proposition(
    "IV.11",
    CONSTRUCTION,
    sample=samples.segment,
    note="The high point of Book IV. Its side is the golden section of the radius, "
    "so the vertices live in Q(sqrt 5) -- and the kernel keeps them there exactly.",
)
def prop_IV_11(o: Point, a: Point) -> Out:
    """Inscribe a regular pentagon in the circle centred at O and through A."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")

    # The side subtending a fifth of the circumference satisfies
    # s^2 = R^2 (5 - sqrt 5) / 2, which is the golden section of II.11 in disguise.
    side2 = len2(o, a) * (5 - sqrt(5)) / 2
    vertices = [a]
    current = a
    for step in range(4):
        stepper = circle_with_radius2(current, side2, f"step {step + 1}")
        onward = [point for point in meet(stepper, around) if point not in vertices]
        if not onward:
            break
        current = posit(onward[0], "BCDE"[step])
        vertices.append(current)

    claim("stepping the chord round the circle reaches five distinct points", "Post.3",
          len(vertices) == 5)
    for index in range(5):
        line(vertices[index], vertices[(index + 1) % 5])

    claim("every vertex lies on the given circle", "Def.15",
          all(on_circle(vertex, around) for vertex in vertices))
    claim("the pentagon is equilateral", "Def.19",
          all(eq_len(vertices[i], vertices[(i + 1) % 5], vertices[0], vertices[1])
              for i in range(5)))
    claim("and equiangular", "III.27",
          all(eq_angle(vertices[i - 1], vertices[i], vertices[(i + 1) % 5],
                       vertices[4], vertices[0], vertices[1]) for i in range(5)))
    golden = (sqrt(5) - 1) / 2
    claim("the diagonal exceeds the side in extreme and mean ratio", "II.11",
          length(vertices[0], vertices[2]) * golden == length(vertices[0], vertices[1]))
    return Out(pentagon=tuple(vertices))
