"""Every proposition certified, and the facts each book is worth pinning.

Corpus-wide invariants are in test_corpus.py; the dependency graph is in
test_graph.py. What is here is per-book: the certification sweep, and the
results that would still pass a sweep while being wrong.
"""

import collections
import math
import random
from fractions import Fraction

import pytest

import euclid.elements  # noqa: F401
from euclid.elements import all_propositions, run, run_sampled
from euclid.elements.book05 import anthyphairesis, commensurable, separating_witness
from euclid.elements.arithmetic import gcd, is_prime
from euclid.elements.book09 import is_perfect
from euclid.elements.book10 import (
    SPECIES,
    classify,
    commensurable_in_square,
    is_medial,
    is_medial_area,
    is_rational_in_square,
)
from euclid.kernel import Context, sqrt
from euclid.kernel.field import to_float
from euclid.plane import Point, eq_len, len2, right_angle

PLANE_XIII = [entry for entry in all_propositions()
              if entry.book == "XIII" and entry.number <= 12]


# ---------------------------------------------------------------------------
# Book II and IV: the golden section and the pentagon
# ---------------------------------------------------------------------------


def test_equilateral_triangle_has_the_exact_apex():
    with Context():
        result = run("I.1", Point(0, 0), Point(2, 0))
        apex = result.value.apex
        assert apex.x == 1
        assert apex.y == sqrt(3)
        assert eq_len(apex, Point(0, 0), Point(0, 0), Point(2, 0))


def test_pythagoras_on_an_irrational_triangle():
    """The 3-4-5 case would prove nothing; give it legs of sqrt(2) and sqrt(3)."""
    with Context():
        b = Point(0, 0)
        a = Point(sqrt(2), 0)
        c = Point(0, sqrt(3))
        assert right_angle(a, b, c)
        run("I.47", a, b, c)
        assert len2(a, c) == 5


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


def _interior_angle(angle) -> int:
    return round(math.degrees(math.acos(max(-1.0, min(1.0, to_float(angle.cos))))))


def test_the_pentagon_sampler_offers_both_figures():
    """XIII.7 is a real check only while it sees more than one shape.

    The convex pentagon and the pentagram have the same vertices and the same
    claim to being equilateral, and their angles differ. A sampler that drifted
    to producing one of them would leave the proposition passing every run
    while asking a question with a single answer.
    """
    seen = collections.Counter()
    for seed in range(24):
        result = run_sampled("XIII.7", random.Random(seed))
        seen[_interior_angle(result.value.angles[0])] += 1
    assert set(seen) == {36, 108}, f"only these figures were drawn: {dict(seen)}"
    assert min(seen.values()) >= 6, f"one figure is nearly absent: {dict(seen)}"


def test_the_decagon_side_is_cut_from_the_circle():
    """XIII.9 and XIII.10 would both hold if the side were posited.

    Their content is that three figures inscribed in *one* circle stand in a
    relation, so the decagon side has to come off that circle. It is taken as
    the arc bisection of III.30, and this pins it to the value that
    construction gives.
    """
    for seed in range(6):
        result = run_sampled("XIII.10", random.Random(seed))
        radius2, decagon2 = result.value.hexagon, result.value.decagon
        # The side of the decagon subtends a tenth of the circumference, so it
        # is the golden section of the radius: d = R(sqrt 5 - 1)/2.
        expected = radius2 * (3 - sqrt(5, tower=result.context.tower)) / 2
        assert decagon2 == expected
        assert result.value.pentagon == radius2 + decagon2


def test_book_x_still_names_the_segments_of_the_golden_cut():
    """XIII.6 claims a family; the species is what the classifier adds.

    The hypothesis started life as commensurability in length, which is
    narrower than Euclid's Definition 3 and was reported by the necessity
    analysis as surviving being broken. Widening it brought two more species
    pairs into reach, and this pins all three.
    """
    with Context("XIII.6"):
        root5 = sqrt(5)
        cases = {
            "commensurable in length": Fraction(2),
            "in square only": sqrt(3),
            "commensurable with root five": 2 * root5,
        }
        found = {}
        for sense, whole in cases.items():
            greater = whole * (root5 - 1) / 2
            lesser = whole - greater
            assert classify(greater).family == "apotome", sense
            assert classify(lesser).family == "apotome", sense
            found[sense] = (classify(greater).species, classify(lesser).species)
        assert found == {
            "commensurable in length": ("fifth", "first"),
            "in square only": ("sixth", "third"),
            "commensurable with root five": ("fourth", "second"),
        }, found


def test_the_five_metrical_readings_are_five_different_facts():
    """XIII.1 to XIII.5 all speak of one cut, and none implies the next here.

    Each is checked as its own identity in Q(sqrt 5). Recording them together
    is what shows they are distinct: a single relation restated five ways would
    give the same five numbers.
    """
    with Context("XIII.1-5"):
        root5 = sqrt(5)
        whole = Fraction(1)
        greater = (root5 - 1) / 2
        lesser = whole - greater
        half_whole, half_greater = whole / 2, greater / 2
        readings = {
            "XIII.1": (greater + half_whole) ** 2 / half_whole ** 2,
            "XIII.3": (lesser + half_greater) ** 2 / half_greater ** 2,
            "XIII.4": (whole ** 2 + lesser ** 2) / greater ** 2,
        }
        assert readings["XIII.1"] == 5
        assert readings["XIII.3"] == 5
        assert readings["XIII.4"] == 3
        # XIII.5: the whole with the greater segment added is cut in the same
        # ratio, and the old whole is now the greater segment.
        longer = whole + greater
        assert longer * greater == whole * whole


@pytest.mark.parametrize("ref", ["XIII.8", "XIII.9", "XIII.10", "XIII.11", "XIII.12"])
def test_the_pentagon_propositions_stand_on_a_real_pentagon(ref):
    """Each calls IV.11 or IV.15 to build its figure.

    Laying the vertices out from the known coordinates would pass every check
    and would make the proposition a statement about arithmetic. Calls are
    recorded as they happen, so the proposition has to run before they exist.
    """
    entry = next(e for e in PLANE_XIII if e.ref == ref)
    run_sampled(ref, random.Random(0))
    assert entry.calls & {"IV.11", "IV.15"}, f"{ref} builds its own figure"


def test_the_diagonals_cut_each_other_in_the_side():
    """XIII.8's greater segment equals the side, which is why XIII.17 works."""
    result = run_sampled("XIII.8", random.Random(0))
    corners, cross = result.value.pentagon, result.value.cross
    assert len2(corners[0], cross) == len2(corners[0], corners[1])
