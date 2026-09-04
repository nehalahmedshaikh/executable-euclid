"""Book XII: content, and the method of exhaustion.

Ten of the eighteen propositions are about polygons, pyramids, prisms and
polyhedra.  Their content is a polynomial in the coordinates, so they are
checked outright: the figure is cut into tetrahedra and the pieces are added,
which is what :func:`euclid.solid.solids.content` does and all it does.

The other eight are about circles, cones, cylinders and spheres, whose measure
no straightedge and compass can name.  Nothing is posited about them.  What each
gets is Euclid's own inscribed and circumscribed figures at every stage --
exact, constructible solids -- and the two facts his reductio runs on: that the
enclosure holds the ratio he claims, and that it narrows past half its width
each time, which is X.1.  See :mod:`euclid.solid.exhaust`.  The passage to the
limit is not executed, because a limit is not a finite computation.

XII.1 and XII.2 are about plane figures, and are placed in a plane in space so
that the whole book stands on the one kernel the solid propositions need.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import sign, sqrt
from ..solid.angles import length3
from ..solid.construct import line3, plane_through, posit3, sphere_through
from ..solid.exhaust import (
    circle_bounds,
    cone_bounds,
    cylinder_bounds,
    inradius,
    polygon_area,
    polyhedron_in_sphere,
    regular_polygon,
    sphere_bounds,
    squeeze,
    turn,
)
from ..solid.objects import Point3, midpoint_of, vector_between
from ..solid.predicates import (
    collinear3,
    coplanar,
    cross3,
    dot3,
    inside_sphere,
    len2,
    on_plane,
    on_sphere,
    parallel_planes,
)
from ..solid.solids import (
    Solid,
    content,
    height_over,
    parallelogram_area,
    prism,
    pyramid,
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
from .book11 import prop_XI_33, prop_XI_34

__all__: list = []

# The stages the enclosures are run through: the square, the octagon, the
# sixteen-sided figure. Three is enough to see the width fall past half twice,
# which is what X.1 asks, and each stage doubles the work.
STAGES = (2, 3, 4)
# The polyhedra in a sphere grow far faster -- stage four already has a hundred
# and fourteen vertices -- so the sphere is squeezed through two stages.
GLOBE_STAGES = (2, 3)


def _drawn(solid: Solid) -> Solid:
    for vertex in solid.vertices:
        posit3(vertex)
    for start, end in solid.edges():
        line3(solid.vertices[start], solid.vertices[end])
    return solid


def _ring(corners: tuple, label: str = "") -> tuple:
    for corner in corners:
        posit3(corner)
    for position, corner in enumerate(corners):
        line3(corner, corners[(position + 1) % len(corners)], label)
    return corners


def _axis_of(base: tuple) -> tuple:
    """The direction at right angles to the plane three points describe."""
    return cross3(vector_between(base[0], base[1]), vector_between(base[0], base[2]))


@proposition("XII.1", THEOREM, sample=samples3.circle_in_space)
def prop_XII_1(o: Point3, a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Similar polygons inscribed in circles are to one another as the squares
    on the diameters."""
    hypothesis("the four points are on one circle about the centre",
               len2(o, a) == len2(o, b) == len2(o, c) == len2(o, d))
    hypothesis("they are not all in one straight line", not collinear3(a, b, c))
    _ring((a, b, c, d), "the polygon in the first circle")

    # The second circle and the polygon in it are the first carried over in one
    # ratio, which is what makes the figures similar and similarly inscribed.
    ratio = Fraction(5, 3)
    centre = posit3(Point3(o.x + 8, o.y, o.z), "P")
    carried = tuple(posit3(Point3(centre.x + ratio * (point.x - o.x),
                                  centre.y + ratio * (point.y - o.y),
                                  centre.z + ratio * (point.z - o.z)))
                    for point in (a, b, c, d))
    _ring(carried, "the polygon in the second circle")

    here, there = polygon_area((a, b, c, d)), polygon_area(carried)
    across, beyond = 4 * len2(o, a), 4 * len2(centre, carried[0])
    claim("the polygons are similar, their sides in one ratio", "VI.Def.1",
          all(len2(carried[i], carried[j]) == ratio * ratio * len2(one, other)
              for (i, j), (one, other) in
              zip(((0, 1), (1, 2), (2, 3), (3, 0)),
                  ((a, b), (b, c), (c, d), (d, a)))))
    claim("as the polygon is to the polygon, so is the square on the diameter "
          "to the square on the diameter", "XII.1", here * beyond == there * across)
    return Out(areas=(here, there), squares=(across, beyond))


@proposition("XII.2", THEOREM, sample=samples3.circle_in_space)
def prop_XII_2(o: Point3, a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Circles are to one another as the squares on their diameters."""
    hypothesis("the four points are on one circle about the centre",
               len2(o, a) == len2(o, b) == len2(o, c) == len2(o, d))
    hypothesis("they are not all in one straight line", not collinear3(a, b, c))
    because(prop_XII_1, o, a, b, c, d)

    normal = _axis_of((a, b, c))
    radius, ratio = length3(o, a), Fraction(5, 3)
    centre = posit3(Point3(o.x + 8, o.y, o.z), "P")
    for stage in STAGES:
        _ring(regular_polygon(o, radius, normal, stage))
        _ring(regular_polygon(centre, ratio * radius, normal, stage))

    squares = (4 * len2(o, a), 4 * ratio * ratio * len2(o, a))
    found = squeeze(
        lambda stage: (circle_bounds(o, radius, normal, stage)
                       / circle_bounds(centre, ratio * radius, normal, stage)),
        squares[0] / squares[1], STAGES)

    claim("at every stage the figures inscribed in the two circles are similar, "
          "so the enclosure holds the ratio of the squares on the diameters",
          "XII.1", found.held)
    claim("and what is left over falls short of half itself at each stage, so "
          "no other ratio can survive", "X.1", found.narrowing)
    claim("therefore the circles are to one another as the squares on the "
          "diameters", "XII.2", found.held and found.narrowing)
    return Out(enclosures=found.enclosures, squares=squares)


def _bisections(a: Point3, b: Point3, c: Point3, d: Point3) -> tuple:
    """The six midpoints of a pyramid's edges, in Euclid's order."""
    return (midpoint_of(a, b), midpoint_of(b, c), midpoint_of(c, a),
            midpoint_of(a, d), midpoint_of(d, b), midpoint_of(d, c))


def _divided(a: Point3, b: Point3, c: Point3, d: Point3) -> tuple:
    """XII.3's division: two pyramids at opposite corners and two prisms.

    The pyramids are the corners at *a* and at *d*, each on the triangle of
    midpoints next to it.  What is left is not one figure but two prisms, and
    the second is the first turned over -- each has a parallelogram face on the
    original pyramid's surface and an edge of midpoints opposite it.
    """
    e, f, g, h, k, ell = _bisections(a, b, c, d)
    return (pyramid((e, g, h), a, "the pyramid at the first corner"),
            pyramid((h, k, ell), d, "the pyramid at the opposite corner"),
            prism((e, g, h), vector_between(e, b), "the first prism"),
            prism((h, k, ell), vector_between(h, g), "the second prism"))


@proposition("XII.3", THEOREM, sample=samples3.polygon_base)
def prop_XII_3(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """A pyramid on a triangular base divides into two pyramids similar to the
    whole and two equal prisms, and the prisms are greater than half of it."""
    hypothesis("the four points are not in one plane", not coplanar(a, b, c, d))
    whole = _drawn(pyramid((a, b, c), d, "the pyramid"))
    first, second, one_prism, other_prism = _divided(a, b, c, d)
    for piece in (first, second, one_prism, other_prism):
        _drawn(piece)

    held = content(whole)
    e, f, g, h, k, ell = _bisections(a, b, c, d)
    claim("the two pyramids are equal to one another and similar to the whole, "
          "every edge of each being half the edge it answers to", "XI.Def.9",
          content(first) == content(second)
          and all(4 * len2(near, far) == len2(one, other) for near, far, one, other in
                  ((e, g, b, c), (g, h, c, d), (e, h, b, d),
                   (h, k, a, b), (k, ell, b, c), (h, ell, a, c))))
    claim("the pieces together make the whole pyramid", "XII.3",
          content(first) + content(second) + content(one_prism)
          + content(other_prism) == held)
    claim("the two prisms are equal to one another", "XI.39",
          content(one_prism) == content(other_prism))
    claim("and the two prisms together are greater than the half of the whole "
          "pyramid", "XII.3",
          sign(2 * (content(one_prism) + content(other_prism)) - held) > 0)
    return Out(pyramids=(first, second), prisms=(one_prism, other_prism),
               whole=whole)


@proposition("XII.4", THEOREM, sample=samples3.polygon_base)
def prop_XII_4(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Two pyramids of the same height on triangular bases, each divided as
    before: as base is to base, so are all the prisms to all the prisms."""
    hypothesis("the four points are not in one plane", not coplanar(a, b, c, d))
    first = _drawn(pyramid((a, b, c), d, "the first pyramid"))
    # A second pyramid of the same height on a wider base: the apex is carried
    # across so that it stands off the base plane by the same perpendicular.
    wider = tuple(posit3(Point3(a.x + 2 * (point.x - a.x), a.y + 2 * (point.y - a.y),
                                a.z + 2 * (point.z - a.z)), name)
                  for point, name in ((b, "P"), (c, "Q")))
    apex = posit3(Point3(d.x + (b.x - a.x), d.y + (b.y - a.y), d.z + (b.z - a.z)), "R")
    second = _drawn(pyramid((a, *wider), apex, "the second pyramid"))

    because(prop_XII_3, a, b, c, d)

    ground = plane_through(a, b, c, "the plane of the bases")
    bases = (parallelogram_area(vector_between(a, b), vector_between(a, c)) / 2,
             parallelogram_area(vector_between(a, wider[0]),
                                vector_between(a, wider[1])) / 2)
    prisms = [sum((content(piece) for piece in _divided(*corners)[2:]), Fraction(0))
              for corners in ((a, b, c, d), (a, wider[0], wider[1], apex))]

    claim("the two pyramids are of the same height", "XI.Def.9",
          on_plane(a, ground) and on_plane(wider[0], ground)
          and on_plane(wider[1], ground)
          and dot3(ground.normal(), vector_between(d, apex)) == 0)
    claim("as the base is to the base, so are all the prisms in the one to all "
          "the prisms in the other", "XII.4",
          bases[0] * prisms[1] == bases[1] * prisms[0])
    return Out(bases=bases, prisms=tuple(prisms))


@proposition("XII.5", THEOREM, sample=samples3.polygon_base)
def prop_XII_5(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Pyramids of the same height on triangular bases are to one another as
    their bases."""
    hypothesis("the four points are not in one plane", not coplanar(a, b, c, d))
    first = _drawn(pyramid((a, b, c), d, "the first pyramid"))
    wider = tuple(posit3(Point3(a.x + 2 * (point.x - a.x), a.y + 2 * (point.y - a.y),
                                a.z + 2 * (point.z - a.z)), name)
                  for point, name in ((b, "P"), (c, "Q")))
    apex = posit3(Point3(d.x + (b.x - a.x), d.y + (b.y - a.y), d.z + (b.z - a.z)), "R")
    second = _drawn(pyramid((a, *wider), apex, "the second pyramid"))

    because(prop_XII_4, a, b, c, d)

    ground = plane_through(a, b, c, "the plane of the bases")
    bases = (parallelogram_area(vector_between(a, b), vector_between(a, c)) / 2,
             parallelogram_area(vector_between(a, wider[0]),
                                vector_between(a, wider[1])) / 2)
    claim("the two pyramids are of the same height", "XI.Def.9",
          dot3(ground.normal(), vector_between(d, apex)) == 0)
    claim("as the base is to the base, so is the pyramid to the pyramid",
          "XII.5", bases[0] * content(second) == bases[1] * content(first))
    return Out(pyramids=(first, second), bases=bases)


@proposition("XII.6", THEOREM, sample=samples3.polygon_base)
def prop_XII_6(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Pyramids of the same height on polygonal bases are to one another as
    their bases."""
    hypothesis("the four points are not in one plane", not coplanar(a, b, c, d))
    # A four-sided base, which is two triangles: XII.6 is XII.5 carried to any
    # polygon by dividing the base into the triangles XII.5 already answers for.
    corner = posit3(Point3(b.x + (c.x - a.x), b.y + (c.y - a.y), b.z + (c.z - a.z)), "P")
    base = (a, b, corner, c)
    first = _drawn(pyramid(base, d, "the pyramid on the polygon"))
    wider = tuple(Point3(a.x + 2 * (point.x - a.x), a.y + 2 * (point.y - a.y),
                         a.z + 2 * (point.z - a.z)) for point in base)
    apex = posit3(Point3(d.x + (b.x - a.x), d.y + (b.y - a.y), d.z + (b.z - a.z)), "R")
    second = _drawn(pyramid(wider, apex, "the second such pyramid"))

    because(prop_XII_5, a, b, c, d)

    bases = (polygon_area(base), polygon_area(wider))
    pieces = (content(pyramid((a, b, corner), d)) + content(pyramid((a, corner, c), d)))
    claim("the pyramid on the polygon is the pyramids on the triangles it "
          "divides into", "XII.5", pieces == content(first))
    claim("as the base is to the base, so is the pyramid to the pyramid",
          "XII.6", bases[0] * content(second) == bases[1] * content(first))
    return Out(pyramids=(first, second), bases=bases)


@proposition("XII.7", THEOREM, sample=samples3.polygon_base)
def prop_XII_7(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """A prism on a triangular base divides into three equal pyramids on
    triangular bases."""
    hypothesis("the four points are not in one plane", not coplanar(a, b, c, d))
    step = vector_between(a, d)
    whole = _drawn(prism((a, b, c), step, "the prism"))
    top = whole.vertices[3:]
    pieces = (pyramid((a, b, c), top[0], "the first pyramid"),
              pyramid((b, c, top[0]), top[2], "the second"),
              pyramid((b, top[0], top[1]), top[2], "the third"))
    for piece in pieces:
        _drawn(piece)

    because(prop_XII_5, a, b, c, d)

    held = [content(piece) for piece in pieces]
    claim("the three pyramids have triangular bases", "XI.Def.12",
          all(len(piece.faces) == 4 for piece in pieces))
    claim("they are equal to one another", "XII.7", held[0] == held[1] == held[2])
    claim("and together they are the prism", "XII.7",
          held[0] + held[1] + held[2] == content(whole))
    return Out(pyramids=pieces, prism=whole)


@proposition("XII.8", THEOREM, sample=samples3.polygon_base)
def prop_XII_8(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """Similar pyramids on triangular bases are in the triplicate ratio of
    their corresponding sides."""
    hypothesis("the four points are not in one plane", not coplanar(a, b, c, d))
    first = _drawn(pyramid((a, b, c), d, "the first pyramid"))
    scale = Fraction(3, 2)
    carried = tuple(posit3(Point3(a.x + scale * (point.x - a.x),
                                  a.y + scale * (point.y - a.y),
                                  a.z + scale * (point.z - a.z)), name)
                    for point, name in ((b, "P"), (c, "Q"), (d, "R")))
    second = _drawn(pyramid((a, carried[0], carried[1]), carried[2],
                            "the similar pyramid"))

    because(prop_XI_33, a, b, c, d)

    side, answering = length3(a, b), length3(a, carried[0])
    claim("the pyramids are similar, their edges in one ratio", "XI.Def.9",
          all(len2(a, far) == scale * scale * len2(a, near)
              for near, far in zip((b, c, d), carried)))
    claim("as the pyramid is to the pyramid, so is the cube on the side to the "
          "cube on the answering side", "XII.8",
          content(first) * answering * answering * answering
          == content(second) * side * side * side)
    return Out(pyramids=(first, second), sides=(side, answering))


@proposition("XII.9", THEOREM, sample=samples3.polygon_base)
def prop_XII_9(a: Point3, b: Point3, c: Point3, d: Point3) -> Out:
    """In equal pyramids on triangular bases the bases are reciprocally
    proportional to the heights, and conversely."""
    hypothesis("the four points are not in one plane", not coplanar(a, b, c, d))
    first = _drawn(pyramid((a, b, c), d, "the first pyramid"))
    # A second pyramid equal to the first, its base doubled and its height
    # halved: the reciprocation the proposition is about, made rather than found.
    wider = posit3(Point3(a.x + 2 * (b.x - a.x), a.y + 2 * (b.y - a.y),
                          a.z + 2 * (b.z - a.z)), "P")
    ground = plane_through(a, b, c, "the plane of the bases")
    lower = posit3(midpoint_of(_foot(d, ground), d), "R")
    second = _drawn(pyramid((a, wider, c), lower, "the second pyramid"))

    because(prop_XI_34, a, b, c, d)

    bases = (parallelogram_area(vector_between(a, b), vector_between(a, c)) / 2,
             parallelogram_area(vector_between(a, wider), vector_between(a, c)) / 2)
    heights = (height_over(d, ground), height_over(lower, ground))
    claim("the two pyramids are equal", "XII.5",
          content(first) == content(second))
    claim("so as the base is to the base, so is the height to the height "
          "reciprocally", "XII.9", bases[0] * heights[0] == bases[1] * heights[1])
    claim("and pyramids whose bases are reciprocally proportional to their "
          "heights are equal", "XII.9",
          3 * content(first) == bases[0] * heights[0]
          and 3 * content(second) == bases[1] * heights[1])
    return Out(pyramids=(first, second), bases=bases, heights=heights)


def _foot(point: Point3, plane) -> Point3:
    normal = plane.normal()
    step = plane.evaluate(point) / dot3(normal, normal)
    return Point3(point.x - step * normal[0], point.y - step * normal[1],
                  point.z - step * normal[2])


def _cone_figure(centre: Point3, edge: Point3, apex: Point3) -> tuple:
    radius = length3(centre, edge)
    axis = vector_between(centre, apex)
    return radius, axis


@proposition("XII.10", THEOREM, sample=samples3.cone_figure)
def prop_XII_10(o: Point3, a: Point3, d: Point3) -> Out:
    """Any cone is a third part of the cylinder on the same base and of the
    same height."""
    hypothesis("the axis stands at right angles to the base, so the cone is a "
               "right one", dot3(vector_between(o, a), vector_between(o, d)) == 0)
    hypothesis("the base has a positive radius and the height is not nothing",
               o != a and o != d)
    radius, axis = _cone_figure(o, a, d)
    line3(o, a, "the radius of the base")
    line3(o, d, "the axis")
    for stage in STAGES:
        _drawn(pyramid(regular_polygon(o, radius, axis, stage), d))
        _drawn(prism(regular_polygon(o, radius, axis, stage), axis))

    aside = Point3(o.x + axis[1] * (a.z - o.z) - axis[2] * (a.y - o.y),
                   o.y + axis[2] * (a.x - o.x) - axis[0] * (a.z - o.z),
                   o.z + axis[0] * (a.y - o.y) - axis[1] * (a.x - o.x))
    because(prop_XII_7, o, a, aside, d)

    found = squeeze(lambda stage: (cone_bounds(o, radius, d, stage)
                                   / cylinder_bounds(o, radius, axis, stage)),
                    Fraction(1, 3), STAGES)
    claim("at every stage the pyramid in the cone is a third of the prism in "
          "the cylinder, so the enclosure holds a third", "XII.7", found.held)
    claim("and what is left over falls short of half itself at each stage",
          "X.1", found.narrowing)
    claim("therefore the cone is a third part of the cylinder", "XII.10",
          found.held and found.narrowing)
    return Out(enclosures=found.enclosures)


@proposition("XII.11", THEOREM, sample=samples3.cone_figure)
def prop_XII_11(o: Point3, a: Point3, d: Point3) -> Out:
    """Cones and cylinders of the same height are to one another as their
    bases."""
    hypothesis("the axis stands at right angles to the base",
               dot3(vector_between(o, a), vector_between(o, d)) == 0)
    hypothesis("the base has a positive radius and the height is not nothing",
               o != a and o != d)
    radius, axis = _cone_figure(o, a, d)
    ratio = Fraction(3, 2)
    centre = posit3(Point3(o.x + 9 * (a.x - o.x), o.y + 9 * (a.y - o.y),
                           o.z + 9 * (a.z - o.z)), "P")
    apex = posit3(Point3(centre.x + axis[0], centre.y + axis[1],
                         centre.z + axis[2]), "Q")
    line3(o, d, "the first axis")
    line3(centre, apex, "the second axis, equal to it")
    for stage in STAGES:
        _ring(regular_polygon(o, radius, axis, stage))
        _ring(regular_polygon(centre, ratio * radius, axis, stage))

    because(prop_XII_2, o, *regular_polygon(o, radius, axis, 2))

    bases = (len2(o, a), ratio * ratio * len2(o, a))
    found = squeeze(lambda stage: (cone_bounds(o, radius, d, stage)
                                   / cone_bounds(centre, ratio * radius, apex, stage)),
                    bases[0] / bases[1], STAGES)
    cylinders = squeeze(lambda stage: (cylinder_bounds(o, radius, axis, stage)
                                       / cylinder_bounds(centre, ratio * radius,
                                                         axis, stage)),
                        bases[0] / bases[1], STAGES)
    claim("the enclosure of each ratio holds the ratio of the bases", "XII.2",
          found.held and cylinders.held)
    claim("and what is left over falls short of half itself at each stage",
          "X.1", found.narrowing and cylinders.narrowing)
    claim("therefore cones and cylinders of the same height are as their bases",
          "XII.11", found.held and cylinders.held)
    return Out(cones=found.enclosures, cylinders=cylinders.enclosures, bases=bases)


@proposition("XII.12", THEOREM, sample=samples3.cone_figure)
def prop_XII_12(o: Point3, a: Point3, d: Point3) -> Out:
    """Similar cones and cylinders are to one another in the triplicate ratio of
    the diameters of their bases."""
    hypothesis("the axis stands at right angles to the base",
               dot3(vector_between(o, a), vector_between(o, d)) == 0)
    hypothesis("the base has a positive radius and the height is not nothing",
               o != a and o != d)
    radius, axis = _cone_figure(o, a, d)
    ratio = Fraction(3, 2)
    centre = posit3(Point3(o.x + 9 * (a.x - o.x), o.y + 9 * (a.y - o.y),
                           o.z + 9 * (a.z - o.z)), "P")
    # Similar: the height is enlarged in the same ratio as the base, which is
    # what XI Def. 24 asks of two cones cut from similar triangles.
    taller = tuple(ratio * component for component in axis)
    apex = posit3(Point3(centre.x + taller[0], centre.y + taller[1],
                         centre.z + taller[2]), "Q")
    line3(o, d, "the first axis")
    line3(centre, apex, "the second axis")
    for stage in STAGES:
        _ring(regular_polygon(o, radius, axis, stage))
        _ring(regular_polygon(centre, ratio * radius, axis, stage))

    found = squeeze(lambda stage: (cone_bounds(o, radius, d, stage)
                                   / cone_bounds(centre, ratio * radius, apex, stage)),
                    1 / (ratio * ratio * ratio), STAGES)
    cylinders = squeeze(lambda stage: (cylinder_bounds(o, radius, axis, stage)
                                       / cylinder_bounds(centre, ratio * radius,
                                                         taller, stage)),
                        1 / (ratio * ratio * ratio), STAGES)
    claim("the cones are similar, base and height enlarged in one ratio",
          "XI.Def.24",
          length3(centre, apex) == ratio * length3(o, d))
    claim("the enclosure of each ratio holds the triplicate ratio of the "
          "diameters", "XII.11", found.held and cylinders.held)
    claim("and what is left over falls short of half itself at each stage",
          "X.1", found.narrowing and cylinders.narrowing)
    claim("therefore similar cones and cylinders are in the triplicate ratio of "
          "the diameters of their bases", "XII.12",
          found.held and cylinders.held)
    return Out(cones=found.enclosures, cylinders=cylinders.enclosures)


@proposition("XII.13", THEOREM, sample=samples3.cone_figure)
def prop_XII_13(o: Point3, a: Point3, d: Point3) -> Out:
    """A cylinder cut by a plane parallel to its bases: as cylinder is to
    cylinder, so is the axis to the axis."""
    hypothesis("the axis stands at right angles to the base",
               dot3(vector_between(o, a), vector_between(o, d)) == 0)
    hypothesis("the base has a positive radius and the height is not nothing",
               o != a and o != d)
    radius, axis = _cone_figure(o, a, d)
    part = Fraction(2, 5)
    cut = posit3(Point3(o.x + part * axis[0], o.y + part * axis[1],
                        o.z + part * axis[2]), "P")
    sideways = vector_between(o, a)
    other = cross3(axis, sideways)
    ground = plane_through(o, a, Point3(o.x + other[0], o.y + other[1],
                                        o.z + other[2]), "the plane of the base")
    cutter = plane_through(cut,
                           Point3(cut.x + sideways[0], cut.y + sideways[1],
                                  cut.z + sideways[2]),
                           Point3(cut.x + other[0], cut.y + other[1],
                                  cut.z + other[2]), "the cutting plane")
    line3(o, d, "the axis")
    line3(o, a, "the radius of the base")
    for stage in STAGES:
        _drawn(prism(regular_polygon(o, radius, axis, stage), axis))

    nearer = tuple(part * component for component in axis)
    beyond = tuple((1 - part) * component for component in axis)
    found = squeeze(lambda stage: (cylinder_bounds(o, radius, nearer, stage)
                                   / cylinder_bounds(cut, radius, beyond, stage)),
                    part / (1 - part), STAGES)
    claim("the cutting plane is parallel to the bases", "XI.14",
          parallel_planes(cutter, ground) and cutter != ground)
    claim("the enclosure holds the ratio of the axes at every stage", "XII.11",
          found.held)
    claim("and what is left over falls short of half itself at each stage",
          "X.1", found.narrowing)
    claim("therefore as the cylinder is to the cylinder, so is the axis to the "
          "axis", "XII.13", found.held and found.narrowing)
    return Out(enclosures=found.enclosures, cut=cut)


@proposition("XII.14", THEOREM, sample=samples3.cone_figure)
def prop_XII_14(o: Point3, a: Point3, d: Point3) -> Out:
    """Cones and cylinders on equal bases are to one another as their heights."""
    hypothesis("the axis stands at right angles to the base",
               dot3(vector_between(o, a), vector_between(o, d)) == 0)
    hypothesis("the base has a positive radius and the height is not nothing",
               o != a and o != d)
    radius, axis = _cone_figure(o, a, d)
    ratio = Fraction(7, 4)
    centre = posit3(Point3(o.x + 9 * (a.x - o.x), o.y + 9 * (a.y - o.y),
                           o.z + 9 * (a.z - o.z)), "P")
    taller = tuple(ratio * component for component in axis)
    apex = posit3(Point3(centre.x + taller[0], centre.y + taller[1],
                         centre.z + taller[2]), "Q")
    line3(o, d, "the first axis")
    line3(centre, apex, "the second axis")
    for stage in STAGES:
        _ring(regular_polygon(o, radius, axis, stage))
        _ring(regular_polygon(centre, radius, axis, stage))

    because(prop_XII_13, o, a, d)

    found = squeeze(lambda stage: (cylinder_bounds(o, radius, axis, stage)
                                   / cylinder_bounds(centre, radius, taller, stage)),
                    1 / ratio, STAGES)
    cones = squeeze(lambda stage: (cone_bounds(o, radius, d, stage)
                                   / cone_bounds(centre, radius, apex, stage)),
                    1 / ratio, STAGES)
    claim("the two bases are equal, the figures inscribed in them at every "
          "stage being equal", "XII.2",
          all(polygon_area(regular_polygon(o, radius, axis, stage))
              == polygon_area(regular_polygon(centre, radius, axis, stage))
              for stage in STAGES))
    claim("the enclosure holds the ratio of the heights at every stage",
          "XII.13", found.held and cones.held)
    claim("and what is left over falls short of half itself at each stage",
          "X.1", found.narrowing and cones.narrowing)
    claim("therefore cones and cylinders on equal bases are as their heights",
          "XII.14", found.held and cones.held)
    return Out(cylinders=found.enclosures, cones=cones.enclosures)


@proposition("XII.15", THEOREM, sample=samples3.cone_figure)
def prop_XII_15(o: Point3, a: Point3, d: Point3) -> Out:
    """In equal cones and cylinders the bases are reciprocally proportional to
    the heights, and conversely."""
    hypothesis("the axis stands at right angles to the base",
               dot3(vector_between(o, a), vector_between(o, d)) == 0)
    hypothesis("the base has a positive radius and the height is not nothing",
               o != a and o != d)
    radius, axis = _cone_figure(o, a, d)
    # The base doubled in area is the radius taken in the ratio of the side of
    # the square on two, and the height halved answers it: so the two cylinders
    # are equal, and reciprocally proportional is what they are.
    spread = sqrt(Fraction(2))
    centre = posit3(Point3(o.x + 9 * (a.x - o.x), o.y + 9 * (a.y - o.y),
                           o.z + 9 * (a.z - o.z)), "P")
    lower = tuple(component / 2 for component in axis)
    top = posit3(Point3(centre.x + lower[0], centre.y + lower[1],
                        centre.z + lower[2]), "Q")
    line3(o, d, "the first axis")
    line3(centre, top, "the second axis")
    for stage in STAGES:
        _ring(regular_polygon(o, radius, axis, stage))
        _ring(regular_polygon(centre, spread * radius, axis, stage))

    because(prop_XII_14, o, a, d)

    bases = (len2(o, a), 2 * len2(o, a))
    heights = (length3(o, d), length3(o, d) / 2)
    found = squeeze(lambda stage: (cylinder_bounds(o, radius, axis, stage)
                                   / cylinder_bounds(centre, spread * radius,
                                                     lower, stage)),
                    Fraction(1), STAGES)
    claim("the bases are reciprocally proportional to the heights", "XII.15",
          bases[0] * heights[0] == bases[1] * heights[1])
    claim("the enclosure of the ratio of the two cylinders holds unity at every "
          "stage, so they are equal", "XII.14", found.held)
    claim("and what is left over falls short of half itself at each stage",
          "X.1", found.narrowing)
    claim("therefore equal cones and cylinders have their bases reciprocally "
          "proportional to their heights, and conversely", "XII.15",
          found.held and found.narrowing)
    return Out(enclosures=found.enclosures, bases=bases, heights=heights)


@proposition("XII.16", CONSTRUCTION, sample=samples3.two_radii)
def prop_XII_16(o: Point3, a: Point3, b: Point3) -> Out:
    """In the greater of two circles about one centre, inscribe an equilateral
    polygon with an even number of sides that does not touch the lesser."""
    hypothesis("the two circles are about one centre, and one is the greater",
               sign(len2(o, a) - len2(o, b)) > 0)
    hypothesis("the lesser circle has a positive radius", o != b)
    hypothesis("the two radii describe the plane the circles are in",
               not collinear3(o, a, b))
    greater, lesser = length3(o, a), length3(o, b)
    normal = _axis_of((o, a, b))
    line3(o, a, "the radius of the greater circle")
    line3(o, b, "the radius of the lesser")

    # Bisecting again and again carries the side of the figure past the lesser
    # circle: the perpendicular from the centre to a side is the radius times
    # the cosine of half the angle, and that rises to the radius.
    stage = 2
    while stage < 12 and sign(greater * turn(stage + 1)[0] - lesser) <= 0:
        stage += 1
    corners = _ring(regular_polygon(o, greater, normal, stage),
                    "the polygon inscribed")

    apothem = greater * turn(stage + 1)[0]
    claim("the polygon has an even number of sides", "XII.16",
          len(corners) % 2 == 0 and len(corners) >= 4)
    claim("it is equilateral, and inscribed in the greater circle", "IV.6",
          len({len2(corners[i], corners[(i + 1) % len(corners)])
               for i in range(len(corners))}) == 1
          and all(len2(o, corner) == len2(o, a) for corner in corners))
    claim("and no side of it touches the lesser circle", "XII.16",
          sign(apothem - lesser) > 0)
    return Out(polygon=corners, stage=stage)


@proposition("XII.17", CONSTRUCTION, sample=samples3.two_radii)
def prop_XII_17(o: Point3, a: Point3, b: Point3) -> Out:
    """In the greater of two spheres about one centre, inscribe a polyhedron
    that does not touch the lesser at its surface."""
    hypothesis("the two spheres are about one centre, and one is the greater",
               sign(len2(o, a) - len2(o, b)) > 0)
    hypothesis("the lesser sphere has a positive radius", o != b)
    greater, lesser = length3(o, a), length3(o, b)
    outer = sphere_through(o, a, "the greater sphere")
    inner = sphere_through(o, b, "the lesser sphere")

    because(prop_XII_16, o, a, b)

    stage = 2
    while stage < 5:
        solid = polyhedron_in_sphere(o, greater, stage)
        if sign(inradius(solid, o) - lesser) > 0:
            break
        stage += 1
    _drawn(solid)

    claim("every vertex of the polyhedron is on the greater sphere", "XI.Def.14",
          all(on_sphere(vertex, outer) for vertex in solid.vertices))
    claim("every vertex stands outside the lesser sphere", "XI.Def.14",
          not any(inside_sphere(vertex, inner) for vertex in solid.vertices))
    claim("and no face of it touches the lesser sphere, the least perpendicular "
          "from the centre to a face being greater than its radius", "XII.17",
          sign(inradius(solid, o) - lesser) > 0)
    return Out(polyhedron=solid, stage=stage)


@proposition("XII.18", THEOREM, sample=samples3.two_radii)
def prop_XII_18(o: Point3, a: Point3, b: Point3) -> Out:
    """Spheres are to one another in the triplicate ratio of their diameters."""
    hypothesis("the two spheres are about one centre, and one is the greater",
               sign(len2(o, a) - len2(o, b)) > 0)
    hypothesis("the lesser sphere has a positive radius", o != b)
    greater, lesser = length3(o, a), length3(o, b)
    sphere_through(o, a, "the greater sphere")
    sphere_through(o, b, "the lesser sphere")
    line3(o, a, "the radius of the greater")
    line3(o, b, "the radius of the lesser")

    because(prop_XII_17, o, a, b)

    for stage in GLOBE_STAGES:
        _drawn(polyhedron_in_sphere(o, greater, stage))

    ratio = greater / lesser
    found = squeeze(lambda stage: (sphere_bounds(o, greater, stage)
                                   / sphere_bounds(o, lesser, stage)),
                    ratio * ratio * ratio, GLOBE_STAGES)
    claim("the polyhedra inscribed in the two spheres are similar, so at every "
          "stage the enclosure holds the triplicate ratio of the diameters",
          "XII.17", found.held)
    claim("and what is left over falls short of half itself at each stage",
          "X.1", found.narrowing)
    claim("therefore the spheres are to one another in the triplicate ratio of "
          "their diameters", "XII.18", found.held and found.narrowing)
    return Out(enclosures=found.enclosures, ratio=ratio)
