"""Book I: every proposition certified, and the graph it induces."""

import pytest

import euclid.elements  # noqa: F401  registers the corpus
from euclid.elements import all_propositions, get, run
from euclid.graph import build
from euclid.kernel import Context, sqrt
from euclid.plane import Point, eq_len, len2, right_angle
from euclid.verify import certify

BOOK_I = [entry for entry in all_propositions() if entry.book == "I"]


def test_the_whole_of_book_one_is_present():
    numbers = sorted(entry.number for entry in BOOK_I)
    assert numbers == list(range(1, 49))


@pytest.mark.parametrize("entry", BOOK_I, ids=lambda entry: entry.ref)
def test_proposition_is_certified(entry):
    report = certify(entry.ref, trials=8)
    assert not report.failures, report.failures[0].message
    assert report.verified > 0, f"{entry.ref}: the sampler produced no valid configuration"


def test_every_proposition_checks_something():
    for entry in BOOK_I:
        report = certify(entry.ref, trials=8)
        assert report.claims_checked > 0, f"{entry.ref} asserts nothing"


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


def test_dependency_graph_is_extracted_not_declared():
    graph = build()
    # I.47 leans on I.46, which leans on I.11, and so back to I.1
    assert "I.46" in graph.needs("I.47")
    assert "I.11" in graph.needs("I.46")
    assert "I.1" in graph.ancestors("I.47")
    assert graph.depth("I.47") > 5


def test_the_parallel_postulate_enters_at_I_29():
    graph = build()
    assert not graph.uses_parallel_postulate("I.27")
    assert not graph.uses_parallel_postulate("I.28")
    assert graph.uses_parallel_postulate("I.29")
    assert graph.uses_parallel_postulate("I.47")


def test_tree_shaking_yields_a_self_contained_book():
    graph = build()
    minimal = graph.tree_shake("I.47")
    assert minimal[-1] == "I.47"
    assert len(minimal) < 48, "tree-shaking should drop something"
    seen: set[str] = set()
    for ref in minimal:
        assert graph.needs(ref) <= seen, f"{ref} appears before its dependencies"
        seen.add(ref)


def test_the_first_proposition_carries_the_most_weight():
    graph = build()
    ranking = graph.load_bearing()
    assert ranking[0][0] == "I.1"
    assert len(graph.descendants("I.1")) > 30


def test_proposition_sources_are_available_for_the_site():
    for ref in ("I.1", "I.47"):
        assert "def prop_" in get(ref).source()
