"""Book III: circles, chords, tangents, and the angles they subtend.

The book where continuity does most of its unstated work. Nearly every
proposition intersects a circle with something, and no postulate says the
intersection exists.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import is_zero, sign, to_float
from ..plane.angles import RIGHT, STRAIGHT, angle_at, length
from ..plane.construct import (
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
    right_angle,
    same_side,
)
from . import samples
from .book01_foundations import prop_I_10
from .figures import _across, _centre_of, _tangent_at, _turn
from .registry import CONSTRUCTION, THEOREM, Out, claim, hypothesis, proposition


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
