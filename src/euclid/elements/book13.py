"""Book XIII: the golden section, the pentagon, and the five regular solids.

The book divides in two. Propositions 1 to 12 are plane lemmas -- five metrical
facts about a line cut in extreme and mean ratio, one that hands the segments to
Book X to be named, and six about the pentagon, hexagon and decagon inscribed in
one circle. Only from 13 onwards does the book leave the plane, and everything
it does there is prepared here.

Where Euclid says "let AB be cut in extreme and mean ratio", VI.30 is called and
cuts it, so the point on the page is the one that construction produces. Where
the decagon is wanted, its side is cut from the circle by bisecting the arc the
pentagon subtends, which is what makes "inscribed in the same circle" mean
something.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import sqrt
from ..plane.angles import angle_at, length
from ..plane.construct import circle, line, meet, outline, posit, result
from ..plane.objects import Circle, Point, midpoint_of
from ..plane.predicates import (
    between,
    collinear,
    eq_angle,
    eq_len,
    len2,
    on_circle,
    on_line,
)
from . import samples
from .book01_foundations import prop_I_10
from .book04 import prop_IV_11, prop_IV_15
from .book06 import prop_VI_30
from .book10 import classify, is_rational_in_square
from .registry import THEOREM, Out, claim, hypothesis, proposition


def _along(origin: Point, towards: Point, part) -> Point:
    """The point a given fraction of the way from one point towards another.

    A negative fraction runs the other way, which is how the propositions that
    produce a line beyond its end place their point.
    """
    return Point(origin.x + part * (towards.x - origin.x),
                 origin.y + part * (towards.y - origin.y))


def _arc_midpoint(centre: Point, first: Point, second: Point, around) -> Point:
    """Where the bisector of the arc meets the circle, on the near side.

    III.30 bisects an arc by dropping the perpendicular bisector of its chord;
    the line from the centre through the chord's midpoint meets the circle
    twice, and the point wanted is the one on the same side as the chord.
    """
    near = midpoint_of(first, second)
    reached = meet(line(centre, near), around)
    return min(reached, key=lambda point: len2(point, near))


# ---------------------------------------------------------------------------
# XIII.1-5: a line cut in extreme and mean ratio, measured five ways
# ---------------------------------------------------------------------------


@proposition(
    "XIII.1",
    THEOREM,
    sample=samples.segment,
    note="The first of five metrical readings of the same cut. Each is an "
    "identity in Q(sqrt 5), and each is checked against the point VI.30 "
    "produces.",
)
def prop_XIII_1(a: Point, b: Point) -> Out:
    hypothesis("A and B are distinct", a != b)
    section = prop_VI_30(a, b).section
    half = posit(_along(a, b, Fraction(-1, 2)), "D")
    line(half, b, "DB, the whole with its half set out beyond A")
    result(half)

    claim("D lies on BA produced, with AD half of AB", ["Post.2", "I.10"],
          collinear(half, a, b) and between(half, a, b)
          and 4 * len2(a, half) == len2(a, b))
    claim("the square on CD is five times the square on AD", "II.6",
          len2(section, half) == 5 * len2(a, half))
    return Out(section=section, half=half)


def _five_times(rng):
    """A segment AB with the point C on it whose square AB stands five times over."""
    a, b = samples.segment(rng)
    return a, b, _along(a, b, 1 / sqrt(5))


@proposition(
    "XIII.2",
    THEOREM,
    sample=_five_times,
    note="The converse of XIII.1. Alone among the five, its given configuration "
    "needs sqrt 5 before any construction begins: C stands at a fifth part of "
    "the square, so the sampler leaves the rationals to lay the figure out.",
)
def prop_XIII_2(a: Point, b: Point, c: Point) -> Out:
    hypothesis("C lies on AB", collinear(a, b, c) and between(a, c, b))
    hypothesis("the square on AB is five times the square on AC",
               len2(a, b) == 5 * len2(a, c))
    line(a, b, "the given line AB")
    doubled = posit(_along(a, c, -1), "D")
    section = prop_VI_30(c, doubled).section
    result(doubled)

    claim("CD is double of AC", "Post.2",
          collinear(c, doubled, a) and len2(c, doubled) == 4 * len2(a, c))
    claim("the greater segment of CD equals the remainder CB", "VI.30",
          len2(c, section) == len2(c, b))
    claim("and it is the greater of the two", "Def.3",
          len2(c, section) > len2(section, doubled))
    return Out(doubled=doubled, section=section)


@proposition(
    "XIII.3",
    THEOREM,
    sample=samples.segment,
    note="XIII.1 read of the greater segment instead of the whole.",
)
def prop_XIII_3(a: Point, b: Point) -> Out:
    hypothesis("A and B are distinct", a != b)
    section = prop_VI_30(a, b).section
    half = prop_I_10(a, section).midpoint
    result(half)

    claim("D bisects the greater segment AC", "I.10",
          4 * len2(a, half) == len2(a, section))
    claim("the square on DB is five times the square on DC", "II.6",
          len2(half, b) == 5 * len2(half, section))
    return Out(section=section, half=half)


@proposition(
    "XIII.4",
    THEOREM,
    sample=samples.segment,
    note="A relation among the three lengths the cut already provides, so it "
    "needs no point beyond them.",
)
def prop_XIII_4(a: Point, b: Point) -> Out:
    hypothesis("A and B are distinct", a != b)
    section = prop_VI_30(a, b).section

    claim("AC is the greater segment", "Def.3", len2(a, section) > len2(section, b))
    claim("the squares on the whole and on the lesser segment together are "
          "triple of the square on the greater", "II.7",
          len2(a, b) + len2(section, b) == 3 * len2(a, section))
    return Out(section=section)


@proposition(
    "XIII.5",
    THEOREM,
    sample=samples.segment,
    note="The cut reproduces itself: adding the greater segment to the whole "
    "makes a longer line cut in the same ratio, of which the old whole is now "
    "the greater segment.",
)
def prop_XIII_5(a: Point, b: Point) -> Out:
    hypothesis("A and B are distinct", a != b)
    section = prop_VI_30(a, b).section
    added = posit(_along(a, section, -1), "D")
    line(added, b, "DB, the whole with the greater segment added to it")
    result(added)

    claim("AD equals the greater segment AC", "Post.2",
          eq_len(a, added, a, section) and between(added, a, b))
    claim("DB is cut at A in extreme and mean ratio", "VI.30",
          length(added, b) * length(added, a) == len2(a, b))
    claim("and AB is its greater segment", "Def.3", len2(a, b) > len2(added, a))
    return Out(section=section, added=added)


def _rational_line(rng):
    """A segment rational in Book X's sense.

    Definition 3 admits a line commensurable with the assigned line in length
    or in square only, and the two give different species in XIII.6, so a
    sampler offering the first alone would leave half the proposition
    unexercised.
    """
    a, b = samples.segment(rng)
    if rng.random() < 0.5:
        return a, b
    return a, _along(a, b, sqrt(rng.choice([2, 3, 5, 6, 7])))


@proposition(
    "XIII.6",
    THEOREM,
    sample=_rational_line,
    note="Book X is asked to name the two segments, and finds both to be "
    "apotomes. Euclid stops there; the species is what the classifier adds, "
    "and it turns on the given line. Commensurable in length, the segments are "
    "of the fifth and first species; commensurable in square only, the sixth "
    "and third; commensurable with the square root of five, the fourth and "
    "second, because there the greater segment has a rational term.",
)
def prop_XIII_6(a: Point, b: Point) -> Out:
    hypothesis("A and B are distinct", a != b)
    # Book X Def. 3: a rational straight line is one commensurable with the
    # assigned line in length or in square only. Asking for commensurability in
    # length is a narrower condition than Euclid's, and the conclusion does not
    # need it -- the necessity analysis reported this hypothesis as surviving
    # being broken, which is what a condition doing no work looks like.
    hypothesis("the given line is rational", is_rational_in_square(length(a, b)))
    section = prop_VI_30(a, b).section
    greater, lesser = length(a, section), length(section, b)
    named, other = classify(greater), classify(lesser)

    claim("the greater segment is the irrational line called apotome", "X.73",
          named.family == "apotome")
    claim("and so is the lesser", "X.73", other.family == "apotome")
    claim("the two are of different species", ["X.85", "X.89"],
          named.species != other.species)
    return Out(greater=greater, lesser=lesser,
               species=(named.species, other.species))


# ---------------------------------------------------------------------------
# XIII.7-12: the pentagon, the hexagon and the decagon
# ---------------------------------------------------------------------------


def _equilateral_pentagon(rng):
    """A pentagon of five equal sides, convex or star, in general position.

    Both are wanted. The convex pentagon and the pentagram have the same five
    vertices and the same claim to being equilateral, and their angles differ --
    108 degrees against 36 -- so a check that passes on one and not the other is
    a check that has found something.
    """
    centre, first = samples.segment(rng)
    radius2 = len2(centre, first)
    side2 = radius2 * (5 - sqrt(5)) / 2
    vertices = [first]
    current = first
    for _ in range(4):
        onward = [point for point
                  in meet(Circle(current, side2), Circle(centre, radius2))
                  if point not in vertices]
        if not onward:  # pragma: no cover - the pentagon always closes
            break
        current = onward[0]
        vertices.append(current)
    if rng.random() < 0.5:
        vertices = [vertices[(2 * i) % 5] for i in range(5)]
    return tuple(vertices)


@proposition(
    "XIII.7",
    THEOREM,
    sample=_equilateral_pentagon,
    note="Searching the equilateral pentagons numerically turns up none with "
    "three equal angles and a fourth unequal, save those with a vanishing "
    "angle, where two vertices have run together and no pentagon is left. "
    "Euclid's word for the figure rules those out; the guard below says so.",
)
def prop_XIII_7(a: Point, b: Point, c: Point, d: Point, e: Point) -> Out:
    corners = (a, b, c, d, e)
    angles = [angle_at(corners[i - 1], corners[i], corners[(i + 1) % 5])
              for i in range(5)]
    hypothesis("the pentagon is equilateral", all(
        eq_len(corners[i], corners[(i + 1) % 5], a, b) for i in range(5)))
    hypothesis("no angle of it has vanished", all(
        not collinear(corners[i - 1], corners[i], corners[(i + 1) % 5])
        for i in range(5)), guard=True)
    hypothesis("three of its angles are equal, taken in order or not",
               max(sum(1 for other in angles if other == one)
                   for one in angles) >= 3)
    outline(*corners)

    claim("the lines subtending the equal angles are equal, the sides "
          "containing them being equal", "I.4",
          eq_len(b, e, a, c) and eq_len(a, c, b, d))
    claim("so the triangles standing on them are isosceles and their base "
          "angles equal", "I.5",
          eq_angle(b, e, d, b, d, e) and eq_angle(a, c, d, a, d, c))
    claim("therefore the pentagon is equiangular", ["I.5", "C.N.2"],
          all(angle == angles[0] for angle in angles))
    return Out(pentagon=corners, angles=tuple(angles))


@proposition(
    "XIII.8",
    THEOREM,
    sample=samples.segment,
    note="Why the pentagon carries the golden section at all: its diagonals cut "
    "each other in extreme and mean ratio, and the greater piece is a side.",
)
def prop_XIII_8(o: Point, a: Point) -> Out:
    hypothesis("the circle has positive radius", o != a)
    corners = prop_IV_11(o, a).pentagon
    first, second = line(corners[0], corners[2]), line(corners[1], corners[3])
    cross = posit(meet(first, second)[0], "H")
    result(cross)

    whole = length(corners[0], corners[2])
    greater, lesser = length(corners[0], cross), length(cross, corners[2])
    claim("the diagonals meet within the pentagon", "Post.1",
          between(corners[0], cross, corners[2]))
    claim("AC is cut at H in extreme and mean ratio", "VI.30",
          whole * lesser == greater * greater)
    claim("and its greater segment equals the side of the pentagon", "Def.3",
          greater == length(corners[0], corners[1]) and greater > lesser)
    return Out(pentagon=corners, cross=cross)


@proposition(
    "XIII.9",
    THEOREM,
    sample=samples.segment,
    note="The decagon side is cut from the circle: bisecting the arc the "
    "pentagon subtends halves it into two decagon arcs. That the hexagon side "
    "is the radius is IV.15's, and is cited here as Euclid cites it.",
)
def prop_XIII_9(o: Point, a: Point) -> Out:
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")
    corners = prop_IV_11(o, a).pentagon
    tenth = posit(_arc_midpoint(o, corners[0], corners[1], around), "K")
    decagon = length(corners[0], tenth)
    hexagon = length(o, a)  # IV.15: the side of the hexagon is the radius
    end = posit(_along(a, o, -decagon / hexagon), "L")
    line(o, end, "the hexagon side with the decagon side added to it")
    result(tenth, end)

    claim("K bisects the arc the pentagon side subtends, so AK is the side of "
          "the decagon", "III.30",
          on_circle(tenth, around) and eq_len(tenth, corners[0], tenth, corners[1]))
    claim("OL is the side of the hexagon with the side of the decagon added "
          "to it", ["IV.15", "Post.2"],
          on_line(end, line(o, a)) and length(o, end) == hexagon + decagon
          and between(o, a, end))
    claim("OL is cut at A in extreme and mean ratio", "VI.30",
          length(o, end) * length(a, end) == hexagon * hexagon)
    claim("and its greater segment is the side of the hexagon", "Def.3",
          hexagon > decagon)
    return Out(decagon=decagon, hexagon=hexagon, whole=end)


@proposition(
    "XIII.10",
    THEOREM,
    sample=samples.segment,
    note="The three inscribed figures in one relation, and the one XIII.16 will "
    "need to put the icosahedron in its sphere.",
)
def prop_XIII_10(o: Point, a: Point) -> Out:
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")
    corners = prop_IV_11(o, a).pentagon
    tenth = posit(_arc_midpoint(o, corners[0], corners[1], around), "K")
    result(tenth)

    pentagon = len2(corners[0], corners[1])
    hexagon = len2(o, a)  # IV.15: the side of the hexagon is the radius
    decagon = len2(corners[0], tenth)
    claim("K bisects the arc, so AK is the side of the decagon", "III.30",
          on_circle(tenth, around) and eq_len(tenth, corners[0], tenth, corners[1]))
    claim("the square on the side of the pentagon equals the squares on the "
          "sides of the hexagon and of the decagon", ["I.47", "IV.15"],
          pentagon == hexagon + decagon)
    return Out(pentagon=pentagon, hexagon=hexagon, decagon=decagon)


@proposition(
    "XIII.11",
    THEOREM,
    sample=_rational_line,
    note="Book X names the pentagon's side, as it named the segments of XIII.6. "
    "The name holds for either sense in which the diameter can be rational.",
)
def prop_XIII_11(o: Point, a: Point) -> Out:
    hypothesis("the circle has positive radius", o != a)
    hypothesis("the diameter of the circle is rational",
               is_rational_in_square(2 * length(o, a)))
    corners = prop_IV_11(o, a).pentagon
    side = length(corners[0], corners[1])
    named = classify(side)

    claim("the side of the pentagon is the irrational line called minor",
          "X.76", named.name == "minor")
    claim("it is of the fourth degree over the rationals, so no rational line "
          "and no medial one", ["X.21", "X.73"], named.algebraic_degree == 4)
    return Out(side=side, name=named.name)


@proposition(
    "XIII.12",
    THEOREM,
    sample=samples.segment,
    note="Stepping the radius round the circle gives the hexagon; every other "
    "vertex of it gives the equilateral triangle.",
)
def prop_XIII_12(o: Point, a: Point) -> Out:
    hypothesis("the circle has positive radius", o != a)
    corners = prop_IV_15(o, a).hexagon
    triangle = (corners[0], corners[2], corners[4])
    outline(*triangle)
    result(*triangle)

    claim("the alternate vertices of the hexagon form an equilateral triangle",
          "IV.15",
          eq_len(triangle[0], triangle[1], triangle[1], triangle[2])
          and eq_len(triangle[1], triangle[2], triangle[2], triangle[0]))
    claim("the square on its side is triple of the square on the radius",
          "I.47", len2(triangle[0], triangle[1]) == 3 * len2(o, a))
    return Out(triangle=triangle)
