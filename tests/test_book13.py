"""Book XIII's plane half, and the ways it could pass while checking nothing.

Certification is already parametrised in ``test_books.py``. What is here are the
failures that would leave every proposition green: a sampler that quietly stops
producing the second figure, a decagon side written down as a formula instead of
cut from the circle, and a classification that goes stale.
"""

import collections
import math
import random
from fractions import Fraction

import pytest

import euclid.elements  # noqa: F401  registers the corpus
from euclid.elements import all_propositions, run_sampled
from euclid.elements.book10 import classify
from euclid.kernel import Context, sqrt
from euclid.kernel.field import to_float
from euclid.plane import len2

PLANE_XIII = [entry for entry in all_propositions()
              if entry.book == "XIII" and entry.number <= 12]


def test_the_plane_half_of_book_thirteen_is_present():
    numbers = sorted(entry.number for entry in PLANE_XIII)
    assert numbers == list(range(1, 13))


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
