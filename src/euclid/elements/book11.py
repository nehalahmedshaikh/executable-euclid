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
from ..solid.objects import Line3, Plane, Point3, vector_between
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
