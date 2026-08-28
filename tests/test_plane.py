"""The plane layer: primitives, intersections and exact predicates."""

from fractions import Fraction

import pytest

from euclid.kernel import Context, sqrt
from euclid.plane import (
    Circle,
    Line,
    Point,
    angle_cmp,
    between,
    circle,
    collinear,
    eq_angle,
    eq_len,
    free_point,
    line,
    meet,
    parallel,
    perpendicular,
    right_angle,
    same_side,
)


def test_line_line_intersection():
    with Context():
        a, b = Point(0, 0), Point(4, 0)
        c, d = Point(2, -1), Point(2, 3)
        (crossing,) = meet(Line.through(a, b), Line.through(c, d))
        assert crossing == Point(2, 0)


def test_parallel_lines_do_not_meet():
    with Context():
        u = Line.through(Point(0, 0), Point(1, 0))
        v = Line.through(Point(0, 1), Point(1, 1))
        assert meet(u, v) == []
        assert parallel(u, v)


def test_equilateral_apex_is_exact():
    """Euclid I.1 in raw primitives: the apex height is exactly sqrt(3)/2."""
    with Context():
        a, b = free_point(0, 0, "A"), free_point(1, 0, "B")
        left = meet(circle(a, b), circle(b, a))[0]
        assert left.x == Fraction(1, 2)
        assert left.y == sqrt(3) / 2
        assert eq_len(a, b, a, left) and eq_len(a, b, b, left)


def test_circle_circle_ordering_is_left_then_right():
    with Context():
        a, b = Point(0, 0, "A"), Point(1, 0, "B")
        upper, lower = meet(circle(a, b), circle(b, a))
        assert upper.y > 0 and lower.y < 0


def test_line_circle_ordering_follows_the_line_direction():
    with Context():
        centre = Point(0, 0)
        k = Circle.centred(centre, Point(2, 0))
        forward = Line.through(Point(-5, 0), Point(5, 0))
        first, second = meet(forward, k)
        assert first == Point(-2, 0) and second == Point(2, 0)
        backward = Line.through(Point(5, 0), Point(-5, 0))
        first, second = meet(backward, k)
        assert first == Point(2, 0) and second == Point(-2, 0)


def test_tangent_line_yields_exactly_one_point():
    with Context():
        k = Circle.centred(Point(0, 0), Point(0, 2))
        tangent = Line.through(Point(-3, 2), Point(3, 2))
        assert meet(tangent, k) == [Point(0, 2)]


def test_disjoint_circles_yield_nothing():
    with Context():
        left = Circle.centred(Point(0, 0), Point(1, 0))
        right = Circle.centred(Point(10, 0), Point(11, 0))
        assert meet(left, right) == []


def test_betweenness_and_sides():
    with Context():
        a, b, c = Point(0, 0), Point(1, 0), Point(3, 0)
        assert between(a, b, c)
        assert not between(b, a, c)
        assert not between(a, c, b)
        base = Line.through(a, c)
        assert same_side(Point(1, 1), Point(2, 5), base)
        assert not same_side(Point(1, 1), Point(2, -5), base)


def test_angle_comparison_distinguishes_obtuse_from_acute():
    """The naive squared-cosine test would call these two angles equal."""
    with Context():
        vertex = Point(0, 0)
        right = Point(1, 0)
        acute = Point(1, 1)
        obtuse = Point(-1, 1)
        assert angle_cmp(right, vertex, acute, right, vertex, obtuse) < 0
        assert not eq_angle(right, vertex, acute, right, vertex, obtuse)
        assert eq_angle(right, vertex, acute, acute, vertex, right)


def test_right_angle_and_perpendicular():
    with Context():
        origin, east, north = Point(0, 0), Point(3, 0), Point(0, 5)
        assert right_angle(east, origin, north)
        assert perpendicular(Line.through(origin, east), Line.through(origin, north))


def test_isosceles_base_angles_are_equal_on_irrational_coordinates():
    with Context():
        apex = Point(0, sqrt(3))
        left, right = Point(-1, 0), Point(1, 0)
        assert eq_len(apex, left, apex, right)
        assert eq_angle(apex, left, right, apex, right, left)


def test_collinearity_survives_irrational_coordinates():
    with Context():
        root = sqrt(2)
        assert collinear(Point(0, 0), Point(root, root), Point(3 * root, 3 * root))
        assert not collinear(Point(0, 0), Point(root, root), Point(3 * root, 2 * root))


def test_zero_radius_circle_is_rejected():
    with Context():
        with pytest.raises(ValueError):
            circle(Point(0, 0, "O"), Point(0, 0, "O"))


def test_coordinates_must_be_exact():
    with Context():
        with pytest.raises(TypeError):
            Point(0.5, 0)
