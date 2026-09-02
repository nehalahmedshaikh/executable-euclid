"""The dependency graph, and what can be read off it.

These tests lived in a file named for Book I because I.47 is the example they
all use. They are about the graph.
"""

import euclid.elements  # noqa: F401  registers the corpus
from euclid.elements import get
from euclid.graph import build


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
