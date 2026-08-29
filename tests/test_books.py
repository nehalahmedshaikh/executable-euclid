"""Books II through X."""

from fractions import Fraction

import pytest

import euclid.elements  # noqa: F401
from euclid.elements import all_propositions, run
from euclid.elements.book05 import anthyphairesis, commensurable, separating_witness
from euclid.elements.book07_09 import gcd, is_perfect, is_prime
from euclid.elements.book10 import (
    SPECIES,
    classify,
    commensurable_in_square,
    is_medial,
    is_medial_area,
    is_rational_in_square,
)
from euclid.kernel import Context, sqrt
from euclid.plane import Point
from euclid.verify import certify

BEYOND_BOOK_I = [entry for entry in all_propositions() if entry.book != "I"]


@pytest.mark.parametrize("entry", BEYOND_BOOK_I, ids=lambda entry: entry.ref)
def test_proposition_is_certified(entry):
    report = certify(entry.ref, trials=6)
    assert not report.failures, report.failures[0].message
    assert report.verified > 0, f"{entry.ref}: no valid configuration was sampled"


# ---------------------------------------------------------------------------
# Book II and IV: the golden section and the pentagon
# ---------------------------------------------------------------------------


def test_the_golden_section_is_exact():
    with Context():
        result = run("II.11", Point(0, 0), Point(1, 0))
        cut = result.value.section
        assert cut.x == (sqrt(5) - 1) / 2
        assert cut.y == 0


def test_the_pentagon_is_regular_and_lives_in_the_field_of_sqrt_five():
    with Context() as context:
        result = run("IV.11", Point(0, 0), Point(1, 0))
        vertices = result.value.pentagon
        assert len(vertices) == 5
        assert len(set(vertices)) == 5
        first = vertices[0]
        for index in range(5):
            here, following = vertices[index], vertices[(index + 1) % 5]
            side = (following.x - here.x) ** 2 + (following.y - here.y) ** 2
            reference = (vertices[1].x - first.x) ** 2 + (vertices[1].y - first.y) ** 2
            assert side == reference
        assert any(radicand == 5 for radicand in context.tower.radicands)


# ---------------------------------------------------------------------------
# Book V: Eudoxus
# ---------------------------------------------------------------------------


def test_equal_ratios_admit_no_separating_equimultiples():
    with Context():
        assert separating_witness(Fraction(2), Fraction(3), Fraction(4), Fraction(6)) is None
        assert separating_witness(sqrt(2), Fraction(1), sqrt(8), Fraction(2)) is None


def test_unequal_ratios_always_yield_a_witness():
    with Context():
        witness = separating_witness(Fraction(2), Fraction(3), Fraction(5), Fraction(7))
        assert witness is not None
        m, n = witness
        # n/m separates 2/3 from 5/7
        assert Fraction(2, 3) < Fraction(n, m) <= Fraction(5, 7)


def test_a_witness_exists_even_for_very_close_ratios():
    with Context():
        witness = separating_witness(Fraction(1000), Fraction(1001), Fraction(1001), Fraction(1002))
        assert witness is not None


def test_anthyphairesis_terminates_exactly_when_commensurable():
    with Context():
        _, ended = anthyphairesis(Fraction(35), Fraction(15))
        assert ended
        assert commensurable(Fraction(35), Fraction(15))

        quotients, ended = anthyphairesis(sqrt(2), Fraction(1), steps=12)
        assert not ended, "the diagonal and the side have no common measure"
        assert not commensurable(sqrt(2), Fraction(1))
        # the continued fraction of sqrt(2) is [1; 2, 2, 2, ...]
        assert quotients[:5] == [1, 2, 2, 2, 2]


# ---------------------------------------------------------------------------
# Books VII-IX: arithmetic
# ---------------------------------------------------------------------------


def test_euclidean_algorithm():
    assert gcd(1071, 462) == 21
    assert gcd(17, 5) == 1


def test_infinitude_of_primes_is_constructive():
    with Context():
        result = run("IX.20", [2, 3, 5, 7, 11, 13])
        assert result.value.new_prime not in (2, 3, 5, 7, 11, 13)
        assert is_prime(result.value.new_prime)
        assert result.value.from_product == 30031


def test_perfect_numbers_from_mersenne_primes():
    with Context():
        assert run("IX.36", 2).value.perfect == 6
        assert run("IX.36", 3).value.perfect == 28
        assert run("IX.36", 5).value.perfect == 496
        assert run("IX.36", 7).value.perfect == 8128
        assert all(is_perfect(n) for n in (6, 28, 496, 8128))


# ---------------------------------------------------------------------------
# Book X: the classifier
# ---------------------------------------------------------------------------


def test_rational_and_medial():
    with Context():
        assert classify(Fraction(3, 2)).name == "rational"
        assert classify(sqrt(5)).name == "rational (commensurable in square only)"
        assert is_rational_in_square(sqrt(5))
        fourth_root = sqrt(sqrt(2))
        assert is_medial(fourth_root)
        assert classify(fourth_root).name == "medial"


@pytest.mark.parametrize(
    "build, expected",
    [
        (lambda: 3 + sqrt(2), "fourth binomial"),
        (lambda: 1 + sqrt(5), "fifth binomial"),
        (lambda: sqrt(2) + sqrt(3), "sixth binomial"),
        (lambda: 3 - sqrt(2), "fourth apotome"),
        (lambda: sqrt(5) - 1, "fifth apotome"),
        (lambda: sqrt(3) - sqrt(2), "sixth apotome"),
    ],
)
def test_binomials_and_apotomes_get_their_species(build, expected):
    with Context():
        assert classify(build()).name == expected


def test_the_first_binomial_needs_a_commensurable_difference():
    """First binomial (X.48): the greater term is commensurable with the assigned
    line, and sqrt(a^2 - b^2) is commensurable with the greater."""
    with Context():
        assert classify(5 + sqrt(16)).name == "rational", "sqrt(16) is not irrational"
        # 25 - 24 = 1, a rational square, and 1 is commensurable with 5
        assert classify(5 + sqrt(24)).name == "first binomial"
        # 25 - 20 = 5, whose root is incommensurable with 5
        assert classify(5 + sqrt(20)).name == "fourth binomial"


def test_commensurable_terms_are_not_a_binomial():
    """sqrt(18) + sqrt(2) is really 4*sqrt(2): one term, not two."""
    with Context():
        value = sqrt(18) + sqrt(2)
        assert value == 4 * sqrt(2)
        assert classify(value).name == "rational (commensurable in square only)"


def test_bimedials():
    with Context():
        quarter = sqrt(sqrt(2))
        first_bimedial = quarter + sqrt(2) * quarter
        assert classify(first_bimedial).name == "first bimedial"
        assert classify(sqrt(2) * quarter - quarter).name == "first apotome of a medial line"


def test_the_second_bimedial_needs_a_medial_rectangle():
    """X.38: the rectangle is a *medial area*, which is one square shallower
    than a medial line -- irrational with a rational square."""
    with Context():
        quarter = sqrt(sqrt(2))
        greater = sqrt(3) * quarter
        assert is_medial(quarter) and is_medial(greater)
        assert is_medial_area(greater * quarter)  # sqrt 6
        assert classify(greater + quarter).name == "second bimedial"
        assert classify(greater - quarter).name == "second apotome of a medial line"


def test_medial_terms_must_be_commensurable_in_square():
    """"In square only" is two conditions. 3^(1/4) and 6^(1/4) are both medial
    and incommensurable, but their squares are incommensurable too, so the sum
    is not a bimedial at all."""
    with Context():
        a, b = sqrt(sqrt(3)), sqrt(sqrt(2)) * sqrt(sqrt(3))
        assert is_medial(a) and is_medial(b)
        assert not commensurable_in_square(a, b)
        assert "bimedial" not in classify(a + b).name


def _pair(square_sum, rectangle):
    """The two lines u > v > 0 with u^2 + v^2 and uv as given."""
    root = sqrt(square_sum * square_sum - 4 * rectangle * rectangle)
    return sqrt((square_sum + root) / 2), sqrt((square_sum - root) / 2)


@pytest.mark.parametrize(
    "square_sum, rectangle, added, subtracted",
    [
        # X.39 / X.76: squares rational, rectangle medial
        (Fraction(1), lambda: sqrt(2) / 4, "major", "minor"),
        # X.40 / X.77: squares medial, rectangle rational
        (None, lambda: Fraction(1, 2),
         "the side of a rational plus a medial area",
         "that which produces with a rational area a medial whole"),
        # X.41 / X.78: both medial, and incommensurable with one another
        (None, lambda: sqrt(3) / 2,
         "the side of the sum of two medial areas",
         "that which produces with a medial area a medial whole"),
    ],
)
def test_the_species_compounded_of_incommensurable_squares(
    square_sum, rectangle, added, subtracted
):
    """X.39-41 and their duals.

    These six are the species the basis expansion cannot see: u and v are the
    two roots of one quadratic, so v lies inside the extension u generates and
    the sum shows no seam. They are recovered by squaring.
    """
    with Context():
        total = Fraction(1) if square_sum is not None else sqrt(5)
        u, v = _pair(total, rectangle())
        assert not commensurable_in_square(u, v)
        assert classify(u + v).name == added
        assert classify(u - v).name == subtracted


def test_every_one_of_the_thirteen_species_is_reachable():
    """The taxonomy is finished: nothing named in Book X is unimplemented."""
    with Context():
        quarter = sqrt(sqrt(2))
        witnesses = [
            quarter,                                    # medial
            3 + sqrt(2), 3 - sqrt(2),                   # binomial, apotome
            quarter + sqrt(2) * quarter,                # first bimedial
            sqrt(2) * quarter - quarter,                # first apotome of a medial
            sqrt(3) * quarter + quarter,                # second bimedial
            sqrt(3) * quarter - quarter,                # second apotome of a medial
        ]
        named = {classify(value).family for value in witnesses}
        assert named == {"medial", "binomial", "apotome", "medial-based"}

        found = set()
        for total, rectangle in ((Fraction(1), sqrt(2) / 4), (sqrt(5), Fraction(1, 2)),
                                 (sqrt(5), sqrt(3) / 2)):
            u, v = _pair(total, rectangle)
            found.add(classify(u + v).name)
            found.add(classify(u - v).name)
        assert found == {
            "major", "minor",
            "the side of a rational plus a medial area",
            "that which produces with a rational area a medial whole",
            "the side of the sum of two medial areas",
            "that which produces with a medial area a medial whole",
        }
        assert found <= set(SPECIES)


def test_the_golden_ratio_is_a_fifth_binomial():
    with Context():
        assert classify((1 + sqrt(5)) / 2).name == "fifth binomial"


def test_classification_reports_its_reasoning():
    with Context():
        report = classify(3 + sqrt(2)).report()
        assert "fourth binomial" in report
        assert "commensurable" in report
