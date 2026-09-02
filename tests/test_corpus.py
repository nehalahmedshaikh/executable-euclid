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


# -- a claim that cannot come out false -------------------------------------
#
# This began as a search for two shapes: a literal ``True``, and a comparison
# whose two sides read alike. Both had happened -- VI.16 and VII.19 each stated
# a converse as ``(x == y) == (x == y)``, which reads like a biconditional and
# asserts nothing -- and reading the source found them.
#
# Reading the source is not enough, because a name stands in the way. X.54 said
#
#     area = compound
#     claim("...", "X.20", area == compound * 1)
#
# which is the same assertion wearing a second name, and twenty-four
# propositions of Book X said it. So the two sides are put in a normal form
# first: assignments are followed back to what they were assigned, the
# operations that leave a value alone are dropped, and sums and products are
# sorted so that ``a * b`` and ``b * a`` land in the same place. That last one
# matters -- ``a * (b * scale) == b * (a * scale)`` was standing in for "the
# sides are proportional" in three propositions, and is true of any four numbers.
#
# What this cannot see is a claim that is forced for a reason no rewriting
# reaches. euclid.measure.mutation is the analysis for those: it bends the
# figure underneath a claim and reports which claims never noticed.

_IDENTITIES = {(ast.Mult, 1), (ast.Div, 1), (ast.Add, 0), (ast.Sub, 0), (ast.Pow, 1)}
_ONE_SIDED = (ast.Div, ast.Sub, ast.Pow)  # x/1 is x; 1/x is not
_COMMUTATIVE = (ast.Add, ast.Mult, ast.BitAnd, ast.BitOr)


def _fold(node):
    """Drop the operations that leave a value alone: ``*1``, ``/1``, ``+0``, ``-0``."""
    if not isinstance(node, ast.BinOp):
        return node
    left, right = _fold(node.left), _fold(node.right)
    for side, other in ((right, left), (left, right)):
        if not (isinstance(side, ast.Constant) and isinstance(side.value, int)):
            continue
        if (type(node.op), side.value) not in _IDENTITIES:
            continue
        if side is left and isinstance(node.op, _ONE_SIDED):
            continue
        return other
    return ast.BinOp(left=left, op=node.op, right=right)


def _substitute(node, env, depth=0):
    """Replace each name by what it was last assigned, as far as that goes."""
    if depth > 12:
        return node
    step = lambda n: _substitute(n, env, depth + 1)  # noqa: E731
    if isinstance(node, ast.Name):
        return step(env[node.id]) if node.id in env else node
    if isinstance(node, ast.BinOp):
        return ast.BinOp(left=step(node.left), op=node.op, right=step(node.right))
    if isinstance(node, ast.UnaryOp):
        return ast.UnaryOp(op=node.op, operand=step(node.operand))
    if isinstance(node, ast.Call):
        return ast.Call(func=step(node.func), args=[step(a) for a in node.args],
                        keywords=[ast.keyword(arg=k.arg, value=step(k.value))
                                  for k in node.keywords])
    if isinstance(node, ast.Attribute):
        return ast.Attribute(value=step(node.value), attr=node.attr, ctx=ast.Load())
    if isinstance(node, ast.Subscript):
        return ast.Subscript(value=step(node.value), slice=step(node.slice),
                             ctx=ast.Load())
    if isinstance(node, (ast.Tuple, ast.List)):
        return type(node)(elts=[step(e) for e in node.elts], ctx=ast.Load())
    return node


def _flatten(node, op):
    if isinstance(node, ast.BinOp) and isinstance(node.op, op):
        return _flatten(node.left, op) + _flatten(node.right, op)
    return [node]


def _canonical(node):
    """A string that does not care which way round a sum or a product was written."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, _COMMUTATIVE):
        parts = sorted(_canonical(p) for p in _flatten(node, type(node.op)))
        joiner = " + " if isinstance(node.op, ast.Add) else " * "
        return "(" + joiner.join(parts) + ")"
    if isinstance(node, ast.BinOp):
        return (f"({_canonical(node.left)} {type(node.op).__name__} "
                f"{_canonical(node.right)})")
    if isinstance(node, ast.Call):
        return f"{_canonical(node.func)}({', '.join(_canonical(a) for a in node.args)})"
    if isinstance(node, ast.Attribute):
        return f"{_canonical(node.value)}.{node.attr}"
    return ast.unparse(node)


def _normal(node, env):
    return _canonical(_fold(_substitute(_fold(node), env)))


def _bound_by(node):
    """Every name this statement may rebind."""
    found = set()
    for inner in ast.walk(node):
        targets = []
        if isinstance(inner, ast.Assign):
            targets = inner.targets
        elif isinstance(inner, (ast.AugAssign, ast.AnnAssign)):
            targets = [inner.target]
        elif isinstance(inner, (ast.For, ast.comprehension)):
            targets = [inner.target]
        elif isinstance(inner, ast.withitem) and inner.optional_vars is not None:
            targets = [inner.optional_vars]
        for target in targets:
            found |= {n.id for n in ast.walk(target) if isinstance(n, ast.Name)}
    return found


def _judge(target, env, offenders, where):
    if isinstance(target, ast.BoolOp):
        for part in target.values:
            _judge(part, env, offenders, where)
    elif isinstance(target, ast.Constant):
        offenders.append(f"{where} asserts a literal {target.value!r}")
    elif isinstance(target, ast.Compare) and len(target.ops) == 1:
        left, right = _normal(target.left, env), _normal(target.comparators[0], env)
        if left == right:
            offenders.append(f"{where} compares {ast.unparse(target)[:64]} "
                             f"with itself -- both sides are {left[:50]}")


def _scan(body, env, offenders, filename):
    """Walk one block in order, carrying what each name has been assigned."""
    for stmt in body:
        for call in ast.walk(stmt):
            if (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id in ("claim", "hypothesis") and call.args):
                _judge(call.args[-1], env, offenders,
                       f"{filename}:{call.lineno}")
        if (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)):
            env[stmt.targets[0].id] = stmt.value
        else:
            # Anything else -- a loop, a branch, a tuple unpacking -- may bind a
            # name to something this walk cannot follow, so it stops following it.
            for name in _bound_by(stmt):
                env.pop(name, None)


def test_no_claim_is_incapable_of_failing():
    offenders = []
    for path in BOOK_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                _scan(node.body, {}, offenders, path.name)
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


# Books being written now, and how far they have got. A book listed here must
# be encoded up to its stated number with no holes; a book absent from it must
# be empty or complete. The dict is emptied when the last book lands, and an
# entry that reaches the book's full size is a stale one.
IN_PROGRESS = {"XIII": 12}


@pytest.mark.parametrize("book", [b for b in BOOK_ORDER if b in BOOK_SIZES])
def test_each_book_is_complete_or_declared_empty(book):
    """A book is finished, untouched, or a declared prefix of itself.

    Partial books are the dangerous state: a gap in the middle looks exactly
    like a book that is merely unfinished, so nothing would catch a proposition
    quietly skipped for being hard. Requiring a prefix makes a hole fail.
    """
    encoded = {entry.number for entry in all_propositions() if entry.book == book}
    reached = IN_PROGRESS.get(book, BOOK_SIZES[book] if encoded else 0)
    assert reached <= BOOK_SIZES[book], f"Book {book} has only {BOOK_SIZES[book]}"
    assert reached < BOOK_SIZES[book] or book not in IN_PROGRESS, (
        f"Book {book} is complete: drop it from IN_PROGRESS")
    missing = [n for n in range(1, reached + 1) if n not in encoded]
    beyond = sorted(n for n in encoded if n > reached)
    assert not missing, f"Book {book} is missing {missing}"
    assert not beyond, f"Book {book} jumps ahead to {beyond}, leaving a hole behind"


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


def test_no_proposition_states_a_condition_euclid_does_not(corpus):
    """An added hypothesis narrows a theorem, and narrowing it is not faithful.

    VIII.8, VIII.10 and VIII.13 required their ratio to be in least terms.
    Heath's enunciations say no such thing -- squaring a continued proportion
    gives a continued proportion whatever the ratio -- and the necessity
    analysis found all three, because a condition that does no work survives
    being broken.

    The guard here is narrow and mechanical: where Euclid's own words say
    "least", the encoding must too. It cannot detect an over-constraint whose
    vocabulary differs from his.
    """
    from euclid.elements.registry import HEATH

    missing = [entry.ref for entry in all_propositions()
               if "least" in HEATH[entry.ref].lower()
               and "least" not in entry.source().lower()]
    assert not missing, f"leastness dropped from {missing}"


def test_a_guard_is_marked_as_one(corpus):
    """Well-formedness conditions are ours; Euclid's hypotheses are his.

    A ratio that is not 1, a count of at least three, a positive magnitude --
    breaking those says nothing about the Elements. Reporting them beside real
    hypotheses made the necessity figure mean less than it looked like.
    """
    import re

    unmarked = []
    for entry in all_propositions():
        source = entry.source()
        for match in re.finditer(r'hypothesis\(\s*"([^"]+)"', source):
            text = match.group(1).lower()
            if any(word in text for word in ("genuine", "are positive", "proper one")):
                tail = source[match.start():match.start() + 400]
                if "guard=True" not in tail.split("hypothesis(")[1][:300]:
                    unmarked.append((entry.ref, match.group(1)))
    assert not unmarked, f"unmarked well-formedness guards: {unmarked[:5]}"


def test_an_appeal_is_carried_out_and_recorded():
    """``because`` runs the cited proposition and records the edge.

    Both halves matter. Running it is what checks the appeal: a step citing a
    result that does not apply to its own points fails instead of passing. And
    the edge has to be recorded, because the executed share of the graph is
    read off exactly these calls.
    """
    import random

    from euclid.elements.book01_foundations import prop_I_4
    from euclid.elements.registry import BadConfiguration, because, get, run_sampled
    from euclid.kernel.field import Context
    from euclid.plane.objects import Point

    entry = get("I.5")
    entry.calls.discard("I.4")
    run_sampled("I.5", random.Random(0))
    assert "I.4" in entry.calls, "I.5 appeals to I.4 and the call went unrecorded"

    with Context("test:appeal"), pytest.raises(BadConfiguration):
        # I.4 wants two sides and the included angle equal, and these are not
        # that, so the appeal must refuse the figure rather than pass it.
        because(prop_I_4, Point(0, 0), Point(1, 0), Point(0, 1),
                Point(0, 0), Point(2, 0), Point(0, 1))


def test_an_appeal_does_not_follow_the_appeals_beneath_it():
    """One level of appeal is the whole of it.

    II.13 appeals to I.47 twice and I.47 appeals onward. Following every appeal
    beneath those turned one run into a thousand nested constructions that
    re-derived Book I from I.1, and cost seven minutes where it now costs two
    seconds. Each proposition is certified in its own right, so the depth buys
    no assurance -- only time.
    """
    import random

    from euclid.elements.registry import run_sampled

    nested = run_sampled("II.13", random.Random(0)).trace.descendants()
    assert nested, "II.13 carries out the propositions it appeals to"
    assert len(nested) < 150, (
        f"II.13 ran {len(nested)} nested propositions; the appeal depth is unbounded")


def test_a_length_can_be_cut_off_from_a_line_it_starts_on():
    """I.3 must take a lesser line that already begins at the point.

    I.2 carries a length to a point because the compass collapses; a line
    already at the point needs no carrying, and asking for it made Postulate 1
    draw a line from A to itself. Six propositions cut off a length that way --
    I.5, I.9, I.11, I.18, IV.10 and VI.9 -- and each had to name the line
    backwards to get past it.
    """
    from euclid.elements.book01_foundations import prop_I_3
    from euclid.kernel.field import Context
    from euclid.plane.objects import Point
    from euclid.plane.predicates import eq_len

    with Context("test:cut"):
        a, b = Point(0, 0), Point(10, 0)
        short = Point(3, 0)
        cut = prop_I_3(a, b, a, short).cut       # the lesser line starts at A
        assert eq_len(a, cut, a, short)
        other = prop_I_3(a, b, short, a).cut     # and named the other way round
        assert eq_len(a, other, a, short)
