"""The solid kernel, checked before anything is built on it.

Book XI is where Euclid stops having postulates, so the thing most worth
pinning is not that the arithmetic works -- it is that the encoding says so.
Every primitive in space is recorded as unlicensed, and these tests fail if one
quietly borrows a postulate from the plane.
"""

from fractions import Fraction as F

import pytest

from euclid.kernel.field import (
    Context,
    Pythagorean,
    Rational,
    RootNotInField,
    is_zero,
    sqrt,
    to_float,
)
from euclid.plane.construct import GeometryError
from euclid.plane.objects import Line, Point
from euclid.plane.trace import Trace, pop_trace, push_trace
from euclid.solid.angles import SolidAngle, angle_at3, dihedral, length3
from euclid.solid.construct import (
    line3,
    meet_line_plane,
    meet_line_sphere,
    meet_planes,
    plane_through,
    posit3,
    sphere_through,
)
from euclid.solid.objects import Line3, Plane, Point3, Sphere
from euclid.solid.predicates import (
    collinear3,
    coplanar,
    len2,
    on_plane,
    on_sphere,
    same_side_of_plane,
    volume6,
)


# --------------------------------------------------------------------------
# the representation, against the one it was promoted from
# --------------------------------------------------------------------------


def test_a_plane_names_its_sides_as_a_line_does():
    """``Plane`` is ``Line`` with one more coefficient, so it must agree with it.

    Laid in the *xy* plane, a vertical plane through two points cuts space the
    way the line through those points cuts the plane, and the two ``side_of``
    calls should say the same of every witness.
    """
    with Context("test:sides"):
        flat = Line.through(Point(0, 0), Point(2, 1))
        upright = Plane.through(Point3(0, 0, 0), Point3(2, 1, 0), Point3(0, 0, 1))
        for x, y in ((3, 0), (0, 3), (-2, 5), (4, 2), (1, F(1, 2))):
            assert flat.side_of(Point(x, y)) == upright.side_of(Point3(x, y, 0))
            # and off the plane, since the third coordinate must not matter
            assert upright.side_of(Point3(x, y, 7)) == flat.side_of(Point(x, y))


def test_equal_planes_are_equal_however_they_were_drawn():
    with Context("test:plane-eq"):
        first = Plane.through(Point3(0, 0, 0), Point3(1, 0, 0), Point3(0, 1, 0))
        second = Plane.through(Point3(3, 4, 0), Point3(-1, 0, 0), Point3(0, 9, 0))
        assert first == second and hash(first) == hash(second)


def test_three_points_in_a_line_describe_no_plane():
    with Context("test:degenerate"):
        with pytest.raises(GeometryError):
            plane_through(Point3(0, 0, 0), Point3(1, 1, 1), Point3(2, 2, 2))


def test_a_line_in_space_is_the_same_line_from_either_pair_of_its_points():
    """``Line3`` cannot normalise coefficients the way ``Plane`` does, so its
    equality is collinearity of both points and this is worth checking."""
    with Context("test:line3"):
        first = Line3.through(Point3(0, 0, 0), Point3(1, 2, 3))
        assert first == Line3.through(Point3(2, 4, 6), Point3(-1, -2, -3))
        assert first != Line3.through(Point3(0, 0, 1), Point3(1, 2, 4))


def test_the_triple_product_decides_coplanarity_and_names_the_side():
    with Context("test:volume"):
        o, x, y = Point3(0, 0, 0), Point3(1, 0, 0), Point3(0, 1, 0)
        assert coplanar(o, x, y, Point3(5, -3, 0))
        assert not coplanar(o, x, y, Point3(0, 0, 1))
        above, below = volume6(o, x, y, Point3(0, 0, 1)), volume6(o, x, y, Point3(0, 0, -1))
        assert above == -below
        assert collinear3(o, x, Point3(3, 0, 0))


def test_a_sphere_keeps_its_radius_squared():
    with Context("test:sphere"):
        ball = Sphere.centred(Point3(0, 0, 0), Point3(1, 1, 1))
        assert ball.r2 == 3  # and no root was taken to say so
        assert on_sphere(Point3(1, 1, 1), ball)
        with pytest.raises(ValueError):
            Sphere.centred(Point3(0, 0, 0), Point3(0, 0, 0))


# --------------------------------------------------------------------------
# the field: a length in space is a hypotenuse
# --------------------------------------------------------------------------


def test_a_distance_in_space_is_admitted_by_the_pythagorean_field():
    """``sqrt(x^2 + y^2 + z^2)`` is ``sqrt(sqrt(x^2 + y^2)^2 + z^2)``.

    An iterated hypotenuse, so it belongs to the Pythagorean field exactly as a
    plane distance does. Requiring the witness to be a pair would have put every
    solid length outside the rung and made it useless for Books XI to XIII.
    """
    with Context("test:pyth", policy=Pythagorean()):
        assert to_float(length3(Point3(0, 0, 0), Point3(1, 1, 1))) == pytest.approx(3 ** 0.5)
        assert length3(Point3(0, 0, 0), Point3(1, 2, 2)) == 3  # rational, no extension


def test_a_solid_length_is_still_refused_over_the_rationals():
    with Context("test:rational", policy=Rational()):
        with pytest.raises(RootNotInField):
            length3(Point3(0, 0, 0), Point3(1, 1, 1))


def test_the_witness_is_checked_and_not_taken_on_trust():
    """A root that is no sum of squares must be refused even with a witness."""
    with Context("test:witness", policy=Pythagorean()):
        with pytest.raises(RootNotInField):
            sqrt(F(7), witness=(F(1), F(1), F(1)))  # 3, not 7


# --------------------------------------------------------------------------
# angles
# --------------------------------------------------------------------------


def test_an_angle_in_space_carries_a_cosine_and_no_sine():
    """There is no side to be on in space, so there is no sine to store."""
    with Context("test:angle"):
        right = angle_at3(Point3(1, 0, 0), Point3(0, 0, 0), Point3(0, 1, 0))
        assert right.cos == 0
        assert not hasattr(right, "sin")
        straight = angle_at3(Point3(1, 0, 0), Point3(0, 0, 0), Point3(-1, 0, 0))
        assert straight.cos == -1
        assert straight.cos < right.cos and right < straight  # larger angle, smaller cosine


def test_the_dihedral_angle_of_two_perpendicular_planes_is_right():
    with Context("test:dihedral"):
        o = Point3(0, 0, 0)
        flat = Plane.through(o, Point3(1, 0, 0), Point3(0, 1, 0))
        upright = Plane.through(o, Point3(1, 0, 0), Point3(0, 0, 1))
        assert dihedral(flat, upright) == SolidAngle(0)


# --------------------------------------------------------------------------
# the instruction set, and what licenses it
# --------------------------------------------------------------------------


@pytest.fixture
def drawn():
    """One figure using every solid primitive, with its trace."""
    with Context("test:instructions"):
        trace = push_trace(Trace(proposition="test:solid"))
        try:
            centre = posit3(Point3(0, 0, 0), "O")
            flat = plane_through(centre, Point3(1, 0, 0), Point3(0, 1, 0), "the plane")
            upright = plane_through(centre, Point3(1, 0, 0), Point3(0, 0, 1), "upright")
            meet_planes(flat, upright)
            ball = sphere_through(centre, Point3(1, 0, 0), "the sphere")
            through = line3(Point3(0, 0, -2), Point3(0, 0, 5), "a line")
            meet_line_plane(through, flat)
            meet_line_sphere(through, ball)
        finally:
            pop_trace()
        yield trace


def test_no_solid_primitive_claims_a_postulate(drawn):
    """The finding, as a test.

    Postulates 1 to 5 are postulates of the plane. A solid primitive that named
    one would be borrowing a licence the Elements does not give, and the whole
    point of Book XI's ledger is that there is none to borrow.
    """
    borrowed = [(move.kind, move.postulate) for move in drawn.moves if move.postulate]
    assert not borrowed, f"solid moves claiming a postulate: {borrowed}"


def test_every_solid_intersection_is_recorded_as_unlicensed(drawn):
    assert drawn.intersections, "the figure should have used intersection"
    licensed = [event.kind for event in drawn.intersections
                if event.guaranteed_by_postulates]
    assert not licensed, f"solid intersections claiming a postulate: {licensed}"
    assert {event.kind for event in drawn.intersections} == {
        "plane-plane", "line-plane", "line-sphere"}


def test_the_intersections_land_where_they_say(drawn):
    """The recording would be worth nothing if the arithmetic were wrong."""
    with Context("test:lands"):
        o = Point3(0, 0, 0)
        flat = plane_through(o, Point3(1, 0, 0), Point3(0, 1, 0))
        upright = plane_through(o, Point3(1, 0, 0), Point3(0, 0, 1))
        section = meet_planes(flat, upright)
        assert on_plane(section.p, flat) and on_plane(section.p, upright)
        assert section.holds(Point3(5, 0, 0))

        through = line3(Point3(0, 0, -2), Point3(0, 0, 5))
        assert meet_line_plane(through, flat) == o
        ball = sphere_through(o, Point3(1, 0, 0))
        assert sorted(p.z for p in meet_line_sphere(through, ball)) == [-1, 1]


def test_parallel_planes_have_no_common_section():
    with Context("test:parallel"):
        low = plane_through(Point3(0, 0, 0), Point3(1, 0, 0), Point3(0, 1, 0))
        high = plane_through(Point3(0, 0, 1), Point3(1, 0, 1), Point3(0, 1, 1))
        with pytest.raises(GeometryError):
            meet_planes(low, high)


def test_a_line_that_misses_the_sphere_says_so():
    with Context("test:miss"):
        ball = sphere_through(Point3(0, 0, 0), Point3(1, 0, 0))
        away = line3(Point3(5, 0, -1), Point3(5, 0, 1))
        with pytest.raises(GeometryError):
            meet_line_sphere(away, ball)


def test_the_side_of_a_plane_is_strict():
    with Context("test:strict-side"):
        flat = Plane.through(Point3(0, 0, 0), Point3(1, 0, 0), Point3(0, 1, 0))
        assert same_side_of_plane(Point3(0, 0, 1), Point3(3, 3, 5), flat)
        assert not same_side_of_plane(Point3(0, 0, 1), Point3(0, 0, -1), flat)
        # a point on the plane is on neither side
        assert not same_side_of_plane(Point3(0, 0, 0), Point3(0, 0, 1), flat)


def test_coordinates_in_space_stay_exact():
    with Context("test:exact"):
        with pytest.raises(TypeError):
            Point3(0.5, 0, 0)
        assert is_zero(len2(Point3(F(1, 3), 0, 0), Point3(F(1, 3), 0, 0)))


# --------------------------------------------------------------------------
# moving a solid figure, and drawing it
# --------------------------------------------------------------------------


def test_a_frame_of_space_is_exact_and_keeps_every_distance():
    """Rotations of space come from an integer quaternion, so they are rational.

    A proposition that held only for the figure as the sampler placed it has not
    been tested, so the figure is moved first -- and the move must not disturb
    what is about to be measured.
    """
    import random

    from euclid.elements.samples import frame3

    rng = random.Random(11)
    with Context("test:frame3"):
        for _ in range(6):
            move = frame3(rng, scaled=False)
            a, b, c = Point3(1, 2, 3), Point3(-2, 0, 5), Point3(F(1, 3), 4, -1)
            assert len2(a, b) == len2(move(a), move(b))
            assert len2(b, c) == len2(move(b), move(c))
            # and it is a genuine motion, not the identity dressed up
            assert move(a) != a or move(b) != b


def test_the_projection_shows_the_figure_and_not_a_squashed_one():
    """The two axes are equal in length and at right angles, so the map is a
    similarity: a length across the line of sight keeps its ratio to every
    other. Unequal axes would draw a cube as a cuboid."""
    from euclid.render.project import DIRECTIONS, _scale2, project_point

    with Context("test:similarity"):
        direction = DIRECTIONS[0]  # (2, 3, 6), of length 7
        scale = _scale2(direction)
        origin = project_point(Point3(0, 0, 0), direction)
        for across in (Point3(3, -6, 2), Point3(6, 2, -3), Point3(9, -4, -1)):
            assert is_zero(sum(a * b for a, b in
                               zip((across.x, across.y, across.z), direction)))
            here = project_point(across, direction)
            flat = (here.x - origin.x) ** 2 + (here.y - origin.y) ** 2
            assert flat == len2(Point3(0, 0, 0), across) * scale


def test_every_direction_offered_has_a_whole_number_length():
    """Which is what lets the axes be equalised without leaving the rationals."""
    from euclid.render.project import DIRECTIONS, _reach

    for direction in DIRECTIONS:
        reach = _reach(direction)
        assert reach * reach == sum(c * c for c in direction)


def test_a_solid_figure_reaches_the_renderer_as_plane_objects():
    """``svg.py`` is not taught about space; the projection stands in front."""
    from euclid.render.project import flatten
    from euclid.render.svg import _collect, render_trace

    with Context("test:flatten"):
        trace = push_trace(Trace(proposition="test:cube"))
        try:
            corners = [posit3(Point3(x, y, z), f"V{x}{y}{z}")
                       for x in (0, 1) for y in (0, 1) for z in (0, 1)]
            for near in corners:
                for far in corners:
                    step = (near.x - far.x, near.y - far.y, near.z - far.z)
                    if (sum(1 for c in step if c != 0) == 1
                            and (near.x, near.y, near.z) < (far.x, far.y, far.z)):
                        line3(near, far)
            plane_through(corners[0], corners[1], corners[2], "a face")
            sphere_through(Point3(0, 0, 0), Point3(1, 0, 0))
        finally:
            pop_trace()

        shadow = flatten(trace)
        assert all(isinstance(move.obj, (Point, Line, type(None)))
                   or type(move.obj).__name__ == "Circle"
                   for move in shadow.moves), "a solid object reached the renderer"
        points, lines, circles = _collect(shadow)
        assert (len(points), len(lines), len(circles)) == (8, 12, 1)
        assert "<svg" in render_trace(shadow, "test:cube")


def test_a_trace_with_nothing_solid_in_it_is_left_alone():
    from euclid.render.project import flatten

    plain = Trace(proposition="test:plane-only")
    assert flatten(plain) is plain


def test_the_chosen_direction_keeps_distinct_vertices_distinct():
    from euclid.render.project import DIRECTIONS, separates

    with Context("test:separates"):
        corners = [Point3(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
        assert separates(corners, DIRECTIONS[0])
        # a direction along an edge collapses two pairs of the cube's vertices
        assert not separates(corners, (F(1), F(0), F(0)))
