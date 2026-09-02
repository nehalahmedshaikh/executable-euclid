"""Execution traces.

Everything downstream reads traces rather than re-deriving anything: the SVG
renderer draws them, the assumption ledger audits them, and the site generator
turns them into pages.  A trace records three kinds of event:

``moves``
    the primitive straightedge-and-compass operations, in order;
``predicates``
    every exact geometric test that was evaluated, with its truth value -- this
    is what lets the ledger detect facts that are true of *this diagram* rather
    than of every legal configuration;
``claims``
    the proof steps, each citing the proposition, definition, postulate or
    common notion that Euclid appeals to, and each independently checked
    against the model.

A trace may also carry ``results``: the objects the proposition was carried out
to produce.  A construction that leans on three levels of helper propositions
inherits all their scaffolding, and the figure becomes unreadable; naming the
answer lets the renderer draw it firmly and hold the scaffolding back.  Marking
is optional, and a proposition that marks nothing is drawn entirely firm, as
before.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Optional

__all__ = [
    "Claim",
    "IntersectionEvent",
    "Move",
    "PredicateEvent",
    "Trace",
    "broadcast_intersection",
    "broadcast_move",
    "current_trace",
    "drawn_apart",
    "push_trace",
    "pop_trace",
    "record_predicate",
    "record_result",
]


@dataclass
class Move:
    """One primitive operation: a point posited, a line drawn, a circle drawn."""

    kind: str  # "free" | "line" | "circle" | "intersect" | "derived"
    label: str
    obj: Any = None
    inputs: tuple = ()
    postulate: str = ""
    note: str = ""


@dataclass
class IntersectionEvent:
    """A use of intersection, recorded because existence is not a postulate.

    Euclid's five postulates let you draw lines and circles; none of them says
    that two circles which *look* like they cross actually share a point.  Every
    record here is therefore a place where the text relies on continuity it
    never states.
    """

    kind: str  # "line-line" | "line-circle" | "circle-circle"
    count: int
    guaranteed_by_postulates: bool
    detail: str = ""


@dataclass
class PredicateEvent:
    name: str
    value: Any
    detail: str = ""
    order_sensitive: bool = False


@dataclass
class Claim:
    """A proof step: a statement, its Euclidean justification, and its check."""

    text: str
    by: tuple[str, ...]
    holds: bool
    detail: str = ""


@dataclass
class Trace:
    proposition: str = ""
    moves: list[Move] = field(default_factory=list)
    intersections: list[IntersectionEvent] = field(default_factory=list)
    predicates: list[PredicateEvent] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    results: list[Any] = field(default_factory=list)
    children: list["Trace"] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)

    # -- recording ----------------------------------------------------------
    def add_move(self, move: Move) -> Move:
        self.moves.append(move)
        return move

    def add_intersection(self, event: IntersectionEvent) -> None:
        self.intersections.append(event)

    def add_predicate(self, event: PredicateEvent) -> None:
        self.predicates.append(event)

    def add_claim(self, claim: Claim) -> None:
        self.claims.append(claim)

    # -- summaries ----------------------------------------------------------
    @property
    def step_count(self) -> int:
        return sum(1 for move in self.moves if move.kind in ("line", "circle"))

    @property
    def continuity_assumptions(self) -> list[IntersectionEvent]:
        return [event for event in self.intersections if not event.guaranteed_by_postulates]

    def descendants(self) -> list["Trace"]:
        found: list[Trace] = []
        for child in self.children:
            found.append(child)
            found.extend(child.descendants())
        return found

    def signature(self) -> tuple:
        """A shape fingerprint: same construction path, same signature.

        Two runs of the same proposition on different inputs should agree here.
        When they do not, the proof is following a different route through the
        diagram -- exactly the case-dependence Euclid leaves unremarked.
        """
        return (
            tuple((move.kind, move.label) for move in self.moves),
            tuple((event.kind, event.count) for event in self.intersections),
            tuple((event.name, bool(event.value)) for event in self.predicates),
            tuple(child.signature() for child in self.children),
        )


_STACK: list[Trace] = []


def push_trace(trace: Trace) -> Trace:
    """Begin a nested trace.  Figure-level events fan out to every enclosing
    trace (a caller's diagram genuinely does contain the callee's lines), while
    predicates and claims stay with the proposition that made them."""
    if _STACK:
        _STACK[-1].children.append(trace)
    _STACK.append(trace)
    return trace


def pop_trace() -> Optional[Trace]:
    return _STACK.pop() if _STACK else None


def current_trace() -> Optional[Trace]:
    return _STACK[-1] if _STACK else None


# Where the innermost appeal began: the depth its own trace sits at.  Moves fan
# out to that trace and to anything it opens beneath it, and no further.
_APPEAL_FLOOR: list[int] = []


@contextmanager
def drawn_apart():
    """Keep what an appealed proposition draws out of the caller's figure.

    A figure-level move fans out to every enclosing trace, because a caller's
    diagram really does contain the lines its helpers drew.  A proposition
    carried out to check an appeal is different: II.13 appeals to I.47 twice, and
    fanning those out put both windmills into II.13's diagram -- twenty-one
    figures across the corpus became too crowded to read, and none of them are
    crowded in Euclid.

    The appeal still gets its own figure whole.  What it draws through helpers of
    its own belongs to it, and only the caller is spared: I.38 reached through an
    appeal must still hold the parallel it draws by I.31, because that parallel
    is the figure I.38 is about.

    Intersections fan out regardless.  Those are the continuity debt, and a step
    that carries out a proposition crossing two circles has incurred it however
    the figure is drawn; that inheritance is the whole finding about I.20.  So
    the appeal lends the caller its debt without its lines.
    """
    _APPEAL_FLOOR.append(len(_STACK))
    try:
        yield
    finally:
        _APPEAL_FLOOR.pop()


def _holders() -> list[Trace]:
    return _STACK[_APPEAL_FLOOR[-1]:] if _APPEAL_FLOOR else _STACK


def broadcast_move(move: Move) -> Move:
    for trace in _holders():
        trace.moves.append(move)
    return move


def broadcast_intersection(event: IntersectionEvent) -> IntersectionEvent:
    for trace in _STACK:
        trace.intersections.append(event)
    return event


def replay_trace(trace: Trace) -> None:
    """Attach a sub-trace that was computed earlier in this run.

    A proposition carried out twice on the same points draws the same figure,
    so the second time it is not carried out again -- the record of the first is
    hung here instead.  The moves fan out exactly as they did then, which is
    what keeps the caller's diagram whole; skipping that would leave a figure
    missing the very lines its argument is about.  Inside an appeal they fan out
    exactly as far, which is to say no further than the appeal itself.
    """
    if _STACK:
        _STACK[-1].children.append(trace)
    for holder in _holders():
        holder.moves.extend(trace.moves)
    for holder in _STACK:
        holder.intersections.extend(trace.intersections)


def record_result(*objects: Any) -> None:
    """Name the objects this proposition was carried out to produce.

    Kept on the proposition's own trace rather than broadcast: a helper's
    answer is scaffolding to its caller, which has an answer of its own.
    """
    trace = current_trace()
    if trace is None:
        return
    for item in objects:
        if item not in trace.results:
            trace.results.append(item)


def record_predicate(name: str, value: Any, detail: str = "", order_sensitive: bool = False) -> Any:
    trace = current_trace()
    if trace is not None:
        trace.add_predicate(PredicateEvent(name, value, detail, order_sensitive))
    return value
