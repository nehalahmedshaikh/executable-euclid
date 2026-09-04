"""Solid figures: the parallelepiped, the prism, the pyramid, and their content.

A solid is held as the vertices that bound it and the faces those vertices make,
which is what Euclid's definitions give and nothing more.  There is no volume
formula anywhere in this module.  Content is got by cutting the solid into
tetrahedra from a point inside it and adding them up, and the tetrahedron's
content is the scalar triple product already in
:func:`euclid.solid.predicates.volume6` -- a polynomial in the coordinates, so
the content of every figure in Books XI to XIII is exact and no proposition has
to be told what it is meant to prove.

That matters most in Book XII.  ``content(cone)`` would be assuming XII.10, so
there is no cone here: what the book gets is inscribed and circumscribed
polyhedra, whose content this module supplies, and the squeeze between them.
See :mod:`euclid.solid.exhaust`.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Optional, Sequence

from ..kernel.field import Constructible, is_zero, sign, sqrt
from .objects import Plane, Point3, vector_between
from .predicates import cross3, dot3, len2, volume6

__all__ = [
    "Solid",
    "content",
    "cube_on",
    "edge_lengths",
    "frame_on",
    "height_over",
    "parallelepiped",
    "parallelogram_area",
    "prism",
    "pyramid",
    "unit",
]


class Solid:
    """A bounded figure, held as its vertices and the faces they make.

    Faces are tuples of indices into ``vertices``, each face's points in order
    round it.  Nothing here requires the faces to be oriented consistently:
    :func:`content` cuts from an interior point and takes each piece positively,
    which is the reading that works for every convex figure the *Elements*
    builds and asks nothing of the caller.
    """

    __slots__ = ("vertices", "faces", "label")

    def __init__(self, vertices: Sequence[Point3], faces: Sequence[Sequence[int]],
                 label: str = "") -> None:
        if len(vertices) < 4:
            raise ValueError("a solid needs at least four vertices")
        self.vertices = tuple(vertices)
        self.faces = tuple(tuple(face) for face in faces)
        self.label = label

    def face_points(self, index: int) -> tuple:
        return tuple(self.vertices[i] for i in self.faces[index])

    def centre(self) -> Point3:
        """The mean of the vertices, which lies inside any convex figure."""
        share = Fraction(1, len(self.vertices))
        return Point3(sum((v.x for v in self.vertices), Fraction(0)) * share,
                      sum((v.y for v in self.vertices), Fraction(0)) * share,
                      sum((v.z for v in self.vertices), Fraction(0)) * share)

    def face_plane(self, index: int) -> Plane:
        points = self.face_points(index)
        return Plane.through(points[0], points[1], points[2])

    def edges(self) -> tuple:
        """Every edge once, as a pair of vertex indices."""
        seen = []
        for face in self.faces:
            for position, start in enumerate(face):
                end = face[(position + 1) % len(face)]
                pair = (start, end) if start < end else (end, start)
                if pair not in seen:
                    seen.append(pair)
        return tuple(seen)

    def __repr__(self) -> str:
        tag = f" [{self.label}]" if self.label else ""
        return f"Solid({len(self.vertices)} vertices, {len(self.faces)} faces){tag}"


def content(solid: Solid) -> Constructible:
    """The content of a solid, exactly.

    Every face is fanned into triangles and every triangle is joined to a point
    inside, so the figure is cut into tetrahedra that fill it once.  Each piece
    is taken positively, so the faces need no agreed sense; the sum is a
    polynomial in the coordinates and takes no root.
    """
    inside = solid.centre()
    total = Fraction(0)
    for face in solid.faces:
        first = solid.vertices[face[0]]
        for position in range(1, len(face) - 1):
            piece = volume6(inside, first, solid.vertices[face[position]],
                            solid.vertices[face[position + 1]])
            total = total + (piece if sign(piece) > 0 else -piece)
    return total / 6


def parallelogram_area(first: tuple, second: tuple) -> Constructible:
    """The area of the parallelogram two directions contain.

    ``|u x v|``, and the three components of the cross product are the witness,
    so the root is a hypotenuse in space and the field ladder counts it as one.
    """
    across = cross3(first, second)
    return sqrt(dot3(across, across), witness=across)


def height_over(point: Point3, plane: Plane) -> Constructible:
    """How far a point stands from a plane, measured along the perpendicular."""
    normal = plane.normal()
    reach = plane.evaluate(point)
    span = sqrt(dot3(normal, normal), witness=normal)
    return (reach if sign(reach) > 0 else -reach) / span


def unit(direction: tuple) -> tuple:
    """The direction of unit length, exactly."""
    span = sqrt(dot3(direction, direction), witness=direction)
    if is_zero(span):
        raise ValueError("a direction must not be the zero vector")
    return direction[0] / span, direction[1] / span, direction[2] / span


def frame_on(direction: tuple) -> tuple:
    """Three directions of unit length at right angles, the first as given.

    XI.26 sets a solid angle up on a line already drawn, so what it needs is a
    frame the given line begins.  The other two are got by crossing with an axis
    the line is not along, which is exact and needs no choice made about the
    figure the angle came from.
    """
    first = unit(direction)
    for axis in ((Fraction(1), Fraction(0), Fraction(0)),
                 (Fraction(0), Fraction(1), Fraction(0)),
                 (Fraction(0), Fraction(0), Fraction(1))):
        across = cross3(first, axis)
        if not all(is_zero(component) for component in across):
            second = unit(across)
            return first, second, cross3(first, second)
    raise ValueError("a direction must not be the zero vector")


def _shifted(point: Point3, *steps: tuple) -> Point3:
    x, y, z = point.x, point.y, point.z
    for step in steps:
        x, y, z = x + step[0], y + step[1], z + step[2]
    return Point3(x, y, z)


def parallelepiped(corner: Point3, a: Point3, b: Point3, c: Point3,
                   label: str = "") -> Solid:
    """The parallelepiped on three arms from one corner (XI Def. 25 and XI.24).

    Bounded by six parallelograms in three opposite pairs, which is what XI.24
    proves of any solid contained by parallel planes and what every proposition
    from XI.25 to XI.37 then takes for granted.
    """
    u = vector_between(corner, a)
    v = vector_between(corner, b)
    w = vector_between(corner, c)
    if is_zero(dot3(cross3(u, v), w)):
        raise ValueError("three arms in one plane contain no solid")
    vertices = [corner, _shifted(corner, u), _shifted(corner, u, v), _shifted(corner, v),
                _shifted(corner, w), _shifted(corner, u, w),
                _shifted(corner, u, v, w), _shifted(corner, v, w)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7),      # the pair on the third arm
             (0, 1, 5, 4), (3, 2, 6, 7),      # the pair on the second
             (0, 3, 7, 4), (1, 2, 6, 5)]      # the pair on the first
    return Solid(vertices, faces, label)


def cube_on(corner: Point3, edge, label: str = "") -> Solid:
    """The cube on a given edge, set square to the axes."""
    return parallelepiped(corner,
                          Point3(corner.x + edge, corner.y, corner.z),
                          Point3(corner.x, corner.y + edge, corner.z),
                          Point3(corner.x, corner.y, corner.z + edge), label)


def prism(base: Sequence[Point3], step: tuple, label: str = "") -> Solid:
    """The prism on a polygonal base, carried along one direction (XI Def. 13)."""
    size = len(base)
    if size < 3:
        raise ValueError("a prism needs a base of at least three sides")
    vertices = list(base) + [_shifted(point, step) for point in base]
    faces = [tuple(range(size)), tuple(range(size, 2 * size))]
    for position in range(size):
        onward = (position + 1) % size
        faces.append((position, onward, size + onward, size + position))
    return Solid(vertices, faces, label)


def pyramid(base: Sequence[Point3], apex: Point3, label: str = "") -> Solid:
    """The pyramid on a polygonal base, meeting at a point (XI Def. 12)."""
    size = len(base)
    if size < 3:
        raise ValueError("a pyramid needs a base of at least three sides")
    vertices = list(base) + [apex]
    faces = [tuple(range(size))]
    for position in range(size):
        faces.append((position, (position + 1) % size, size))
    return Solid(vertices, faces, label)


def edge_lengths(solid: Solid) -> tuple:
    """The squared length of every edge, in the order :meth:`Solid.edges` gives."""
    return tuple(len2(solid.vertices[i], solid.vertices[j]) for i, j in solid.edges())
