"""Book I, propositions 27-48: parallels, area, and Pythagoras.

Postulate 5 first draws breath at I.29.  Everything before it (I.27, I.28) is
neutral geometry -- true on the hyperbolic plane as well -- and the dependency
graph makes the boundary visible: ask for the ancestry of I.29 and Post.5
appears; ask for I.27 and it does not.

The area propositions I.35-I.41 are checked with exact shoelace areas, and the
application-of-areas constructions I.42-I.45 are carried out with straightedge
and compass rather than by solving for a length.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import sign
from ..plane.angles import RIGHT, STRAIGHT, angle_at, length
from ..plane.construct import (
    GeometryError,
    circle_with_radius2,
    line,
    meet,
    meet_one,
    outline,
    outline_result,
    posit,
    result,
)
from ..plane.objects import Line, Point
from ..plane.predicates import (
    between,
    collinear,
    eq_angle,
    eq_area,
    eq_len,
    eq_polygon_area,
    len2,
    on_line,
    parallel,
    polygon_area2,
    right_angle,
    same_side,
    signed_area2,
)
from . import samples
from .book01_foundations import (
    prop_I_1,
    prop_I_3,
    prop_I_4,
    prop_I_8,
    prop_I_10,
    prop_I_11,
    prop_I_13,
    prop_I_15,
    prop_I_16,
    prop_I_20,
    prop_I_22,
    prop_I_23,
    prop_I_26,
)
from .registry import (
    CONSTRUCTION,
    THEOREM,
    Out,
    because,
    claim,
    hypothesis,
    proposition,
)

# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------


def _along(origin: Point, towards: Point, distance) -> Point:
    """The point on ray ``origin -> towards`` at the given exact distance."""
    dx, dy = towards.x - origin.x, towards.y - origin.y
    scale = distance / length(origin, towards)
    return Point(origin.x + scale * dx, origin.y + scale * dy)


def _fourth_vertex(corner: Point, first: Point, second: Point) -> Point:
    """Complete the parallelogram with sides ``corner->first`` and ``corner->second``."""
    return Point(first.x + second.x - corner.x, first.y + second.y - corner.y)


def _area(*points: Point):
    """The exact (unsigned) area of a simple polygon."""
    value = polygon_area2(list(points))
    return (value if value >= 0 else -value) / 2


def _transversal(rng):
    """Parallel lines AB and CD cut by the transversal GH, in Euclid's lettering."""
    move = samples.frame(rng)
    cosine, sine = samples.rational_rotation(rng)
    if sine == 0:
        cosine, sine = Fraction(3, 5), Fraction(4, 5)
    reach = samples.nonzero(rng, 2, 5)
    left, right = samples.nonzero(rng, 1, 4), samples.nonzero(rng, 1, 4)
    g = Point(0, 0)
    h = Point(reach * cosine, reach * sine)
    return (
        move(Point(-left, 0)),
        move(Point(right, 0)),
        move(Point(h.x - left, h.y)),
        move(Point(h.x + right, h.y)),
        move(g),
        move(h),
    )


def _three_parallels(rng):
    move = samples.frame(rng)
    span = samples.nonzero(rng, 2, 5)
    first, second = samples.nonzero(rng, 1, 4), samples.nonzero(rng, 1, 4)
    rows = [0, first, first + second]
    points = []
    for height in rows:
        offset = samples.scalar(rng, -3, 3)
        points.append(move(Point(offset, height)))
        points.append(move(Point(offset + span, height)))
    return tuple(points)


# ---------------------------------------------------------------------------
# I.27 - I.31  parallels
# ---------------------------------------------------------------------------


@proposition(
    "I.27",
    THEOREM,
    sample=_transversal,
    note="Neutral geometry: no appeal to Postulate 5.",
)
def prop_I_27(a: Point, b: Point, c: Point, d: Point, g: Point, h: Point) -> Out:
    first, second = line(a, b, "AB"), line(c, d, "CD")
    line(g, h, "the transversal GH")
    hypothesis("G lies on AB and H on CD", on_line(g, first) and on_line(h, second))
    hypothesis("the alternate angles AGH and GHD are equal", eq_angle(a, g, h, g, h, d))

    # The triangle Euclid argues about is the one AB and CD would make if they
    # met. They are parallel, so there is no meeting point to build it from and
    # no figure for I.16 to speak of. Unlike the suppositions of I.14 and I.39,
    # which are drawable, this citation cannot be executed.
    claim("were AB and CD to meet, a triangle would arise whose exterior angle equalled "
          "an interior and opposite angle, contrary to I.16; so they do not meet", "I.16",
          parallel(first, second))
    return Out(first=first, second=second)


@proposition(
    "I.28",
    THEOREM,
    sample=_transversal,
)
def prop_I_28(a: Point, b: Point, c: Point, d: Point, g: Point, h: Point) -> Out:
    first, second = line(a, b, "AB"), line(c, d, "CD")
    line(g, h, "the transversal GH")
    hypothesis("G lies on AB and H on CD", on_line(g, first) and on_line(h, second))
    interior = angle_at(b, g, h) + angle_at(g, h, d)
    hypothesis("the interior angles on the same side sum to two right angles",
               interior == STRAIGHT)

    span = (b.x - a.x, b.y - a.y)
    prop_I_13(Point(g.x - span[0], g.y - span[1]), g,
              Point(g.x + span[0], g.y + span[1]), h)
    because(prop_I_27, a, b, c, d, g, h)

    claim("the angle BGH is the supplement of AGH", "I.13",
          angle_at(a, g, h) + angle_at(b, g, h) == STRAIGHT)
    claim("hence the alternate angles AGH and GHD are equal", "C.N.3",
          eq_angle(a, g, h, g, h, d))
    claim("therefore AB is parallel to CD", "I.27", parallel(first, second))
    return Out()


@proposition(
    "I.29",
    THEOREM,
    sample=_transversal,
    note="The first proposition in the Elements that needs the parallel postulate.",
)
def prop_I_29(a: Point, b: Point, c: Point, d: Point, g: Point, h: Point) -> Out:
    first, second = line(a, b, "AB"), line(c, d, "CD")
    line(g, h, "the transversal GH")
    hypothesis("G lies on AB and H on CD", on_line(g, first) and on_line(h, second))
    hypothesis("AB is parallel to CD", parallel(first, second))

    # I.13 and I.15 speak of a line standing within another, so each line is
    # taken on both sides of the point the transversal crosses it at. G may be
    # an end of AB -- I.32 hands it the vertex -- and then A and B alone will
    # not do.
    span, across = (b.x - a.x, b.y - a.y), (d.x - c.x, d.y - c.y)
    before_g = Point(g.x - span[0], g.y - span[1])
    after_g = Point(g.x + span[0], g.y + span[1])
    before_h = Point(h.x - across[0], h.y - across[1])
    after_h = Point(h.x + across[0], h.y + across[1])
    beyond = posit(Point(g.x + (g.x - h.x), g.y + (g.y - h.y)), "K")
    line(beyond, h, "the transversal produced to K")
    because(prop_I_13, before_g, g, after_g, h)
    because(prop_I_13, before_h, h, after_h, g)
    because(prop_I_15, before_g, after_g, beyond, h)

    claim("were the alternate angles unequal, the interior angles on one side would sum "
          "to less than two right angles, and by Postulate 5 the lines would meet",
          ["Post.5", "I.13"], eq_angle(a, g, h, g, h, d))
    claim("the exterior angle BGH equals the interior and opposite angle GHD's supplement",
          "I.15", eq_angle(b, g, h, g, h, c))
    claim("and the interior angles on the same side sum to two right angles", "I.13",
          angle_at(b, g, h) + angle_at(g, h, d) == STRAIGHT)
    return Out()


@proposition(
    "I.30",
    THEOREM,
    sample=_three_parallels,
)
def prop_I_30(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    first, second, third = line(a, b, "AB"), line(c, d, "CD"), line(e, f, "EF")
    hypothesis("AB is parallel to CD", parallel(first, second))
    hypothesis("EF is parallel to CD", parallel(third, second))

    # One transversal across all three, and I.29 read off it twice. Alternate
    # angles lie on opposite sides of the transversal, so each line is named by
    # the pair of points either side of where it is crossed, in that order.
    transversal = Line.through(a, f)
    crossing = meet_one(transversal, second)

    def straddling(at: Point, along: Point, from_: Point) -> tuple:
        step = (along.x - from_.x, along.y - from_.y)
        near = Point(at.x + step[0], at.y + step[1])
        far = Point(at.x - step[0], at.y - step[1])
        return (near, far) if transversal.side_of(near) > 0 else (far, near)

    up_ab, down_ab = straddling(a, b, a)
    up_cd, down_cd = straddling(crossing, d, c)
    up_ef, down_ef = straddling(f, f, e)
    because(prop_I_29, up_ab, down_ab, up_cd, down_cd, a, crossing)
    because(prop_I_29, up_cd, down_cd, up_ef, down_ef, crossing, f)

    claim("a transversal makes equal alternate angles with each, so AB is parallel to EF",
          "I.29", parallel(first, third))
    return Out()


@proposition(
    "I.31",
    CONSTRUCTION,
    sample=samples.line_and_external_point,
)
def prop_I_31(a: Point, b: Point, c: Point) -> Out:
    """Through A, parallel to BC.  Euclid copies the angle ADC over to A on the
    far side of AD, and I.27 does the rest."""
    given = line(b, c, "the given line BC")
    hypothesis("A does not lie on BC", not on_line(a, given))

    joined = line(a, b, "join AD")
    copied = prop_I_23(a, b, c, a, b, apart_from=c)
    e = posit(copied.ray_through, "E")
    drawn = line(a, e, "the parallel EF")

    # AD crosses EF at A and BC at B, at an end of each, so both are named by
    # points straddling the crossing before I.27 is asked for the parallel.
    prop_I_27(e, Point(2 * a.x - e.x, 2 * a.y - e.y),
              Point(2 * b.x - c.x, 2 * b.y - c.y), c, a, b)

    claim("the angle EAD equals the angle ADC, and they are alternate", "I.23",
          eq_angle(e, a, b, a, b, c))
    claim("therefore EF is parallel to BC", "I.27", parallel(drawn, given))
    return Out(parallel=drawn, through=e)


def _parallel_through(point: Point, first: Point, second: Point) -> Line:
    """The line through ``point`` parallel to the line ``first``-``second``."""
    return prop_I_31(point, first, second).parallel


def _square_outward(first: Point, second: Point, apex: Point):
    """The square on ``first``-``second``, standing on the far side from ``apex``.

    I.46 raises its square on whichever side its two arguments determine, so for
    a figure that cares which side -- I.47's windmill does -- the order has to be
    chosen. Swapping the arguments reflects the square, and the traversal is put
    back so that the result always reads ``first, second, next to second, next
    to first``.
    """
    if sign(signed_area2(first, second, apex)) < 0:
        return prop_I_46(first, second).square
    _, _, beside_first, beside_second = prop_I_46(second, first).square
    return (first, second, beside_second, beside_first)


# ---------------------------------------------------------------------------
# I.32 - I.34  angle sums and parallelograms
# ---------------------------------------------------------------------------


@proposition(
    "I.32",
    THEOREM,
    sample=samples.triangle,
)
def prop_I_32(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    d = posit(Point(c.x + (c.x - b.x), c.y + (c.y - b.y)), "D")
    line(b, d, "BC produced to D")
    alongside = prop_I_31(c, a, b).through

    # AC falls across AB and the parallel through C, meeting each at an end of
    # itself, so each line is named by two points straddling the crossing. The
    # alternate angle to BAC is on the far side of AC, which fixes which way
    # along the parallel to look.
    edge = Line.through(a, c)
    if edge.side_of(alongside) * edge.side_of(b) > 0:
        alongside = Point(2 * c.x - alongside.x, 2 * c.y - alongside.y)
    back_a = Point(2 * a.x - b.x, 2 * a.y - b.y)
    back_c = Point(2 * c.x - alongside.x, 2 * c.y - alongside.y)

    because(prop_I_29, b, back_a, back_c, alongside, a, c)
    because(prop_I_13, b, c, d, a)

    alpha, beta, gamma = angle_at(b, a, c), angle_at(a, b, c), angle_at(a, c, b)
    claim("the exterior angle ACD equals the sum of the angles at A and B", "I.29",
          angle_at(a, c, d) == alpha + beta)
    claim("adding the angle at C, the three angles equal two right angles", "I.13",
          alpha + beta + gamma == STRAIGHT)
    return Out(exterior=angle_at(a, c, d))


@proposition(
    "I.33",
    THEOREM,
    sample=samples.parallelogram,
)
def prop_I_33(a: Point, b: Point, c: Point, d: Point) -> Out:
    hypothesis("AB equals DC", eq_len(a, b, d, c))
    hypothesis("AB is parallel to DC", parallel(Line.through(a, b), Line.through(d, c)))
    joined_one, joined_two = line(a, d, "AD"), line(b, c, "BC")
    line(a, c, "the diagonal AC")

    # AC crosses each pair of lines at an end of itself, so each is named by
    # points straddling the crossing -- the same care I.29 and I.27 want.
    back_a, back_c = Point(2 * a.x - b.x, 2 * a.y - b.y), Point(2 * c.x - d.x, 2 * c.y - d.y)
    off_a, off_c = Point(2 * a.x - d.x, 2 * a.y - d.y), Point(2 * c.x - b.x, 2 * c.y - b.y)
    because(prop_I_29, b, back_a, back_c, d, a, c)
    because(prop_I_4, a, b, c, c, d, a)
    because(prop_I_27, d, off_a, off_c, b, a, c)

    claim("the alternate angles BAC and ACD are equal", "I.29", eq_angle(b, a, c, a, c, d))
    claim("so the triangles ABC and CDA are equal, giving AD = BC", "I.4", eq_len(a, d, b, c))
    claim("and the alternate angles being equal, AD is parallel to BC", "I.27",
          parallel(joined_one, joined_two))
    return Out()


@proposition(
    "I.34",
    THEOREM,
    sample=samples.parallelogram,
)
def prop_I_34(a: Point, b: Point, c: Point, d: Point) -> Out:
    hypothesis("ABCD is a parallelogram",
               parallel(Line.through(a, b), Line.through(d, c))
               and parallel(Line.through(a, d), Line.through(b, c)))
    outline(a, b, c, d)
    diameter = line(a, c, "the diameter AC")

    # BC falls across the parallels AB and DC, meeting each at an end of itself,
    # so each is named by points straddling the crossing. The triangles the
    # diameter makes then answer to I.26 on two angles and the side between,
    # and to I.4 on two sides and the angle between.
    beyond_b = Point(2 * b.x - a.x, 2 * b.y - a.y)
    beyond_c = Point(2 * c.x - d.x, 2 * c.y - d.y)
    because(prop_I_29, a, beyond_b, d, beyond_c, b, c)
    because(prop_I_26, a, b, c, c, d, a)
    because(prop_I_4, b, a, c, d, c, a)

    claim("the alternate angles ABC and CDA are equal", "I.29", eq_angle(a, b, c, c, d, a))
    claim("hence the triangles ABC and CDA are equal in every part", "I.26",
          eq_len(a, b, d, c) and eq_len(b, c, a, d))
    claim("the opposite angles are equal", "C.N.2", eq_angle(b, a, d, b, c, d))
    claim("and the diameter bisects the parallelogram", "I.4", eq_area((a, b, c), (a, c, d)))
    return Out(diameter=diameter)


# ---------------------------------------------------------------------------
# I.35 - I.41  equality of areas
# ---------------------------------------------------------------------------


@proposition(
    "I.35",
    THEOREM,
    sample=samples.two_parallelograms_same_base,
)
def prop_I_35(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("ABCD is a parallelogram",
               parallel(Line.through(a, b), Line.through(d, c))
               and parallel(Line.through(a, d), Line.through(b, c)))
    hypothesis("ABEF is a parallelogram on the same base",
               parallel(Line.through(a, b), Line.through(f, e))
               and parallel(Line.through(a, f), Line.through(b, e)))
    hypothesis("C, D, E, F lie on one parallel to AB",
               collinear(d, c, e) and collinear(d, c, f))
    outline(a, b, c, d)
    outline(a, b, e, f)

    because(prop_I_34, a, b, c, d)
    because(prop_I_34, a, b, e, f)
    because(prop_I_4, a, d, f, b, c, e)

    claim("AD = BC and AF = BE, the opposite sides", "I.34",
          eq_len(a, d, b, c) and eq_len(a, f, b, e))
    claim("DF = CE, adding or subtracting the common part", "C.N.2", eq_len(d, f, c, e))
    claim("so the triangles ADF and BCE are equal", "I.4", eq_area((a, d, f), (b, c, e)))
    claim("taking each from the trapezium, the parallelograms are equal", "C.N.3",
          eq_polygon_area([a, b, c, d], [a, b, e, f]))
    return Out()


def _parallelograms_equal_bases(rng):
    move = samples.frame(rng)
    base = samples.nonzero(rng, 2, 5)
    gap = samples.nonzero(rng, 1, 4)
    height = samples.nonzero(rng, 2, 5)
    lean_one, lean_two = samples.scalar(rng, -2, 2), samples.scalar(rng, -2, 2)
    return (
        move(Point(0, 0)),
        move(Point(base, 0)),
        move(Point(base + lean_one, height)),
        move(Point(lean_one, height)),
        move(Point(base + gap, 0)),
        move(Point(2 * base + gap, 0)),
        move(Point(2 * base + gap + lean_two, height)),
        move(Point(base + gap + lean_two, height)),
    )


@proposition(
    "I.36",
    THEOREM,
    sample=_parallelograms_equal_bases,
)
def prop_I_36(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point, g: Point, h: Point) -> Out:
    hypothesis("the bases AB and EF are equal", eq_len(a, b, e, f))
    hypothesis("the bases lie on one straight line", collinear(a, b, e) and collinear(a, b, f))
    hypothesis("the tops lie on one parallel", collinear(d, c, g) and collinear(d, c, h))
    outline(a, b, c, d)
    outline(e, f, g, h)
    # AB and HG are equal and parallel, so joining their ends gives a third
    # parallelogram by I.33; each of the two then equals it by I.35, on the
    # base they share with it.
    because(prop_I_33, a, b, g, h)
    because(prop_I_35, a, b, c, d, g, h)
    because(prop_I_35, h, g, f, e, b, a)

    claim("joining the ends of the equal and parallel bases gives a parallelogram", "I.33",
          eq_len(a, b, e, f))
    claim("both parallelograms equal that one, hence one another", "I.35",
          eq_polygon_area([a, b, c, d], [e, f, g, h]))
    return Out()


@proposition(
    "I.37",
    THEOREM,
    sample=samples.triangles_same_base,
)
def prop_I_37(a: Point, b: Point, c: Point, d: Point) -> Out:
    hypothesis("C and D lie on one parallel to AB",
               parallel(Line.through(a, b), Line.through(c, d)))
    outline(a, b, c)
    outline(a, b, d)
    line(c, d, "the parallel through the apexes")

    top_c, top_d = _fourth_vertex(b, a, c), _fourth_vertex(b, a, d)
    because(prop_I_35, a, b, c, top_c, d, top_d)
    because(prop_I_34, a, b, c, top_c)

    claim("completing the parallelograms on AB, they are equal", "I.35",
          eq_polygon_area(
              [a, b, c, _fourth_vertex(b, a, c)], [a, b, d, _fourth_vertex(b, a, d)]))
    claim("each triangle is half its parallelogram, so the triangles are equal", "I.34",
          eq_area((a, b, c), (a, b, d)))
    return Out()


@proposition(
    "I.38",
    THEOREM,
    sample=samples.triangles_equal_bases,
)
def prop_I_38(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("the bases AB and DE are equal", eq_len(a, b, d, e))
    hypothesis("the bases lie on one straight line", collinear(a, b, d) and collinear(a, b, e))
    # Euclid names the parallel by joining the apexes, which needs two of them,
    # and the commonest use of I.38 has one: I.42 compares ABE with AEC, and
    # every triangle standing on a cut base in Book VI stands on the same point.
    # The parallel through C is that line whether or not F is C, so I.31 draws
    # it and F is asked to lie on it. Naming it by the join instead cost five
    # citations, which were left recorded but unrun.
    through_apexes = _parallel_through(c, a, b)
    hypothesis("the apexes lie on one parallel to the bases", on_line(f, through_apexes))
    outline(a, b, c)
    outline(d, e, f)
    if c != f:
        line(c, f, "the parallel through the apexes")

    top_c, top_f = _fourth_vertex(b, a, c), _fourth_vertex(e, d, f)
    because(prop_I_36, a, b, c, top_c, d, e, f, top_f)
    because(prop_I_34, a, b, c, top_c)

    claim("the completed parallelograms on equal bases are equal", "I.36",
          eq_polygon_area(
              [a, b, c, _fourth_vertex(b, a, c)], [d, e, f, _fourth_vertex(e, d, f)]))
    claim("and each triangle is half of its parallelogram", "I.34",
          eq_area((a, b, c), (d, e, f)))
    return Out()


def _equal_triangles_same_base(rng):
    return samples.triangles_same_base(rng)


@proposition(
    "I.39",
    THEOREM,
    sample=_equal_triangles_same_base,
)
def prop_I_39(a: Point, b: Point, c: Point, d: Point) -> Out:
    base = Line.through(a, b)
    hypothesis("C and D are on the same side of AB", same_side(c, d, base))
    hypothesis("the triangles ABC and ABD are equal", eq_area((a, b, c), (a, b, d)))
    outline(a, b, c)
    outline(a, b, d)
    line(c, d)

    # The parallel Euclid supposes drawn through C is drawable; where it cuts
    # BD is the point his argument compares against, and I.37 speaks of it.
    alongside = prop_I_31(c, a, b).parallel
    cut = meet_one(alongside, Line.through(b, d))
    because(prop_I_37, a, b, c, cut)

    claim("were CD not parallel to AB, a parallel through C would cut BD and I.37 would "
          "make a part equal the whole", "I.37", parallel(Line.through(c, d), base))
    return Out()


def _equal_triangles_equal_bases(rng):
    return samples.triangles_equal_bases(rng)


@proposition(
    "I.40",
    THEOREM,
    sample=_equal_triangles_equal_bases,
)
def prop_I_40(a: Point, b: Point, c: Point, d: Point, e: Point, f: Point) -> Out:
    hypothesis("the bases are equal and in one straight line",
               eq_len(a, b, d, e) and collinear(a, b, d) and collinear(a, b, e))
    hypothesis("C and F are on the same side", same_side(c, f, Line.through(a, b)))
    hypothesis("the triangles are equal", eq_area((a, b, c), (d, e, f)))
    outline(a, b, c)
    outline(d, e, f)
    line(c, f)

    alongside = prop_I_31(c, a, b).parallel
    cut = meet_one(alongside, Line.through(e, f))
    because(prop_I_38, a, b, c, d, e, cut)

    claim("were CF not parallel to the bases, I.38 would make a part equal the whole", "I.38",
          parallel(Line.through(c, f), Line.through(a, b)))
    return Out()


def _parallelogram_and_triangle(rng):
    move = samples.frame(rng)
    base = samples.nonzero(rng, 3, 7)
    height = samples.nonzero(rng, 2, 5)
    lean = samples.scalar(rng, -3, 3)
    return (
        move(Point(0, 0)),
        move(Point(base, 0)),
        move(Point(base + lean, height)),
        move(Point(lean, height)),
        move(Point(samples.scalar(rng, -3, 6), height)),
    )


@proposition(
    "I.41",
    THEOREM,
    sample=_parallelogram_and_triangle,
)
def prop_I_41(a: Point, b: Point, c: Point, d: Point, e: Point) -> Out:
    hypothesis("ABCD is a parallelogram",
               parallel(Line.through(a, b), Line.through(d, c))
               and parallel(Line.through(a, d), Line.through(b, c)))
    hypothesis("E lies on the parallel DC", collinear(d, c, e))
    outline(a, b, c, d)
    outline(a, b, e)

    # I.37 compares two triangles on the base by joining their apexes, so it has
    # nothing to join when they are the same point -- which happens when the
    # parallelogram's far corner is where the triangle's apex already stands.
    if e != c:
        because(prop_I_37, a, b, e, c)
    because(prop_I_34, a, b, c, d)

    claim("the triangle ABE equals the triangle ABC", "I.37", eq_area((a, b, e), (a, b, c)))
    claim("the diameter halves the parallelogram, so it is double the triangle", "I.34",
          _area(a, b, c, d) == 2 * _area(a, b, e))
    return Out()


# ---------------------------------------------------------------------------
# I.42 - I.45  the application of areas
# ---------------------------------------------------------------------------


def _triangle_and_angle(rng):
    a, b, c = samples.triangle(rng)
    p, q, r = samples.angle_config(rng)
    return a, b, c, p, q, r


@proposition(
    "I.42",
    CONSTRUCTION,
    sample=_triangle_and_angle,
)
def prop_I_42(a: Point, b: Point, c: Point, p: Point, q: Point, r: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    hypothesis("PQR is a genuine angle", not collinear(p, q, r), guard=True)
    outline(p, q, r, close=False)  # the arms of the given angle

    middle = posit(prop_I_10(b, c).midpoint, "E")
    line(a, middle, "join AE")
    copied = prop_I_23(p, q, r, middle, c, beside=a)
    ray_point = posit(copied.ray_through, "S")

    through_a = _parallel_through(a, middle, c)
    f = posit(meet_one(through_a, line(middle, ray_point, "EF")), "F")
    through_c = _parallel_through(c, middle, f)
    g = posit(meet_one(through_c, through_a), "G")

    # FECG stands on the base EC with A on the parallel through F and G, which
    # is I.41's configuration. The other half of the argument is I.38 on the
    # triangles ABE and AEC: E bisects BC, so the bases are equal and lie on one
    # line, and both stand on A.
    because(prop_I_41, middle, c, g, f, a)
    because(prop_I_38, b, middle, a, middle, c, a)

    claim("the angle FEC equals the given angle", "I.23", eq_angle(f, middle, c, p, q, r))
    claim("FECG is a parallelogram",
          "I.31",
          parallel(Line.through(f, middle), Line.through(g, c))
          and parallel(Line.through(f, g), Line.through(middle, c)))
    claim("the parallelogram is double the triangle AEC", "I.41",
          _area(f, middle, c, g) == 2 * _area(a, middle, c))
    claim("and the triangle AEC is half of ABC, so the areas are equal", "I.38",
          _area(f, middle, c, g) == _area(a, b, c))
    return Out(parallelogram=(f, middle, c, g), angle_at=middle)


def _line_triangle_angle(rng):
    a, b = samples.segment(rng)
    c, d, e = samples.triangle(rng)
    p, q, r = samples.angle_config(rng)
    return a, b, c, d, e, p, q, r


@proposition(
    "I.44",
    CONSTRUCTION,
    sample=_line_triangle_angle,
    note="The application of areas -- the engine of Book II and, later, of the "
    "Greek solution of quadratic problems.",
)
def prop_I_44(
    a: Point,
    b: Point,
    c: Point,
    d: Point,
    e: Point,
    p: Point,
    q: Point,
    r: Point,
    away_from: "Point | None" = None,
) -> Out:
    hypothesis("A and B are distinct", a != b)
    hypothesis("CDE is a genuine triangle", not collinear(c, d, e), guard=True)
    hypothesis("PQR is a genuine angle", not collinear(p, q, r), guard=True)
    outline(p, q, r, close=False)  # the arms of the given angle

    # Carry a parallelogram equal to the triangle, in the given angle, over to B,
    # with its base along AB produced (I.3 for the lengths, I.23 for the angle).
    model = prop_I_42(c, d, e, p, q, r)
    corner_f, corner_e, corner_c, corner_g = model.parallelogram
    base_length = length(corner_e, corner_c)
    side_length = length(corner_e, corner_f)

    # AB is produced far enough past B for I.3 to cut the base off it: I.3 asks
    # for the greater line, and the base carried over may exceed AB itself.
    span = 2 * base_length / length(a, b) + 1
    beyond = posit(Point(b.x + span * (b.x - a.x), b.y + span * (b.y - a.y)), "B'")
    placed_e = posit(prop_I_3(b, beyond, corner_e, corner_c).cut, "E")
    turned = prop_I_23(corner_f, corner_e, corner_c, b, placed_e, apart_from=away_from)
    placed_g = posit(_along(b, turned.ray_through, side_length), "G")
    placed_f = posit(_fourth_vertex(b, placed_e, placed_g), "F")

    claim("BEFG equals the given triangle and has the given angle", ["I.3", "I.23", "I.42"],
          _area(b, placed_e, placed_f, placed_g) == _area(c, d, e)
          and eq_angle(placed_e, b, placed_g, p, q, r))

    # the gnomon: complete the figure about the diameter HB produced
    top = line(placed_f, placed_g, "FG produced")
    h = posit(meet_one(top, _parallel_through(a, b, placed_g)), "H")
    diameter = line(h, b, "the diameter HB")
    side = line(placed_f, placed_e, "FE produced")
    if parallel(diameter, side):
        raise GeometryError("HB and FE do not meet in this configuration")
    k = posit(meet_one(diameter, side), "K")
    through_k = _parallel_through(k, placed_e, a)
    l = posit(meet_one(through_k, Line.through(h, a)), "L")
    m = posit(meet_one(through_k, Line.through(placed_g, b)), "M")

    claim("HLKF is a parallelogram and HK its diameter", "I.31",
          parallel(Line.through(h, l), Line.through(placed_f, k))
          and parallel(Line.through(h, placed_f), Line.through(l, k)))
    # HLKF is the parallelogram, HK its diameter, and B the point on it: I.43's
    # own configuration. The angles at B are vertical, which is I.15's.
    because(prop_I_43, h, l, k, placed_f, b)
    because(prop_I_15, placed_g, m, placed_e, a)

    claim("the complements about the diameter are equal, so LABM equals BEFG", "I.43",
          _area(l, a, b, m) == _area(b, placed_e, placed_f, placed_g))
    claim("therefore the applied parallelogram equals the given triangle", "C.N.1",
          _area(l, a, b, m) == _area(c, d, e))
    claim("and the angle ABM equals the given angle, being vertical to GBE", "I.15",
          eq_angle(a, b, m, p, q, r))

    # What the enunciation is about: the parallelogram applied to AB, and the
    # triangle it is equal to. Three levels of helper construction stand behind
    # them, and stay in the figure, drawn back.
    outline_result(l, a, b, m)
    outline_result(c, d, e)
    return Out(parallelogram=(l, a, b, m))


def _parallelogram_with_diameter_point(rng):
    a, b, c, d = samples.parallelogram(rng)
    weight = Fraction(rng.randint(1, 3), 4)
    k = Point(a.x + weight * (c.x - a.x), a.y + weight * (c.y - a.y))
    return a, b, c, d, k


@proposition(
    "I.43",
    THEOREM,
    sample=_parallelogram_with_diameter_point,
)
def prop_I_43(a: Point, b: Point, c: Point, d: Point, k: Point) -> Out:
    hypothesis("ABCD is a parallelogram",
               parallel(Line.through(a, b), Line.through(d, c))
               and parallel(Line.through(a, d), Line.through(b, c)))
    hypothesis("K lies on the diameter AC, strictly inside", on_line(k, Line.through(a, c))
               and k != a and k != c)
    line(a, c, "the diameter AC")

    across = _parallel_through(k, a, b)
    along = _parallel_through(k, a, d)
    e = posit(meet_one(along, Line.through(a, b)), "E")
    f = posit(meet_one(along, Line.through(d, c)), "F")
    g = posit(meet_one(across, Line.through(b, c)), "G")
    h = posit(meet_one(across, Line.through(a, d)), "H")

    # The whole and each parallelogram about the diameter answer to I.34.
    because(prop_I_34, a, b, c, d)
    because(prop_I_34, a, e, k, h)
    because(prop_I_34, k, g, c, f)

    claim("the diameter bisects the whole parallelogram", "I.34",
          _area(a, b, c) == _area(a, c, d))
    claim("and it bisects each of the parallelograms about it", "I.34",
          _area(a, e, k, h) == 2 * _area(a, e, k) and _area(k, g, c, f) == 2 * _area(k, g, c))
    claim("so the complements EBGK and HKFD are equal", "C.N.3",
          _area(e, b, g, k) == _area(h, k, f, d))
    return Out(complements=((e, b, g, k), (h, k, f, d)))


def _figure_and_angle(rng):
    a, b, c, d = samples.quadrilateral(rng)
    p, q, r = samples.angle_config(rng)
    return a, b, c, d, p, q, r


@proposition(
    "I.45",
    CONSTRUCTION,
    sample=_figure_and_angle,
)
def prop_I_45(a: Point, b: Point, c: Point, d: Point, p: Point, q: Point, r: Point) -> Out:
    """The quadrilateral is cut into two triangles; the first gets a
    parallelogram by I.42, the second is applied to its side by I.44."""
    hypothesis("PQR is a genuine angle", not collinear(p, q, r), guard=True)
    outline(p, q, r, close=False)  # the arms of the given angle
    hypothesis("ABCD is a genuine quadrilateral",
               not collinear(a, b, c) and not collinear(a, c, d), guard=True)
    diameter = line(a, c, "the diameter AC dividing the figure")

    first = prop_I_42(a, b, c, p, q, r)
    corner_f, corner_e, corner_c, corner_g = first.parallelogram
    second = prop_I_44(corner_f, corner_g, a, c, d, p, q, r, away_from=corner_e)
    l, applied_a, applied_b, m = second.parallelogram

    total = _area(corner_f, corner_e, corner_c, corner_g) + _area(l, applied_a, applied_b, m)
    claim("the first parallelogram equals the triangle ABC", "I.42",
          _area(corner_f, corner_e, corner_c, corner_g) == _area(a, b, c))
    claim("the second, applied to its side, equals the triangle ACD", "I.44",
          _area(l, applied_a, applied_b, m) == _area(a, c, d))
    claim("together they equal the whole figure", "C.N.2",
          total == _area(a, b, c) + _area(a, c, d))
    claim("and each is in the given angle", "I.44", eq_angle(applied_a, applied_b, m, p, q, r))

    # The given figure, the diameter that halves it, and the two parallelograms
    # that together equal it -- everything the enunciation names, and nothing
    # of the three levels of helper construction underneath.
    outline_result(a, b, c, d)
    result(diameter)
    outline_result(corner_f, corner_e, corner_c, corner_g)
    outline_result(l, applied_a, applied_b, m)
    return Out(pieces=((corner_f, corner_e, corner_c, corner_g), (l, applied_a, applied_b, m)))


# ---------------------------------------------------------------------------
# I.46 - I.48  squares and Pythagoras
# ---------------------------------------------------------------------------


@proposition(
    "I.46",
    CONSTRUCTION,
    sample=samples.segment,
)
def prop_I_46(a: Point, b: Point) -> Out:
    hypothesis("A and B are distinct", a != b)
    beyond = posit(Point(a.x + (a.x - b.x), a.y + (a.y - b.y)), "A'")
    upright = prop_I_11(beyond, b, a).perpendicular
    # AD is cut off from the upright equal to AB, which is I.3's business. The
    # lesser line is named BA: I.3 places it at A through I.2, and I.2 joins the
    # point to an end of the line.
    span = circle_with_radius2(a, len2(a, b) * 4, "circle centre A, twice AB")
    far = meet(upright, span)[1]
    d = posit(prop_I_3(a, far, b, a).cut, "D")
    e = posit(_fourth_vertex(a, b, d), "E")
    line(b, e)
    line(d, e)
    because(prop_I_34, a, b, e, d)

    claim("AD = AB by construction", "I.3", eq_len(a, d, a, b))
    claim("ADEB is a parallelogram, so the opposite sides are equal", "I.34",
          eq_len(a, d, b, e) and eq_len(a, b, d, e))
    claim("the angle at A is right", "I.11", right_angle(d, a, b))
    claim("and therefore all four angles are right", "I.34",
          right_angle(a, b, e) and right_angle(b, e, d) and right_angle(e, d, a))
    claim("the figure is equilateral and right-angled: a square", "Def.22",
          eq_len(a, b, b, e) and eq_len(b, e, e, d) and eq_len(e, d, d, a))
    return Out(square=(a, b, e, d))


@proposition(
    "I.47",
    THEOREM,
    sample=samples.right_triangle,
    note="Pythagoras. Euclid proves it by cutting the large square into two rectangles, "
    "each equal to one of the small squares -- the windmill figure.",
)
def prop_I_47(a: Point, b: Point, c: Point) -> Out:
    """The right angle is at B."""
    hypothesis("the angle ABC is right", right_angle(a, b, c))
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)

    on_hypotenuse = _square_outward(a, c, b)
    on_first = _square_outward(a, b, c)
    on_second = _square_outward(c, b, a)
    _, _, far_c, far_a = on_hypotenuse

    claim("the squares are described on the three sides, each falling away from "
          "the triangle", "I.46",
          _area(*on_hypotenuse) == len2(a, c)
          and _area(*on_first) == len2(a, b)
          and _area(*on_second) == len2(c, b))

    # Euclid draws the parallel through the right angle to a side of the square
    # on the hypotenuse.  It is the perpendicular to AC, and it cuts that square
    # into the two rectangles the proof is about.
    divider = _parallel_through(b, a, far_a)
    foot = posit(meet_one(divider, Line.through(a, c)), "L")
    across = posit(meet_one(divider, Line.through(far_a, far_c)), "M")
    claim("the parallel through B meets AC within it, and the far side beyond",
          "I.31", between(a, foot, c) and between(far_a, across, far_c))

    halves = []
    for near, far, corner, square in ((a, c, far_a, on_first),
                                      (c, a, far_c, on_second)):
        outer, inner = square[3], square[2]
        # The two triangles of the windmill: one on a side of the square on the
        # hypotenuse, one on a side of the smaller square.
        because(prop_I_4, near, b, corner, near, outer, far)
        # Each is half of its own figure, being on the same base and between the
        # same parallels.
        because(prop_I_41, near, corner, across, foot, b)
        because(prop_I_41, outer, near, b, inner, far)
        halves.append(_area(near, corner, across, foot))

    claim("each rectangle is double a triangle that is half one of the smaller "
          "squares, so the two are equal", ["I.4", "I.41"],
          halves[0] == _area(*on_first) and halves[1] == _area(*on_second))
    claim("therefore the square on AC equals the squares on AB and BC together", "C.N.2",
          _area(*on_hypotenuse) == halves[0] + halves[1])
    return Out(squares=(on_hypotenuse, on_first, on_second),
               rectangles=(halves[0], halves[1]), foot=foot)


@proposition(
    "I.48",
    THEOREM,
    sample=samples.right_triangle,
)
def prop_I_48(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    hypothesis("the square on AC equals those on AB and BC",
               len2(a, c) == len2(a, b) + len2(b, c))
    outline(a, b, c)

    # Erect BD at right angles to BC and equal to BA, and join DC. I.47 gives
    # DC the square that AC has, and I.8 then matches the two triangles.
    back_b = Point(2 * b.x - c.x, 2 * b.y - c.y)
    upright = prop_I_11(back_b, c, b).perpendicular
    reach = circle_with_radius2(b, len2(b, a), "circle centre B with radius BA")
    d = posit(meet(upright, reach)[1], "D")
    line(d, c, "join DC")
    because(prop_I_47, d, b, c)
    because(prop_I_8, a, b, c, d, b, c)

    claim("erecting a perpendicular at B equal to BA gives, by I.47, a triangle with the "
          "same three sides; so by I.8 the angle ABC is right", ["I.11", "I.47", "I.8"],
          right_angle(a, b, c))
    return Out()
