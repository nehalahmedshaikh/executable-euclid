"""The kernel carries every correctness claim in the project, so it gets the
heaviest tests: field axioms on random tower elements, exactness of sqrt, and
-- most importantly -- that the tower's non-square invariant is maintained."""

import random
from fractions import Fraction

import pytest

from euclid.kernel import Context, Surd, fmt, is_zero, sign, sqrt, to_float
from euclid.kernel.field import _exact_sqrt


def test_rational_sqrt_stays_rational():
    with Context():
        assert sqrt(Fraction(9, 4)) == Fraction(3, 2)
        assert sqrt(0) == 0
        assert sqrt(Fraction(1, 16)) == Fraction(1, 4)


def test_irrational_sqrt_extends_the_tower():
    with Context() as ctx:
        root2 = sqrt(2)
        assert isinstance(root2, Surd)
        assert ctx.tower.depth == 1
        assert root2 * root2 == 2


def test_sqrt_reuses_the_tower_instead_of_stacking_levels():
    """sqrt(8) inside Q(sqrt 2) must collapse to 2*sqrt(2), not add a level."""
    with Context() as ctx:
        root2 = sqrt(2)
        root8 = sqrt(8)
        assert ctx.tower.depth == 1, "sqrt(8) spuriously extended the tower"
        assert root8 == 2 * root2
        assert sqrt(Fraction(1, 2)) == root2 / 2
        assert ctx.tower.depth == 1


def test_sqrt_denests_across_levels():
    """sqrt(5 + 2*sqrt 6) = sqrt 2 + sqrt 3, and the kernel must notice."""
    with Context() as ctx:
        root2, root3 = sqrt(2), sqrt(3)
        depth_before = ctx.tower.depth
        value = 5 + 2 * sqrt(6)
        root = sqrt(value)
        assert ctx.tower.depth == depth_before, "failed to denest; tower grew"
        assert root == root2 + root3
        assert root * root == value


def test_nested_radicals_that_genuinely_need_a_new_level():
    with Context() as ctx:
        inner = 1 + sqrt(2)
        outer = sqrt(inner)
        assert ctx.tower.depth == 2
        assert outer * outer == inner
        assert sign(outer) == 1


def test_zero_test_is_structural_and_exact():
    with Context():
        value = (sqrt(3) + sqrt(2)) * (sqrt(3) - sqrt(2)) - 1
        assert is_zero(value)
        assert sign(value) == 0
        assert value == 0


def test_sign_matches_high_precision_floats():
    random.seed(20250828)
    with Context():
        atoms = [sqrt(2), sqrt(3), sqrt(5), sqrt(7), 1 + sqrt(11)]
        for _ in range(300):
            value = Fraction(random.randint(-20, 20), random.randint(1, 9))
            for atom in random.sample(atoms, k=random.randint(1, 3)):
                value = value + Fraction(random.randint(-9, 9), random.randint(1, 7)) * atom
            approximation = to_float(value)
            if abs(approximation) > 1e-9:
                assert sign(value) == (1 if approximation > 0 else -1)


def test_field_axioms_on_random_elements():
    random.seed(11)
    with Context():
        pool = [Fraction(3, 2), sqrt(2), sqrt(3), 1 + sqrt(5), sqrt(1 + sqrt(2))]
        for _ in range(200):
            x, y, z = (random.choice(pool) for _ in range(3))
            assert x * (y + z) == x * y + x * z
            assert (x + y) + z == x + (y + z)
            assert (x * y) * z == x * (y * z)
            if not is_zero(x):
                assert x * (1 / x) == 1


def test_ordering_is_exact():
    with Context():
        assert sqrt(2) < sqrt(3)
        assert sqrt(2) > 1
        assert 2 > sqrt(3)
        assert sqrt(4) == 2
        golden = (1 + sqrt(5)) / 2
        assert golden * golden == golden + 1


def test_sqrt_always_returns_the_non_negative_root():
    """The descent finds *a* root; a magnitude has to be the positive one.

    (3 - sqrt 5)/2 is a square in Q(sqrt 5), and the recursion naturally
    surfaces 1/2 - sqrt(5/4), which is negative.
    """
    with Context():
        value = (3 - sqrt(5)) / 2
        root = sqrt(value)
        assert sign(root) > 0
        assert root * root == value
        assert root == (sqrt(5) - 1) / 2


def test_negative_sqrt_is_rejected():
    with Context():
        with pytest.raises(ValueError):
            sqrt(-2)


def test_floats_are_rejected_at_the_boundary():
    with Context():
        with pytest.raises(TypeError):
            sqrt(2) + 0.5


def test_exact_sqrt_reports_failure_rather_than_guessing():
    with Context() as ctx:
        sqrt(2)
        assert _exact_sqrt(ctx.tower, Fraction(3), ctx.tower.depth) is None


def test_formatting_is_readable():
    with Context():
        assert fmt(sqrt(2)) == "sqrt(2)"
        assert fmt((1 + sqrt(5)) / 2) == "1/2 + 1/2*sqrt(5)"
        assert fmt(1 - sqrt(2)) == "1 - sqrt(2)"


def test_contexts_are_isolated():
    with Context() as first:
        sqrt(2)
        assert first.tower.depth == 1
    with Context() as second:
        assert second.tower.depth == 0
