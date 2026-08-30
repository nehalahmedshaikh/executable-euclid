"""The superoptimizer.

Only the fast cases run here; the deep compass-only searches take a minute
apiece and live in the benchmark instead.
"""

import pytest

from euclid.search import INSTRUCTION_SETS, PROBLEMS, solve
from euclid.search.isa import Move
from euclid.search.score import score


def test_euclid_I_1_is_optimal():
    """Two circles. Euclid could not have done better, and now we know it."""
    result = solve("equilateral-triangle", max_depth=3)
    assert result.found
    assert result.length == 2
    assert result.exhaustive, "the search must have covered every 1- and 2-move figure"
    assert result.verified
    assert all(move.kind == "circle" for move in result.moves)


def test_no_one_move_construction_of_the_apex_exists():
    result = solve("equilateral-triangle", max_depth=1)
    assert not result.found
    assert result.exhaustive, "an exhaustive failure is a proof of impossibility at depth 1"


def test_perpendicular_bisector_takes_three_moves():
    result = solve("perpendicular-bisector", max_depth=3)
    assert result.found and result.length == 3 and result.exhaustive
    assert result.verified


def test_midpoint_takes_four_moves():
    result = solve("midpoint", max_depth=4)
    assert result.found and result.length == 4 and result.exhaustive
    assert result.verified


def test_perpendicular_at_a_point_takes_five():
    result = solve("perpendicular-at-a-point", max_depth=5)
    assert result.found and result.length == 5 and result.exhaustive
    assert result.verified


@pytest.mark.parametrize("name", sorted(PROBLEMS))
def test_every_problem_is_solved_and_verified(name):
    result = solve(name, max_depth=5)
    assert result.found, f"{name} unsolved within five moves"
    assert result.verified, f"{name} failed exact verification"


def test_compass_alone_still_reaches_the_apex():
    """Mohr-Mascheroni in miniature: no straightedge, same answer."""
    result = solve("equilateral-triangle", isa="compass-only", max_depth=3)
    assert result.found and result.length == 2 and result.verified


def test_compass_alone_can_double_a_segment():
    result = solve("double-a-segment", isa="compass-only", max_depth=4)
    assert result.found and result.length == 3 and result.verified
    assert all(move.kind == "circle" for move in result.moves)


def test_a_line_goal_is_unreachable_without_a_straightedge():
    result = solve("perpendicular-bisector", isa="compass-only", max_depth=4)
    assert not result.found, "the compass cannot draw a line, only find points"


def test_geometrography_grades_the_two_primitives():
    result = solve("perpendicular-bisector", max_depth=3)
    grading = score(result.moves)
    assert grading.s2 == 1, "one line was drawn"
    assert grading.c3 == 2, "two circles were described"
    assert grading.simplicity == 9
    assert "2C3" in grading.notation()


def test_instruction_sets_are_all_described():
    for name, isa in INSTRUCTION_SETS.items():
        assert isa.description
        assert isa.lines or isa.circles


def test_results_report_whether_the_search_was_exhaustive():
    """A search stopped by its budget must not claim to have proved anything."""
    starved = solve("square-on-a-segment", max_depth=5, node_budget=100)
    assert not starved.found
    assert not starved.exhaustive

    complete = solve("square-on-a-segment", max_depth=2)
    assert not complete.found
    assert complete.exhaustive, "12 figures is the whole of depth 2, so this is a proof"


# ---------------------------------------------------------------------------
# exact enumeration: the negative half of "shortest"
# ---------------------------------------------------------------------------


def test_the_exact_goal_is_the_same_goal_the_search_solved():
    """A weaker exact goal makes the replay verify something else entirely.

    ``_bisector_exact`` used to ask only for two points with x == 1/2, while the
    search required the line through them to be drawn. The two circles of the
    usual construction produce both points at two moves, so exact enumeration
    "found" a two-move answer to a three-move problem -- and the exact
    verification had been passing on figures without the line in them.
    """
    from euclid.search.exact import enumerate_exactly

    for name in ("perpendicular-bisector", "perpendicular-at-a-point"):
        problem = PROBLEMS[name]
        found = solve(name, max_depth=5)
        assert found.found
        short = enumerate_exactly(problem, "full", depth=found.length - 1)
        assert not short.found, f"{name}: exact enumeration beat the search"
        assert short.exhausted


def test_provably_minimal_means_exactly_enumerated():
    """I.1's two circles, with every one-move figure ruled out in the kernel."""
    result = solve("equilateral-triangle", max_depth=3)
    assert result.found and result.length == 2
    assert result.exact_minimal, "the minimality of I.1 is not certified"
    assert result.exact_figures > 0


def test_exhaustive_alone_does_not_license_provably_minimal():
    """``exhaustive`` is a statement about a budget, not about arithmetic.

    The whole float search can be exhaustive and still have lost a construction
    to a 1e-7 dedup, so the report must not promise minimality on that basis.
    """
    from euclid.search.optimizer import Result

    row = Result(problem="x", isa="full", found=True, exhaustive=True)
    row.moves = [Move("line", 0, 1)]
    assert "provably minimal" not in row.report()

    row.exact_minimal = True
    assert "provably minimal" in row.report()
