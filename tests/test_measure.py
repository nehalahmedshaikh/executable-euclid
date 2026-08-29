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
    assert [text for _ref, text in violations] == ["this is not so"]


def test_relaxation_does_not_leak_out_of_its_block():
    with Context("test:leak"):
        with relaxed_hypotheses():
            hypothesis("recorded", False)
        with pytest.raises(registry.BadConfiguration):
            hypothesis("must raise again", False)


# --------------------------------------------------------------------------
# depth
# --------------------------------------------------------------------------


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


def test_arithmetic_books_never_leave_the_rationals():
    """Books VII to IX are about numbers; a square root there would be a bug."""
    tops = ceilings(depth_profile())
    for book in ("VII", "VIII", "IX"):
        assert tops[book] == 1, f"Book {book} should stay rational, got {tops[book]}"


def test_every_degree_is_a_power_of_two():
    """Constructible means a tower of quadratic extensions. Nothing else fits."""
    for item in depth_profile().values():
        assert item.degree & (item.degree - 1) == 0, f"{item.ref} has degree {item.degree}"


def test_each_book_has_a_ceiling_and_each_degree_a_first_appearance():
    profile = depth_profile()
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


def test_a_hypothesis_that_cannot_be_isolated_is_not_reported_at_all():
    """I.4 is the honest limit of the method, and worth pinning down.

    Side-angle-side states three hypotheses over six points, and moving any one
    point breaks at least two of them at once -- move B and both ``AB = DE`` and
    the included angle go together.  No run can attribute an outcome to one
    hypothesis, so every run is discarded and I.4 contributes nothing.

    That must show up as *absence*, never as a hypothesis that survived: the
    difference between "not tested" and "not needed" is the whole credibility of
    this analysis.  It is also where the 36% coverage figure comes from.
    """
    assert hypothesis_necessity(get("I.4"), trials=24) == []


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


def test_the_recorded_findings_agree_with_recomputing_them():
    """The exact parts are recomputed; the sampled parts cannot be."""
    measured = load_findings()
    assert measured["depth"]["ceilings"] == ceilings(depth_profile())


def test_the_recorded_findings_state_their_method():
    measured = load_findings()
    assert "empirical" in measured["method"].lower()
    need = measured["necessity"]
    assert need["judged"] <= need["hypotheses"]
    assert need["needed"] + need["well_defined"] + len(need["candidates"]) == need["judged"]


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


def test_the_readme_findings_match_what_was_measured():
    """The findings section quotes numbers, and quoted numbers go stale.

    Every one below is read out of ``findings.json`` or off the graph, so a
    measurement that moves fails here instead of leaving a wrong claim in the
    README.  These are the numbers the whole novelty argument rests on.
    """
    from pathlib import Path

    readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(
        encoding="utf-8"
    )
    measured = load_findings()

    tops = measured["depth"]["ceilings"]
    row = "| **Highest degree** | " + " | ".join(
        str(tops[book]) for book in BOOK_ORDER if book in tops
    )
    assert row in readme, f"the depth table is stale; expected row: {row}"

    deepest = measured["depth"]["deepest"][0]
    assert f"**{deepest['ref']}, at\ndegree {deepest['degree']}**" in readme

    need = measured["necessity"]
    assert f"{need['hypotheses']} hypotheses are stated" in readme
    assert f"**{need['judged']} could be broken" in readme
    assert f"({100 * need['coverage']:.0f}% coverage)**" in readme
    assert f"**{need['needed']} proved necessary**" in readme
    assert f"**{len(need['candidates'])} survived" in readme

    witness = measured["book_x_gaps"]["witnesses"][0]
    assert witness["expression"] in readme
    assert witness["minimal_polynomial"] in readme

    executed, cited = build_graph().provenance()
    assert f"**{executed} are\nexecuted**" in readme
    assert f"**{cited} are cited**" in readme
    assert f"only {100 * executed // (executed + cited)}% of the graph" in readme


def test_the_graph_knows_which_edges_it_executed():
    graph = build_graph()
    executed, cited = graph.provenance()
    assert executed > 0 and cited > 0
    assert executed + cited == sum(
        len(graph.executed.get(ref, ())) + len(graph.cited.get(ref, ()))
        for ref in graph.nodes
    )
