"""Book XI: lines and planes in space.

The book where Euclid has no postulates.  Postulates 1 to 5 speak of the plane,
and Book XI opens with definitions and then argues from them, so every
construction here is recorded as unlicensed and the assumption ledger counts
what that costs.  See :mod:`euclid.solid.construct`.

XI.1 and XI.2 are the two Heath himself calls invalid, and they are encoded as
what they are: XI.1 has no figure at all, because the configuration it denies
cannot be built, and what is checked is the denial.  Where Euclid argues from a
picture, the picture is the thing this project cannot supply, and saying so is
better than supplying a different argument under his name.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import sign, sqrt
from ..solid.angles import angle_at3, dihedral, length3
from ..solid.construct import (
    line3,
    meet_line_plane,
    meet_planes,
    plane_through,
    posit3,
)
from ..solid.objects import Line3, Plane, Point3, midpoint_of, vector_between
from ..solid.solids import (
    Solid,
    content,
    edge_lengths,
    frame_on,
    height_over,
    parallelepiped,
    parallelogram_area,
    prism,
    unit,
)
from ..solid.predicates import (
    collinear3,
    coplanar,
    cross3,
    dot3,
    eq_len3,
    len2,
    on_line3,
    on_plane,
    parallel_planes,
    same_side_of_plane,
    volume6,
)
from . import samples3
from .registry import (
    CONSTRUCTION,
    THEOREM,
    Out,
    because,
    claim,
    hypothesis,
    proposition,
)

__all__: list = []


def _parallel3(first: Line3, second: Line3) -> bool:
    """Two lines in space with directions one way, which is Def. XI.8 read
    exactly: parallel lines are in one plane and do not meet."""
    return all(component == 0
               for component in cross3(first.direction(), second.direction()))


def _perpendicular_to_plane(line: Line3, plane: Plane) -> bool:
    """Def. XI.3: a line at right angles to every line in the plane it meets.

    Said exactly by the direction being along the normal, which is the same
    condition and is decidable without drawing every line of the plane.
    """
    return all(component == 0
               for component in cross3(line.direction(), plane.normal()))


@proposition(
    "XI.1",
    THEOREM,
    sample=samples3.cutting_lines,
    note="Heath calls the proof invalid: Euclid argues from a picture, and what "
    "he needs is a definition of 'plane' he never gives.",
)
def prop_XI_1(o: Point3, a: Point3, b: Point3) -> Out:
    """No part of a straight line is in one plane and the rest above it."""
    hypothesis("the three points are not in a straight line", not collinear3(o, a, b))
    surface = plane_through(o, a, b, "the plane of reference")

    # The proposition denies a configuration, so there is no figure of it to
    # draw: what is checked is that the denial holds. Every point of the line
    # OA lies in the plane, and that is what "no part of it is more elevated"
    # says. Euclid argues instead that the part outside would make two straight
    # lines with common ends, which is where Heath's objection falls.
    stretch = line3(o, a, "the straight line OA")
    along = [stretch.at(Fraction(k, 4)) for k in range(-8, 9)]
    claim("every point of the line lies in the plane of reference, so no part "
          "of it is elevated above", "XI.Def.7",
          all(on_plane(point, surface) for point in along))
    claim("and the line is not merely touching it at the two named points",
          "XI.Def.7", on_plane(stretch.at(Fraction(1, 3)), surface))
    return Out(plane=surface, line=stretch)


@proposition(
    "XI.2",
    THEOREM,
    sample=samples3.cutting_lines,
    note="Also unsound in Euclid: the proof assumes the very thing about planes "
    "that XI.1 was meant to establish.",
)
def prop_XI_2(o: Point3, a: Point3, b: Point3) -> Out:
    """Two straight lines that cut one another are in one plane."""
    # Euclid's own condition -- "if two straight lines cut one another" -- and
    # not a guard of ours: two lines through O are one line exactly when the
    # three points are in a straight line.
    hypothesis("the two straight lines cut one another at O",
               not collinear3(o, a, b))
    surface = plane_through(o, a, b, "their plane")
    line3(o, a)
    line3(o, b)
    line3(a, b, "the triangle is closed")

    claim("the two lines lie in one plane", "XI.Def.7",
          on_plane(o, surface) and on_plane(a, surface) and on_plane(b, surface))
    claim("and so does the whole triangle they make", "XI.2",
          all(on_plane(Point3(a.x + (b.x - a.x) * Fraction(k, 4),
                              a.y + (b.y - a.y) * Fraction(k, 4),
                              a.z + (b.z - a.z) * Fraction(k, 4)), surface)
              for k in range(5)))
    claim("the plane is the only one holding all three, being determined by them",
          "XI.Def.7", plane_through(o, a, b) == surface)
    return Out(plane=surface)


@proposition(
    "XI.3",
    THEOREM,
    sample=samples3.four_in_space,
    note="The one Euclid proves rather than assumes, which is why the kernel "
    "records a call to it as a step and not as a primitive.",
)
def prop_XI_3(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """If two planes cut one another, their common section is a straight line."""
    hypothesis("the four points are not in one plane", not coplanar(a, b, c, d))
    first = plane_through(a, b, c, "the first plane")
    second = plane_through(a, b, d, "the second")
    hypothesis("the two planes are not one plane", first != second)

    section = meet_planes(first, second)
    claim("the common section is a straight line", "XI.3",
          isinstance(section, Line3))
    claim("and every point of it lies in both planes", "XI.3",
          all(on_plane(section.at(Fraction(k, 3)), first)
              and on_plane(section.at(Fraction(k, 3)), second)
              for k in range(-6, 7)))
    claim("the two points the planes share lie on it", "XI.3",
          section.holds(a) and section.holds(b))
    return Out(section=section)


@proposition(
    "XI.4",
    THEOREM,
    sample=samples3.right_angled_at_origin,
)
def prop_XI_4(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """A line at right angles to two lines that cut it is at right angles to
    their plane."""
    hypothesis("OA and OB cut one another at O", not collinear3(o, a, b))
    hypothesis("OC is at right angles to both",
               dot3(vector_between(o, c), vector_between(o, a)) == 0
               and dot3(vector_between(o, c), vector_between(o, b)) == 0)
    surface = plane_through(o, a, b, "the plane of OA and OB")
    upright = line3(o, c, "the line set up at right angles")
    line3(o, a)
    line3(o, b)

    # "At right angles to the plane" is Definition XI.3: at right angles to
    # every straight line of the plane that meets it. Checking a spread of them
    # is checking the definition rather than a convenient consequence.
    through = [Point3(o.x + (a.x - o.x) * Fraction(k, 3) + (b.x - o.x) * Fraction(m, 3),
                      o.y + (a.y - o.y) * Fraction(k, 3) + (b.y - o.y) * Fraction(m, 3),
                      o.z + (a.z - o.z) * Fraction(k, 3) + (b.z - o.z) * Fraction(m, 3))
               for k in range(-3, 4) for m in range(-3, 4)]
    claim("OC is at right angles to every straight line of the plane meeting it",
          "XI.Def.3",
          all(dot3(vector_between(o, c), vector_between(o, point)) == 0
              for point in through if point != o))
    claim("so OC is at right angles to the plane itself", "XI.4",
          _perpendicular_to_plane(upright, surface))
    return Out(plane=surface, upright=upright)


@proposition(
    "XI.5",
    THEOREM,
    sample=samples3.right_angled_at_origin,
)
def prop_XI_5(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """A line at right angles to three concurrent lines puts those three in one
    plane."""
    hypothesis("OA and OB are not in a straight line", not collinear3(o, a, b))
    hypothesis("the line is at right angles to all three",
               dot3(vector_between(o, c), vector_between(o, a)) == 0
               and dot3(vector_between(o, c), vector_between(o, b)) == 0)
    # The third line of Euclid's figure is any other perpendicular to OC at O,
    # and the proposition is that it cannot escape the plane of the first two.
    third = posit3(Point3(o.x + (a.x - o.x) + (b.x - o.x),
                          o.y + (a.y - o.y) + (b.y - o.y),
                          o.z + (a.z - o.z) + (b.z - o.z)), "D")
    surface = plane_through(o, a, b, "the plane of the three")
    line3(o, c, "the perpendicular")

    claim("the third line is at right angles to OC as well", "XI.Def.3",
          dot3(vector_between(o, c), vector_between(o, third)) == 0)
    claim("and the three lines are in one plane", "XI.5",
          on_plane(a, surface) and on_plane(b, surface) and on_plane(third, surface))
    return Out(plane=surface)


@proposition(
    "XI.6",
    THEOREM,
    sample=samples3.plane_and_point,
)
def prop_XI_6(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Two lines at right angles to the same plane are parallel."""
    hypothesis("the three points describe a plane", not collinear3(a, b, c))
    hypothesis("D is off that plane", not coplanar(a, b, c, d))
    surface = plane_through(a, b, c, "the plane")
    normal = surface.normal()

    # Two uprights, one at A and one at B: both along the normal, which is what
    # being at right angles to the plane means.
    first_top = posit3(Point3(a.x + normal[0], a.y + normal[1], a.z + normal[2]), "E")
    second_top = posit3(Point3(b.x + normal[0], b.y + normal[1], b.z + normal[2]), "F")
    first = line3(a, first_top, "the upright at A")
    second = line3(b, second_top, "the upright at B")

    claim("both are at right angles to the plane", "XI.Def.3",
          _perpendicular_to_plane(first, surface)
          and _perpendicular_to_plane(second, surface))
    claim("therefore they are parallel", "XI.6", _parallel3(first, second))
    claim("and being distinct lines, they never meet", "XI.Def.8",
          not first.holds(b))
    return Out(first=first, second=second)


@proposition(
    "XI.7",
    THEOREM,
    sample=samples3.parallel_lines3,
)
def prop_XI_7(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """The line joining points on two parallels is in their plane."""
    first, second = Line3.through(a, b), Line3.through(c, d)
    hypothesis("the two lines are parallel", _parallel3(first, second))
    hypothesis("they are two lines and not one", not first.holds(c))
    surface = plane_through(a, b, c, "the plane of the parallels")
    line3(a, b)
    line3(c, d)
    joining = line3(a, c, "the joining line")

    claim("both parallels lie in the one plane", "XI.Def.8",
          on_plane(a, surface) and on_plane(b, surface)
          and on_plane(c, surface) and on_plane(d, surface))
    claim("and the joining line lies in it throughout", "XI.7",
          all(on_plane(joining.at(Fraction(k, 4)), surface) for k in range(-8, 9)))
    return Out(plane=surface, joining=joining)


@proposition(
    "XI.8",
    THEOREM,
    sample=samples3.plane_and_point,
)
def prop_XI_8(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """If one of two parallels is at right angles to a plane, so is the other."""
    hypothesis("the three points describe a plane", not collinear3(a, b, c))
    hypothesis("D is off that plane", not coplanar(a, b, c, d))
    surface = plane_through(a, b, c, "the plane")
    normal = surface.normal()
    top = posit3(Point3(a.x + normal[0], a.y + normal[1], a.z + normal[2]), "E")
    upright = line3(a, top, "the upright at A")
    alongside = line3(b, posit3(Point3(b.x + normal[0], b.y + normal[1],
                                       b.z + normal[2]), "F"), "its parallel")

    hypothesis("the two are parallel", _parallel3(upright, alongside))
    claim("the first is at right angles to the plane", "XI.Def.3",
          _perpendicular_to_plane(upright, surface))
    claim("so the second is at right angles to the same plane", "XI.8",
          _perpendicular_to_plane(alongside, surface))
    return Out(upright=upright, alongside=alongside)


@proposition(
    "XI.9",
    THEOREM,
    sample=samples3.parallel_lines3,
)
def prop_XI_9(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Lines parallel to the same line, and not in one plane with it, are
    parallel to one another."""
    middle = Line3.through(a, b)
    second = Line3.through(c, d)
    hypothesis("the second is parallel to the first", _parallel3(middle, second))
    hypothesis("they are distinct lines", not middle.holds(c))
    step = middle.direction()
    # The third parallel must be out of the plane the first two lie in, which is
    # the whole point: lift it along that plane's normal, so it is off the plane
    # by construction rather than by hoping the sampler put it there.
    up = plane_through(a, b, c).normal()
    away = posit3(Point3(c.x + up[0], c.y + up[1], c.z + up[2]), "E")
    third = line3(away, posit3(Point3(away.x + step[0], away.y + step[1],
                                      away.z + step[2]), "F"), "the third parallel")
    line3(a, b)
    line3(c, d)

    hypothesis("the third is parallel to the first as well", _parallel3(middle, third))
    # Two lines of one direction always lie in some plane together, so Euclid's
    # "not in the same plane with it" cannot mean that pair: it means the third
    # is out of the plane the first two already determine, which is the case his
    # proof is about and the only one that needs proving.
    hypothesis("the third is out of the plane of the first two",
               not coplanar(a, b, c, away))
    claim("the second and third are parallel to one another", "XI.9",
          _parallel3(second, third))
    return Out(lines=(middle, second, third))


@proposition(
    "XI.10",
    THEOREM,
    sample=samples3.tetrahedron,
)
def prop_XI_10(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Two lines meeting, parallel to two others meeting elsewhere, contain
    equal angles."""
    hypothesis("the arms are not in one plane", not coplanar(o, a, b, c))
    hypothesis("neither pair is in a straight line",
               not collinear3(o, a, b))
    # The second pair is the first carried over to another point, so the arms
    # really are parallel: that is the hypothesis, and building it is how the
    # figure gets one that satisfies it.
    step = vector_between(o, c)
    away = posit3(Point3(o.x + step[0], o.y + step[1], o.z + step[2]), "D")
    far_a = posit3(Point3(a.x + step[0], a.y + step[1], a.z + step[2]), "E")
    far_b = posit3(Point3(b.x + step[0], b.y + step[1], b.z + step[2]), "F")
    for pair in ((o, a), (o, b), (away, far_a), (away, far_b)):
        line3(*pair)

    claim("the arms are parallel, each to each", "XI.Def.8",
          _parallel3(Line3.through(o, a), Line3.through(away, far_a))
          and _parallel3(Line3.through(o, b), Line3.through(away, far_b)))
    claim("so the angles they contain are equal", "XI.10",
          angle_at3(a, o, b) == angle_at3(far_a, away, far_b))
    return Out(angles=(angle_at3(a, o, b), angle_at3(far_a, away, far_b)))


def _foot_on_plane(point: Point3, plane: Plane) -> Point3:
    """Where the perpendicular from a point meets a plane.

    The drop is along the normal, and the multiple of it is a quotient of exact
    quantities, so the foot stays in the field the figure was built in and no
    root is taken to find it.
    """
    normal = plane.normal()
    step = plane.evaluate(point) / dot3(normal, normal)
    return Point3(point.x - step * normal[0],
                  point.y - step * normal[1],
                  point.z - step * normal[2])


def _sum_exceeds(first, second, third) -> bool:
    """Whether two angles taken together exceed a third, decided exactly.

    ``cos(x + y) = cos x cos y - sin x sin y``, and both sines are positive on
    ``[0, pi]``, so ``sin x sin y`` is one root of ``(1 - c1^2)(1 - c2^2)`` --
    a single root of a product, which the field can take without a second
    extension. The sum exceeds the third angle when its cosine is the smaller;
    if the two together pass a straight angle there is nothing left to exceed,
    and that case is answered before the root is asked for.
    """
    c1, c2, c3 = first.cos, second.cos, third.cos
    product = (1 - c1 * c1) * (1 - c2 * c2)
    if sign(product) <= 0:
        return sign(c1 * c2 - c3) <= 0
    return sign(c1 * c2 - sqrt(product) - c3) <= 0


@proposition("XI.11", CONSTRUCTION, sample=samples3.plane_and_point)
def prop_XI_11(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """From an elevated point, draw a line perpendicular to a given plane."""
    hypothesis("the three points describe a plane", not collinear3(a, b, c))
    hypothesis("D is elevated above that plane", not coplanar(a, b, c, d))
    surface = plane_through(a, b, c, "the given plane")
    foot = posit3(_foot_on_plane(d, surface), "F")
    dropped = line3(d, foot, "the perpendicular")

    claim("the foot lies in the given plane", "XI.Def.7", on_plane(foot, surface))
    claim("and the line drawn is at right angles to the plane", "XI.11",
          _perpendicular_to_plane(dropped, surface))
    claim("so it is at right angles to every line of the plane through the foot",
          "XI.Def.3",
          all(dot3(vector_between(d, foot), vector_between(foot, point)) == 0
              for point in (a, b, c) if point != foot))
    return Out(perpendicular=dropped, foot=foot)


@proposition("XI.12", CONSTRUCTION, sample=samples3.three_in_space)
def prop_XI_12(a: Point3, b: Point3, c: Point3) -> Out:
    """Set up a line at right angles to a plane, from a point in it."""
    hypothesis("the three points describe a plane", not collinear3(a, b, c))
    surface = plane_through(a, b, c, "the given plane")
    normal = surface.normal()
    top = posit3(Point3(a.x + normal[0], a.y + normal[1], a.z + normal[2]), "D")
    upright = line3(a, top, "the line set up")

    claim("the line stands on the given point of the plane", "XI.Def.7",
          on_plane(a, surface) and not on_plane(top, surface))
    claim("and it is at right angles to the plane", "XI.12",
          _perpendicular_to_plane(upright, surface))
    return Out(upright=upright)


@proposition("XI.13", THEOREM, sample=samples3.three_in_space)
def prop_XI_13(a: Point3, b: Point3, c: Point3) -> Out:
    """Two perpendiculars cannot stand at one point on one side of a plane."""
    hypothesis("the three points describe a plane", not collinear3(a, b, c))
    surface = plane_through(a, b, c, "the given plane")
    normal = surface.normal()
    top = posit3(Point3(a.x + normal[0], a.y + normal[1], a.z + normal[2]), "D")
    line3(a, top, "the perpendicular")

    # The proposition denies a second one, so what is checked is the denial:
    # every other line drawn from A leans, and only the normal direction meets
    # the whole plane squarely.
    others = [Point3(top.x + (b.x - a.x) * Fraction(k, 4),
                     top.y + (b.y - a.y) * Fraction(k, 4),
                     top.z + (b.z - a.z) * Fraction(k, 4))
              for k in range(1, 5)]
    claim("no other line from the same point is at right angles to the plane",
          "XI.13",
          not any(_perpendicular_to_plane(Line3.through(a, other), surface)
                  for other in others))
    claim("and each of those lines is on the same side as the first", "XI.13",
          all(same_side_of_plane(other, top, surface) for other in others))
    return Out(perpendicular=Line3.through(a, top))


@proposition("XI.14", THEOREM, sample=samples3.plane_and_point)
def prop_XI_14(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Planes at right angles to the same line are parallel."""
    hypothesis("the three points describe a plane", not collinear3(a, b, c))
    hypothesis("D is off that plane", not coplanar(a, b, c, d))
    first = plane_through(a, b, c, "the first plane")
    normal = first.normal()
    step = vector_between(a, d)
    lifted = [posit3(Point3(p.x + step[0], p.y + step[1], p.z + step[2]), name)
              for p, name in zip((a, b, c), ("E", "F", "G"))]
    second = plane_through(*lifted, "the second plane")
    upright = line3(a, posit3(Point3(a.x + normal[0], a.y + normal[1],
                                     a.z + normal[2]), "H"), "the perpendicular")

    claim("the one line is at right angles to both planes", "XI.Def.3",
          _perpendicular_to_plane(upright, first)
          and _perpendicular_to_plane(upright, second))
    claim("therefore the planes are parallel", "XI.14",
          parallel_planes(first, second))
    claim("and being two planes and not one, they nowhere meet", "XI.Def.8",
          first != second)
    return Out(planes=(first, second))


@proposition("XI.16", THEOREM, sample=samples3.plane_and_point)
def prop_XI_16(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Two parallel planes cut by a third have parallel common sections."""
    hypothesis("the three points describe a plane", not collinear3(a, b, c))
    hypothesis("D is off that plane", not coplanar(a, b, c, d))
    step = vector_between(a, d)
    first = plane_through(a, b, c, "the first plane")
    lifted = [posit3(Point3(p.x + step[0], p.y + step[1], p.z + step[2]), name)
              for p, name in zip((a, b, c), ("E", "F", "G"))]
    second = plane_through(*lifted, "the second, parallel to it")
    hypothesis("the two planes are parallel", parallel_planes(first, second))

    cutter = plane_through(a, lifted[0], b, "the cutting plane")
    here = meet_planes(first, cutter)
    there = meet_planes(second, cutter)

    claim("each common section is a straight line", "XI.3",
          isinstance(here, Line3) and isinstance(there, Line3))
    claim("and the two sections are parallel to one another", "XI.16",
          _parallel3(here, there))
    return Out(sections=(here, there))


@proposition("XI.18", THEOREM, sample=samples3.plane_and_point)
def prop_XI_18(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Every plane through a perpendicular is perpendicular to the same plane."""
    hypothesis("the three points describe a plane", not collinear3(a, b, c))
    hypothesis("D is off that plane", not coplanar(a, b, c, d))
    surface = plane_through(a, b, c, "the given plane")
    normal = surface.normal()
    top = posit3(Point3(a.x + normal[0], a.y + normal[1], a.z + normal[2]), "H")
    upright = line3(a, top, "the perpendicular")
    hypothesis("the line is at right angles to the plane",
               _perpendicular_to_plane(upright, surface))

    through = [plane_through(a, top, point, label)
               for point, label in ((b, "the plane through B"),
                                    (c, "the plane through C"))]
    claim("each of those planes holds the whole perpendicular", "XI.Def.7",
          all(on_plane(a, plane) and on_plane(top, plane) for plane in through))
    claim("and each is at right angles to the given plane", "XI.18",
          all(dot3(plane.normal(), normal) == 0 for plane in through))
    return Out(planes=tuple(through))


@proposition("XI.19", THEOREM, sample=samples3.plane_and_point)
def prop_XI_19(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Two planes at right angles to a third cut it in a perpendicular line."""
    hypothesis("the three points describe a plane", not collinear3(a, b, c))
    hypothesis("D is off that plane", not coplanar(a, b, c, d))
    surface = plane_through(a, b, c, "the given plane")
    normal = surface.normal()
    top = posit3(Point3(a.x + normal[0], a.y + normal[1], a.z + normal[2]), "H")
    first = plane_through(a, top, b, "the first plane")
    second = plane_through(a, top, c, "the second")
    hypothesis("both are at right angles to the given plane",
               dot3(first.normal(), normal) == 0
               and dot3(second.normal(), normal) == 0)
    hypothesis("they are two planes and not one", first != second)

    section = meet_planes(first, second)
    claim("their common section is a straight line", "XI.3",
          isinstance(section, Line3))
    claim("and it is at right angles to the given plane", "XI.19",
          _perpendicular_to_plane(section, surface))
    return Out(section=section)


@proposition("XI.20", THEOREM, sample=samples3.tetrahedron)
def prop_XI_20(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Any two plane angles of a solid angle exceed the third."""
    hypothesis("the solid angle is a genuine one", not coplanar(o, a, b, c),
               guard=True)
    for arm in (a, b, c):
        line3(o, arm)

    first, second, third = angle_at3(a, o, b), angle_at3(b, o, c), angle_at3(a, o, c)
    claim("any two of the three plane angles, taken together, are greater than "
          "the remaining one", "XI.20",
          all(_sum_exceeds(x, y, z) for x, y, z in
              ((first, second, third), (second, third, first), (first, third, second))))
    return Out(angles=(first, second, third))


@proposition("XI.15", THEOREM, sample=samples3.tetrahedron)
def prop_XI_15(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Two pairs of meeting lines, parallel each to each, lie in parallel planes."""
    hypothesis("the arms are not in one plane", not coplanar(o, a, b, c))
    hypothesis("neither pair is in a straight line", not collinear3(o, a, b))
    step = vector_between(o, c)
    away = posit3(Point3(o.x + step[0], o.y + step[1], o.z + step[2]), "D")
    far_a = posit3(Point3(a.x + step[0], a.y + step[1], a.z + step[2]), "E")
    far_b = posit3(Point3(b.x + step[0], b.y + step[1], b.z + step[2]), "F")
    for pair in ((o, a), (o, b), (away, far_a), (away, far_b)):
        line3(*pair)

    first = plane_through(o, a, b, "the plane of the first pair")
    second = plane_through(away, far_a, far_b, "the plane of the second")
    hypothesis("the two pairs are not in one plane", first != second)

    claim("the arms are parallel, each to each", "XI.Def.8",
          _parallel3(Line3.through(o, a), Line3.through(away, far_a))
          and _parallel3(Line3.through(o, b), Line3.through(away, far_b)))
    claim("so the planes through them are parallel", "XI.15",
          parallel_planes(first, second))
    return Out(planes=(first, second))


@proposition("XI.17", THEOREM, sample=samples3.plane_and_point)
def prop_XI_17(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Two straight lines cut by parallel planes are cut in the same ratios."""
    hypothesis("the three points describe a plane", not collinear3(a, b, c))
    hypothesis("D is off that plane", not coplanar(a, b, c, d))
    step = vector_between(a, d)
    first = plane_through(a, b, c, "the first plane")
    lifted = [posit3(Point3(p.x + step[0], p.y + step[1], p.z + step[2]), name)
              for p, name in zip((a, b, c), ("E", "F", "G"))]
    second = plane_through(*lifted, "the second, parallel to it")
    # A third plane parallel to both, cutting each line partway along.
    half = Fraction(1, 2)
    middle = [posit3(Point3(p.x + half * step[0], p.y + half * step[1],
                            p.z + half * step[2]), name)
              for p, name in zip((a, b, c), ("K", "L", "M"))]
    third = plane_through(*middle, "the plane between them")
    hypothesis("the three planes are parallel",
               parallel_planes(first, second) and parallel_planes(first, third))

    # Two lines cut by all three: A to its lift, and B to its lift.
    one = line3(a, lifted[0], "the first line")
    other = line3(b, lifted[1], "the second line")
    here = meet_line_plane(one, third)
    there = meet_line_plane(other, third)

    claim("each line is cut by the middle plane", "XI.Def.7",
          on_plane(here, third) and on_plane(there, third))
    # Ratios of lengths along a line are ratios of squared lengths crosswise,
    # which keeps the comparison exact and takes no root.
    claim("and the two are cut in the same ratio", "XI.17",
          len2(a, here) * len2(there, lifted[1]) == len2(here, lifted[0]) * len2(b, there))
    return Out(sections=(here, there))


def _cos_of_sum(first, second):
    """``cos(x + y)`` for two angles of a solid angle, exactly.

    ``cos(x + y) = cos x cos y - sin x sin y``, and both sines are positive on
    ``[0, pi]``, so their product is the single root of ``(1 - c1^2)(1 - c2^2)``.
    One root of one product, so the field gains one extension and not two.
    """
    c1, c2 = first.cos, second.cos
    product = (1 - c1 * c1) * (1 - c2 * c2)
    if sign(product) <= 0:
        return c1 * c2
    return c1 * c2 - sqrt(product)


def _under_four_right_angles(first, second, third) -> bool:
    """Whether three plane angles together fall short of four right angles.

    There is no arc to add, so the comparison is made through cosines. Each
    angle lies in ``(0, pi)``. If the first two together fall short of two right
    angles the three cannot reach four, and ``cos x > -cos y`` says so. Otherwise
    ``x + y`` is at least a straight angle, and the three fall short of four
    right angles exactly when ``z`` falls short of ``2pi - (x + y)``, which --
    both being at most a straight angle -- is ``cos z > cos(x + y)``.
    """
    if sign(first.cos + second.cos) > 0:
        return True
    return sign(third.cos - _cos_of_sum(first, second)) > 0


@proposition("XI.21", THEOREM, sample=samples3.tetrahedron)
def prop_XI_21(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Any solid angle is contained by plane angles less than four right angles."""
    hypothesis("the solid angle is a genuine one", not coplanar(o, a, b, c),
               guard=True)
    for arm in (a, b, c):
        line3(o, arm)

    first, second, third = angle_at3(a, o, b), angle_at3(b, o, c), angle_at3(a, o, c)
    claim("each plane angle is less than two right angles", "XI.Def.11",
          all(sign(angle.cos + 1) > 0 for angle in (first, second, third)))
    claim("and the three together are less than four right angles", "XI.21",
          _under_four_right_angles(first, second, third)
          and _under_four_right_angles(second, third, first)
          and _under_four_right_angles(first, third, second))
    return Out(angles=(first, second, third))


@proposition("XI.22", THEOREM, sample=samples3.tetrahedron)
def prop_XI_22(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Three plane angles, any two exceeding the third, on equal arms: the joins
    make a triangle."""
    hypothesis("the arms are not in one plane", not coplanar(o, a, b, c))
    # Euclid's figure has the containing lines equal, so the arms are cut to one
    # length. The cut is I.3's move carried into space, and the length is
    # squared throughout so no root is taken to make it.
    reach = len2(o, a)
    arms = []
    for point, name in ((a, "A"), (b, "B"), (c, "C")):
        scale = reach / len2(o, point)
        step = vector_between(o, point)
        # The equal arm is along the same ray; its square is ``reach`` by
        # construction, and comparing squares is comparing lengths.
        arms.append(posit3(Point3(o.x + step[0] * scale, o.y + step[1] * scale,
                                  o.z + step[2] * scale), name + "'"))
    for arm in arms:
        line3(o, arm)
    joins = [line3(arms[i], arms[j], "a join") for i, j in ((0, 1), (1, 2), (0, 2))]

    angles = (angle_at3(a, o, b), angle_at3(b, o, c), angle_at3(a, o, c))
    hypothesis("any two of the plane angles exceed the third",
               all(_sum_exceeds(x, y, z) for x, y, z in
                   ((angles[0], angles[1], angles[2]),
                    (angles[1], angles[2], angles[0]),
                    (angles[0], angles[2], angles[1]))))

    sides = [len2(arms[0], arms[1]), len2(arms[1], arms[2]), len2(arms[0], arms[2])]
    claim("the joins are the bases of the three triangles on equal arms", "I.4",
          len(joins) == 3 and all(sign(side) > 0 for side in sides))
    # A triangle can be made of three lengths when each falls short of the other
    # two together. Squared lengths compare by squaring the inequality, which
    # stays exact: (p + q)^2 > r^2 with all positive is p^2 + q^2 + 2pq > r^2.
    claim("and a triangle can be made of the three joins", "XI.22",
          all(_triangle_from(sides[i], sides[j], sides[k])
              for i, j, k in ((0, 1, 2), (1, 2, 0), (0, 2, 1))))
    return Out(arms=tuple(arms), joins=tuple(joins))


def _triangle_from(first, second, third) -> bool:
    """Whether three squared lengths admit a triangle, decided exactly.

    ``p + q > r`` with every length positive is ``p^2 + q^2 + 2pq > r^2``, and
    ``pq`` is the single root of the product of the two squares -- so the test
    stays in the field and needs no length taken on its own.
    """
    return sign(first + second + 2 * sqrt(first * second) - third) > 0


@proposition("XI.23", CONSTRUCTION, sample=samples3.tetrahedron)
def prop_XI_23(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Construct a solid angle out of three plane angles, any two exceeding the
    third."""
    hypothesis("the arms are not in one plane", not coplanar(o, a, b, c))
    angles = (angle_at3(a, o, b), angle_at3(b, o, c), angle_at3(a, o, c))
    hypothesis("any two of the given angles exceed the third",
               all(_sum_exceeds(x, y, z) for x, y, z in
                   ((angles[0], angles[1], angles[2]),
                    (angles[1], angles[2], angles[0]),
                    (angles[0], angles[2], angles[1]))))
    hypothesis("the three together fall short of four right angles",
               _under_four_right_angles(*angles))

    # The solid angle asked for is the one these three angles already contain:
    # the construction is to set it up at a named point, which is the figure
    # carried over -- and carrying a figure over is exact.
    corner = posit3(Point3(0, 0, 0), "D")
    arms = []
    for point, name in ((a, "E"), (b, "F"), (c, "G")):
        step = vector_between(o, point)
        arms.append(posit3(Point3(corner.x + step[0], corner.y + step[1],
                                  corner.z + step[2]), name))
    for arm in arms:
        line3(corner, arm)

    made = (angle_at3(arms[0], corner, arms[1]),
            angle_at3(arms[1], corner, arms[2]),
            angle_at3(arms[0], corner, arms[2]))
    claim("the solid angle constructed is contained by the three given angles",
          "XI.23", made == angles)
    claim("and it is a genuine solid angle, its arms not in one plane", "XI.Def.11",
          not coplanar(corner, *arms))
    return Out(corner=corner, arms=tuple(arms), angles=made)


# ---------------------------------------------------------------------------
# XI.24 - XI.39: the parallelepipedal solids
#
# From here the book is about content, and content is got the way Euclid gets
# it: by cutting a figure into pieces and adding them up.  Nothing in this
# section is told what a volume is.  See :mod:`euclid.solid.solids`.
# ---------------------------------------------------------------------------


def _built(solid: Solid) -> Solid:
    """Post a solid's vertices and join its edges, so the figure is the solid."""
    for vertex in solid.vertices:
        posit3(vertex)
    for start, end in solid.edges():
        line3(solid.vertices[start], solid.vertices[end])
    return solid


def _is_parallelogram(points: tuple) -> bool:
    """Four points in order, opposite sides equal and parallel (I.34's figure)."""
    if len(points) != 4:
        return False
    one = vector_between(points[0], points[1])
    other = vector_between(points[3], points[2])
    across = vector_between(points[1], points[2])
    back = vector_between(points[0], points[3])
    return one == other and across == back


def _same_figure(first: tuple, second: tuple) -> bool:
    """Two four-sided faces equal: sides and diagonals alike, so I.8 applies."""
    pairs = ((0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3))
    return all(len2(first[i], first[j]) == len2(second[i], second[j])
               for i, j in pairs)


def _base_area(corner: Point3, first: Point3, second: Point3):
    return parallelogram_area(vector_between(corner, first),
                              vector_between(corner, second))


def _triangle_area(corner: Point3, first: Point3, second: Point3):
    """Half the parallelogram on the same two sides, which is I.34's figure."""
    return _base_area(corner, first, second) / 2


def _along(corner: Point3, towards: Point3, part) -> Point3:
    step = vector_between(corner, towards)
    return Point3(corner.x + part * step[0], corner.y + part * step[1],
                  corner.z + part * step[2])


def _arm_at(corner: Point3, direction: tuple, reach) -> Point3:
    return Point3(corner.x + reach * direction[0], corner.y + reach * direction[1],
                  corner.z + reach * direction[2])


@proposition("XI.24", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_24(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """A solid contained by parallel planes has opposite faces equal and
    parallelogrammic."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    solid = _built(parallelepiped(o, a, b, c, "the solid"))
    faces = [solid.face_points(index) for index in range(6)]
    planes = [solid.face_plane(index) for index in range(6)]
    opposite = ((0, 1), (2, 3), (4, 5))

    claim("the solid is contained by planes parallel two and two", "XI.14",
          all(parallel_planes(planes[here], planes[there])
              and planes[here] != planes[there] for here, there in opposite))
    claim("the opposite sides of each face are parallel, so each is a "
          "parallelogram", "XI.16",
          all(_is_parallelogram(face) for face in faces))
    claim("and the opposite faces are equal to one another", "I.34",
          all(_same_figure(faces[here], faces[there]) for here, there in opposite))
    return Out(solid=solid, faces=tuple(faces))


@proposition("XI.25", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_25(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """A parallelepiped cut by a plane parallel to the opposite planes: as the
    base is to the base, so is the solid to the solid."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    because(prop_XI_24, o, a, b, c)
    # The cutting plane is set a third of the way along the first arm, which is
    # a ratio Euclid may take at will: what the proposition asserts holds of
    # every such cut, and the necessity sweep bends this one.
    part = Fraction(1, 3)
    cut = posit3(_along(o, a, part), "K")
    over = posit3(cut + (b - o), "L")
    above = posit3(cut + (c - o), "M")

    nearer = _built(parallelepiped(o, cut, b, c, "the nearer solid"))
    beyond = _built(parallelepiped(cut, a, over, above, "the further solid"))
    cutter = plane_through(cut, over, above, "the cutting plane")

    claim("the cutting plane is parallel to the two opposite planes", "XI.15",
          parallel_planes(cutter, nearer.face_plane(4))
          and parallel_planes(cutter, beyond.face_plane(5)))
    here, there = _base_area(o, cut, b), _base_area(cut, a, over)
    claim("as the base is to the base, so is the solid to the solid", "XI.25",
          here * content(beyond) == there * content(nearer))
    return Out(nearer=nearer, beyond=beyond, cut=cut, bases=(here, there))


def _solid_angle_of(corner: Point3, arms: tuple) -> tuple:
    return (angle_at3(arms[0], corner, arms[1]),
            angle_at3(arms[1], corner, arms[2]),
            angle_at3(arms[0], corner, arms[2]))


def _arms_making(corner: Point3, direction: tuple, angles: tuple) -> tuple:
    """Three arms of unit length from a corner, containing the given angles.

    The first runs along the direction given, which is what "on a given straight
    line, and at a given point on it" asks for.  The second is laid in the plane
    the first two of the frame span, and the third is fixed by its cosines with
    both -- so the figure is determined by the angles and by nothing else, and
    the two square roots it takes are the only extensions the construction
    needs.
    """
    first, second, third = frame_on(direction)
    twelve, twenty_three, thirteen = angles
    across = sqrt(1 - twelve.cos * twelve.cos)
    arm_b = tuple(twelve.cos * first[i] + across * second[i] for i in range(3))
    along = thirteen.cos
    sideways = (twenty_three.cos - twelve.cos * thirteen.cos) / across
    upward = sqrt(1 - along * along - sideways * sideways)
    arm_c = tuple(along * first[i] + sideways * second[i] + upward * third[i]
                  for i in range(3))
    return (_arm_at(corner, first, Fraction(1)),
            _arm_at(corner, arm_b, Fraction(1)),
            _arm_at(corner, arm_c, Fraction(1)))


@proposition("XI.26", CONSTRUCTION, sample=samples3.two_corners)
def prop_XI_26(o: Point3, a: Point3, b: Point3, c: Point3,
               d: Point3, e: Point3, f: Point3, g: Point3) -> Out:
    """On a given straight line, and at a given point on it, construct a solid
    angle equal to a given solid angle."""
    hypothesis("the arms of the given angle are not in one plane",
               not coplanar(o, a, b, c))
    hypothesis("the given straight line has two distinct ends", d != e)
    given = _solid_angle_of(o, (a, b, c))
    hypothesis("no two of the given plane angles are together a straight angle",
               all(sign(1 - angle.cos * angle.cos) > 0 for angle in given),
               guard=True)
    for arm in (a, b, c):
        line3(o, arm)
    line3(d, e, "the given straight line")

    because(prop_XI_23, o, a, b, c)
    arms = tuple(posit3(point, name) for point, name in
                 zip(_arms_making(d, vector_between(d, e), given), ("P", "Q", "R")))
    for arm in arms:
        line3(d, arm)
    made = _solid_angle_of(d, arms)

    claim("the first arm is set up along the given straight line, at the given "
          "point on it", "XI.Def.11",
          on_line3(arms[0], Line3.through(d, e))
          and sign(dot3(vector_between(d, arms[0]), vector_between(d, e))) > 0)
    claim("the angle constructed is contained by plane angles equal to the "
          "given ones", "XI.26", made == given)
    claim("and it is a solid angle, its arms not in one plane", "XI.23",
          not coplanar(d, *arms))
    return Out(corner=d, arms=arms, angles=made)


@proposition("XI.27", CONSTRUCTION, sample=samples3.two_corners)
def prop_XI_27(o: Point3, a: Point3, b: Point3, c: Point3,
               d: Point3, e: Point3, f: Point3, g: Point3) -> Out:
    """On a given straight line describe a parallelepiped similar and similarly
    situated to a given one."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    hypothesis("the given straight line has two distinct ends", d != e)
    given = _built(parallelepiped(o, a, b, c, "the given solid"))
    reach = len2(o, a)
    # Similar means the edges in one ratio, so the scale is fixed by the given
    # line against the edge it answers to. Both are squared, and the quotient of
    # two squares is the square of the quotient, so one root gives the ratio.
    scale = sqrt(len2(d, e) / reach)

    corner = posit3(d, "")
    arms = []
    for point, name in ((a, "P"), (b, "Q"), (c, "R")):
        step = vector_between(o, point)
        arms.append(posit3(Point3(d.x + scale * step[0], d.y + scale * step[1],
                                  d.z + scale * step[2]), name))
    described = _built(parallelepiped(d, *arms, "the solid described"))

    claim("the solid is described on the given straight line", "XI.26",
          len2(d, arms[0]) == len2(d, e))
    claim("its edges are to the edges of the given solid in one ratio", "VI.Def.1",
          all(side == scale * scale * given_side for side, given_side in
              zip(edge_lengths(described), edge_lengths(given))))
    claim("and the solid angles at the answering corners are equal, so it is "
          "similarly situated", "XI.Def.9",
          _solid_angle_of(d, tuple(arms)) == _solid_angle_of(o, (a, b, c)))
    return Out(described=described, given=given, scale=scale)


@proposition("XI.28", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_28(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """A parallelepiped cut by a plane through the diagonals of the opposite
    faces is bisected by that plane."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    solid = _built(parallelepiped(o, a, b, c, "the solid"))
    whole = content(solid)
    across = vector_between(o, c)

    near, far = solid.vertices[2], solid.vertices[6]
    line3(o, near, "the diagonal of the base")
    line3(solid.vertices[4], far, "the diagonal of the opposite face")
    cutter = plane_through(o, near, far, "the cutting plane")

    first = _built(prism((o, a, near), across, "the first prism"))
    second = _built(prism((o, near, b), across, "the second prism"))

    claim("the plane is carried through the diagonals of the opposite faces",
          "XI.3",
          on_plane(o, cutter) and on_plane(near, cutter)
          and on_plane(solid.vertices[4], cutter) and on_plane(far, cutter))
    claim("the two prisms it makes are equal to one another", "I.34",
          content(first) == content(second))
    claim("so the solid is bisected by the plane", "XI.28",
          content(first) + content(second) == whole
          and 2 * content(first) == whole)
    return Out(prisms=(first, second), plane=cutter)


@proposition("XI.29", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_29(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Parallelepipeds on the same base and of the same height, whose standing
    sides end on the same straight lines, are equal."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    first = _built(parallelepiped(o, a, b, c, "the first solid"))
    # The second stands on the same base and reaches the same plane, its top
    # slid along the line the first solid's top edge lies in. That is what "the
    # extremities of the sides which stand up are on the same straight lines"
    # says, and it is the only freedom the figure has.
    slide = vector_between(o, a)
    leaned = posit3(Point3(c.x + slide[0], c.y + slide[1], c.z + slide[2]), "M")
    second = _built(parallelepiped(o, a, b, leaned, "the second solid"))
    line3(c, leaned, "the line the tops end on")

    claim("the two solids stand on the same base", "XI.24",
          _same_figure(first.face_points(0), second.face_points(0)))
    claim("their tops are in one plane, so they are of the same height", "XI.14",
          parallel_planes(first.face_plane(1), first.face_plane(0))
          and second.face_plane(1) == first.face_plane(1))
    claim("and the solids are equal to one another", "XI.29",
          content(first) == content(second))
    return Out(solids=(first, second))


@proposition("XI.30", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_30(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Parallelepipeds on the same base and of the same height, whose standing
    sides do not end on the same straight lines, are equal."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    first = _built(parallelepiped(o, a, b, c, "the first solid"))
    # Slid across both arms of the base, so the top runs in neither of the lines
    # XI.29 leaves it in: the same plane is reached by a different route.
    one, other = vector_between(o, a), vector_between(o, b)
    leaned = posit3(Point3(c.x + one[0] + other[0], c.y + one[1] + other[1],
                           c.z + one[2] + other[2]), "M")
    second = _built(parallelepiped(o, a, b, leaned, "the second solid"))

    because(prop_XI_29, o, a, b, c)

    claim("the two solids stand on the same base and reach the same plane",
          "XI.29",
          _same_figure(first.face_points(0), second.face_points(0))
          and second.face_plane(1) == first.face_plane(1))
    claim("the tops do not lie in the same straight lines", "XI.Def.10",
          not on_line3(leaned, Line3.through(c, first.vertices[5]))
          and not on_line3(leaned, Line3.through(c, first.vertices[7])))
    claim("and the solids are equal to one another", "XI.30",
          content(first) == content(second))
    return Out(solids=(first, second))


@proposition("XI.31", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_31(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Parallelepipeds on equal bases and of the same height are equal."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    first = _built(parallelepiped(o, a, b, c, "the first solid"))
    # A second base in the same plane, of the same area but not the same figure:
    # one side doubled and the other halved leaves the parallelogram on them
    # equal to the first, which is I.35 and I.36 done with the arms themselves.
    stretched = posit3(_along(o, a, Fraction(2)), "P")
    shrunk = posit3(_along(o, b, Fraction(1, 2)), "Q")
    second = _built(parallelepiped(o, stretched, shrunk, c, "the second solid"))

    because(prop_XI_30, o, a, b, c)

    claim("the two bases are equal, and are not the same figure", "I.35",
          _base_area(o, a, b) == _base_area(o, stretched, shrunk)
          and not _same_figure(first.face_points(0), second.face_points(0)))
    claim("the bases are in one plane and the tops in one plane, so the heights "
          "are the same", "XI.14",
          first.face_plane(0) == second.face_plane(0)
          and first.face_plane(1) == second.face_plane(1))
    claim("and the solids are equal to one another", "XI.31",
          content(first) == content(second))
    return Out(solids=(first, second))


@proposition("XI.32", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_32(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Parallelepipeds of the same height are to one another as their bases."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    first = _built(parallelepiped(o, a, b, c, "the first solid"))
    wider = posit3(_along(o, a, Fraction(5, 2)), "P")
    second = _built(parallelepiped(o, wider, b, c, "the second solid"))

    because(prop_XI_31, o, a, b, c)

    here, there = _base_area(o, a, b), _base_area(o, wider, b)
    claim("the two solids are of the same height", "XI.14",
          first.face_plane(0) == second.face_plane(0)
          and first.face_plane(1) == second.face_plane(1))
    claim("as the base is to the base, so is the solid to the solid", "XI.32",
          here * content(second) == there * content(first))
    return Out(solids=(first, second), bases=(here, there))


@proposition("XI.33", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_33(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Similar parallelepipeds are to one another in the triplicate ratio of
    their corresponding sides."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    first = _built(parallelepiped(o, a, b, c, "the first solid"))
    scale = Fraction(3, 2)
    arms = tuple(posit3(_along(o, point, scale), name)
                 for point, name in ((a, "P"), (b, "Q"), (c, "R")))
    second = _built(parallelepiped(o, *arms, "the second solid"))

    because(prop_XI_27, o, a, b, c, o, a, b, c)

    side, answering = length3(o, a), length3(o, arms[0])
    claim("the solids are similar, their edges in one ratio and their solid "
          "angles equal", "XI.Def.9",
          all(other == scale * scale * one for one, other in
              zip(edge_lengths(first), edge_lengths(second)))
          and _solid_angle_of(o, (a, b, c)) == _solid_angle_of(o, arms))
    claim("as the solid is to the solid, so is the cube on the side to the cube "
          "on the answering side", "XI.33",
          content(first) * answering * answering * answering
          == content(second) * side * side * side)
    return Out(solids=(first, second), sides=(side, answering))


@proposition("XI.34", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_34(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """In equal parallelepipeds the bases are reciprocally proportional to the
    heights, and conversely."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    first = _built(parallelepiped(o, a, b, c, "the first solid"))
    # A second solid equal to the first, its base twice as wide and its height
    # halved: the reciprocation the proposition is about, made rather than found.
    wider = posit3(_along(o, a, Fraction(2)), "P")
    lower = posit3(_along(o, c, Fraction(1, 2)), "R")
    second = _built(parallelepiped(o, wider, b, lower, "the second solid"))

    because(prop_XI_32, o, a, b, c)

    bases = (_base_area(o, a, b), _base_area(o, wider, b))
    heights = (height_over(c, first.face_plane(0)),
               height_over(lower, second.face_plane(0)))
    claim("the two solids are equal", "XI.31", content(first) == content(second))
    claim("so as the base is to the base, so is the height to the height "
          "reciprocally", "XI.34",
          bases[0] * heights[0] == bases[1] * heights[1])
    # The converse is the same equation read the other way, and Euclid states
    # both halves, so both are checked.
    claim("and solids whose bases are reciprocally proportional to their "
          "heights are equal", "XI.34",
          content(first) == bases[0] * heights[0]
          and content(second) == bases[1] * heights[1])
    return Out(solids=(first, second), bases=bases, heights=heights)


@proposition("XI.35", THEOREM, sample=samples3.two_corners)
def prop_XI_35(o: Point3, a: Point3, b: Point3, c: Point3,
               d: Point3, e: Point3, f: Point3, g: Point3) -> Out:
    """Two equal plane angles, with elevated lines making equal angles with
    their sides: the elevated lines make equal angles with the joins from the
    feet of the perpendiculars."""
    hypothesis("the elevated line is out of the plane of the given angle",
               not coplanar(o, a, b, c))
    hypothesis("the second angle's arms have two distinct ends", d != e)
    for arm in (a, b, c):
        line3(o, arm)

    base = plane_through(o, a, b, "the plane of the given angle")
    foot = posit3(_foot_on_plane(c, base), "L")
    hypothesis("the elevated line is not itself at right angles to the plane, "
               "so there is a join from the foot to the vertex", o != foot)
    line3(c, foot, "the perpendicular")
    line3(o, foot, "the join from the foot")
    because(prop_XI_11, o, a, b, c)

    # The second figure is set up from the angles alone, by XI.26's frame: the
    # plane angle and the two the elevated line makes with its sides. Nothing
    # of the first figure's coordinates crosses over, so the equality claimed
    # at the end is a conclusion and not a restatement.
    flat = angle_at3(a, o, b)
    with_first, with_second = angle_at3(a, o, c), angle_at3(b, o, c)
    hypothesis("no two of the three angles are together a straight angle",
               all(sign(1 - angle.cos * angle.cos) > 0
                   for angle in (flat, with_first, with_second)),
               guard=True)
    arms = tuple(posit3(point, name) for point, name in
                 zip(_arms_making(d, vector_between(d, e),
                                  (flat, with_second, with_first)), ("P", "Q", "M")))
    for arm in arms:
        line3(d, arm)
    second_base = plane_through(d, arms[0], arms[1], "the plane of the second angle")
    second_foot = posit3(_foot_on_plane(arms[2], second_base), "N")
    line3(arms[2], second_foot, "the second perpendicular")
    line3(d, second_foot, "the second join")

    claim("the two plane angles are equal", "I.Def.8",
          angle_at3(arms[0], d, arms[1]) == flat)
    claim("and the elevated lines contain equal angles with their sides", "XI.26",
          angle_at3(arms[0], d, arms[2]) == with_first
          and angle_at3(arms[1], d, arms[2]) == with_second)
    claim("therefore the elevated lines contain equal angles with the joins",
          "XI.35",
          angle_at3(c, o, foot) == angle_at3(arms[2], d, second_foot))
    return Out(feet=(foot, second_foot),
               angles=(angle_at3(c, o, foot), angle_at3(arms[2], d, second_foot)))


@proposition("XI.36", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_36(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """If three straight lines be proportional, the parallelepiped on them is
    equal to the equilateral one on the mean which is equiangular with it."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    ratio = Fraction(3, 2)
    # Three lines in proportion, taken as one length, that length by the ratio,
    # and by the ratio again: the mean is the square root of the extremes'
    # rectangle exactly, and every one of the three stays rational.
    lines = (Fraction(1), ratio, ratio * ratio)
    hypothesis("the three straight lines are proportional",
               lines[1] * lines[1] == lines[0] * lines[2])

    directions = tuple(unit(vector_between(o, point)) for point in (a, b, c))
    unequal = _built(parallelepiped(
        o, *[posit3(_arm_at(o, step, reach), name)
             for step, reach, name in zip(directions, lines, ("P", "Q", "R"))],
        "the solid on the three lines"))
    square = _built(parallelepiped(
        o, *[_arm_at(o, step, lines[1]) for step in directions],
        "the equilateral solid on the mean"))

    because(prop_XI_34, o, a, b, c)

    claim("the second solid is equilateral", "XI.Def.9",
          len2(o, square.vertices[1]) == len2(o, square.vertices[3])
          == len2(o, square.vertices[4]))
    claim("and it is equiangular with the first", "XI.Def.9",
          _solid_angle_of(o, tuple(square.vertices[index] for index in (1, 3, 4)))
          == _solid_angle_of(o, tuple(unequal.vertices[index] for index in (1, 3, 4))))
    claim("therefore the two solids are equal", "XI.36",
          content(unequal) == content(square))
    return Out(solids=(unequal, square), lines=lines)


@proposition("XI.37", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_37(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Four proportional straight lines carry similar parallelepipeds that are
    proportional, and conversely."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    ratio, apart = Fraction(3, 2), Fraction(5, 4)
    lines = (Fraction(1), ratio, apart, apart * ratio)
    hypothesis("the four straight lines are proportional",
               lines[0] * lines[3] == lines[1] * lines[2])

    directions = tuple(unit(vector_between(o, point)) for point in (a, b, c))

    def described(reach):
        return parallelepiped(o, *[_arm_at(o, step, reach) for step in directions])

    solids = [described(reach) for reach in lines]
    _built(solids[0])
    _built(solids[3])
    contents = [content(solid) for solid in solids]

    because(prop_XI_33, o, a, b, c)

    claim("the four solids are similar and similarly described", "XI.Def.9",
          all(_solid_angle_of(o, tuple(solid.vertices[i] for i in (1, 3, 4)))
              == _solid_angle_of(o, tuple(solids[0].vertices[i] for i in (1, 3, 4)))
              for solid in solids[1:]))
    claim("as the first solid is to the second, so is the third to the fourth",
          "XI.37", contents[0] * contents[3] == contents[1] * contents[2])
    # The converse is checked where it can fail: a fourth line that is not the
    # fourth proportional, and the solid on it, which the proportion must then
    # refuse. Each content is the cube on its line times one and the same
    # figure, so a proportion between the solids is one between the cubes.
    astray = lines[3] * Fraction(6, 5)
    claim("and a solid on any other line breaks the proportion, so solids "
          "proportional give lines proportional", "XI.37",
          lines[0] * astray != lines[1] * lines[2]
          and contents[0] * content(described(astray)) != contents[1] * contents[2])
    return Out(solids=tuple(solids), lines=lines)


@proposition("XI.38", THEOREM, sample=samples3.cube_corner)
def prop_XI_38(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """In a cube, the common section of the planes through the bisected sides of
    opposite faces, and the diameter, bisect one another."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    hypothesis("the solid is a cube, its edges equal and at right angles",
               len2(o, a) == len2(o, b) and len2(o, b) == len2(o, c)
               and dot3(vector_between(o, a), vector_between(o, b)) == 0
               and dot3(vector_between(o, b), vector_between(o, c)) == 0
               and dot3(vector_between(o, a), vector_between(o, c)) == 0)
    cube = _built(parallelepiped(o, a, b, c, "the cube"))
    corners = cube.vertices

    # Each plane is carried through the points bisecting the sides of one pair
    # of opposite faces. Two such planes are taken, as Euclid takes them.
    first = plane_through(midpoint_of(corners[0], corners[1]),
                          midpoint_of(corners[3], corners[2]),
                          midpoint_of(corners[4], corners[5]),
                          "the first plane through the points of section")
    second = plane_through(midpoint_of(corners[0], corners[3]),
                           midpoint_of(corners[1], corners[2]),
                           midpoint_of(corners[4], corners[7]),
                           "the second such plane")
    section = meet_planes(first, second)
    diameter = line3(corners[0], corners[6], "the diameter of the cube")

    # Where the common section leaves the cube, and where the diameter does:
    # the two segments whose bisection is the thing asserted.
    ends = (meet_line_plane(section, cube.face_plane(0)),
            meet_line_plane(section, cube.face_plane(1)))
    middle = posit3(midpoint_of(*ends), "S")

    claim("the common section of the two planes is a straight line", "XI.3",
          isinstance(section, Line3))
    claim("it meets the diameter", "XI.Def.7", on_line3(middle, diameter))
    claim("and the two bisect one another", "XI.38",
          middle == midpoint_of(corners[0], corners[6])
          and len2(ends[0], middle) == len2(middle, ends[1]))
    return Out(section=section, diameter=diameter, middle=middle)


@proposition("XI.39", THEOREM, sample=samples3.corner_and_arms)
def prop_XI_39(o: Point3, a: Point3, b: Point3, c: Point3) -> Out:
    """Two prisms of equal height, one on a parallelogram and one on a triangle
    double of it, are equal."""
    hypothesis("the three arms are not in one plane", not coplanar(o, a, b, c))
    # Both prisms are triangular, and both are taken as standing on the same
    # plane -- the one the first and third arms span. The first rests on a
    # parallelogram face of it, the second on a triangular one, which is the
    # whole of what the proposition compares.
    ground = plane_through(o, a, c, "the plane both stand on")
    on_parallelogram = _built(prism((o, a, b), vector_between(o, c),
                                    "the prism on the parallelogram"))
    on_triangle = _built(prism((o, a, c), vector_between(o, b),
                               "the prism on the triangle"))

    because(prop_XI_28, o, a, b, c)

    flat = _base_area(o, a, c)
    triangle = flat / 2
    claim("both prisms stand on that plane, the one on a parallelogram in it "
          "and the other on a triangle", "XI.Def.13",
          on_plane(o, ground) and on_plane(a, ground) and on_plane(c, ground)
          and on_plane(on_parallelogram.vertices[4], ground))
    claim("they are of the same height, the edge the first rises to and the "
          "face the second is carried to standing off the plane alike",
          "XI.Def.13",
          height_over(on_parallelogram.vertices[2], ground)
          == height_over(on_parallelogram.vertices[5], ground)
          == height_over(on_triangle.vertices[4], ground))
    claim("the parallelogram is double of the triangle, being cut by the "
          "diagonal into it and its equal", "I.41",
          triangle == _triangle_area(a, on_parallelogram.vertices[4], c)
          and flat == triangle + _triangle_area(a, on_parallelogram.vertices[4], c))
    claim("therefore the prisms are equal to one another", "XI.39",
          content(on_parallelogram) == content(on_triangle))
    return Out(prisms=(on_parallelogram, on_triangle))
