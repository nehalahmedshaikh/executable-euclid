"""The method of exhaustion, executed.

Eight of Book XII's propositions are about circles, cones, cylinders and
spheres, and none of those magnitudes can be named by straightedge and compass.
Positing that a cone is a third of its cylinder would assume XII.10, so nothing
is posited.  What the book gets instead is what Euclid gives it: an inscribed
figure and a circumscribed one at every stage, both of them exact constructible
solids, and the magnitude somewhere between.

A stage is a regular figure on ``2^k`` sides, so every vertex is reached by
bisecting an angle already in hand and every bound stays in the field the figure
was built in.  :class:`Bounds` is that enclosure, and :func:`squeeze` checks the
two things Euclid's argument turns on, both exactly:

* the enclosure holds the claimed ratio at every stage, so no stage refutes it;
* the enclosure narrows past half its width each time, which is X.1's criterion
  and the engine of every proof in the book.

The passage to the limit stays unexecuted.  A limit is not a finite computation
and no amount of machinery makes it one; what is executed is the argument that
Euclid actually writes down, which is the reductio these two facts feed.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Callable, Sequence

from ..kernel.field import Constructible, sign, sqrt
from .objects import Point3, vector_between
from .predicates import cross3, dot3
from .solids import (
    Solid,
    content,
    height_over,
    parallelogram_area,
    prism,
    pyramid,
    unit,
)

__all__ = [
    "Bounds",
    "Squeeze",
    "circle_bounds",
    "cone_bounds",
    "cylinder_bounds",
    "inradius",
    "polygon_area",
    "polyhedron_in_sphere",
    "regular_polygon",
    "sphere_bounds",
    "squeeze",
    "turn",
]


class Bounds:
    """An exact enclosure: the magnitude is at least ``lower`` and at most ``upper``.

    Every arithmetic operation is the one that keeps the enclosure honest --
    a product of enclosures of positive magnitudes runs from the product of the
    lower bounds to the product of the uppers, and a quotient reverses the
    divisor.  Nothing here ever narrows an enclosure by a step it cannot justify.
    """

    __slots__ = ("lower", "upper")

    def __init__(self, lower: Constructible, upper: Constructible) -> None:
        if sign(upper - lower) < 0:
            raise ValueError("an enclosure cannot end before it begins")
        self.lower, self.upper = lower, upper

    def width(self) -> Constructible:
        return self.upper - self.lower

    def contains(self, value: Constructible) -> bool:
        return sign(value - self.lower) >= 0 and sign(self.upper - value) >= 0

    def __mul__(self, factor) -> "Bounds":
        if isinstance(factor, Bounds):
            return Bounds(self.lower * factor.lower, self.upper * factor.upper)
        if sign(factor) < 0:
            return Bounds(self.upper * factor, self.lower * factor)
        return Bounds(self.lower * factor, self.upper * factor)

    __rmul__ = __mul__

    def __truediv__(self, other: "Bounds") -> "Bounds":
        """The enclosure of the ratio: least over greatest, greatest over least."""
        if sign(other.lower) <= 0:
            raise ValueError("a ratio needs a divisor known to be positive")
        return Bounds(self.lower / other.upper, self.upper / other.lower)

    def __repr__(self) -> str:
        return f"Bounds({self.lower}, {self.upper})"


# The cosine and sine of the angle a regular figure on 2^k sides subtends at the
# centre, got by bisecting the right angle over and over. Each bisection is one
# square root of a quantity already in hand, which is what makes every vertex of
# every stage constructible.
#
# Nothing is remembered between calls.  A constructible number belongs to the
# field tower that built it and cannot be combined with another's, and every
# proposition runs in its own tower, so a cache across them would hand back a
# value from a tower that has nothing to do with the figure in hand.
def turn(stage: int) -> tuple:
    """``cos`` and ``sin`` of ``2 pi / 2^stage``, exactly."""
    if stage < 2:
        raise ValueError("the first regular figure is the square")
    cosine, sine = Fraction(0), Fraction(1)
    for _ in range(stage - 2):
        cosine, sine = sqrt((1 + cosine) / 2), sqrt((1 - cosine) / 2)
    return cosine, sine


def _frame_in_plane(normal: tuple) -> tuple:
    """Two directions of unit length in the plane with the given normal."""
    for axis in ((Fraction(1), Fraction(0), Fraction(0)),
                 (Fraction(0), Fraction(1), Fraction(0)),
                 (Fraction(0), Fraction(0), Fraction(1))):
        across = cross3(normal, axis)
        if sign(dot3(across, across)) > 0:
            first = unit(across)
            return first, unit(cross3(normal, first))
    raise ValueError("a plane needs a normal that is not the zero vector")


def regular_polygon(centre: Point3, radius: Constructible, normal: tuple,
                    stage: int, circumscribed: bool = False) -> tuple:
    """The regular figure on ``2^stage`` sides, in the plane through the centre.

    Inscribed, its vertices are on the circle.  Circumscribed, its sides touch
    the circle, so its vertices stand out by the secant of half the angle and
    are turned by half the angle -- the same figure read the other way about,
    and the one Euclid circumscribes.
    """
    sides = 2 ** stage
    cosine, sine = turn(stage)
    first, second = _frame_in_plane(normal)
    if circumscribed:
        half_cos, half_sin = turn(stage + 1)
        reach = radius / half_cos
        start = (half_cos, half_sin)
    else:
        reach = radius
        start = (Fraction(1), Fraction(0))
    corners, (along, across) = [], start
    for _ in range(sides):
        corners.append(Point3(
            centre.x + reach * (along * first[0] + across * second[0]),
            centre.y + reach * (along * first[1] + across * second[1]),
            centre.z + reach * (along * first[2] + across * second[2])))
        along, across = along * cosine - across * sine, along * sine + across * cosine
    return tuple(corners)


def polygon_area(corners: Sequence[Point3]) -> Constructible:
    """The area of a figure, by cutting it into triangles from one vertex.

    No formula: the figure is divided and the pieces are added, which is how
    every area in the *Elements* is got.
    """
    total = Fraction(0)
    for position in range(1, len(corners) - 1):
        total = total + parallelogram_area(
            vector_between(corners[0], corners[position]),
            vector_between(corners[0], corners[position + 1])) / 2
    return total


def circle_bounds(centre: Point3, radius: Constructible, normal: tuple,
                  stage: int) -> Bounds:
    """The circle's area, enclosed between the figures of the given stage."""
    return Bounds(polygon_area(regular_polygon(centre, radius, normal, stage)),
                  polygon_area(regular_polygon(centre, radius, normal, stage,
                                               circumscribed=True)))


def cone_bounds(centre: Point3, radius: Constructible, apex: Point3,
                stage: int) -> Bounds:
    """The cone's content, enclosed between the pyramids of the given stage.

    The pyramids are built and their content is got by cutting them up, the way
    :func:`euclid.solid.solids.content` gets every content -- so this encloses
    the cone without ever being told what a cone holds.
    """
    normal = vector_between(centre, apex)
    return Bounds(
        content(pyramid(regular_polygon(centre, radius, normal, stage), apex)),
        content(pyramid(regular_polygon(centre, radius, normal, stage,
                                        circumscribed=True), apex)))


def cylinder_bounds(centre: Point3, radius: Constructible, axis: tuple,
                    stage: int) -> Bounds:
    """The cylinder's content, enclosed between the prisms of the given stage."""
    return Bounds(
        content(prism(regular_polygon(centre, radius, axis, stage), axis)),
        content(prism(regular_polygon(centre, radius, axis, stage,
                                      circumscribed=True), axis)))


def polyhedron_in_sphere(centre: Point3, radius: Constructible, stage: int) -> Solid:
    """A polyhedron inscribed in a sphere, on the stage's figure both ways round.

    Its vertices are the points where the parallels through one regular figure's
    divisions meet the meridians through another's, so every one of them is on
    the sphere and every one is constructible.  The faces are triangles, because
    four points so placed are in general not in one plane and a face must be.
    """
    rings, spokes = 2 ** (stage - 1), 2 ** stage
    cosine, sine = turn(stage)
    lifts = []
    height, reach = Fraction(1), Fraction(0)
    for _ in range(2 ** stage):
        lifts.append((height, reach))
        height, reach = height * cosine - reach * sine, height * sine + reach * cosine
    poles = (Point3(centre.x, centre.y, centre.z + radius),
             Point3(centre.x, centre.y, centre.z - radius))
    vertices, faces = list(poles), []
    for ring in range(1, rings):
        height, reach = lifts[ring]
        for spoke in range(spokes):
            along, across = _spin(cosine, sine, spoke)
            vertices.append(Point3(centre.x + radius * reach * along,
                                   centre.y + radius * reach * across,
                                   centre.z + radius * height))
    def at(ring: int, spoke: int) -> int:
        return 2 + (ring - 1) * spokes + spoke % spokes

    for spoke in range(spokes):
        faces.append((0, at(1, spoke), at(1, spoke + 1)))
        faces.append((1, at(rings - 1, spoke + 1), at(rings - 1, spoke)))
    for ring in range(1, rings - 1):
        for spoke in range(spokes):
            here, onward = at(ring, spoke), at(ring, spoke + 1)
            below, beyond = at(ring + 1, spoke), at(ring + 1, spoke + 1)
            faces.append((here, onward, beyond))
            faces.append((here, beyond, below))
    return Solid(vertices, faces, "the polyhedron in the sphere")


def _spin(cosine: Constructible, sine: Constructible, times: int) -> tuple:
    along, across = Fraction(1), Fraction(0)
    for _ in range(times):
        along, across = along * cosine - across * sine, along * sine + across * cosine
    return along, across


def inradius(solid: Solid, centre: Point3) -> Constructible:
    """The least distance from a point inside to any of the bounding planes."""
    least = None
    for index in range(len(solid.faces)):
        reach = height_over(centre, solid.face_plane(index))
        if least is None or sign(reach - least) < 0:
            least = reach
    return least


def sphere_bounds(centre: Point3, radius: Constructible, stage: int) -> Bounds:
    """The sphere's content, enclosed between two similar polyhedra.

    The inner one has its vertices on the sphere (XII.17's figure).  The outer
    one is that same polyhedron enlarged about the centre until the planes that
    bound it stand off by the radius, so the sphere is inside it -- similar and
    similarly situated, which is what makes the two ends of the enclosure move
    together as the stage rises.
    """
    inner = polyhedron_in_sphere(centre, radius, stage)
    held = content(inner)
    spread = radius / inradius(inner, centre)
    return Bounds(held, held * spread * spread * spread)


class Squeeze:
    """What running Euclid's argument through the stages found."""

    __slots__ = ("stages", "enclosures", "claimed", "held", "narrowing", "reached")

    def __init__(self, stages: Sequence[int], enclosures: Sequence[Bounds],
                 claimed: Constructible) -> None:
        self.stages = tuple(stages)
        self.enclosures = tuple(enclosures)
        self.claimed = claimed
        self.held = all(bound.contains(claimed) for bound in enclosures)
        # X.1's criterion: what is left over is less than half of what was left
        # over before, which is the step every proof in Book XII takes.
        self.narrowing = all(
            sign(later.width() * 2 - earlier.width()) < 0
            for earlier, later in zip(enclosures, enclosures[1:]))
        self.reached = enclosures[-1].width() if enclosures else None

    def within(self, bound: Constructible) -> bool:
        """Whether the last enclosure is narrower than a given magnitude."""
        return sign(bound - self.reached) > 0

    def __repr__(self) -> str:
        return (f"Squeeze(stages={self.stages}, held={self.held}, "
                f"narrowing={self.narrowing})")


def squeeze(enclosure: Callable[[int], Bounds], claimed: Constructible,
            stages: Sequence[int]) -> Squeeze:
    """Run the enclosure through the stages and see what survives."""
    return Squeeze(stages, [enclosure(stage) for stage in stages], claimed)
