"""Book I, propositions 1-26: congruence, inequality, and the basic constructions.

Everything here is proved without the parallel postulate.  Euclid keeps
Postulate 5 in reserve until I.29, and so do we -- the dependency graph shows
the seam.

Each proposition below constructs its figure with the postulate primitives and
then walks Euclid's own argument, one :func:`claim` per step, citing what he
cites.  The citation is bookkeeping; the check is exact and independent, so a
misattributed step still cannot let a false statement through.
"""

from __future__ import annotations

from ..plane.angles import STRAIGHT, angle_at, length
from ..plane.construct import circle, circle_with_radius2, line, meet, meet_one, posit
from ..plane.objects import Line, Point
from ..plane.predicates import (
    angle_cmp,
    between,
    collinear,
    congruent_sss,
    eq_angle,
    eq_area,
    eq_len,
    len2,
    on_line,
    perpendicular,
    right_angle,
    same_side,
)
from . import samples
from .registry import CONSTRUCTION, THEOREM, Out, claim, hypothesis, proposition

# ---------------------------------------------------------------------------
# I.1 - I.3  the transfer of magnitude
# ---------------------------------------------------------------------------


@proposition(
    "I.1",
    "On a given finite straight line to construct an equilateral triangle.",
    CONSTRUCTION,
    sample=samples.segment,
)
def prop_I_1(a: Point, b: Point) -> Out:
    """The first construction in the *Elements*, and the first thing it takes
    on faith: that the two circles meet at all."""
    around_a = circle(a, b, "circle centre A through B")
    around_b = circle(b, a, "circle centre B through A")
    apex = posit(meet(around_a, around_b)[0], "C")
    line(a, apex)
    line(b, apex)

    claim("CA = AB, both radii of the circle centre A", "Def.15", eq_len(apex, a, a, b))
    claim("CB = BA, both radii of the circle centre B", "Def.15", eq_len(apex, b, b, a))
    claim("therefore CA = CB", "C.N.1", eq_len(apex, a, apex, b))
    return Out(apex=apex, triangle=(a, b, apex))


@proposition(
    "I.2",
    "To place at a given point (as an extremity) a straight line equal to a given straight line.",
    CONSTRUCTION,
    sample=samples.point_and_segment,
)
def prop_I_2(a: Point, b: Point, c: Point) -> Out:
    """Euclid cannot simply carry a length across the plane -- his compass
    collapses -- so he transports it through an equilateral triangle."""
    hypothesis("A and B are distinct", a != b)
    hypothesis("BC is a genuine magnitude", b != c)

    apex = prop_I_1(a, b).apex.named("D")
    through_b = line(apex, b, "DB produced")
    through_a = line(apex, a, "DA produced")

    radius_bc = circle(b, c, "circle centre B through C")
    g = posit(meet(through_b, radius_bc)[1], "G")

    radius_dg = circle_with_radius2(apex, len2(apex, g), "circle centre D through G")
    placed = posit(meet(through_a, radius_dg)[1], "L")

    claim("DA = DB, sides of the equilateral triangle", "I.1", eq_len(apex, a, apex, b))
    claim("BG = BC, radii of the circle centre B", "Def.15", eq_len(b, g, b, c))
    claim("DL = DG, radii of the circle centre D", "Def.15", eq_len(apex, placed, apex, g))
    claim("so AL = BG, the remainders", "C.N.3", eq_len(a, placed, b, g))
    claim("therefore AL = BC", "C.N.1", eq_len(a, placed, b, c))
    return Out(placed=placed, equal_to=(b, c))


@proposition(
    "I.3",
    "Given two unequal straight lines, to cut off from the greater a straight line equal to the less.",
    CONSTRUCTION,
    sample=samples.unequal_segments,
)
def prop_I_3(a: Point, b: Point, c: Point, d: Point) -> Out:
    hypothesis("AB is greater than CD", len2(a, b) > len2(c, d))

    placed = prop_I_2(a, c, d).placed
    reach = circle_with_radius2(a, len2(a, placed), "circle centre A with radius CD")
    cut = posit(meet(line(a, b), reach)[1], "E")

    claim("AE = AL = CD", "I.2", eq_len(a, cut, c, d))
    claim("E falls between A and B, since AB is the greater", "C.N.5", between(a, cut, b))
    return Out(cut=cut)


# ---------------------------------------------------------------------------
# I.4 - I.8  congruence
# ---------------------------------------------------------------------------


def _sas_pair(rng):
    """Two triangles built from the same data: two sides and the included angle."""
    a, b, c = samples.triangle(rng)
    move = samples.isometry(rng)
    return a, b, c, move(a), move(b), move(c)


@proposition(
    "I.4",
    "If two triangles have two sides equal to two sides respectively, and have the angles "
    "contained by the equal straight lines equal, then they also have the base equal to the "
    "base, the triangle equals the triangle, and the remaining angles equal the remaining angles.",
    THEOREM,
    sample=_sas_pair,
    note="Side-angle-side. Euclid argues by superposition; the machine checks the "
    "conclusion exactly on every sampled configuration meeting the hypothesis.",
)
def prop_I_4(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("AB = DE", eq_len(a, b, d, e))
    hypothesis("AC = DF", eq_len(a, c, d, f))
    hypothesis("the included angles BAC and EDF are equal", eq_angle(b, a, c, e, d, f))

    claim("the base BC equals the base EF", "Def.4", eq_len(b, c, e, f))
    claim("the triangles are equal in area", "C.N.4", eq_area((a, b, c), (d, e, f)))
    claim("angle ABC = angle DEF", "C.N.4", eq_angle(a, b, c, d, e, f))
    claim("angle ACB = angle DFE", "C.N.4", eq_angle(a, c, b, d, f, e))
    return Out()


@proposition(
    "I.5",
    "In isosceles triangles the angles at the base equal one another, and if the equal "
    "straight lines are produced further, then the angles under the base equal one another.",
    THEOREM,
    sample=samples.isosceles,
    note="The pons asinorum. Euclid's proof produces the equal sides and applies I.4 twice.",
)
def prop_I_5(a: Point, b: Point, c: Point) -> Out:
    hypothesis("AB = AC", eq_len(a, b, a, c))

    # produce AB to F and AC to G, cutting off equal parts (I.3)
    reach = len2(a, b) * 2
    beyond = circle_with_radius2(a, reach, "circle centre A with radius AF")
    f = posit(meet(line(a, b), beyond)[1], "F")
    g = posit(meet(line(a, c), beyond)[1], "G")
    line(f, c)
    line(g, b)

    claim("AF = AG by construction", "I.3", eq_len(a, f, a, g))
    claim("triangles AFC and AGB have two sides and the included angle equal", "I.4",
          eq_len(f, c, g, b))
    claim("hence angle ACF = angle ABG", "I.4", eq_angle(a, c, f, a, b, g))
    claim("BF = CG, the remainders of equals", "C.N.3", eq_len(b, f, c, g))
    claim("triangles BFC and CGB are then equal by two sides and the included angle", "I.4",
          eq_angle(b, f, c, c, g, b))
    claim("angle FBC = angle GCB, the angles under the base", "I.4", eq_angle(f, b, c, g, c, b))
    claim("therefore angle ABC = angle ACB, the angles at the base", "C.N.3",
          eq_angle(a, b, c, a, c, b))
    return Out()


@proposition(
    "I.6",
    "If in a triangle two angles equal one another, then the sides opposite the equal "
    "angles also equal one another.",
    THEOREM,
    sample=samples.isosceles,
    note="Converse of I.5, proved by Euclid's first reductio.",
)
def prop_I_6(a: Point, b: Point, c: Point) -> Out:
    hypothesis("angle ABC = angle ACB", eq_angle(a, b, c, a, c, b))
    claim("were AB unequal to AC, the greater could be cut down to the less (I.3) and "
          "I.4 would make a part equal the whole, which is absurd; so AB = AC",
          ["I.3", "I.4", "C.N.5"], eq_len(a, b, a, c))
    return Out()


def _reflect(point: Point, first: Point, second: Point) -> Point:
    """Reflect ``point`` in the line through ``first`` and ``second`` (exactly)."""
    dx, dy = second.x - first.x, second.y - first.y
    vx, vy = point.x - first.x, point.y - first.y
    scale = 2 * (vx * dx + vy * dy) / (dx * dx + dy * dy)
    return Point(first.x + scale * dx - vx, first.y + scale * dy - vy)


def _apex_pair(rng):
    """A base AB with two apexes carrying equal legs -- the figure of I.7.

    The only two candidates are C itself and its reflection in AB, so the
    sampler offers both; the reflection is rejected by the same-side hypothesis,
    which is exactly the restriction Euclid states.
    """
    a, b, c = samples.triangle(rng)
    twin = c if rng.random() < 0.5 else _reflect(c, a, b)
    return a, b, c, twin


@proposition(
    "I.7",
    "Given two straight lines constructed on a straight line from its extremities and "
    "meeting in a point, there cannot be constructed on the same straight line from its "
    "extremities, and on the same side of it, two other straight lines meeting in another "
    "point and equal to the former two respectively.",
    THEOREM,
    sample=_apex_pair,
    note="The uniqueness of the apex. Stated here as: equal legs on the same side force "
    "the same point.",
)
def prop_I_7(a: Point, b: Point, c: Point, d: Point) -> Out:
    hypothesis("AC = AD", eq_len(a, c, a, d))
    hypothesis("BC = BD", eq_len(b, c, b, d))
    hypothesis("C and D lie on the same side of AB, or on it",
               not (Line.through(a, b).side_of(c) * Line.through(a, b).side_of(d) < 0))
    claim("if C and D were distinct, I.5 would give an angle both greater and less than "
          "another; so C and D coincide", "I.5", c == d)
    return Out()


def _sss_pair(rng):
    a, b, c = samples.triangle(rng)
    move = samples.isometry(rng)
    return a, b, c, move(a), move(b), move(c)


@proposition(
    "I.8",
    "If two triangles have the two sides equal to two sides respectively, and also have "
    "the base equal to the base, then they also have the angles equal which are contained "
    "by the equal straight lines.",
    THEOREM,
    sample=_sss_pair,
)
def prop_I_8(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("the three sides are equal respectively", congruent_sss((a, b, c), (d, e, f)))
    claim("applying one triangle to the other, I.7 forbids the apexes to differ, "
          "so angle BAC = angle EDF", "I.7", eq_angle(b, a, c, e, d, f))
    claim("likewise angle ABC = angle DEF", "I.7", eq_angle(a, b, c, d, e, f))
    claim("and angle BCA = angle EFD", "I.7", eq_angle(b, c, a, e, f, d))
    return Out()


# ---------------------------------------------------------------------------
# I.9 - I.12  bisection and perpendiculars
# ---------------------------------------------------------------------------


@proposition(
    "I.9",
    "To bisect a given rectilinear angle.",
    CONSTRUCTION,
    sample=samples.angle_config,
)
def prop_I_9(a: Point, b: Point, c: Point) -> Out:
    """Cut equal lengths along the two rays, then hang an equilateral triangle
    between their ends; the line to its apex bisects the angle."""
    reach = min(len2(b, a), len2(b, c))
    gauge = circle_with_radius2(b, reach, "circle centre B")
    d = posit(meet(line(b, a), gauge)[1], "D")
    e = posit(meet(line(b, c), gauge)[1], "E")

    apex = posit(prop_I_1(d, e).apex, "F")
    if apex == b:
        # the equilateral apex landed on the vertex itself (a 60-degree angle);
        # the triangle on the other side of DE serves just as well
        apex = posit(meet(circle(d, e), circle(e, d))[1], "F")
    bisector = line(b, apex, "the bisector BF")

    claim("BD = BE by construction", "I.3", eq_len(b, d, b, e))
    claim("DF = EF, sides of the equilateral triangle DEF", "I.1", eq_len(d, apex, e, apex))
    claim("triangles BDF and BEF have three sides equal", "I.8", congruent_sss((b, d, apex), (b, e, apex)))
    claim("therefore angle ABF = angle FBC: the angle is bisected", "I.8",
          eq_angle(a, b, apex, apex, b, c))
    return Out(bisector=bisector, through=apex)


@proposition(
    "I.10",
    "To bisect a given finite straight line.",
    CONSTRUCTION,
    sample=samples.segment,
)
def prop_I_10(a: Point, b: Point) -> Out:
    apex = prop_I_1(a, b).apex.named("C")
    bisected = prop_I_9(a, apex, b)
    middle = posit(meet_one(bisected.bisector, line(a, b)), "D")

    claim("AD = DB: the line is bisected", "I.4", eq_len(a, middle, middle, b))
    claim("D lies on AB", "Def.4", on_line(middle, Line.through(a, b)))
    claim("D lies between A and B", "C.N.5", between(a, middle, b))
    return Out(midpoint=middle)


@proposition(
    "I.11",
    "To draw a straight line at right angles to a given straight line from a given point on it.",
    CONSTRUCTION,
    sample=samples.point_on_segment,
)
def prop_I_11(a: Point, b: Point, c: Point) -> Out:
    hypothesis("C lies on AB", on_line(c, Line.through(a, b)))
    hypothesis("C is not an endpoint", c != a and c != b)

    reach = min(len2(c, a), len2(c, b))
    gauge = circle_with_radius2(c, reach, "circle centre C")
    d, e = meet(line(a, b), gauge, "DE")
    d, e = posit(d, "D"), posit(e, "E")
    apex = posit(prop_I_1(d, e).apex, "F")
    upright = line(c, apex, "the perpendicular CF")

    claim("CD = CE by construction", "I.3", eq_len(c, d, c, e))
    claim("FD = FE, sides of the equilateral triangle", "I.1", eq_len(apex, d, apex, e))
    claim("triangles DCF and ECF have three sides equal", "I.8",
          congruent_sss((d, c, apex), (e, c, apex)))
    claim("so the adjacent angles are equal, and each is right", "Def.10",
          right_angle(a, c, apex))
    claim("CF is at right angles to AB", "Def.10", perpendicular(upright, Line.through(a, b)))
    return Out(perpendicular=upright, through=apex)


@proposition(
    "I.12",
    "To draw a straight line perpendicular to a given infinite straight line from a given "
    "point not on it.",
    CONSTRUCTION,
    sample=samples.line_and_external_point,
)
def prop_I_12(a: Point, b: Point, c: Point) -> Out:
    base = Line.through(a, b)
    hypothesis("C does not lie on AB", not on_line(c, base))

    # A circle centred at C large enough to cut AB twice: the distance from C
    # to the line is at most |CA|, so this radius strictly exceeds it.
    reach = len2(c, a) + len2(c, b)
    sweep = circle_with_radius2(c, reach, "circle centre C cutting AB")
    g, h = meet(line(a, b), sweep, "GH")
    g, h = posit(g, "G"), posit(h, "H")

    middle = posit(prop_I_10(g, h).midpoint, "E")
    dropped = line(c, middle, "the perpendicular CE")

    claim("CG = CH, radii of the circle centre C", "Def.15", eq_len(c, g, c, h))
    claim("GE = EH, since E bisects GH", "I.10", eq_len(g, middle, middle, h))
    claim("triangles CGE and CHE have three sides equal", "I.8",
          congruent_sss((c, g, middle), (c, h, middle)))
    claim("hence the adjacent angles at E are equal, so CE is perpendicular to AB", "Def.10",
          perpendicular(dropped, base))
    return Out(perpendicular=dropped, foot=middle)


# ---------------------------------------------------------------------------
# I.13 - I.15  angles at a point
# ---------------------------------------------------------------------------


@proposition(
    "I.13",
    "If a straight line stands on a straight line, then it makes either two right angles "
    "or angles whose sum equals two right angles.",
    THEOREM,
    sample=samples.straight_line_with_ray,
)
def prop_I_13(a: Point, b: Point, c: Point, d: Point) -> Out:
    hypothesis("B lies between A and C", between(a, b, c))
    hypothesis("D does not lie on AC", not collinear(a, b, d))

    left = angle_at(a, b, d)
    right = angle_at(d, b, c)
    claim("angle ABD together with angle DBC equals two right angles", "Def.10",
          left + right == STRAIGHT)
    return Out(angles=(left, right))


@proposition(
    "I.14",
    "If with any straight line, and at a point on it, two straight lines not lying on the "
    "same side make the sum of the adjacent angles equal to two right angles, then the two "
    "straight lines are in a straight line with one another.",
    THEOREM,
    sample=samples.straight_line_with_ray,
)
def prop_I_14(a: Point, b: Point, c: Point, d: Point) -> Out:
    hypothesis("D is off the line and A, C lie on opposite sides of B",
               not collinear(a, b, d) and between(a, b, c))
    total = angle_at(a, b, d) + angle_at(d, b, c)
    hypothesis("the adjacent angles sum to two right angles", total == STRAIGHT)
    claim("BA and BC are therefore in one straight line", "I.13", collinear(a, b, c))
    return Out()


@proposition(
    "I.15",
    "If two straight lines cut one another, then they make the vertical angles equal to one another.",
    THEOREM,
    sample=samples.crossing_lines,
)
def prop_I_15(a: Point, b: Point, c: Point, d: Point) -> Out:
    crossing = posit(meet_one(line(a, b), line(c, d)), "E")
    hypothesis("the lines genuinely cross between the endpoints",
               between(a, crossing, b) and between(c, crossing, d))

    claim("angle AEC and angle CEB together are two right angles", "I.13",
          angle_at(a, crossing, c) + angle_at(c, crossing, b) == STRAIGHT)
    claim("angle CEB and angle BED together are two right angles", "I.13",
          angle_at(c, crossing, b) + angle_at(b, crossing, d) == STRAIGHT)
    claim("therefore the vertical angles AEC and BED are equal", "C.N.3",
          eq_angle(a, crossing, c, b, crossing, d))
    claim("and likewise AED equals CEB", "C.N.3", eq_angle(a, crossing, d, c, crossing, b))
    return Out(crossing=crossing)


# ---------------------------------------------------------------------------
# I.16 - I.21  inequalities
# ---------------------------------------------------------------------------


@proposition(
    "I.16",
    "In any triangle, if one of the sides is produced, then the exterior angle is greater "
    "than either of the interior and opposite angles.",
    THEOREM,
    sample=samples.triangle,
    note="Euclid's proof needs the produced line to fall where the diagram shows it -- "
    "a betweenness assumption the postulates do not supply. It is the classic example "
    "of a step that fails on a sphere.",
)
def prop_I_16(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))

    # produce BC to D
    d = posit(Point(c.x + (c.x - b.x), c.y + (c.y - b.y)), "D")
    line(b, d, "BC produced to D")
    middle = posit(prop_I_10(a, c).midpoint, "E")
    f = posit(Point(middle.x + (middle.x - b.x), middle.y + (middle.y - b.y)), "F")
    line(b, f, "BE produced to F")

    claim("AE = EC and BE = EF by construction", "I.10",
          eq_len(a, middle, middle, c) and eq_len(b, middle, middle, f))
    claim("the vertical angles at E are equal", "I.15",
          eq_angle(a, middle, b, c, middle, f))
    claim("so triangles AEB and CEF are equal, giving angle BAE = angle ECF", "I.4",
          eq_angle(b, a, middle, middle, c, f))
    claim("the exterior angle ACD exceeds the interior and opposite angle BAC", "C.N.5",
          angle_at(a, c, d) > angle_at(b, a, c))
    claim("and likewise it exceeds the angle ABC", "C.N.5",
          angle_at(a, c, d) > angle_at(a, b, c))
    return Out(produced=d)


@proposition(
    "I.17",
    "In any triangle the sum of any two angles is less than two right angles.",
    THEOREM,
    sample=samples.triangle,
)
def prop_I_17(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
    alpha, beta, gamma = angle_at(b, a, c), angle_at(a, b, c), angle_at(a, c, b)
    claim("angle A and angle B together fall short of two right angles", "I.16",
          alpha + beta < STRAIGHT)
    claim("so do angle B and angle C", "I.16", beta + gamma < STRAIGHT)
    claim("and so do angle C and angle A", "I.16", gamma + alpha < STRAIGHT)
    return Out()


def _unequal_sides(rng):
    """A triangle relabelled so that AC is strictly the greater of the two
    sides at A -- the hypothesis of I.18 and, equivalently, of I.19."""
    while True:
        a, b, c = samples.triangle(rng)
        if len2(a, b) == len2(a, c):
            continue
        return (a, b, c) if len2(a, c) > len2(a, b) else (a, c, b)


@proposition(
    "I.18",
    "In any triangle the greater side subtends the greater angle.",
    THEOREM,
    sample=_unequal_sides,
)
def prop_I_18(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
    hypothesis("AC is greater than AB", len2(a, c) > len2(a, b))
    claim("cutting AD equal to AB from the greater side and using I.5 and I.16, "
          "the angle ABC exceeds the angle BCA", ["I.3", "I.5", "I.16"],
          angle_cmp(a, b, c, b, c, a) > 0)
    return Out()


@proposition(
    "I.19",
    "In any triangle the greater angle is subtended by the greater side.",
    THEOREM,
    sample=_unequal_sides,
)
def prop_I_19(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
    hypothesis("the angle ABC is greater than the angle BCA", angle_cmp(a, b, c, b, c, a) > 0)
    claim("were AC not greater than AB, I.5 or I.18 would contradict the hypothesis",
          ["I.5", "I.18"], len2(a, c) > len2(a, b))
    return Out()


@proposition(
    "I.20",
    "In any triangle the sum of any two sides is greater than the remaining one.",
    THEOREM,
    sample=samples.triangle,
    note="The triangle inequality -- which the Epicureans mocked as evident even to an ass.",
)
def prop_I_20(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
    ab, bc, ca = length(a, b), length(b, c), length(c, a)
    claim("BA together with AC is greater than BC", ["I.5", "I.19"], ab + ca > bc)
    claim("AB together with BC is greater than AC", ["I.5", "I.19"], ab + bc > ca)
    claim("BC together with CA is greater than BA", ["I.5", "I.19"], bc + ca > ab)
    return Out()


@proposition(
    "I.21",
    "If from the ends of one of the sides of a triangle two straight lines are constructed "
    "meeting within the triangle, then the sum of the straight lines so constructed is less "
    "than the sum of the remaining two sides of the triangle, but the constructed lines "
    "contain a greater angle.",
    THEOREM,
    sample=samples.triangle_with_interior_point,
)
def prop_I_21(a: Point, b: Point, c: Point, d: Point) -> Out:
    base = Line.through(a, b)
    hypothesis("D lies inside the triangle ABC",
               same_side(d, c, base)
               and same_side(d, a, Line.through(b, c))
               and same_side(d, b, Line.through(a, c)))
    line(a, d)
    line(b, d)
    claim("BD together with DA is less than BC together with CA", "I.20",
          length(b, d) + length(d, a) < length(b, c) + length(c, a))
    claim("but the angle BDA is greater than the angle BCA", "I.16",
          angle_at(b, d, a) > angle_at(b, c, a))
    return Out()


# ---------------------------------------------------------------------------
# I.22 - I.23  constructing from given data
# ---------------------------------------------------------------------------


def _choose_side(
    candidates: list[Point],
    reference: Line,
    beside: "Point | None",
    apart_from: "Point | None",
) -> Point:
    """Pick the intersection that falls on the requested side of a line."""
    if beside is None and apart_from is None:
        return candidates[0]
    wanted = reference.side_of(beside) if beside is not None else -reference.side_of(apart_from)
    for candidate in candidates:
        if reference.side_of(candidate) == wanted:
            return candidate
    return candidates[0]


def _three_lengths(rng):
    a, b, c = samples.triangle(rng)
    base = samples.nonzero(rng, 2, 6)
    return a, b, c, Point(0, 0), Point(base, 0)


@proposition(
    "I.22",
    "To construct a triangle out of three straight lines which equal three given straight "
    "lines; it is necessary that the sum of any two of the given lines be greater than the "
    "remaining one.",
    CONSTRUCTION,
    sample=_three_lengths,
    note="The proviso is I.20, and Euclid states it as a necessary condition without "
    "proving it sufficient -- another place where continuity is doing silent work.",
)
def prop_I_22(
    a: Point,
    b: Point,
    c: Point,
    p: Point,
    q: Point,
    beside: "Point | None" = None,
    apart_from: "Point | None" = None,
) -> Out:
    """Build a triangle on the ray PQ whose sides equal AB, BC and CA.

    The two circles meet on both sides of PQ, and either intersection answers
    the problem.  ``beside`` and ``apart_from`` say which one is wanted -- a
    choice Euclid makes silently by drawing the figure one way round.
    """
    first, second, third = len2(a, b), len2(b, c), len2(c, a)
    hypothesis("the three given lines satisfy the triangle inequality",
               length(a, b) + length(b, c) > length(c, a)
               and length(b, c) + length(c, a) > length(a, b)
               and length(c, a) + length(a, b) > length(b, c))
    hypothesis("P and Q are distinct", p != q)

    ray = line(p, q, "the ray PQ")
    around_p = circle_with_radius2(p, first, "circle radius AB about P")
    foot = posit(meet(ray, around_p)[1], "F")
    around_f = circle_with_radius2(foot, second, "circle radius BC about F")
    closing = circle_with_radius2(p, third, "circle radius CA about P")
    candidates = meet(around_f, closing)
    apex = posit(_choose_side(candidates, Line.through(p, q), beside, apart_from), "G")

    claim("PG equals the third given line CA", "Def.15", eq_len(p, apex, c, a))
    claim("FG equals the second given line BC", "Def.15", eq_len(foot, apex, b, c))
    claim("PF equals the first given line AB", "Def.15", eq_len(p, foot, a, b))
    claim("so the triangle PFG is built from the three given lines", "I.8",
          congruent_sss((p, foot, apex), (a, b, c)))
    return Out(triangle=(p, foot, apex))


def _angle_and_ray(rng):
    a, b, c = samples.angle_config(rng)
    move = samples.frame(rng)
    p, q = move(Point(0, 0)), move(Point(samples.nonzero(rng, 2, 6), 0))
    return a, b, c, p, q


@proposition(
    "I.23",
    "To construct a rectilinear angle equal to a given rectilinear angle on a given "
    "straight line and at a point on it.",
    CONSTRUCTION,
    sample=_angle_and_ray,
)
def prop_I_23(
    a: Point,
    b: Point,
    c: Point,
    p: Point,
    q: Point,
    beside: "Point | None" = None,
    apart_from: "Point | None" = None,
) -> Out:
    hypothesis("ABC is a genuine angle", not collinear(a, b, c))
    hypothesis("P and Q are distinct", p != q)

    line(a, c, "join AC")
    built = prop_I_22(b, a, c, p, q, beside=beside, apart_from=apart_from)
    _, foot, apex = built.triangle
    line(p, apex, "the new side")

    claim("the triangle on PQ has sides equal to BA, AC and CB", "I.22",
          congruent_sss((p, foot, apex), (b, a, c)))
    claim("therefore the angle at P equals the given angle ABC", "I.8",
          eq_angle(foot, p, apex, a, b, c))
    return Out(vertex=p, ray_through=apex)


# ---------------------------------------------------------------------------
# I.24 - I.26  further congruence
# ---------------------------------------------------------------------------


def _hinge_pair(rng):
    """Two triangles with the same pair of sides, hinged open by different angles.

    Both apexes are placed with rational rotations, so the two included angles
    are exactly comparable; the wider one is returned first, which is the
    hypothesis of I.24 (and, read backwards, of I.25).
    """
    while True:
        first_turn, second_turn = samples.rational_rotation(rng), samples.rational_rotation(rng)
        if first_turn[0] != second_turn[0] and first_turn[1] != 0 and second_turn[1] != 0:
            break
    # a smaller cosine means a wider angle
    wide, narrow = sorted((first_turn, second_turn), key=lambda turn: turn[0])
    first_leg, second_leg = samples.nonzero(rng, 3, 6), samples.nonzero(rng, 3, 6)

    def build(turn):
        sine = turn[1] if turn[1] > 0 else -turn[1]
        return (
            Point(0, 0),
            Point(first_leg, 0),
            Point(second_leg * turn[0], second_leg * sine),
        )

    move_one, move_two = samples.isometry(rng), samples.isometry(rng)
    wider = tuple(move_one(p) for p in build(wide))
    narrower = tuple(move_two(p) for p in build(narrow))
    return (wider[0], wider[1], wider[2], narrower[0], narrower[1], narrower[2])


@proposition(
    "I.24",
    "If two triangles have two sides equal to two sides respectively, but have one of the "
    "angles contained by the equal straight lines greater than the other, then they also "
    "have the base greater than the base.",
    THEOREM,
    sample=_hinge_pair,
    note="The hinge theorem.",
)
def prop_I_24(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("AB = DE and AC = DF", eq_len(a, b, d, e) and eq_len(a, c, d, f))
    hypothesis("the angle at A is greater than the angle at D",
               angle_cmp(b, a, c, e, d, f) > 0)
    claim("the base BC is greater than the base EF", ["I.4", "I.19"], len2(b, c) > len2(e, f))
    return Out()


@proposition(
    "I.25",
    "If two triangles have two sides equal to two sides respectively, but have the base "
    "greater than the base, then they also have the one of the angles contained by the "
    "equal straight lines greater than the other.",
    THEOREM,
    sample=_hinge_pair,
)
def prop_I_25(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("AB = DE and AC = DF", eq_len(a, b, d, e) and eq_len(a, c, d, f))
    hypothesis("the base BC is greater than the base EF", len2(b, c) > len2(e, f))
    claim("were the angle at A not greater, I.4 or I.24 would contradict the bases",
          ["I.4", "I.24"], angle_cmp(b, a, c, e, d, f) > 0)
    return Out()


def _asa_pair(rng):
    a, b, c = samples.triangle(rng)
    move = samples.isometry(rng)
    return a, b, c, move(a), move(b), move(c)


@proposition(
    "I.26",
    "If two triangles have two angles equal to two angles respectively, and one side equal "
    "to one side, namely either the side adjoining the equal angles or that subtending one "
    "of the equal angles, then the remaining sides equal the remaining sides and the "
    "remaining angle equals the remaining angle.",
    THEOREM,
    sample=_asa_pair,
    note="Angle-side-angle, and angle-angle-side.",
)
def prop_I_26(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("angle ABC = angle DEF", eq_angle(a, b, c, d, e, f))
    hypothesis("angle BCA = angle EFD", eq_angle(b, c, a, e, f, d))
    hypothesis("the adjoining side BC = EF", eq_len(b, c, e, f))
    claim("were AB unequal to DE, cutting off an equal part and applying I.4 would make "
          "the exterior angle equal to the interior and opposite, contrary to I.16; "
          "so AB = DE", ["I.4", "I.16"], eq_len(a, b, d, e))
    claim("hence also AC = DF", "I.4", eq_len(a, c, d, f))
    claim("and the remaining angle BAC equals the remaining angle EDF", "I.4",
          eq_angle(b, a, c, e, d, f))
    return Out()
