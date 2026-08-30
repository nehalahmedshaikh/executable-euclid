"""Invariants that must hold of every proposition in the corpus.

These are the checks that were being run by hand, one at a time, while the
books were written -- and every one of them caught something. A claim that
cannot fail, a proposition whose hypotheses no sample can satisfy, a citation
naming something that does not exist: each was found by looking, and none of
them would fail any test that existed at the time.

They are cheap, they run over all of Book I to Book X at once, and they are the
difference between "every proposition certifies" and "every proposition is
actually checked".
"""

import ast
import collections
import pathlib
import re

import pytest

import euclid.elements  # noqa: F401  -- registers the propositions
from euclid.elements.registry import (
    BOOK_ORDER,
    HEATH,
    all_propositions,
    reference_kind,
)
from euclid.verify import certify

ELEMENTS = pathlib.Path(euclid.elements.__file__).parent
BOOK_FILES = sorted(ELEMENTS.glob("book*.py"))

# How many propositions each book of the Elements actually has.
BOOK_SIZES = {
    "I": 48, "II": 14, "III": 37, "IV": 16, "V": 25, "VI": 33,
    "VII": 39, "VIII": 27, "IX": 36, "X": 115, "XI": 39, "XII": 18, "XIII": 18,
}


def test_no_claim_is_incapable_of_failing():
    """A check that cannot come out false is not a check.

    Two shapes have turned up in practice, both of them passing every test:
    a literal ``True``, and a comparison of something with itself. VI.16 and
    VII.19 both stated their converse as ``(x == y) == (x == y)``, which reads
    like a real biconditional and asserts nothing at all.
    """
    offenders = []
    for path in BOOK_FILES:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in ("claim", "hypothesis") and node.args):
                continue
            target = node.args[-1]
            if isinstance(target, ast.Constant):
                offenders.append(f"{path.name}:{node.lineno} asserts a literal "
                                 f"{target.value!r}")
            elif (isinstance(target, ast.Compare) and len(target.ops) == 1
                  and ast.unparse(target.left) == ast.unparse(target.comparators[0])):
                offenders.append(f"{path.name}:{node.lineno} compares "
                                 f"{ast.unparse(target.left)[:60]} with itself")
    assert not offenders, "claims that cannot fail:\n  " + "\n  ".join(offenders)


def test_no_proposition_overwrites_a_given():
    """A hypothesis you assign rather than check always passes.

    V.7 once did ``b = a`` after being handed ``b``, and then "checked" that the
    two were equal. It certified perfectly and tested nothing. Rebinding a
    parameter is the give-away.
    """
    offenders = []
    for path in BOOK_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("prop_"):
                continue
            givens = {arg.arg for arg in node.args.args}
            for inner in ast.walk(node):
                if not isinstance(inner, ast.Assign):
                    continue
                for target in inner.targets:
                    names = ([target] if isinstance(target, ast.Name)
                             else [t for t in getattr(target, "elts", [])
                                   if isinstance(t, ast.Name)])
                    for name in names:
                        if name.id in givens:
                            offenders.append(
                                f"{path.name}:{inner.lineno} {node.name} rebinds "
                                f"its given {name.id!r}")
    assert not offenders, "givens overwritten:\n  " + "\n  ".join(offenders)


@pytest.mark.parametrize("book", [b for b in BOOK_ORDER if b in BOOK_SIZES])
def test_each_book_is_complete_or_declared_empty(book):
    """Books I to X are finished; XI to XIII are not started, and say so."""
    encoded = {entry.number for entry in all_propositions() if entry.book == book}
    if book in ("XI", "XII", "XIII"):
        assert not encoded, f"Book {book} has propositions but is declared unstarted"
        return
    missing = [n for n in range(1, BOOK_SIZES[book] + 1) if n not in encoded]
    assert not missing, f"Book {book} is missing {missing}"


@pytest.fixture(scope="session")
def corpus():
    """Every proposition run once, with what that run found.

    Certifying the whole corpus is the expensive thing in this file, so it is
    done once. It also populates ``cites``, which is recorded at run time.
    """
    return {entry.ref: (entry, certify(entry.ref, trials=8))
            for entry in all_propositions()}


def test_every_proposition_makes_at_least_one_claim(corpus):
    """A proposition that asserts nothing has not been written, only registered."""
    thin = [ref for ref, (_, report) in corpus.items()
            if report.verified and report.claims_checked < report.verified]
    assert not thin, f"propositions asserting nothing: {thin}"


def test_every_proposition_can_be_satisfied(corpus):
    """Hypotheses no sample can meet mean the proposition is never tested.

    Three propositions of Book VII and both of Book VIII's opening pair were in
    this state: green, because a proposition that never runs never fails.
    """
    starved = [ref for ref, (_, report) in corpus.items() if report.verified == 0]
    assert not starved, f"propositions no sample satisfies: {starved}"


def test_every_citation_names_something_real(corpus):
    """A step may cite a proposition, definition, postulate or common notion.

    The citation does not carry the proof -- the check is independent of it --
    but a reference to a proposition that does not exist is a typo, and typos in
    citations quietly corrupt the dependency graph.
    """
    unknown = collections.defaultdict(set)
    for entry, _ in corpus.values():
        for ref in entry.cites:
            if reference_kind(ref) != "proposition":
                continue
            if ref not in HEATH:
                unknown[ref].add(entry.ref)
    assert not unknown, (
        "citations naming no proposition of the Elements: "
        + ", ".join(f"{ref} (from {sorted(who)})" for ref, who in unknown.items())
    )


# Genuine forward references in the text would go here, with a reason. There
# are none: every one found so far was an anachronism in the encoding.
ALLOWED_FORWARD_CITATIONS: dict[str, str] = {}


def test_no_proposition_cites_a_later_one(corpus):
    """Euclid may only lean on what he has already proved.

    A step citing a proposition that comes later is an anachronism in the
    encoding, not a discovery about the text. Six were found this way: II.14
    reached into Book III for the angle in a semicircle, which Euclid does not
    have yet and does not need -- II.5 and I.47 do the work between them.
    """
    def position(ref: str) -> tuple:
        book, number = ref.split(".")
        return BOOK_ORDER.index(book), int(number)

    forward = []
    for entry, _ in corpus.values():
        for ref in entry.cites:
            if reference_kind(ref) != "proposition" or ref == entry.ref:
                continue
            if position(ref) > position(entry.ref) \
                    and ALLOWED_FORWARD_CITATIONS.get(f"{entry.ref}->{ref}") is None:
                forward.append(f"{entry.ref} cites {ref}")
    assert not forward, "propositions reaching forward:\n  " + "\n  ".join(sorted(forward))


def test_every_statement_is_the_parsed_text():
    """Nothing displayed anywhere is written by this project."""
    for entry in all_propositions():
        assert entry.statement == HEATH[entry.ref]
        assert len(entry.statement) > 20, entry.ref


def test_the_kernel_is_never_handed_a_float():
    """Hard rule: no floats in the kernel or the plane.

    Floats are allowed inside `search/`, which explores approximately and then
    replays every hit exactly, and in the two places that deliberately convert
    for display or for a starting guess that is then corrected.
    """
    allowed = {"to_float", "radius_float", "as_floats", "float"}
    offenders = []
    for path in sorted((ELEMENTS.parent / "kernel").glob("*.py")) + \
            sorted((ELEMENTS.parent / "plane").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for number, line in enumerate(source.splitlines(), 1):
            if re.search(r"(?<![\w.])\d+\.\d+", line) and "float" not in line \
                    and not line.lstrip().startswith("#"):
                if not any(name in line for name in allowed):
                    offenders.append(f"{path.name}:{number}: {line.strip()[:70]}")
    assert not offenders, "float literals in exact code:\n  " + "\n  ".join(offenders)


def test_the_ledger_does_not_depend_on_which_configuration_came_first():
    """Continuity and order used to be tallied from ``traces[0]`` alone.

    For a proposition that takes more than one route through its diagram -- and
    four of them do -- that reported whichever route the first sample happened
    to take. The debt is the most it ever incurs, over every configuration.
    """
    from euclid.verify.ledger import audit

    for ref in ("III.23", "III.34", "VI.9"):
        first = audit(ref, trials=8, seed=0)
        other = audit(ref, trials=8, seed=5)
        assert first.continuity_debt == other.continuity_debt, ref


def test_a_flip_is_found_even_when_the_route_varies():
    """The per-predicate check sat in an ``else`` and never ran where it mattered.

    A proposition whose predicate count varies is precisely one that branches on
    its figure, which is where a truth-flip is most likely. III.23 was hiding
    eight of them behind a count that varied.
    """
    from euclid.verify.ledger import audit

    ledger = audit("III.23", trials=8)
    flips = [item for item in ledger.of_kind("case") if "true in some" in item.detail]
    assert len(flips) >= 2, f"only {len(flips)} flips found in III.23"
