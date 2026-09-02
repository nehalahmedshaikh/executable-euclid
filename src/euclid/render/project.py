"""Solid figures, flattened into plane ones before anything draws them.

:mod:`euclid.render.svg` buckets a trace's objects by type and lays them out.
Rather than teach it about space, this sits in front of it and turns the solid
objects into plane ones, so the renderer goes on seeing only ``Point``, ``Line``
and ``Circle`` and needs no change at all.

The projection is orthographic and **exact**.  The direction is a rational
vector and so are the two axes across it, so a projected coordinate is a
rational combination of exact coordinates and stays a ``Constructible``:
``Point`` accepts it unchanged, and nothing is rounded on the way to the page.

Hidden edges are decided by an exact sign, not by a depth buffer: a vertex
behind a face plane is on the far side of it, which is what ``Plane.side_of``
already answers.  Hidden lines are drawn in the same grey the plane figures use
for scaffolding, so the palette gains nothing and no opacity is needed.
"""

from __future__ import annotations

from fractions import Fraction

from ..kernel.field import is_zero, sign
from ..plane.objects import Circle, Line, Point
from ..plane.trace import Move, Trace
from ..solid.objects import Line3, Plane, Point3, Sphere
from ..solid.predicates import cross3, dot3

__all__ = ["DIRECTIONS", "flatten", "project_point", "separates"]

# Directions to try, in order; the first that keeps every vertex apart is used.
#
# Each is a Pythagorean quadruple, so its own length is a whole number. That is
# what lets the two axes across it be scaled to a common length while staying
# rational, and an unequal pair would draw a cube as a cuboid.
DIRECTIONS = (
    (Fraction(2), Fraction(3), Fraction(6)),     # 7
    (Fraction(1), Fraction(2), Fraction(2)),     # 3
    (Fraction(2), Fraction(6), Fraction(9)),     # 11
    (Fraction(1), Fraction(4), Fraction(8)),     # 9
    (Fraction(6), Fraction(6), Fraction(7)),     # 11
    (Fraction(2), Fraction(10), Fraction(11)),   # 15
)


def _reach(direction: tuple) -> Fraction:
    """The length of a direction, which every one of these has as a whole number."""
    squared = dot3(direction, direction)
    whole = round(float(squared) ** 0.5)
    if whole * whole != squared:
        raise ValueError(f"{direction} is no Pythagorean quadruple")
    return Fraction(whole)


def _axes(direction: tuple) -> tuple:
    """Two rational vectors across the direction, spanning the picture plane.

    Equal in length and at right angles, so the projection is a similarity: it
    scales the figure by one factor and shows every incidence and every equality
    of length the figure has. They are not unit vectors, which would want a
    square root; being equal is what matters, and being rational is what keeps
    the projected coordinates exact.
    """
    seed = (Fraction(1), Fraction(0), Fraction(0))
    if is_zero(direction[1]) and is_zero(direction[2]):
        seed = (Fraction(0), Fraction(1), Fraction(0))
    first = cross3(direction, seed)
    second = cross3(direction, first)
    # ``second`` is longer than ``first`` by exactly the length of the
    # direction, because it is that direction crossed into it. Scaling
    # ``first`` up to match makes the projection a similarity rather than a
    # squash, so the picture keeps the shape of the figure.
    reach = _reach(direction)
    return tuple(component * reach for component in first), second


def _scale2(direction: tuple) -> Fraction:
    """The square of the factor this projection multiplies lengths by."""
    across, _ = _axes(direction)
    return dot3(across, across)


def project_point(point: Point3, direction: tuple) -> Point:
    across, up = _axes(direction)
    v = (point.x, point.y, point.z)
    return Point(dot3(v, across), dot3(v, up), point.label)


def separates(points: list, direction: tuple) -> bool:
    """Whether this direction keeps every pair of vertices apart.

    Both conditions the figure needs are decidable exactly, which is why the
    choice of direction is a test rather than a caveat: no two vertices may land
    on one another, and no edge may collapse to a point.
    """
    # Distinct vertices must stay distinct. The same point reaches this twice
    # -- once as a vertex and again as the end of an edge -- so it is the
    # distinct ones that are counted, or every figure would look degenerate.
    distinct = {(p.x, p.y, p.z) for p in points}
    flat = {(q.x, q.y) for q in
            (project_point(Point3(*v), direction) for v in distinct)}
    return len(flat) == len(distinct)


def _choose(points: list) -> tuple:
    for direction in DIRECTIONS:
        if separates(points, direction):
            return direction
    raise ValueError("no rational direction separates these vertices")


def _behind(point: Point3, faces: list, direction: tuple) -> bool:
    """Whether a face hides this point from the viewer.

    The viewer looks along ``direction``; a point is hidden when some face plane
    has the viewer on one side and the point on the other. Both are signs of an
    exact evaluation, so nothing here is a near miss.
    """
    for face in faces:
        towards = dot3(face.normal(), direction)
        if is_zero(towards):
            continue
        if sign(face.evaluate(point)) == -sign(towards):
            return True
    return False


def flatten(trace: Trace, direction: tuple = None) -> Trace:
    """A copy of the trace with every solid object replaced by its shadow.

    Traces that hold nothing solid come back unchanged, so this can sit in front
    of every figure without asking first.
    """
    solid = [move for move in trace.moves
             if isinstance(move.obj, (Point3, Line3, Plane, Sphere))]
    if not solid:
        return trace

    vertices = [move.obj for move in solid if isinstance(move.obj, Point3)]
    for move in solid:
        if isinstance(move.obj, Line3):
            vertices.extend((move.obj.p, move.obj.q))
    direction = direction or _choose(vertices)
    faces = [move.obj for move in solid if isinstance(move.obj, Plane)]

    shadow = Trace(proposition=trace.proposition)
    shadow.intersections = list(trace.intersections)
    shadow.predicates = list(trace.predicates)
    shadow.claims = list(trace.claims)
    for move in trace.moves:
        item = move.obj
        if isinstance(item, Point3):
            drawn = Move(move.kind, move.label, obj=project_point(item, direction),
                         postulate=move.postulate, note=move.note)
        elif isinstance(item, Line3):
            near, far = project_point(item.p, direction), project_point(item.q, direction)
            if near == far:
                continue  # an edge end-on to the viewer draws nothing
            hidden = (_behind(item.p, faces, direction)
                      and _behind(item.q, faces, direction))
            drawn = Move(move.kind, move.label, obj=Line.through(near, far),
                         postulate=move.postulate,
                         note="hidden" if hidden else move.note)
        elif isinstance(item, Sphere):
            # A sphere's outline is a circle about the projected centre, of the
            # same radius scaled by whatever the projection scales lengths by --
            # which the points were scaled by too, so the two agree.
            drawn = Move(move.kind, move.label,
                         obj=Circle(project_point(item.centre, direction),
                                    item.r2 * _scale2(direction)),
                         postulate=move.postulate, note=move.note)
        elif isinstance(item, Plane):
            continue  # a plane has no outline; it decides what is hidden
        else:
            drawn = move
        shadow.moves.append(drawn)
    return shadow
