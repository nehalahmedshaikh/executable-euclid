"""Floating-point search states, and how to tell two of them apart.

The optimiser explores in floats and verifies in exact arithmetic.  That split
is what makes the search tractable: the kernel is far too careful to run
millions of times, but it is exactly what you want once a candidate answer
appears.

Everything here therefore mirrors :mod:`euclid.plane` in cheap arithmetic --
*including the intersection ordering rules*, so that a move sequence found here
replays step for step through the exact primitives.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional

__all__ = ["Circle", "Line", "State", "intersect", "EPSILON"]

EPSILON = 1e-9
ROUNDING = 6


@dataclass(frozen=True)
class Line:
    a: float
    b: float
    c: float
    dx: float  # the direction of the two points that defined it
    dy: float

    @staticmethod
    def through(p: tuple[float, float], q: tuple[float, float]) -> "Line":
        a, b = q[1] - p[1], p[0] - q[0]
        c = a * p[0] + b * p[1]
        scale = math.hypot(a, b)
        return Line(a / scale, b / scale, c / scale, q[0] - p[0], q[1] - p[1])

    def key(self) -> tuple:
        # a line and its negation are the same line
        flip = -1.0 if (self.a < -EPSILON or (abs(self.a) < EPSILON and self.b < 0)) else 1.0
        return (
            round(self.a * flip, ROUNDING),
            round(self.b * flip, ROUNDING),
            round(self.c * flip, ROUNDING),
        )


@dataclass(frozen=True)
class Circle:
    cx: float
    cy: float
    r: float

    @staticmethod
    def centred(centre: tuple[float, float], through: tuple[float, float]) -> "Circle":
        return Circle(centre[0], centre[1], math.dist(centre, through))

    def key(self) -> tuple:
        return round(self.cx, ROUNDING), round(self.cy, ROUNDING), round(self.r, ROUNDING)


def _line_line(u: Line, v: Line) -> list[tuple[float, float]]:
    determinant = u.a * v.b - u.b * v.a
    if abs(determinant) < EPSILON:
        return []
    return [((u.c * v.b - u.b * v.c) / determinant, (u.a * v.c - u.c * v.a) / determinant)]


def _line_circle(u: Line, k: Circle) -> list[tuple[float, float]]:
    offset = u.a * k.cx + u.b * k.cy - u.c  # the line is normalised, so a^2+b^2 = 1
    discriminant = k.r * k.r - offset * offset
    if discriminant < -EPSILON:
        return []
    foot = (k.cx - u.a * offset, k.cy - u.b * offset)
    if discriminant < EPSILON:
        return [foot]
    half = math.sqrt(discriminant)
    first = (foot[0] - u.b * half, foot[1] + u.a * half)
    second = (foot[0] + u.b * half, foot[1] - u.a * half)
    # same rule as the exact primitives: ordered along the defining direction
    forward = (second[0] - first[0]) * u.dx + (second[1] - first[1]) * u.dy
    return [first, second] if forward > 0 else [second, first]


def _circle_circle(j: Circle, k: Circle) -> list[tuple[float, float]]:
    dx, dy = k.cx - j.cx, k.cy - j.cy
    if abs(dx) < EPSILON and abs(dy) < EPSILON:
        return []
    a, b = 2 * dx, 2 * dy
    c = j.r * j.r - k.r * k.r + (k.cx**2 + k.cy**2) - (j.cx**2 + j.cy**2)
    scale = math.hypot(a, b)
    radical = Line(a / scale, b / scale, c / scale, dx, dy)
    points = _line_circle(radical, j)
    if len(points) < 2:
        return points
    first = points[0]
    cross = dx * (first[1] - j.cy) - dy * (first[0] - j.cx)
    return points if cross > 0 else [points[1], points[0]]


def intersect(first, second) -> list[tuple[float, float]]:
    """Intersect two drawn objects, in the same order the exact code would."""
    if isinstance(first, Line) and isinstance(second, Line):
        return _line_line(first, second)
    if isinstance(first, Circle) and isinstance(second, Circle):
        return _circle_circle(first, second)
    if isinstance(first, Circle):
        first, second = second, first
    return _line_circle(first, second)


@dataclass(frozen=True)
class State:
    points: tuple[tuple[float, float], ...]
    objects: tuple

    def object_keys(self) -> set:
        return {item.key() for item in self.objects}

    def canonical(self) -> tuple:
        """A fingerprint invariant under the similarity that fixes the two givens.

        Two search states that differ only by where the figure sits, how big it
        is, or which way round it faces are the same state; without this the
        search re-explores the same construction endlessly.
        """
        if len(self.points) < 2:
            return tuple(sorted((round(x, ROUNDING), round(y, ROUNDING)) for x, y in self.points))
        origin = self.points[0]
        second = self.points[1]
        dx, dy = second[0] - origin[0], second[1] - origin[1]
        span = math.hypot(dx, dy)
        if span < EPSILON:
            return tuple(sorted(self.points))
        cosine, sine = dx / span, dy / span

        def place(point, flip: float) -> tuple[float, float]:
            px, py = point[0] - origin[0], point[1] - origin[1]
            x = (px * cosine + py * sine) / span
            y = flip * (-px * sine + py * cosine) / span
            return round(x, ROUNDING), round(y, ROUNDING)

        upright = tuple(sorted(place(point, 1.0) for point in self.points))
        mirrored = tuple(sorted(place(point, -1.0) for point in self.points))
        return min(upright, mirrored)
