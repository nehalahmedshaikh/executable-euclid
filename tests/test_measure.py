"""The measurements, and the discipline that keeps them honest.

These analyses are the part of the project that says something new, so the
danger is not that they crash -- it is that they quietly say something weaker
than the page claims.  Most of what follows tests the *method*: that a
hypothesis known to matter comes out needed, that a run breaking two hypotheses
at once is thrown away, that the recorded file matches the code that wrote it.
"""

from __future__ import annotations

import json
from fractions import Fraction

import pytest

from euclid.elements import registry
from euclid.elements.registry import (
    BOOK_ORDER,
    all_propositions,
    get,
    hypothesis,
    relaxed_hypotheses,
)
from euclid.graph.dag import build as build_graph
from euclid.kernel.field import Context
from euclid.measure import (
    algebraic_depth,
    ceilings,
    depth_profile,
    first_appearances,
    hypothesis_necessity,
    load_findings,
    necessity_report,
    simplest_gap,
    taxonomy_gaps,
)
from euclid.measure.necessity import NEEDED, SURVIVED, WELL_DEFINED


# --------------------------------------------------------------------------
# relaxed_hypotheses: the mechanism everything else rests on
# --------------------------------------------------------------------------


def test_a_broken_hypothesis_normally_stops_the_proposition():
    with Context("test:strict"):
        with pytest.raises(registry.BadConfiguration):
            hypothesis("this is not so", False)


def test_relaxing_records_the_violation_instead_of_raising():
    with Context("test:relaxed"):
        with relaxed_hypotheses() as violations:
            assert hypothesis("this is not so", False) is False
            assert hypothesis("this is so", True) is True
    assert [text for _ref, text, _guard in violations] == ["this is not so"]


def test_relaxation_does_not_leak_out_of_its_block():
    with Context("test:leak"):
        with relaxed_hypotheses():
            hypothesis("recorded", False)
        with pytest.raises(registry.BadConfiguration):
            hypothesis("must raise again", False)


# --------------------------------------------------------------------------
# depth
# --------------------------------------------------------------------------

@pytest.fixture(scope="session")
def profile():
    """The depth of every proposition, walked once.

    ``depth_profile()`` executes the whole corpus. Four tests below wanted it
    and each called it again, which was three minutes of an eleven-minute suite
    spent recomputing the same dictionary.
    """
    return depth_profile()



def test_the_equilateral_triangle_needs_a_square_root():
    """I.1 puts its apex at an irrational height. Degree 1 would be a bug."""
    assert algebraic_depth(get("I.1")).degree == 2


def test_book_x_is_not_reported_as_rational():
    """Book X returns magnitudes rather than points.

    A walk that only looks at coordinates reports the whole book as degree 1,
    which is how this was wrong the first time.
    """
    profile = depth_profile([e for e in all_propositions() if e.ref.startswith("X.")])
    assert max(item.degree for item in profile.values()) > 2


def test_arithmetic_books_never_leave_the_rationals(profile):
    """Books VII to IX are about numbers; a square root there would be a bug."""
    tops = ceilings(profile)
    for book in ("VII", "VIII", "IX"):
        assert tops[book] == 1, f"Book {book} should stay rational, got {tops[book]}"


def test_every_degree_is_a_power_of_two(profile):
    """Constructible means a tower of quadratic extensions. Nothing else fits."""
    for item in profile.values():
        assert item.degree & (item.degree - 1) == 0, f"{item.ref} has degree {item.degree}"


def test_each_book_has_a_ceiling_and_each_degree_a_first_appearance(profile):
    tops = ceilings(profile)
    assert set(tops) <= set(BOOK_ORDER)
    for degree, ref in first_appearances(profile).items():
        assert profile[ref].degree == degree


# --------------------------------------------------------------------------
# gaps
# --------------------------------------------------------------------------


def test_book_x_misses_a_constructible_number():
    gap = simplest_gap()
    assert gap is not None
    assert gap.degree in (2, 4, 8)
    assert gap.minimal_polynomial.endswith("= 0")
    assert gap.reason


def test_the_witness_is_really_outside_the_thirteen_species():
    """Re-derive the finding by hand rather than trusting the search."""
    from euclid.elements.book10 import classify
    from euclid.kernel.field import sqrt
    from euclid.measure.gaps import UNNAMED

    with Context("test:gap"):
        assert classify(1 + sqrt(2) + sqrt(3)).name == UNNAMED


def test_something_is_still_nameable():
    """A classifier that named nothing would make this finding vacuous."""
    from euclid.elements.book10 import classify
    from euclid.kernel.field import sqrt
    from euclid.measure.gaps import UNNAMED

    with Context("test:named"):
        assert classify(1 + sqrt(2)).name != UNNAMED
        assert classify(1 + sqrt(2)).species is not None


# --------------------------------------------------------------------------
# necessity: the method, not the numbers
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ref, doing_the_work",
    [
        ("I.5", "AB = AC"),                  # drop it and the base angles differ
        ("I.47", "the angle ABC is right"),  # drop it and Pythagoras is false
        ("III.20", "A, B and C lie on the circle centred at O"),
    ],
)
def test_a_hypothesis_that_matters_comes_out_needed(ref, doing_the_work):
    """Three hypotheses nobody doubts. If these read as optional, it is broken."""
    results = hypothesis_necessity(get(ref), trials=16)
    verdicts = {item.text: item.verdict for item in results}
    assert verdicts.get(doing_the_work) == NEEDED, verdicts


def test_side_angle_side_can_now_be_taken_apart():
    """I.4 was the honest limit of the method, and is no longer.

    Three hypotheses over six points: a blind offset changes both the distance
    and the direction from every other point, so it always broke two at once and
    every run was discarded for want of attribution. I.4 contributed nothing,
    and cases like it were the whole of the coverage gap.

    Rotating a point about another moves the angle and keeps the distance;
    sliding it along the ray does the reverse. Each hypothesis can then be
    broken alone, and all three turn out to be doing work.
    """
    results = hypothesis_necessity(get("I.4"), trials=72)
    verdicts = {item.text: item.verdict for item in results}
    assert len(verdicts) == 3, verdicts
    assert all(v == NEEDED for v in verdicts.values()), verdicts


def test_a_perturbation_keeps_the_configuration_exact():
    """The rotation is the rational parametrisation of the circle, so a moved
    point is still a point of the field the sampler built in."""
    from fractions import Fraction as F

    from euclid.measure.necessity import _stretched, _turned
    from euclid.plane.objects import Point as P

    anchor, point = P(F(0), F(0)), P(F(3), F(4))
    turned = _turned(point, anchor, F(1, 2))
    assert turned.x * turned.x + turned.y * turned.y == 25  # distance preserved
    stretched = _stretched(point, anchor, F(2))
    assert (stretched.x, stretched.y) == (6, 8)             # direction preserved


def test_a_candidate_is_reported_as_a_candidate():
    """II.9 and II.10 are the same identity; both should survive breaking.

    This is the finding on the page, so it is checked here rather than trusted.
    """
    for ref in ("II.9", "II.10"):
        results = hypothesis_necessity(get(ref), trials=16)
        assert any(item.verdict == SURVIVED for item in results), ref


def test_the_verdicts_are_the_only_three():
    report = necessity_report(entries=[get("I.4"), get("I.5"), get("II.9")], trials=8)
    for item in report.tested:
        assert item.verdict in (NEEDED, SURVIVED, WELL_DEFINED)


def test_coverage_is_stated_and_honest():
    """A report that hid its coverage would read as far stronger than it is."""
    report = necessity_report(entries=[get("I.1"), get("I.4"), get("I.9")], trials=8)
    assert 0.0 <= report.coverage <= 1.0
    assert len(report.tested) <= report.hypotheses_total
    assert "coverage" in report.summary()
    assert "candidates, not results" in report.summary()


def test_a_run_breaking_two_hypotheses_is_discarded():
    """The attribution rule. Without it every verdict is unattributable."""
    results = hypothesis_necessity(get("I.4"), trials=12)
    # Every recorded verdict must come from runs where exactly one hypothesis
    # broke, so the counts partition the runs that were kept.
    for item in results:
        assert item.broken == item.needed + item.well_defined + item.survived


# --------------------------------------------------------------------------
# the recorded file
# --------------------------------------------------------------------------


def test_the_recorded_findings_match_this_corpus():
    """A stale findings.json would put wrong numbers on the site."""
    measured = load_findings()
    assert measured is not None, "run: euclid measure --write"
    assert measured["corpus"] == len(all_propositions())


def test_the_recorded_findings_agree_with_recomputing_them(profile):
    """The exact parts are recomputed; the sampled parts cannot be."""
    measured = load_findings()
    assert measured["depth"]["ceilings"] == ceilings(profile)


def test_the_recorded_findings_state_their_method():
    measured = load_findings()
    assert "empirical" in measured["method"].lower()
    need = measured["necessity"]
    assert need["judged"] <= need["hypotheses"]
    assert (need["needed"] + need["well_defined"] + len(need["candidates"])
            + need["surviving_guards"]) == need["judged"]


def test_the_findings_page_reports_only_measured_things():
    """The whole point of the rewrite: no finding derived from citations.

    Citations are typed by hand, so a page reporting them reports our own
    transcription.  This reads the generated source rather than the page, so a
    reintroduced ``graph.load_bearing`` finding fails here.
    """
    import inspect

    from euclid.render import site

    source = inspect.getsource(site._findings_page)
    body = source.split('body = [')[0]
    for forbidden in ("load_bearing", "tree_shake", "uses_parallel_postulate"):
        assert forbidden not in body, f"{forbidden} is a citation-derived finding"


def test_the_graph_page_no_longer_claims_there_is_no_index():
    """It said 'No list of cross-references is kept anywhere in this project'.

    There is one: the ``cites`` annotations. 87% of the edges come from it.
    """
    import inspect

    from euclid.render import site

    source = inspect.getsource(site._graph_page)
    assert "No list of cross-references is kept" not in source
    assert "executed" in source and "cited" in source.lower()


def test_the_readme_quotes_only_numbers_it_still_carries():
    """The README states very few numbers now, and these are they.

    It used to reproduce the whole findings section -- seven write-ups, three
    tables -- which meant every measurement existed in two places and the copy
    kept by hand was the one that went stale. The findings live on the generated
    site, where nothing is typed. What is left here is what a reader needs before
    deciding to look further.

    Matched against whitespace-normalised text: the previous version embedded the
    line breaks of one particular wrapping, so it tested paragraph shape rather
    than the number inside it and broke on any reflow.
    """
    from pathlib import Path

    readme = " ".join(
        (Path(__file__).resolve().parent.parent / "README.md")
        .read_text(encoding="utf-8").split()
    )
    measured = load_findings()

    coverage = f"{100 * measured['necessity']['coverage']:.0f}%"
    assert f"Coverage is {coverage}" in readme

    executed, cited = build_graph().provenance()
    assert f"{executed} edges are **executed**" in readme
    assert f"{cited} are **cited**" in readme
    assert f"only {100 * executed // (executed + cited)}% of the graph" in readme


def test_only_an_exactly_enumerated_row_is_called_a_theorem():
    """"Fewest possible" belongs to a row every shorter figure was ruled out for.

    The compass-only midpoint is the case that earned this. It was stated as
    "exactly seven circles, six is not enough, and all of them were tried" while
    being computed nowhere; when it was finally computed, the float search said
    seven and exact enumeration found six. A float-exhaustive search is not a
    proof that nothing shorter exists, and the label has to track which one
    produced the answer.
    """
    from euclid.render.site import _strength

    rows = {(r["problem"], r["isa"]): r for r in load_findings()["constructions"]}
    for row in rows.values():
        if row["found"] and not row["exact_minimal"]:
            assert _strength(row) != "fewest possible", row["problem"]

    deep = rows[("midpoint", "compass-only")]
    assert deep["found"] and deep["verified"]
    assert deep["length"] == 6, "the compass-only midpoint is six circles"
    assert deep["exact_minimal"], "five circles were not ruled out exactly"
    assert deep["beat_float"], "this row is the one the float search got wrong"
    assert _strength(deep) == "fewest possible"


def test_exact_enumeration_is_authoritative_over_the_float_search():
    """When the two disagree the exact answer wins, and says that it did.

    Silently keeping the float answer would leave a false minimum on the page,
    which is what happened for as long as the claim went uncomputed.
    """
    from euclid.search.exact import shortest_is_certified
    from euclid.search.problems import PROBLEMS

    certified, exhaustion = shortest_is_certified(
        PROBLEMS["midpoint"], "compass-only", 6, budget=200_000)
    assert certified and not exhaustion.found, "five circles should be ruled out"


def test_the_graph_knows_which_edges_it_executed():
    graph = build_graph()
    executed, cited = graph.provenance()
    assert executed > 0 and cited > 0
    assert executed + cited == sum(
        len(graph.executed.get(ref, ())) + len(graph.cited.get(ref, ()))
        for ref in graph.nodes
    )


# --------------------------------------------------------------------------
# the soundness of the numbers themselves
# --------------------------------------------------------------------------


def test_depth_is_a_maximum_over_configurations_not_the_first_one():
    """``algebraic_depth`` used to return inside its retry loop.

    ``tries`` only bought a retry when a sample was rejected, so every published
    ceiling rested on whichever figure happened to come up first.
    """
    depth = algebraic_depth(get("I.1"))
    assert depth.configurations > 1, "only one configuration was examined"


def test_a_deep_tower_no_longer_hides_a_degree():
    """I.45 builds ten levels; the old depth bound refused all 514 magnitudes.

    A ceiling with skipped magnitudes behind it is not a ceiling, so the skips
    are counted -- and after bounding by the element's own support rather than
    the tower's depth there are none left to count.
    """
    depth = algebraic_depth(get("I.45"))
    assert depth.tower_height > 8, "I.45 no longer exercises the deep-tower case"
    assert depth.unmeasured == 0, f"{depth.unmeasured} magnitudes still unmeasured"


def test_the_support_bound_is_closed_under_radicands():
    """Bounding by the levels an element uses *directly* is wrong.

    Squaring sqrt(r_k) gives r_k, which lives below k, so a power reaches out of
    the set it started in. Assuming otherwise made 2^(1/4) come out degree 2.
    """
    from euclid.kernel.field import sqrt
    from euclid.kernel.minpoly import closed_support, degree

    with Context("test:support"):
        quartic = sqrt(sqrt(2))
        assert degree(quartic) == 4
        assert len(closed_support(quartic)) == 2
        assert degree(sqrt(sqrt(sqrt(2)))) == 8


def test_hypotheses_are_counted_by_running_not_by_grepping():
    """The coverage denominator came from a text search over source code.

    VII.24 states one hypothesis and states it at runtime; a counter that gives
    zero for it (because the sampler rejects most triples) is worse than the
    grep it replaced, so the count retries until the proposition runs.
    """
    from euclid.measure.necessity import _count_hypotheses

    assert _count_hypotheses(get("VII.24")) == 1
    assert _count_hypotheses(get("I.4")) == 3


# --------------------------------------------------------------------------
# the field ladder
# --------------------------------------------------------------------------


def test_restricting_the_field_changes_nothing_by_default():
    """A tower with no policy is the kernel as it always was."""
    from euclid.kernel.field import Tower, sqrt as field_sqrt

    with Context("test:default") as ctx:
        assert ctx.tower.policy is None
        assert field_sqrt(2) is not None


def test_the_rational_plane_refuses_a_new_root_but_keeps_the_old_ones():
    """Q has sqrt(4). It does not have sqrt(2). The gate fires only on growth."""
    from euclid.kernel.field import Rational, RootNotInField, sqrt as field_sqrt

    with Context("test:Q", policy=Rational()):
        assert field_sqrt(4) == 2
        with pytest.raises(RootNotInField):
            field_sqrt(2)


def test_the_pythagorean_field_wants_a_witness():
    """sqrt(a^2 + b^2) is a hypotenuse; anything else is refused.

    Deciding sum-of-two-squares for a general tower element is a norm
    computation in a multiquadratic field, so the caller carries the pair
    instead. Sound at every depth, and incomplete on purpose.
    """
    from euclid.kernel.field import Pythagorean, RootNotInField, sqrt as field_sqrt

    with Context("test:pyth", policy=Pythagorean()):
        assert field_sqrt(25, witness=(3, 4)) == 5
        with pytest.raises(RootNotInField):
            field_sqrt(2)
        assert field_sqrt(2, witness=(1, 1)) is not None


def test_a_missing_root_is_not_filed_as_an_arithmetic_error():
    """``necessity`` catches ArithmeticError and calls it well-definedness.

    If RootNotInField inherited from it, every restricted run would be buried
    among unrelated outcomes.
    """
    from euclid.kernel.field import RootNotInField

    assert not issubclass(RootNotInField, ArithmeticError)
    assert not issubclass(RootNotInField, ValueError)


def test_an_irrational_sampler_is_untestable_and_never_blamed():
    """Book X's samplers build irrational magnitudes because that is the subject.

    Their configurations are rejected before the policy is armed, so the
    proposition comes back untestable. Calling it ``needs-root`` would blame
    Euclid for our test data.
    """
    from euclid.kernel.field import Rational
    from euclid.measure.fields import UNTESTABLE, field_verdict

    verdict = field_verdict(get("X.21"), Rational(), trials=6)
    assert verdict.verdict == UNTESTABLE
    assert verdict.configurations == 0
    assert verdict.needs_root == 0


def test_the_ladder_separates_measuring_from_intersecting():
    """The finding, on the two cases that show what it is for.

    I.1 crosses two circles, so it fails on both rungs and the blame lands in
    ``construct.py``. I.20 only measures lengths, so the Pythagorean rung is
    enough and the blame lands in ``angles.py``.
    """
    from euclid.kernel.field import Pythagorean, Rational
    from euclid.measure.fields import ALWAYS, CONTINUITY, MEASUREMENT, NEVER, field_verdict

    circles = field_verdict(get("I.1"), Rational(), trials=6)
    assert circles.verdict == NEVER and circles.cause == CONTINUITY
    assert field_verdict(get("I.1"), Pythagorean(), trials=6).verdict == NEVER

    measured = field_verdict(get("I.20"), Rational(), trials=6)
    assert measured.verdict == NEVER and measured.cause == MEASUREMENT
    assert field_verdict(get("I.20"), Pythagorean(), trials=6).verdict == ALWAYS


def test_a_lucky_intersection_is_not_reported_as_pythagorean():
    """I.23's sampler hands it a rational triangle, so its circles meet where
    the configuration already was.

    It passes over Q^pyth while carrying continuity debt, which would read as
    "the angle-copy construction needs only segment transfer" -- a finding about
    ``samples.triangle``. The ledger is what tells the two apart.
    """
    from euclid.kernel.field import Pythagorean
    from euclid.measure.fields import ALWAYS, field_verdict
    from euclid.verify.ledger import audit

    assert field_verdict(get("I.23"), Pythagorean(), trials=6).verdict == ALWAYS
    assert audit("I.23", trials=6).continuity_debt > 0, "no debt: the guard is vacuous"
