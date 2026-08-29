"""The proposition registry: how a passage of Euclid becomes a program.

A proposition is a Python function wearing the :func:`proposition` decorator.
Running it does four things at once:

1. **Constructs.**  Its body calls the postulate primitives, so it really does
   draw the figure rather than describe one.
2. **Proves.**  Each step is a :func:`claim` carrying the justification Euclid
   gives -- a prior proposition, a definition, a postulate, a common notion --
   *and* a predicate that the kernel checks exactly.  A wrong citation cannot
   smuggle a false statement through, because the check is independent of the
   citation.
3. **Reports its dependencies.**  Two kinds, and they are not equally strong.
   The *calls* it makes are recorded as they happen and cannot be wrong.  The
   *citations* it gives are written by hand beside each step, following Heath's
   marginal references; the check on the step never consults them, so a wrong
   one cannot let a false statement through, but the edge is authored rather
   than observed.  About one edge in eight is executed.  See ``graph/dag.py``,
   which says so on every page that reads the graph.
4. **Records a trace**, which the renderer and the assumption ledger consume.

What the machine verifies is precisely this: *the conclusion holds, exactly, of
the model that the construction built*.  That is a model check, not a synthetic
derivation, and the README says so plainly.  Its value is that it is total --
every claim, every step, every proposition, with no appeals to the diagram.
"""

from __future__ import annotations

import inspect
import textwrap
import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Optional

from ..kernel.field import Context, Surd, active_context
from ..plane.objects import Point
from ..plane.trace import Claim, Move, Trace, broadcast_move, current_trace, pop_trace, push_trace

__all__ = [
    "BOOK_TITLES",
    "BadConfiguration",
    "CONSTRUCTION",
    "HEATH",
    "HEATH_CREDIT",
    "Out",
    "ProofFailure",
    "Proposition",
    "Run",
    "THEOREM",
    "all_propositions",
    "claim",
    "get",
    "hypothesis",
    "proposition",
    "reference_kind",
    "relaxed_hypotheses",
    "run",
    "run_sampled",
]

CONSTRUCTION = "construction"
THEOREM = "theorem"

# ---------------------------------------------------------------------------
# Heath's text
# ---------------------------------------------------------------------------
# Statements are Thomas L. Heath's 1908 translation, which is public domain.
# They are parsed by tools/fetch_heath.py rather than retyped, so the words are
# his and nothing else. All 465 propositions of all thirteen books are in the
# file, and a proposition whose ref is missing from it raises rather than
# falling back to anything: there is no second kind of statement to fall back
# to, and no way to smuggle a paraphrase in by omission.
#
# Where the source misprints Heath the correction is recorded in ERRATA in the
# fetch script and shipped in the file, so every departure from the scan can be
# read and checked.

_HEATH_PATH = Path(__file__).with_name("heath.json")


def _load_heath() -> tuple[dict[str, str], list[dict]]:
    payload = json.loads(_HEATH_PATH.read_text(encoding="utf-8"))
    return payload["statements"], payload.get("errata", [])


HEATH, ERRATA = _load_heath()

HEATH_CREDIT = (
    "Thomas L. Heath, <i>The Thirteen Books of Euclid's Elements</i> "
    "(Cambridge University Press, 1908). Public domain."
)

BOOK_ORDER = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]

BOOK_TITLES = {
    "I": "Rectilinear figures",
    "II": "Geometric algebra",
    "III": "Circles",
    "IV": "Inscribed and circumscribed figures",
    "V": "The theory of proportion",
    "VI": "Similar figures",
    "VII": "Elementary number theory",
    "VIII": "Continued proportions",
    "IX": "Numbers, primes and perfect numbers",
    "X": "Incommensurable magnitudes",
    "XI": "Solid geometry",
    "XII": "Method of exhaustion",
    "XIII": "The regular solids",
}


class ProofFailure(AssertionError):
    """A claim did not hold of the constructed model."""


class Out(SimpleNamespace):
    """What a proposition hands back: named results, plus its trace."""

    trace: Trace
    proposition: str


@dataclass
class Proposition:
    ref: str
    book: str
    number: int
    kind: str
    raw: Callable
    wrapped: Callable = field(default=None, repr=False)
    sample: Optional[Callable] = None
    note: str = ""
    calls: set[str] = field(default_factory=set)
    cites: set[str] = field(default_factory=set)

    @property
    def statement(self) -> str:
        """The enunciation, in Heath's words. There is no other kind."""
        try:
            return HEATH[self.ref]
        except KeyError:  # pragma: no cover - every ref of every book is present
            raise KeyError(
                f"{self.ref} has no enunciation in heath.json. Statements are parsed, "
                f"never written: add the proposition to the source text rather than "
                f"describing it here."
            ) from None

    @property
    def depends_on(self) -> set[str]:
        """Propositions this one needs, whether by calling or by citing.

        A proposition naming itself (as VII.2 does, stating the algorithm it is
        about) is not a dependency, and would put a self-loop in the graph.
        """
        return {
            ref
            for ref in self.calls | self.cites
            if reference_kind(ref) == "proposition" and ref != self.ref
        }

    @property
    def axioms_used(self) -> set[str]:
        return {ref for ref in self.cites if reference_kind(ref) != "proposition"}

    def source(self) -> str:
        try:
            return textwrap.dedent(inspect.getsource(self.raw))
        except OSError:  # pragma: no cover - only when source is unavailable
            return ""

    def sort_key(self) -> tuple[int, int]:
        index = BOOK_ORDER.index(self.book) if self.book in BOOK_ORDER else len(BOOK_ORDER)
        return index, self.number

    def __repr__(self) -> str:
        return f"<{self.ref} {self.statement[:52]}>"


@dataclass
class Run:
    proposition: Proposition
    value: Out
    trace: Trace
    context: Context

    @property
    def claims(self) -> list[Claim]:
        return self.trace.claims


_REGISTRY: dict[str, Proposition] = {}
_CALL_STACK: list[Proposition] = []


def reference_kind(ref: str) -> str:
    """Classify a citation: a proposition, or one of Euclid's first principles.

    Only a book numeral followed by a single number names a proposition.  A
    range such as ``X.48-53`` points at a group of them, and ``V.Def.5`` at a
    definition; neither is a node in the graph.
    """
    parts = ref.split(".")
    head = parts[0]
    if head in BOOK_ORDER:
        if len(parts) == 2 and parts[1].isdigit():
            return "proposition"
        if len(parts) >= 2 and parts[1] in ("Def", "Definition"):
            return "definition"
        return "group of propositions"
    if head in ("Post", "Postulate"):
        return "postulate"
    if head == "C" and len(parts) > 1 and parts[1] == "N":
        return "common notion"
    if head in ("CN", "Common"):
        return "common notion"
    if head in ("Def", "Definition"):
        return "definition"
    return "other"


def _register_given(name: str, value: Any) -> Any:
    """Label a proposition's inputs and record them as the figure's givens.

    Parameter names become point labels, so ``def prop_I_1(a, b)`` yields the
    points A and B in the diagram without the body having to say so.
    """
    if isinstance(value, Point):
        labelled = value.named(name.strip("_").upper())
        broadcast_move(Move("free", labelled.label, obj=labelled, note="given"))
        return labelled
    if isinstance(value, (list, tuple)) and value and all(isinstance(v, Point) for v in value):
        labelled = [
            _register_given(f"{name}{index + 1}", point) for index, point in enumerate(value)
        ]
        return type(value)(labelled) if isinstance(value, tuple) else labelled
    return value


def proposition(
    ref: str,
    kind: str = THEOREM,
    sample: Optional[Callable] = None,
    note: str = "",
) -> Callable:
    """Register a proposition and wrap it so that running it records itself.

    There is deliberately no way to give a proposition its own wording.  The
    enunciation is looked up from Heath by ``ref``, so the only thing this
    decorator can say about what a proposition *states* is which one it is.
    ``note`` is commentary, shown as commentary, and never stands in for the
    statement.
    """

    def decorate(function: Callable) -> Callable:
        book, number = ref.split(".")
        if ref not in HEATH:
            raise KeyError(f"{ref} is not a proposition of the Elements")
        entry = Proposition(
            ref=ref,
            book=book,
            number=int(number),
            kind=kind,
            raw=function,
            sample=sample,
            note=note,
        )
        signature = inspect.signature(function)

        def wrapper(*args, **kwargs) -> Out:
            if _CALL_STACK:
                _CALL_STACK[-1].calls.add(ref)
            trace = push_trace(Trace(proposition=ref))
            _CALL_STACK.append(entry)
            try:
                bound = signature.bind(*args, **kwargs)
                bound.apply_defaults()
                for name, value in list(bound.arguments.items()):
                    # Required positional parameters are the figure's givens.
                    # Optional ones are construction choices (which side to put
                    # the angle on, and so forth) and are not lettered points.
                    if signature.parameters[name].default is inspect.Parameter.empty:
                        bound.arguments[name] = _register_given(name, value)
                result = function(*bound.args, **bound.kwargs)
            finally:
                _CALL_STACK.pop()
                pop_trace()
            if result is None:
                result = Out()
            if not isinstance(result, Out):
                raise TypeError(f"{ref} must return an Out(...), got {type(result).__name__}")
            result.trace = trace
            result.proposition = ref
            return result

        wrapper.__name__ = function.__name__
        wrapper.__doc__ = function.__doc__
        wrapper.proposition = entry
        entry.wrapped = wrapper
        _REGISTRY[ref] = entry
        return wrapper

    return decorate


def claim(text: str, by: Any, holds: bool, detail: str = "") -> bool:
    """Assert a proof step, cite its warrant, and check it against the model."""
    citations: tuple[str, ...] = (by,) if isinstance(by, str) else tuple(by)
    if _CALL_STACK:
        _CALL_STACK[-1].cites.update(citations)
    holds = bool(holds)
    trace = current_trace()
    if trace is not None:
        trace.add_claim(Claim(text, citations, holds, detail))
    if not holds:
        owner = _CALL_STACK[-1].ref if _CALL_STACK else "?"
        raise ProofFailure(f"{owner}: claim failed -- {text} (cited: {', '.join(citations)})")
    return holds


def hypothesis(text: str, holds: bool) -> bool:
    """Record and enforce a proposition's stated hypothesis.

    Hypotheses are checked too, but they are not proof steps: they are the
    contract the caller must satisfy, and a violation is a bad input rather
    than a false theorem.
    """
    holds = bool(holds)
    trace = current_trace()
    owner = _CALL_STACK[-1].ref if _CALL_STACK else "?"
    if trace is not None:
        trace.add_claim(Claim(text, ("hypothesis",), holds))
    if not holds:
        if _RELAXED:
            # Someone is asking what happens *without* this hypothesis, so note
            # the violation and let the proposition carry on. See measure.necessity.
            _RELAXED[-1].append((owner, text))
            return False
        raise BadConfiguration(f"{owner}: hypothesis violated -- {text}")
    return holds


# When non-empty, a violated hypothesis is recorded rather than raised. Only
# measure.necessity pushes onto this, and only to ask whether a conclusion
# survives its hypothesis being broken.
_RELAXED: list[list[tuple[str, str]]] = []


@contextmanager
def relaxed_hypotheses():
    """Run without enforcing hypotheses, collecting the ones that fail.

    Ordinarily a violated hypothesis means bad input and the run is abandoned:
    the proposition says nothing about configurations it excludes. To find out
    whether an excluded configuration would have satisfied the conclusion
    anyway, the exclusion has to be lifted. What comes back is the list of
    ``(ref, text)`` violations, so the caller can tell which hypothesis it
    actually broke.
    """
    collected: list[tuple[str, str]] = []
    _RELAXED.append(collected)
    try:
        yield collected
    finally:
        _RELAXED.pop()


class BadConfiguration(ValueError):
    """The inputs do not satisfy the proposition's hypotheses."""


def get(ref: str) -> Proposition:
    if ref not in _REGISTRY:
        raise KeyError(f"no such proposition: {ref}")
    return _REGISTRY[ref]


def all_propositions() -> list[Proposition]:
    return sorted(_REGISTRY.values(), key=Proposition.sort_key)


def _tower_in(value: Any):
    """Find a tower among the arguments, if the caller brought one."""
    if isinstance(value, Surd):
        return value.tower
    if isinstance(value, Point):
        return _tower_in(value.x) or _tower_in(value.y)
    if isinstance(value, (list, tuple)):
        for item in value:
            found = _tower_in(item)
            if found is not None:
                return found
    return None


def run(ref: str, *args, **kwargs) -> Run:
    """Execute a proposition at top level.

    The proposition joins an existing tower when there is one to join -- either
    because the inputs carry constructible coordinates, or because the caller
    is already inside a Context.  Results from two different towers cannot be
    compared, so inheriting is what makes ``run`` composable.
    """
    entry = get(ref)
    open_context = active_context()
    inherited = (
        _tower_in(args)
        or _tower_in(tuple(kwargs.values()))
        or (open_context.tower if open_context is not None else None)
    )
    with Context(ref, tower=inherited) as context:
        value = entry.wrapped(*args, **kwargs)
    return Run(entry, value, value.trace, context)


def run_sampled(ref: str, rng) -> Run:
    """Execute a proposition on freshly sampled inputs."""
    entry = get(ref)
    if entry.sample is None:
        raise ValueError(f"{ref} has no input sampler")
    with Context(ref) as context:
        arguments = entry.sample(rng)
        value = entry.wrapped(*arguments)
    run_result = Run(entry, value, value.trace, context)
    run_result.trace.inputs = {"args": arguments}
    return run_result
