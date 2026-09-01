"""Book IV: figures inscribed in circles and circumscribed about them.

It ends at IV.16 with the fifteen-angled figure, and the pentagon of IV.11 is
the reason: its side is the golden section of the radius, so the vertices live
in Q(sqrt 5) and the kernel keeps them there exactly.
"""

from __future__ import annotations

from ..kernel.field import sign, sqrt
from ..plane.angles import STRAIGHT, angle_at, length
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
    on_circle,
    right_angle,
    same_side,
)
from . import samples
from .book01_foundations import prop_I_10
from .book02 import prop_II_11
from .figures import _across, _centre_of, _foot_of_the_perpendicular, _tangent_at, _turn
from .registry import CONSTRUCTION, Out, claim, hypothesis, proposition


@proposition(
    "IV.1",
    CONSTRUCTION,
    sample=samples.circle_and_chord,
    note="The proviso matters: a chord cannot be longer than a diameter, and "
    "Euclid states the limit rather than letting the construction fail.",
)
def prop_IV_1(o: Point, a: Point, c: Point, d: Point) -> Out:
    """Fit into the circle about O a chord equal to the given line CD."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("CD is a genuine magnitude", c != d, guard=True)
    hypothesis("CD is not greater than the diameter", len2(c, d) <= 4 * len2(o, a))
    given = circle(o, a, "the given circle")
    line(c, d, "the given line CD")

    reach = circle_with_radius2(a, len2(c, d), "circle centre A with radius CD")
    b = posit(meet(reach, given)[0], "B")
    fitted = line(a, b, "the chord AB")

    claim("B lies on the given circle", "Def.15", on_circle(b, given))
    claim("AB equals the given line, both radii of the circle about A", "Def.15",
          eq_len(a, b, c, d))
    return Out(chord=fitted, at=b)


@proposition(
    "IV.5",
    CONSTRUCTION,
    sample=samples.triangle,
    note="The circumcircle. Its centre is where the perpendicular bisectors "
    "cross, and stays rational when the vertices are.",
)
def prop_IV_5(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    outline(a, b, c)

    centre = posit(_centre_of(a, b, c), "O")
    around = circle(centre, a, "the circumscribed circle")
    line(centre, a, "a radius")
    line(centre, b, "a radius")
    line(centre, c, "a radius")

    claim("the centre is equidistant from all three vertices", ["I.10", "I.11"],
          eq_len(centre, a, centre, b) and eq_len(centre, a, centre, c))
    claim("so the circle through A passes through B and C too", "Def.15",
          on_circle(b, around) and on_circle(c, around))
    return Out(centre=centre, circle=around)


@proposition(
    "IV.6",
    CONSTRUCTION,
    sample=samples.segment,
)
def prop_IV_6(o: Point, a: Point) -> Out:
    """Inscribe a square in the circle about O through A, on two diameters at
    right angles."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")

    across = _across(o, a)
    c = posit(Point(o.x - (a.x - o.x), o.y - (a.y - o.y)), "C")
    b = posit(Point(o.x + across[0], o.y + across[1]), "B")
    d = posit(Point(o.x - across[0], o.y - across[1]), "D")
    line(a, c, "the diameter AC")
    line(b, d, "the diameter BD, at right angles to it")
    outline(a, b, c, d)

    claim("the two diameters are at right angles", "I.11", right_angle(a, o, b))
    claim("every vertex lies on the circle", "Def.15",
          all(on_circle(v, around) for v in (a, b, c, d)))
    claim("the four sides are equal", "I.4",
          eq_len(a, b, b, c) and eq_len(b, c, c, d) and eq_len(c, d, d, a))
    claim("and every angle is right, standing on a diameter", "III.31",
          all(right_angle(*corner) for corner in
              ((a, b, c), (b, c, d), (c, d, a), (d, a, b))))
    return Out(square=(a, b, c, d))


@proposition(
    "IV.7",
    CONSTRUCTION,
    sample=samples.segment,
)
def prop_IV_7(o: Point, a: Point) -> Out:
    """Circumscribe a square about the circle, on the tangents at the ends of
    two diameters at right angles."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")

    reach = (a.x - o.x, a.y - o.y)
    across = _across(o, a)
    corners = []
    for index, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        corners.append(posit(
            Point(o.x + sx * reach[0] + sy * across[0], o.y + sx * reach[1] + sy * across[1]),
            "EFGH"[index],
        ))
    outline(*corners)

    touching = [
        posit(Point(o.x + reach[0], o.y + reach[1]), "A"),
        posit(Point(o.x + across[0], o.y + across[1]), "B"),
        posit(Point(o.x - reach[0], o.y - reach[1]), "C"),
        posit(Point(o.x - across[0], o.y - across[1]), "D"),
    ]
    claim("each side meets the circle at the end of a radius, and so touches it", "III.16",
          all(on_circle(point, around) for point in touching)
          and all(right_angle(o, touching[i], corners[i]) for i in range(4)))
    claim("the four sides are equal", "I.34",
          eq_len(corners[0], corners[1], corners[1], corners[2])
          and eq_len(corners[1], corners[2], corners[2], corners[3]))
    claim("and every angle is right", "I.34",
          all(right_angle(corners[i - 1], corners[i], corners[(i + 1) % 4]) for i in range(4)))
    return Out(square=tuple(corners))


@proposition(
    "IV.8",
    CONSTRUCTION,
    sample=samples.square,
)
def prop_IV_8(a: Point, b: Point, c: Point, d: Point) -> Out:
    """Inscribe a circle in the square ABCD."""
    hypothesis("ABCD is a square",
               eq_len(a, b, b, c) and eq_len(b, c, c, d) and eq_len(c, d, d, a)
               and right_angle(d, a, b))
    outline(a, b, c, d)

    centre = posit(prop_I_10(a, c).midpoint, "O")
    feet = [posit(prop_I_10(*side).midpoint, "EFGH"[index])
            for index, side in enumerate(((a, b), (b, c), (c, d), (d, a)))]
    inscribed = circle(centre, feet[0], "the inscribed circle")

    claim("the centre is equally distant from all four sides", "I.34",
          all(eq_len(centre, foot, centre, feet[0]) for foot in feet))
    claim("and each of those distances is at right angles to its side", "I.12",
          all(right_angle(centre, feet[i], (a, b, c, d)[i]) for i in range(4)))
    claim("so the circle touches every side", "III.16",
          all(on_circle(foot, inscribed) for foot in feet))
    return Out(centre=centre, circle=inscribed)


@proposition(
    "IV.9",
    CONSTRUCTION,
    sample=samples.square,
)
def prop_IV_9(a: Point, b: Point, c: Point, d: Point) -> Out:
    """Circumscribe a circle about the square ABCD."""
    hypothesis("ABCD is a square",
               eq_len(a, b, b, c) and eq_len(b, c, c, d) and eq_len(c, d, d, a)
               and right_angle(d, a, b))
    outline(a, b, c, d)
    line(a, c, "the diameter AC")
    line(b, d, "the diameter BD")

    centre = posit(prop_I_10(a, c).midpoint, "O")
    around = circle(centre, a, "the circumscribed circle")

    claim("the diameters bisect one another", "I.34",
          centre == prop_I_10(b, d).midpoint)
    claim("the centre is equally distant from all four corners", "I.6",
          all(eq_len(centre, corner, centre, a) for corner in (b, c, d)))
    claim("so one circle passes through all four", "Def.15",
          all(on_circle(corner, around) for corner in (a, b, c, d)))
    return Out(centre=centre, circle=around)


@proposition(
    "IV.15",
    CONSTRUCTION,
    sample=samples.segment,
    note="The hexagon is the easy one: its side is the radius exactly, so the "
    "compass steps round the circle without being reset.",
)
def prop_IV_15(o: Point, a: Point) -> Out:
    """Inscribe a regular hexagon in the circle about O through A."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")

    side2 = len2(o, a)  # the side of the hexagon is the radius itself
    vertices = [a]
    current = a
    for step in range(5):
        stepper = circle_with_radius2(current, side2, f"step {step + 1}")
        onward = [point for point in meet(stepper, around) if point not in vertices]
        if not onward:
            break
        current = posit(onward[0], "BCDEF"[step])
        vertices.append(current)

    claim("stepping the radius round the circle reaches six distinct points", "Post.3",
          len(vertices) == 6)
    outline(*vertices)
    claim("every vertex lies on the circle", "Def.15",
          all(on_circle(vertex, around) for vertex in vertices))
    claim("the hexagon is equilateral, each side equal to the radius", "Def.15",
          all(eq_len(vertices[i], vertices[(i + 1) % 6], o, a) for i in range(6)))
    claim("and equiangular", "III.27",
          all(eq_angle(vertices[i - 1], vertices[i], vertices[(i + 1) % 6],
                       vertices[5], vertices[0], vertices[1]) for i in range(6)))
    return Out(hexagon=tuple(vertices))


@proposition(
    "IV.2",
    CONSTRUCTION,
    sample=lambda rng: samples.segment(rng) + samples.triangle(rng),
    note="An angle at the circumference stands on twice its own arc (III.20), so "
    "laying off twice each given angle round the centre settles the triangle.",
)
def prop_IV_2(o: Point, a: Point, d: Point, e: Point, f: Point) -> Out:
    """Inscribe in the circle about O a triangle equiangular with DEF."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("DEF is a genuine triangle", not collinear(d, e, f), guard=True)
    around = circle(o, a, "the given circle")
    outline(d, e, f)

    # An angle stands on the arc it does *not* touch, so the arc AB is twice the
    # angle at F, and the arc BC twice the angle at D. Laying those two off
    # leaves the third arc, and with it the third angle, no longer free.
    at_d, at_f = angle_at(f, d, e), angle_at(e, f, d)
    b = posit(_turn(o, a, at_f.doubled()), "B")
    c = posit(_turn(o, b, at_d.doubled()), "C")
    outline(a, b, c)

    claim("all three vertices lie on the given circle", "Def.15",
          on_circle(b, around) and on_circle(c, around))
    claim("the angle at each vertex is half the arc it stands on", "III.20",
          angle_at(b, a, c).doubled() == angle_at(b, o, c)
          or angle_at(b, a, c).doubled() == STRAIGHT + STRAIGHT - angle_at(b, o, c))
    claim("so the inscribed triangle is equiangular with the given one", "III.20",
          eq_angle(b, a, c, f, d, e) and eq_angle(a, b, c, d, e, f))
    return Out(triangle=(a, b, c))


@proposition(
    "IV.3",
    CONSTRUCTION,
    sample=lambda rng: samples.segment(rng) + samples.triangle(rng),
    note="The dual of IV.2. A tangent meets its radius at right angles, so the "
    "angle at a vertex and the arc between its two contact points make two right "
    "angles between them.",
)
def prop_IV_3(o: Point, a: Point, d: Point, e: Point, f: Point) -> Out:
    """Circumscribe about the circle a triangle equiangular with DEF."""
    hypothesis("the circle has positive radius", o != a)
    hypothesis("DEF is a genuine triangle", not collinear(d, e, f), guard=True)
    around = circle(o, a, "the given circle")
    outline(d, e, f)

    at_d, at_e = angle_at(f, d, e), angle_at(d, e, f)
    # The arc between two contact points is the supplement of the angle between
    # the tangents there, so lay the contact points off by those supplements.
    touch_b = posit(_turn(o, a, STRAIGHT - at_d), "P")
    touch_c = posit(_turn(o, touch_b, STRAIGHT - at_e), "Q")
    touches = (a, touch_b, touch_c)
    tangents = [_tangent_at(o, point, f"the tangent at {point.label}") for point in touches]
    for point in touches:
        line(o, point, "a radius")

    corners = [
        posit(meet_one(tangents[index], tangents[(index + 1) % 3]), "GHK"[index])
        for index in range(3)
    ]
    outline(*corners)

    claim("each side touches the circle, meeting a radius at right angles", "III.16",
          all(on_circle(point, around) for point in touches)
          and all(right_angle(o, touches[i], corners[i]) for i in range(3)))
    claim("so the circumscribed triangle is equiangular with the given one", "III.32",
          eq_angle(corners[2], corners[0], corners[1], f, d, e)
          and eq_angle(corners[0], corners[1], corners[2], d, e, f))
    return Out(triangle=tuple(corners), touching=touches)


@proposition(
    "IV.12",
    CONSTRUCTION,
    sample=samples.segment,
    note="The pentagon of IV.11 turned outside in: its vertices become the points "
    "where the circumscribed pentagon touches.",
)
def prop_IV_12(o: Point, a: Point) -> Out:
    """Circumscribe a regular pentagon about the circle about O through A."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")
    touches = prop_IV_11(o, a).pentagon

    tangents = [_tangent_at(o, point) for point in touches]
    corners = [
        posit(meet_one(tangents[index], tangents[(index + 1) % 5]), "GHKLM"[index])
        for index in range(5)
    ]
    outline(*corners)

    claim("each side touches the circle at a vertex of the inscribed pentagon", "III.16",
          all(on_circle(point, around) for point in touches)
          and all(right_angle(o, touches[i], corners[i]) for i in range(5)))
    claim("the circumscribed pentagon is equilateral", "I.47",
          all(eq_len(corners[i], corners[(i + 1) % 5], corners[0], corners[1])
              for i in range(5)))
    claim("and equiangular", "I.8",
          all(eq_angle(corners[i - 1], corners[i], corners[(i + 1) % 5],
                       corners[4], corners[0], corners[1]) for i in range(5)))
    return Out(pentagon=tuple(corners), touching=touches)


@proposition(
    "IV.4",
    CONSTRUCTION,
    sample=samples.triangle,
    note="The incircle. Its centre is where the angle bisectors meet, and unlike "
    "the circumcentre it is irrational in general -- the kernel carries it exactly.",
)
def prop_IV_4(a: Point, b: Point, c: Point) -> Out:
    hypothesis("ABC is a genuine triangle", not collinear(a, b, c), guard=True)
    outline(a, b, c)

    # Where two angle bisectors cross. Weighting each vertex by the opposite
    # side is the same point Euclid reaches with I.9, and reaches it without
    # intersecting two constructed rays.
    opposite = (length(b, c), length(c, a), length(a, b))
    total = opposite[0] + opposite[1] + opposite[2]
    centre = posit(
        Point(
            (opposite[0] * a.x + opposite[1] * b.x + opposite[2] * c.x) / total,
            (opposite[0] * a.y + opposite[1] * b.y + opposite[2] * c.y) / total,
        ),
        "O",
    )
    feet = [
        posit(_foot_of_the_perpendicular(centre, *side), "DEF"[index])
        for index, side in enumerate(((b, c), (c, a), (a, b)))
    ]
    for foot in feet:
        line(centre, foot)
    inscribed = circle(centre, feet[0], "the inscribed circle")

    claim("the centre lies on the bisector of each angle", "I.9",
          all(eq_angle(*pair) for pair in (
              (b, a, centre, centre, a, c),
              (a, b, centre, centre, b, c),
              (a, c, centre, centre, c, b))))
    claim("the perpendiculars from it to the three sides are equal", "I.26",
          eq_len(centre, feet[0], centre, feet[1])
          and eq_len(centre, feet[0], centre, feet[2]))
    claim("each perpendicular meets its side at right angles", "I.12",
          all(right_angle(centre, feet[index], vertex)
              for index, vertex in enumerate((b, c, a))))
    claim("so the circle on that radius touches all three sides", "III.16",
          all(on_circle(foot, inscribed) for foot in feet))
    return Out(centre=centre, circle=inscribed)


@proposition(
    "IV.10",
    CONSTRUCTION,
    sample=samples.segment,
    note="The triangle that makes the pentagon possible: its base angles are "
    "double the apex, which puts 36 degrees within reach of the compass.",
)
def prop_IV_10(a: Point, b: Point) -> Out:
    """Cut AB in extreme and mean ratio, and step the greater segment off the
    circle about A."""
    hypothesis("A and B are distinct", a != b)
    section = prop_II_11(a, b).section
    around = circle(a, b, "circle centre A through B")
    reach = circle_with_radius2(b, len2(a, section), "circle centre B with radius AC")
    d = posit(meet(reach, around)[0], "D")
    outline(a, b, d)
    line(section, d, "CD")

    claim("BD equals the greater segment AC", "I.3", eq_len(b, d, a, section))
    claim("the triangle is isosceles, AB and AD both radii", "Def.15", eq_len(a, b, a, d))
    claim("each angle at the base is double the angle at the apex", ["II.11", "III.32"],
          angle_at(a, b, d) == angle_at(b, a, d).doubled()
          and angle_at(a, d, b) == angle_at(b, a, d).doubled())
    return Out(triangle=(a, b, d), section=section)


@proposition(
    "IV.13",
    CONSTRUCTION,
    sample=samples.segment,
    note="Every regular polygon has an inscribed circle for the same reason: the "
    "centre is as far from every side as from every other.",
)
def prop_IV_13(o: Point, a: Point) -> Out:
    """The pentagon is the one IV.11 inscribes; inscribe a circle in it."""
    hypothesis("the circle has positive radius", o != a)
    vertices = prop_IV_11(o, a).pentagon
    outline(*vertices)

    feet = [posit(prop_I_10(vertices[i], vertices[(i + 1) % 5]).midpoint, "FGHKL"[i])
            for i in range(5)]
    for foot in feet:
        line(o, foot)
    inscribed = circle(o, feet[0], "the inscribed circle")

    claim("the centre is equally distant from every side", "I.4",
          all(eq_len(o, foot, o, feet[0]) for foot in feet))
    claim("and meets each at right angles", "I.12",
          all(right_angle(o, feet[i], vertices[i]) for i in range(5)))
    claim("so the circle touches all five sides", "III.16",
          all(on_circle(foot, inscribed) for foot in feet))
    return Out(centre=o, circle=inscribed, pentagon=vertices)


@proposition(
    "IV.14",
    CONSTRUCTION,
    sample=samples.segment,
)
def prop_IV_14(o: Point, a: Point) -> Out:
    """Circumscribe a circle about the regular pentagon of IV.11."""
    hypothesis("the circle has positive radius", o != a)
    vertices = prop_IV_11(o, a).pentagon
    outline(*vertices)
    for vertex in vertices:
        line(o, vertex)
    around = circle(o, vertices[0], "the circumscribed circle")

    claim("the centre is equally distant from every vertex", "I.6",
          all(eq_len(o, vertex, o, vertices[0]) for vertex in vertices))
    claim("so one circle passes through all five", "Def.15",
          all(on_circle(vertex, around) for vertex in vertices))
    return Out(centre=o, circle=around)


@proposition(
    "IV.16",
    CONSTRUCTION,
    sample=samples.segment,
    note="Fifteen because three and five are prime to one another: a third of the "
    "circumference less a fifth leaves two fifteenths, and bisecting that gives one.",
)
def prop_IV_16(o: Point, a: Point) -> Out:
    """Inscribe a regular fifteen-angled figure, from the hexagon and the pentagon."""
    hypothesis("the circle has positive radius", o != a)
    around = circle(o, a, "the given circle")

    # Euclid's own route. From A, a vertex of the inscribed equilateral triangle
    # stands a third of the way round and a vertex of the pentagon a fifth, so
    # the arc between them is 1/3 - 1/5 = 2/15. Bisecting it gives a fifteenth,
    # and its chord is the side wanted. Nothing here is a formula for the side:
    # it is measured off the figure, as he measures it.
    pentagon = prop_IV_11(o, a).pentagon
    a_fifth = pentagon[1]
    third = circle_with_radius2(a, 3 * len2(o, a), "the chord subtending a third")
    a_third = posit(
        next(point for point in meet(third, around)
             if same_side(point, a_fifth, Line.through(o, a))),
        "T",
    )
    middle = posit(prop_I_10(a_fifth, a_third).midpoint, "M")
    bisected = posit(
        next(point for point in meet(Line.through(o, middle), around)
             if sign((point.x - o.x) * (middle.x - o.x)
                     + (point.y - o.y) * (middle.y - o.y)) > 0),
        "N",
    )
    claim("the arc between the two vertices is two fifteenths of the circle", "IV.11",
          on_circle(a_third, around) and on_circle(a_fifth, around))
    claim("and N bisects it, so AN cuts off one fifteenth", "III.30",
          eq_len(bisected, a_fifth, bisected, a_third))

    side2 = len2(a_fifth, bisected)
    vertices = [a]
    current = a
    for step in range(14):
        stepper = circle_with_radius2(current, side2, f"step {step + 1}")
        onward = [point for point in meet(stepper, around) if point not in vertices]
        if not onward:
            break
        current = posit(onward[0], f"V{step + 2}")
        vertices.append(current)

    claim("stepping the chord round the circle reaches fifteen distinct points", "Post.3",
          len(vertices) == 15)
    outline(*vertices)
    claim("every vertex lies on the circle", "Def.15",
          all(on_circle(vertex, around) for vertex in vertices))
    claim("the figure is equilateral", "Def.19",
          all(eq_len(vertices[i], vertices[(i + 1) % 15], vertices[0], vertices[1])
              for i in range(15)))
    claim("and equiangular", "III.27",
          all(eq_angle(vertices[i - 1], vertices[i], vertices[(i + 1) % 15],
                       vertices[14], vertices[0], vertices[1]) for i in range(15)))
    return Out(polygon=tuple(vertices))


@proposition(
    "IV.11",
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
