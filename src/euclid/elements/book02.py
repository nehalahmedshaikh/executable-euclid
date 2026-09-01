"""Book II: geometric algebra, and the golden section.

Every proposition here is an identity about rectangles and squares, which is why
the book reads as algebra once its figures are drawn. II.11 cuts a line in
extreme and mean ratio, and Book XIII returns to that cut five times.
"""

from __future__ import annotations

from ..kernel.field import sign, sqrt
from ..plane.angles import RIGHT, angle_at, length
from ..plane.construct import circle, circle_with_radius2, line, meet, outline, posit
from ..plane.objects import Line, Point
from ..plane.predicates import (
    between,
    collinear,
    eq_len,
    len2,
    on_line,
    polygon_area2,
    right_angle,
)
from . import samples
from .book01_foundations import prop_I_10, prop_I_11
from .book01_parallels import prop_I_46
from .figures import _across, _foot_of_the_perpendicular
from .registry import CONSTRUCTION, THEOREM, Out, claim, hypothesis, proposition


def _area(*points: Point):
    """The area enclosed by a polygon, positive whichever way it was traced."""
    value = polygon_area2(list(points))
    return (value if value >= 0 else -value) / 2


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
