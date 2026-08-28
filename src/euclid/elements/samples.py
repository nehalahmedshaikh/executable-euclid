"""Input generators for the propositions.

The fuzzer needs configurations that satisfy a proposition's hypotheses
*exactly*, which rules out picking coordinates at random and hoping.  Two
devices do the work:

* **Rational rotations.**  For any rational ``t`` the pair
  ``((1-t^2)/(1+t^2), 2t/(1+t^2))`` is an exact unit vector, so we can rotate a
  figure through a genuinely varying angle without leaving the rationals.
* **Build square, then move.**  Configurations are laid out in convenient
  coordinates (a base along the x-axis, parallels at a fixed height) and then
  pushed through a random similarity.  Shape varies through the parameters;
  position and orientation vary through the frame.

Sampled points are plain :class:`Point` values.  The registry labels them and
records them as the figure's givens when the proposition is called.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Callable, Iterable

from ..plane.objects import Point

__all__ = [
    "frame",
    "nonzero",
    "rational_rotation",
    "scalar",
]


def scalar(rng, low: int = -6, high: int = 6, denominators: Iterable[int] = (1, 1, 2, 3, 4)) -> Fraction:
    return Fraction(rng.randint(low, high), rng.choice(list(denominators)))


def nonzero(rng, low: int = 1, high: int = 6, denominators: Iterable[int] = (1, 1, 2, 3)) -> Fraction:
    value = Fraction(rng.randint(low, high), rng.choice(list(denominators)))
    return value if value != 0 else Fraction(1)


def rational_rotation(rng) -> tuple[Fraction, Fraction]:
    """An exact unit vector ``(cos, sin)`` with rational entries."""
    t = Fraction(rng.randint(-5, 5), rng.randint(1, 5))
    denominator = 1 + t * t
    return (1 - t * t) / denominator, 2 * t / denominator


def frame(rng, allow_reflection: bool = True, scaled: bool = True) -> Callable[[Point], Point]:
    """A random similarity of the plane, exact in the rationals."""
    cosine, sine = rational_rotation(rng)
    scale = nonzero(rng, 1, 4) if scaled else Fraction(1)
    shift_x, shift_y = scalar(rng), scalar(rng)
    flip = -1 if (allow_reflection and rng.random() < 0.5) else 1

    def transform(point: Point) -> Point:
        x, y = point.x, point.y * flip
        return Point(scale * (cosine * x - sine * y) + shift_x, scale * (sine * x + cosine * y) + shift_y)

    return transform


def isometry(rng) -> Callable[[Point], Point]:
    """A random rigid motion (rotation, reflection, translation -- no scaling).

    Congruence hypotheses are statements about *lengths*, so the samplers for
    I.4, I.8, I.24 and I.26 must move figures without resizing them.
    """
    return frame(rng, allow_reflection=True, scaled=False)


# ---------------------------------------------------------------------------
# configurations
# ---------------------------------------------------------------------------


def segment(rng) -> tuple[Point, Point]:
    move = frame(rng)
    length = nonzero(rng, 1, 6)
    return move(Point(0, 0)), move(Point(length, 0))


def point_and_segment(rng) -> tuple[Point, Point, Point]:
    """A point A, and a segment BC, all in general position."""
    move = frame(rng)
    a = move(Point(scalar(rng), nonzero(rng, 1, 5)))
    b = move(Point(0, 0))
    c = move(Point(nonzero(rng, 1, 6), 0))
    return a, b, c


def unequal_segments(rng) -> tuple[Point, Point, Point, Point]:
    """Segments AB and CD with AB strictly the greater."""
    move = frame(rng)
    greater = nonzero(rng, 4, 9)
    lesser = Fraction(greater, 2) - Fraction(rng.randint(0, 2), 4)
    a, b = move(Point(0, 0)), move(Point(greater, 0))
    c = move(Point(scalar(rng), nonzero(rng, 2, 5)))
    d = Point(c.x + lesser, c.y)
    return a, b, c, d


def triangle(rng) -> tuple[Point, Point, Point]:
    move = frame(rng)
    base = nonzero(rng, 2, 7)
    apex_x = scalar(rng, -3, 6)
    apex_y = nonzero(rng, 1, 6)
    return move(Point(0, 0)), move(Point(base, 0)), move(Point(apex_x, apex_y))


def acute_triangle(rng) -> tuple[Point, Point, Point]:
    move = frame(rng)
    base = nonzero(rng, 4, 7)
    apex_x = Fraction(base, 2) + Fraction(rng.randint(-2, 2), 4)
    apex_y = nonzero(rng, 3, 7)
    return move(Point(0, 0)), move(Point(base, 0)), move(Point(apex_x, apex_y))


def isosceles(rng) -> tuple[Point, Point, Point]:
    """Apex A with AB = AC, built by reflecting B in the axis through A."""
    move = frame(rng)
    half_base = nonzero(rng, 1, 5)
    height = nonzero(rng, 1, 6)
    return move(Point(0, height)), move(Point(-half_base, 0)), move(Point(half_base, 0))


def right_triangle(rng) -> tuple[Point, Point, Point]:
    """Right angle at B."""
    move = frame(rng)
    legs = (nonzero(rng, 1, 6), nonzero(rng, 1, 6))
    return move(Point(legs[0], 0)), move(Point(0, 0)), move(Point(0, legs[1]))


def angle_config(rng) -> tuple[Point, Point, Point]:
    """A rectilinear angle ABC with its vertex at B."""
    move = frame(rng)
    cosine, sine = rational_rotation(rng)
    if sine == 0:
        cosine, sine = Fraction(3, 5), Fraction(4, 5)
    first = nonzero(rng, 1, 5)
    second = nonzero(rng, 1, 5)
    return (
        move(Point(first, 0)),
        move(Point(0, 0)),
        move(Point(second * cosine, second * sine)),
    )


def point_on_segment(rng) -> tuple[Point, Point, Point]:
    """A, B and a point C strictly between them."""
    move = frame(rng)
    total = nonzero(rng, 4, 8)
    cut = Fraction(rng.randint(1, 3), 4) * total
    return move(Point(0, 0)), move(Point(total, 0)), move(Point(cut, 0))


def line_and_external_point(rng) -> tuple[Point, Point, Point]:
    """A line AB and a point C not on it."""
    move = frame(rng)
    span = nonzero(rng, 3, 8)
    return (
        move(Point(0, 0)),
        move(Point(span, 0)),
        move(Point(scalar(rng, -2, 8), nonzero(rng, 1, 5))),
    )


def straight_line_with_ray(rng) -> tuple[Point, Point, Point, Point]:
    """A, B, C collinear with B between, and D off the line: Euclid's I.13 figure."""
    move = frame(rng)
    left, right = nonzero(rng, 2, 6), nonzero(rng, 2, 6)
    return (
        move(Point(-left, 0)),
        move(Point(0, 0)),
        move(Point(right, 0)),
        move(Point(scalar(rng, -3, 3), nonzero(rng, 1, 5))),
    )


def crossing_lines(rng) -> tuple[Point, Point, Point, Point]:
    """Two lines AB and CD which cross between their endpoints."""
    move = frame(rng)
    cosine, sine = rational_rotation(rng)
    if sine == 0:
        cosine, sine = Fraction(3, 5), Fraction(4, 5)
    reach = nonzero(rng, 2, 5)
    other = nonzero(rng, 2, 5)
    return (
        move(Point(-reach, 0)),
        move(Point(reach, 0)),
        move(Point(-other * cosine, -other * sine)),
        move(Point(other * cosine, other * sine)),
    )


def triangle_with_interior_point(rng) -> tuple[Point, Point, Point, Point]:
    move = frame(rng)
    base = nonzero(rng, 4, 8)
    apex_x, apex_y = Fraction(base, 2), nonzero(rng, 3, 7)
    weights = [Fraction(rng.randint(1, 4)) for _ in range(3)]
    total = sum(weights)
    corners = [Point(0, 0), Point(base, 0), Point(apex_x, apex_y)]
    inner_x = sum(w * p.x for w, p in zip(weights, corners)) / total
    inner_y = sum(w * p.y for w, p in zip(weights, corners)) / total
    return (
        move(corners[0]),
        move(corners[1]),
        move(corners[2]),
        move(Point(inner_x, inner_y)),
    )


def parallelogram(rng) -> tuple[Point, Point, Point, Point]:
    """ABCD with AB parallel to DC and AD parallel to BC."""
    move = frame(rng)
    base = nonzero(rng, 2, 6)
    lean = scalar(rng, -3, 3)
    height = nonzero(rng, 1, 5)
    return (
        move(Point(0, 0)),
        move(Point(base, 0)),
        move(Point(base + lean, height)),
        move(Point(lean, height)),
    )


def two_parallelograms_same_base(rng) -> tuple[Point, Point, Point, Point, Point, Point]:
    """ABCD and ABFE on the base AB and in the same parallels."""
    move = frame(rng)
    base = nonzero(rng, 3, 7)
    height = nonzero(rng, 2, 5)
    first_lean = scalar(rng, -3, 3)
    second_lean = first_lean + nonzero(rng, 1, 4)
    return (
        move(Point(0, 0)),
        move(Point(base, 0)),
        move(Point(base + first_lean, height)),
        move(Point(first_lean, height)),
        move(Point(base + second_lean, height)),
        move(Point(second_lean, height)),
    )


def triangles_same_base(rng) -> tuple[Point, Point, Point, Point]:
    """Triangles ABC and ABD on the base AB and in the same parallels.

    The two apexes must differ: otherwise there is no line CD to be parallel
    to the base, and Postulate 1 has nothing to join.
    """
    move = frame(rng)
    base = nonzero(rng, 3, 7)
    height = nonzero(rng, 2, 5)
    first = scalar(rng, -3, 6)
    second = first
    while second == first:
        second = scalar(rng, -3, 6)
    return (
        move(Point(0, 0)),
        move(Point(base, 0)),
        move(Point(first, height)),
        move(Point(second, height)),
    )


def triangles_equal_bases(rng) -> tuple[Point, Point, Point, Point, Point, Point]:
    """Triangles ABC and DEF on equal bases along one line, in the same parallels."""
    move = frame(rng)
    base = nonzero(rng, 2, 5)
    gap = nonzero(rng, 1, 4)
    height = nonzero(rng, 2, 5)
    first = scalar(rng, -2, 4)
    second = scalar(rng, -2, 4)
    while base + gap + second == first:  # the two apexes must not coincide
        second = scalar(rng, -2, 4)
    return (
        move(Point(0, 0)),
        move(Point(base, 0)),
        move(Point(first, height)),
        move(Point(base + gap, 0)),
        move(Point(2 * base + gap, 0)),
        move(Point(base + gap + second, height)),
    )


def quadrilateral(rng) -> tuple[Point, Point, Point, Point]:
    """A convex quadrilateral, the "given rectilinear figure" of I.45."""
    move = frame(rng)
    width = nonzero(rng, 3, 7)
    height = nonzero(rng, 2, 6)
    return (
        move(Point(0, 0)),
        move(Point(width, 0)),
        move(Point(width - Fraction(rng.randint(0, 2), 2), height)),
        move(Point(Fraction(rng.randint(0, 2), 2), height)),
    )
