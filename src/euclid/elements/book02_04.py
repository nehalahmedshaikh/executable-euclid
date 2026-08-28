"""Books II, III and IV: geometric algebra, circles, and inscribed figures.

A representative selection rather than the complete books -- enough to show the
machinery is not tuned to Book I, and enough to reach the regular pentagon,
which is where the *Elements* first constructs something genuinely hard.

Book II is algebra without symbols: II.4 is the expansion of ``(a+b)^2``, II.11
cuts a line in extreme and mean ratio, II.14 squares a rectilinear figure.  IV.11
builds the pentagon on top of II.11, and the golden ratio arrives in the kernel
as an exact element of ``Q(sqrt 5)`` rather than as 1.618.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import sqrt
from ..plane.angles import RIGHT, STRAIGHT, angle_at, length
from ..plane.construct import circle, circle_with_radius2, line, meet, outline, posit
from ..plane.objects import Line, Point
from ..plane.predicates import (
    collinear,
    eq_angle,
    eq_len,
    len2,
    on_circle,
    on_line,
    right_angle,
)
from . import samples
from .book01_foundations import prop_I_10, prop_I_11
from .book01_parallels import prop_I_46
from .registry import CONSTRUCTION, THEOREM, Out, claim, hypothesis, proposition

# ---------------------------------------------------------------------------
# Book II -- geometric algebra
# ---------------------------------------------------------------------------


def _adjacent_segments(rng):
    """A, B, C in a straight line with B between: the sides of a rectangle
    laid end to end."""
    move = samples.frame(rng)
    first, second = samples.nonzero(rng, 1, 6), samples.nonzero(rng, 1, 6)
    return move(Point(0, 0)), move(Point(first, 0)), move(Point(first + second, 0))


@proposition(
    "II.4",
    "If a straight line is cut at random, then the square on the whole equals the squares "
    "on the segments plus twice the rectangle contained by the segments.",
    THEOREM,
    sample=_adjacent_segments,
    note="(a+b)^2 = a^2 + 2ab + b^2, four centuries before algebraic notation.",
)
def prop_II_4(a: Point, b: Point, c: Point) -> Out:
    hypothesis("B cuts AC", on_line(b, Line.through(a, c)) and b != a and b != c)
    outline(a, b, c, close=False)
    whole = length(a, c)
    first, second = length(a, b), length(b, c)
    claim("the segments together make the whole", "C.N.2", first + second == whole)
    claim("the square on the whole equals the squares on the parts together with "
          "twice the rectangle they contain", ["I.43", "I.46"],
          whole * whole == first * first + second * second + 2 * first * second)
    return Out()


@proposition(
    "II.5",
    "If a straight line is cut into equal and unequal segments, then the rectangle "
    "contained by the unequal segments of the whole together with the square on the "
    "straight line between the points of section equals the square on the half.",
    THEOREM,
    sample=_adjacent_segments,
    note="Euclid's tool for solving quadratics: ab + ((a-b)/2)^2 = ((a+b)/2)^2.",
)
def prop_II_5(a: Point, b: Point, c: Point) -> Out:
    hypothesis("B cuts AC unequally", on_line(b, Line.through(a, c)) and b != a and b != c)
    middle = posit(prop_I_10(a, c).midpoint, "D")
    first, second = length(a, b), length(b, c)
    half = length(a, middle)
    offset = length(middle, b)
    claim("the rectangle on the unequal segments, with the square on the piece between "
          "the sections, equals the square on the half", ["I.43", "I.46"],
          first * second + offset * offset == half * half)
    return Out(midpoint=middle)


@proposition(
    "II.11",
    "To cut a given straight line so that the rectangle contained by the whole and one "
    "of the segments equals the square on the remaining segment.",
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
    "II.14",
    "To construct a square equal to a given rectilinear figure.",
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

    claim("the angle in the semicircle is right", "III.31", right_angle(a, d, c))
    claim("BD is a mean proportional between AB and BC", "II.5",
          len2(b, d) == length(a, b) * length(b, c))
    claim("so the square on BD equals the given rectangle", "I.46",
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


@proposition(
    "III.3",
    "If a straight line through the centre of a circle bisects a chord not through the "
    "centre, then it cuts it at right angles.",
    THEOREM,
    sample=_points_on_a_circle,
)
def prop_III_3(o: Point, a: Point, b: Point, c: Point) -> Out:
    hypothesis("A, B and C lie on the circle centred at O",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("the chord AC does not pass through the centre", not collinear(o, a, c))
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
    "In a circle the angle at the centre is double the angle at the circumference, when "
    "the angles have the same circumference as base.",
    THEOREM,
    sample=_points_on_a_circle,
)
def prop_III_20(o: Point, a: Point, b: Point, c: Point) -> Out:
    hypothesis("A, B and C lie on the circle centred at O",
               eq_len(o, a, o, b) and eq_len(o, a, o, c))
    hypothesis("the three points are distinct", a != b and b != c and a != c)
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
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
    "In a circle the angle in the semicircle is right.",
    THEOREM,
    sample=_points_on_a_circle,
    note="Thales' theorem, which Euclid gets as a corollary of III.20.",
)
def prop_III_31(o: Point, a: Point, b: Point, c: Point) -> Out:
    hypothesis("AB is a diameter", collinear(a, o, b) and eq_len(o, a, o, b))
    hypothesis("C lies on the circle, off the diameter",
               eq_len(o, c, o, a) and not collinear(a, b, c))
    line(a, c)
    line(b, c)

    claim("the angle at the centre on the diameter is two right angles", "Def.17",
          angle_at(a, o, b) == STRAIGHT)
    claim("the angle at the circumference is half of it", "III.20",
          angle_at(a, c, b) == RIGHT)
    claim("therefore the angle ACB is right", "Def.10", right_angle(a, c, b))
    return Out()


# ---------------------------------------------------------------------------
# Book IV -- inscribed figures
# ---------------------------------------------------------------------------


@proposition(
    "IV.11",
    "To inscribe an equilateral and equiangular pentagon in a given circle.",
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
