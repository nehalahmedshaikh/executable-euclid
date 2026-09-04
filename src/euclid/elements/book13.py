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

from ..kernel.field import sign, sqrt
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
from ..solid.construct import line3, posit3, sphere_through
from ..solid.objects import Point3
from ..solid.predicates import len2 as space_len2, on_sphere
from . import samples
from . import samples3
from .book01_foundations import prop_I_4, prop_I_5, prop_I_10
from .book01_parallels import prop_I_47
from .book02 import prop_II_6, prop_II_7
from .book03 import prop_III_30
from .book10 import prop_X_21, prop_X_73
from .book04 import prop_IV_11, prop_IV_15
from .book06 import prop_VI_30
from .book10 import (
    classify,
    commensurable,
    is_rational_in_square,
    is_rational_line,
    prop_X_73,
)
from .registry import (
    CONSTRUCTION,
    THEOREM,
    Out,
    because,
    claim,
    get,
    hypothesis,
    proposition,
)


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

    because(prop_I_10, a, b)
    because(prop_II_6, half, a, b)

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

    because(prop_II_6, a, half, section)

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

    because(prop_II_7, a, section, b)

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

    # X.73 makes the apotome out of two rational lines commensurable in square
    # only; those are the terms of the greater segment, not the segment itself.
    because(prop_X_73, length(a, b) * sqrt(5) / 2, length(a, b) / 2)
    # Which species an apotome belongs to is settled against the assigned
    # rational line, not against the figure it came from, so the segments of a
    # line of arbitrary length are apotomes of a species that moves with that
    # length: on the unit line the greater is the fifth and the lesser the
    # first, and on others neither. There is no one species proposition the
    # step answers to, and X.85 and X.89 are named here for the pair of species
    # this cut produces rather than for a construction to be carried out.

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

    # The equal sides here are the pentagon's own, so the isosceles triangles
    # stand on its vertices: ABC has BA = BC, and I.4 compares it with BCD,
    # which has the equal included angle. Both appeals were written on AB = AC,
    # a length no pentagon has, and neither ever ran.
    because(prop_I_5, b, a, c)
    because(prop_I_4, b, a, c, c, b, d)

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
    because(prop_VI_30, corners[0], corners[2])

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

    because(prop_III_30, o, corners[0], corners[1])
    because(prop_IV_15, o, a)
    because(prop_VI_30, o, end)

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
    because(prop_III_30, o, corners[0], corners[1])
    because(prop_IV_15, o, a)
    # The perpendicular from the centre to the pentagon side makes the right
    # angle I.47 speaks of.
    because(prop_I_47, o, midpoint_of(corners[0], corners[1]), corners[0])

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

    because(prop_X_21, Fraction(1), sqrt(5))
    # The minor is a difference of two lines incommensurable in square whose
    # squares add to a rational and whose rectangle is medial. For this side
    # those are sqrt(R^2(5 + 2 sqrt 5))/2 and sqrt(R^2(5 - 2 sqrt 5))/2, and
    # X.76 is the proposition that names their difference.
    _r2 = len2(o, a)
    because(get("X.76").wrapped,
            sqrt(_r2 * (5 + 2 * sqrt(5))) / 2,
            sqrt(_r2 * (5 - 2 * sqrt(5))) / 2)
    # X.73 makes an apotome out of two *rational* lines commensurable in square
    # only; the terms of the minor are not rational, so the appeal has no pair
    # of lines here to be about.

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

    because(prop_I_47, o, midpoint_of(triangle[0], triangle[1]), triangle[0])

    claim("the alternate vertices of the hexagon form an equilateral triangle",
          "IV.15",
          eq_len(triangle[0], triangle[1], triangle[1], triangle[2])
          and eq_len(triangle[1], triangle[2], triangle[2], triangle[0]))
    claim("the square on its side is triple of the square on the radius",
          "I.47", len2(triangle[0], triangle[1]) == 3 * len2(o, a))
    return Out(triangle=triangle)


# ---------------------------------------------------------------------------
# XIII.13 - XIII.18: the five regular solids
#
# Each is set out by its vertices, and what makes it the figure Euclid describes
# is checked rather than declared: every vertex on the sphere, every edge equal
# to every other, and the same number of edges meeting at each corner.  The
# edges are not listed by hand either -- they are the joins at the least
# distance, which is what an edge of a regular solid is.
#
# Book X does the last two.  Against the sphere's diameter, taken as the
# rational line, the side of the icosahedron and the side of the dodecahedron
# are irrational, and `classify` names which irrational in the vocabulary that
# X.36-41 and X.73-78 set up.
# ---------------------------------------------------------------------------

def _phi():
    """The greater segment of a line of length one cut in extreme and mean ratio.

    Computed afresh at every call and never kept in a module constant: a
    constructible number belongs to the field tower that built it, each
    proposition runs in its own, and a value carried across from another cannot
    be combined with the figure in hand.
    """
    return (1 + sqrt(Fraction(5))) / 2


def _cyclic(x, y, z) -> tuple:
    """A triple and its two turnings, which is how the last two solids are set out."""
    return ((x, y, z), (y, z, x), (z, x, y))


def _tetrahedron() -> tuple:
    return ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))


def _octahedron() -> tuple:
    return tuple((0,) * axis + (way,) + (0,) * (2 - axis)
                 for axis in range(3) for way in (1, -1))


def _cube() -> tuple:
    return tuple((x, y, z) for x in (1, -1) for y in (1, -1) for z in (1, -1))


def _icosahedron() -> tuple:
    phi = _phi()
    return tuple(turned for y in (1, -1) for z in (phi, -phi)
                 for turned in _cyclic(Fraction(0), Fraction(y), z))


def _dodecahedron() -> tuple:
    phi = _phi()
    corners = [(Fraction(x), Fraction(y), Fraction(z))
               for x in (1, -1) for y in (1, -1) for z in (1, -1)]
    for y in (1, -1):
        for z in (phi, -phi):
            corners.extend(_cyclic(Fraction(0), y / phi, z))
    return tuple(corners)


def _reach2(model: tuple):
    """The square on the radius of the sphere the model figure is set out in."""
    first = model[0]
    return first[0] * first[0] + first[1] * first[1] + first[2] * first[2]


def _edges_of(corners: tuple) -> tuple:
    """The joins at the least distance: the edges of a regular figure.

    Two vertices of a regular solid are joined exactly when nothing else is
    nearer, and comparing squared distances decides that exactly -- so no list
    of edges is written down and none can be written down wrong.
    """
    pairs = [(i, j) for i in range(len(corners)) for j in range(i + 1, len(corners))]
    least = None
    for i, j in pairs:
        span = space_len2(corners[i], corners[j])
        if least is None or sign(span - least) < 0:
            least = span
    return tuple((i, j) for i, j in pairs
                 if space_len2(corners[i], corners[j]) == least)


def _figure(o: Point3, a: Point3, model: tuple, label: str) -> tuple:
    """Set a regular figure out in the sphere about *o* through *a*, and draw it.

    One ratio, applied to every vertex, so the shape is unchanged and every
    vertex lands on the surface.  That ratio is a single square root of a
    quotient already in hand, which is the whole cost of comprehending a figure
    in a sphere.
    """
    scale = sqrt(space_len2(o, a) / _reach2(model))
    corners = tuple(posit3(Point3(o.x + scale * corner[0],
                                  o.y + scale * corner[1],
                                  o.z + scale * corner[2]))
                    for corner in model)
    edges = _edges_of(corners)
    for start, end in edges:
        line3(corners[start], corners[end], label)
    return corners, edges


def _at_each_corner(corners: tuple, edges: tuple) -> set:
    return {sum(1 for start, end in edges if index in (start, end))
            for index in range(len(corners))}


def _edge2(corners: tuple, edges: tuple):
    return space_len2(corners[edges[0][0]], corners[edges[0][1]])


@proposition("XIII.13", CONSTRUCTION, sample=samples3.sphere_about)
def prop_XIII_13(o: Point3, a: Point3) -> Out:
    """Construct a pyramid in a given sphere, and prove the square on the
    diameter is one and a half times the square on the side."""
    hypothesis("the sphere has a positive radius", o != a)
    globe = sphere_through(o, a, "the given sphere")
    line3(o, a, "the radius")
    corners, edges = _figure(o, a, _tetrahedron(), "an edge of the pyramid")

    side2, across = _edge2(corners, edges), 4 * space_len2(o, a)
    claim("every vertex of the pyramid is on the sphere, so it is comprehended "
          "in it", "XI.Def.14", all(on_sphere(corner, globe) for corner in corners))
    claim("it is contained by four equal and equilateral triangles, three edges "
          "meeting at each corner", "XI.Def.25",
          len(corners) == 4 and len(edges) == 6
          and _at_each_corner(corners, edges) == {3}
          and all(space_len2(corners[i], corners[j]) == side2 for i, j in edges))
    claim("and the square on the diameter of the sphere is one and a half times "
          "the square on the side of the pyramid", "XIII.13",
          2 * across == 3 * side2)
    return Out(pyramid=corners, side2=side2, diameter2=across)


@proposition("XIII.14", CONSTRUCTION, sample=samples3.sphere_about)
def prop_XIII_14(o: Point3, a: Point3) -> Out:
    """Construct an octahedron in a sphere, and prove the square on the diameter
    is double the square on the side."""
    hypothesis("the sphere has a positive radius", o != a)
    globe = sphere_through(o, a, "the given sphere")
    line3(o, a, "the radius")
    corners, edges = _figure(o, a, _octahedron(), "an edge of the octahedron")

    because(prop_XIII_13, o, a)

    side2, across = _edge2(corners, edges), 4 * space_len2(o, a)
    claim("every vertex of the octahedron is on the sphere", "XI.Def.14",
          all(on_sphere(corner, globe) for corner in corners))
    claim("it is contained by eight equal and equilateral triangles, four edges "
          "meeting at each corner", "XI.Def.26",
          len(corners) == 6 and len(edges) == 12
          and _at_each_corner(corners, edges) == {4}
          and all(space_len2(corners[i], corners[j]) == side2 for i, j in edges))
    claim("and the square on the diameter of the sphere is double the square on "
          "the side of the octahedron", "XIII.14", across == 2 * side2)
    return Out(octahedron=corners, side2=side2, diameter2=across)


@proposition("XIII.15", CONSTRUCTION, sample=samples3.sphere_about)
def prop_XIII_15(o: Point3, a: Point3) -> Out:
    """Construct a cube in a sphere, and prove the square on the diameter is
    triple the square on the side."""
    hypothesis("the sphere has a positive radius", o != a)
    globe = sphere_through(o, a, "the given sphere")
    line3(o, a, "the radius")
    corners, edges = _figure(o, a, _cube(), "an edge of the cube")

    because(prop_XIII_14, o, a)

    side2, across = _edge2(corners, edges), 4 * space_len2(o, a)
    claim("every vertex of the cube is on the sphere", "XI.Def.14",
          all(on_sphere(corner, globe) for corner in corners))
    claim("it is contained by six equal squares, three edges meeting at each "
          "corner", "XI.Def.25",
          len(corners) == 8 and len(edges) == 12
          and _at_each_corner(corners, edges) == {3}
          and all(space_len2(corners[i], corners[j]) == side2 for i, j in edges))
    claim("and the square on the diameter of the sphere is triple the square on "
          "the side of the cube", "XIII.15", across == 3 * side2)
    return Out(cube=corners, side2=side2, diameter2=across)


@proposition("XIII.16", CONSTRUCTION, sample=samples3.sphere_about)
def prop_XIII_16(o: Point3, a: Point3) -> Out:
    """Construct an icosahedron in a sphere, and prove its side is the
    irrational straight line called minor."""
    hypothesis("the sphere has a positive radius", o != a)
    hypothesis("the diameter of the sphere is rational, being the line every "
               "other is named against",
               is_rational_line(sqrt(4 * space_len2(o, a))))
    globe = sphere_through(o, a, "the given sphere")
    line3(o, a, "the radius")
    corners, edges = _figure(o, a, _icosahedron(), "an edge of the icosahedron")

    because(prop_XIII_15, o, a)

    side2, across = _edge2(corners, edges), 4 * space_len2(o, a)
    side = sqrt(side2 / across)
    named = classify(side)
    # X.76 makes the minor out of two lines incommensurable in square whose
    # squares add to a rational area and whose rectangle is medial. The two are
    # the terms the side itself divides into, so the appeal is carried out on
    # the figure's own magnitudes and not on a pair chosen to suit it.
    because(get("X.76").wrapped, named.terms[0], -named.terms[1])

    claim("every vertex of the icosahedron is on the sphere", "XI.Def.14",
          all(on_sphere(corner, globe) for corner in corners))
    claim("it is contained by twenty equal and equilateral triangles, five "
          "edges meeting at each corner", "XI.Def.27",
          len(corners) == 12 and len(edges) == 30
          and _at_each_corner(corners, edges) == {5}
          and all(space_len2(corners[i], corners[j]) == side2 for i, j in edges))
    claim("and the side of the icosahedron is the irrational straight line "
          "called minor", "X.76", named.name == "minor")
    claim("it is of the fourth degree over the rationals, so neither a rational "
          "line nor a medial one", "X.73", named.algebraic_degree == 4)
    return Out(icosahedron=corners, side2=side2, side=side, name=named.name)


@proposition("XIII.17", CONSTRUCTION, sample=samples3.sphere_about)
def prop_XIII_17(o: Point3, a: Point3) -> Out:
    """Construct a dodecahedron in a sphere, and prove its side is the
    irrational straight line called apotome."""
    hypothesis("the sphere has a positive radius", o != a)
    hypothesis("the diameter of the sphere is rational, being the line every "
               "other is named against",
               is_rational_line(sqrt(4 * space_len2(o, a))))
    globe = sphere_through(o, a, "the given sphere")
    line3(o, a, "the radius")
    corners, edges = _figure(o, a, _dodecahedron(), "an edge of the dodecahedron")

    because(prop_XIII_16, o, a)

    side2, across = _edge2(corners, edges), 4 * space_len2(o, a)
    side = sqrt(side2 / across)
    named = classify(side)
    because(prop_X_73, named.terms[0], -named.terms[1])

    claim("every vertex of the dodecahedron is on the sphere", "XI.Def.14",
          all(on_sphere(corner, globe) for corner in corners))
    claim("it is contained by twelve equal and equilateral pentagons, three "
          "edges meeting at each corner", "XI.Def.28",
          len(corners) == 20 and len(edges) == 30
          and _at_each_corner(corners, edges) == {3}
          and all(space_len2(corners[i], corners[j]) == side2 for i, j in edges))
    claim("and the side of the dodecahedron is the irrational straight line "
          "called apotome", "X.73", named.family == "apotome")
    claim("its two terms are rational lines commensurable in square only",
          "X.73",
          len(named.terms) == 2
          and all(is_rational_in_square(term) for term in
                  (named.terms[0], -named.terms[1]))
          and not commensurable(named.terms[0], -named.terms[1]))
    return Out(dodecahedron=corners, side2=side2, side=side, name=named.name)


def _regular_solids() -> tuple:
    """The pairs a regular solid can be made of, and there are five.

    A face has three sides at least and three faces meet at a solid angle at
    least; by XI.21 the plane angles at that angle fall short of four right
    angles, and the angle of a regular figure on ``p`` sides is
    ``(p - 2) / p`` of two right angles, so ``q (p - 2) / p < 2``.  Written
    without the fraction that is ``(p - 2)(q - 2) < 4``, and it has five answers.
    """
    return tuple((p, q) for p in range(3, 12) for q in range(3, 12)
                 if (p - 2) * (q - 2) < 4)


@proposition("XIII.18", THEOREM, sample=samples3.sphere_about)
def prop_XIII_18(o: Point3, a: Point3) -> Out:
    """Set out the sides of the five figures and compare them with one another."""
    hypothesis("the sphere has a positive radius", o != a)
    hypothesis("the diameter of the sphere is rational",
               is_rational_line(sqrt(4 * space_len2(o, a))))
    line3(o, a, "the radius of the sphere all five are comprehended in")

    sides = (because(prop_XIII_13, o, a).side2,
             because(prop_XIII_14, o, a).side2,
             because(prop_XIII_15, o, a).side2,
             because(prop_XIII_16, o, a).side2,
             because(prop_XIII_17, o, a).side2)
    across = 4 * space_len2(o, a)

    claim("the side of the pyramid is greater than the side of the octahedron, "
          "and that than the side of the cube", "XIII.15",
          sign(sides[0] - sides[1]) > 0 and sign(sides[1] - sides[2]) > 0)
    claim("the side of the cube is greater than the side of the icosahedron, "
          "and that than the side of the dodecahedron", "XIII.17",
          sign(sides[2] - sides[3]) > 0 and sign(sides[3] - sides[4]) > 0)
    claim("the first three have to the diameter a ratio a number can name, and "
          "the last two have not", "X.73",
          all(isinstance(span / across, Fraction) for span in sides[:3])
          and not any(isinstance(span / across, Fraction) for span in sides[3:]))
    claim("and there is no sixth figure", "XI.21",
          len(_regular_solids()) == 5
          and set(_regular_solids()) == {(3, 3), (3, 4), (3, 5), (4, 3), (5, 3)})
    return Out(sides=sides, diameter2=across, figures=_regular_solids())
