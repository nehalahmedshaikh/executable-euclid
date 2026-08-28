"""The verifier and the assumption ledger."""

import euclid.elements  # noqa: F401
from euclid.plane.trace import IntersectionEvent, PredicateEvent, Trace
from euclid.verify import audit, certify
from euclid.verify.ledger import case_assumptions


def test_a_false_claim_would_be_caught():
    """Sanity check on the checker itself: claims are enforced, not decorative."""
    from euclid.elements.registry import ProofFailure, claim

    import pytest

    with pytest.raises(ProofFailure):
        claim("two equals three", "C.N.1", False)


def test_I_1_owes_a_continuity_debt_on_its_very_first_move():
    ledger = audit("I.1", trials=6)
    debts = ledger.of_kind("continuity")
    assert len(debts) == 1
    assert "circle-circle" in debts[0].detail
    assert "no postulate asserts" in debts[0].detail


def test_congruence_theorems_owe_nothing():
    """I.4 draws nothing, so it takes nothing on trust."""
    ledger = audit("I.4", trials=6)
    assert ledger.is_clean


def test_order_facts_are_recorded_where_the_text_reads_the_diagram():
    ledger = audit("I.3", trials=6)
    assert any("between" in item.detail for item in ledger.of_kind("order"))


def test_book_one_takes_nothing_on_trust_beyond_continuity_and_order():
    """As encoded, no Book I construction changes route with the configuration.

    This is a real result rather than an absence of testing: the detector below
    is exercised directly by ``test_case_dependence_is_detected``.
    """
    for ref in ("I.1", "I.9", "I.10", "I.47"):
        assert not audit(ref, trials=8).of_kind("case")


def _trace_with(predicate_values, intersection_counts):
    trace = Trace(proposition="T.1")
    for index, value in enumerate(predicate_values):
        trace.predicates.append(PredicateEvent(f"p{index}", value))
    for count in intersection_counts:
        trace.intersections.append(IntersectionEvent("circle-circle", count, False))
    return trace


def test_case_dependence_is_detected_when_a_fact_flips():
    traces = [_trace_with([True, True], [2]), _trace_with([True, False], [2])]
    found = case_assumptions(traces)
    assert len(found) == 1
    assert "true in some configurations and false in others" in found[0].detail


def test_case_dependence_is_detected_when_a_route_changes_length():
    traces = [_trace_with([True], [2]), _trace_with([True, True], [2])]
    found = case_assumptions(traces)
    assert any("more than one route" in item.detail for item in found)


def test_case_dependence_is_detected_when_an_intersection_count_varies():
    traces = [_trace_with([True], [2]), _trace_with([True], [1])]
    found = case_assumptions(traces)
    assert any("yields [1, 2] points" in item.detail for item in found)


def test_identical_traces_raise_no_case_flags():
    traces = [_trace_with([True, False], [2]) for _ in range(4)]
    assert case_assumptions(traces) == []


def test_certification_counts_claims():
    report = certify("I.47", trials=4)
    assert report.passed
    assert report.claims_checked >= 4 * 3
