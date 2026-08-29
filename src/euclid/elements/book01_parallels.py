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
)
from . import samples
from .book01_foundations import prop_I_1, prop_I_3, prop_I_10, prop_I_11, prop_I_22, prop_I_23
from .registry import CONSTRUCTION, THEOREM, Out, claim, hypothesis, proposition

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

    claim("the angle EAD equals the angle ADC, and they are alternate", "I.23",
          eq_angle(e, a, b, a, b, c))
    claim("therefore EF is parallel to BC", "I.27", parallel(drawn, given))
    return Out(parallel=drawn, through=e)


def _parallel_through(point: Point, first: Point, second: Point) -> Line:
    """The line through ``point`` parallel to the line ``first``-``second``."""
    return prop_I_31(point, first, second).parallel


# ---------------------------------------------------------------------------
# I.32 - I.34  angle sums and parallelograms
# ---------------------------------------------------------------------------


@proposition(
    "I.32",
    THEOREM,
    sample=samples.triangle,
)
def prop_I_32(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
    d = posit(Point(c.x + (c.x - b.x), c.y + (c.y - b.y)), "D")
    line(b, d, "BC produced to D")
    _parallel_through(c, a, b)

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
    hypothesis("the apexes lie on one parallel to the bases",
               parallel(Line.through(a, b), Line.through(c, f)))
    outline(a, b, c)
    outline(d, e, f)
    line(c, f, "the parallel through the apexes")
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
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
    hypothesis("PQR is a genuine angle", not collinear(p, q, r))
    outline(p, q, r, close=False)  # the arms of the given angle

    middle = posit(prop_I_10(b, c).midpoint, "E")
    line(a, middle, "join AE")
    copied = prop_I_23(p, q, r, middle, c, beside=a)
    ray_point = posit(copied.ray_through, "S")

    through_a = _parallel_through(a, middle, c)
    f = posit(meet_one(through_a, line(middle, ray_point, "EF")), "F")
    through_c = _parallel_through(c, middle, f)
    g = posit(meet_one(through_c, through_a), "G")

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
    hypothesis("CDE is a genuine triangle", not collinear(c, d, e))
    hypothesis("PQR is a genuine angle", not collinear(p, q, r))
    outline(p, q, r, close=False)  # the arms of the given angle

    # Carry a parallelogram equal to the triangle, in the given angle, over to B,
    # with its base along AB produced (I.3 for the lengths, I.23 for the angle).
    model = prop_I_42(c, d, e, p, q, r)
    corner_f, corner_e, corner_c, corner_g = model.parallelogram
    base_length = length(corner_e, corner_c)
    side_length = length(corner_e, corner_f)

    beyond = posit(Point(b.x + (b.x - a.x), b.y + (b.y - a.y)), "B'")
    placed_e = posit(_along(b, beyond, base_length), "E")
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
    hypothesis("PQR is a genuine angle", not collinear(p, q, r))
    outline(p, q, r, close=False)  # the arms of the given angle
    hypothesis("ABCD is a genuine quadrilateral",
               not collinear(a, b, c) and not collinear(a, c, d))
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
    reach = circle_with_radius2(a, len2(a, b), "circle centre A with radius AB")
    d = posit(meet(upright, reach)[1], "D")
    e = posit(_fourth_vertex(a, b, d), "E")
    line(b, e)
    line(d, e)

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
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))

    on_hypotenuse = prop_I_46(a, c).square
    on_first = prop_I_46(b, a).square
    on_second = prop_I_46(c, b).square

    claim("the squares are described on the three sides", "I.46",
          _area(*on_hypotenuse) == len2(a, c)
          and _area(*on_first) == len2(b, a)
          and _area(*on_second) == len2(c, b))
    claim("the perpendicular from B divides the square on AC into two rectangles, "
          "each double a triangle equal to half one of the smaller squares",
          ["I.4", "I.41", "I.31"],
          len2(a, c) == len2(a, b) + len2(b, c))
    claim("therefore the square on AC equals the squares on AB and BC together", "C.N.2",
          _area(*on_hypotenuse) == _area(*on_first) + _area(*on_second))
    return Out(squares=(on_hypotenuse, on_first, on_second))


@proposition(
    "I.48",
    THEOREM,
    sample=samples.right_triangle,
)
def prop_I_48(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c))
    hypothesis("the square on AC equals those on AB and BC",
               len2(a, c) == len2(a, b) + len2(b, c))
    outline(a, b, c)
    claim("erecting a perpendicular at B equal to BA gives, by I.47, a triangle with the "
          "same three sides; so by I.8 the angle ABC is right", ["I.11", "I.47", "I.8"],
          right_angle(a, b, c))
    return Out()
