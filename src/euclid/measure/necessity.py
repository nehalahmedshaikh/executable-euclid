"""Which of Euclid's stated hypotheses the conclusions turn out not to need.

A proposition says nothing about configurations its hypotheses exclude, so
ordinarily an excluded configuration is thrown away.  That makes one question
unaskable: *would the conclusion have held anyway?*  Lifting the exclusion makes
it askable.

The method:

1. take a configuration the proposition's own sampler accepts;
2. move one given point by a small rational offset, which breaks something;
3. run with hypotheses recorded rather than enforced;
4. see what happened.

Three outcomes, and they mean different things:

``needed``
    a claim failed.  The hypothesis was holding the conclusion up.
``well-definedness``
    the construction itself broke -- two circles stopped meeting, a line became
    a point.  The hypothesis is keeping the construction possible rather than
    the conclusion true, which is a weaker and less interesting kind of
    necessity, so it is reported apart.
``survived``
    everything still held.  A *candidate* for a hypothesis Euclid states but the
    conclusion does not require.

Two disciplines keep this honest.  A run in which more than one hypothesis broke
is discarded, because the outcome cannot be attributed to either.  And a
candidate is never reported as a result: it is reported as a candidate, with the
number of configurations behind it, because "no counterexample was found among
the ones tried" is not "there is none".

The likeliest explanation for a surviving hypothesis is that the proposition's
claims are too weak to notice the difference -- not that Euclid was redundant.
Read the claims before believing the verdict.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional

from ..elements.registry import (
    BadConfiguration,
    ProofFailure,
    Proposition,
    all_propositions,
    get,
    relaxed_hypotheses,
    run_sampled,
)
from ..kernel.field import Context
from ..plane.construct import GeometryError
from ..plane.objects import Point

__all__ = ["Necessity", "hypothesis_necessity", "necessity_report"]

NEEDED = "needed"
WELL_DEFINED = "well-definedness"
SURVIVED = "survived"


@dataclass
class Necessity:
    """What happened to one hypothesis when it was broken."""

    ref: str
    text: str
    guard: bool = False        # our own well-formedness, not Euclid's condition
    broken: int = 0            # runs where this was the only hypothesis violated
    needed: int = 0            # ...and a claim then failed
    well_defined: int = 0      # ...and the construction broke instead
    survived: int = 0          # ...and everything still held

    @property
    def verdict(self) -> str:
        if self.needed:
            return NEEDED
        if self.survived and not self.well_defined:
            return SURVIVED
        if self.well_defined:
            return WELL_DEFINED
        return "untested"

    def __str__(self) -> str:
        return (f"{self.ref:<8} {self.verdict:<16} "
                f"({self.broken} configurations)  {self.text}")


def _jitter(value, rng, size: Fraction):
    """Move a given a little, so that something about it stops being true."""
    if isinstance(value, Point):
        return Point(value.x + size * rng.choice([-1, 1]),
                     value.y + size * rng.choice([-1, 1, 0]))
    if isinstance(value, (list, tuple)):
        index = rng.randrange(len(value)) if value else 0
        moved = list(value)
        if moved and isinstance(moved[index], Point):
            moved[index] = _jitter(moved[index], rng, size)
            return type(value)(moved) if isinstance(value, tuple) else moved
    if isinstance(value, int) and not isinstance(value, bool):
        return value + rng.choice([-1, 1])
    if isinstance(value, Fraction):
        return value + size * rng.choice([-1, 1])
    return None  # nothing sensible to perturb


def _rational_turn(t: Fraction) -> tuple:
    """An exact rotation: the rational parametrisation of the unit circle."""
    square = t * t
    return (1 - square) / (1 + square), 2 * t / (1 + square)


def _turned(point: Point, anchor: Point, t: Fraction) -> Point:
    """``point`` rotated about ``anchor``.  Keeps the distance, moves the angle."""
    cosine, sine = _rational_turn(t)
    dx, dy = point.x - anchor.x, point.y - anchor.y
    return Point(anchor.x + cosine * dx - sine * dy,
                 anchor.y + sine * dx + cosine * dy)


def _stretched(point: Point, anchor: Point, factor: Fraction) -> Point:
    """``point`` moved along the ray from ``anchor``.  Keeps the angle, moves
    the distance."""
    return Point(anchor.x + factor * (point.x - anchor.x),
                 anchor.y + factor * (point.y - anchor.y))


def _moves(arguments: list) -> list:
    """Every perturbation worth trying on one configuration.

    A blind offset changes both the distance and the direction from every other
    point at once, so on a proposition like I.4 -- three hypotheses over six
    points -- it always breaks two hypotheses together and no run can be
    attributed.  That was the whole of the 64% this analysis could not reach.

    Rotating a point about another keeps their distance and moves the angle;
    sliding it along the ray keeps the angle and moves the distance.  Between
    them a hypothesis about a length and a hypothesis about an angle can be
    broken separately.  Both are exact: the rotation uses the rational
    parametrisation of the circle, so no configuration leaves the field.
    """
    places = [i for i, value in enumerate(arguments) if isinstance(value, Point)]
    plan = [("offset", i, None) for i in range(len(arguments))]
    for i in places:
        for anchor in places:
            if i != anchor:
                plan.append(("turn", i, anchor))
                plan.append(("stretch", i, anchor))
    return plan


def _apply(arguments: list, move, rng, size: Fraction):
    """Carry out one perturbation, or return None if it does not apply."""
    kind, index, anchor = move
    if kind == "offset":
        return _jitter(arguments[index], rng, size)
    point, pivot = arguments[index], arguments[anchor]
    if not (isinstance(point, Point) and isinstance(pivot, Point)):
        return None
    if point == pivot:
        return None
    if kind == "turn":
        return _turned(point, pivot, size / 4)
    return _stretched(point, pivot, 1 + size / 4)


def hypothesis_necessity(
    entry: Proposition, trials: int = 24, seed: int = 0
) -> list[Necessity]:
    """Break each hypothesis of one proposition in turn and see what follows."""
    if entry.sample is None:
        return []
    rng = random.Random(f"necessity:{entry.ref}:{seed}")
    found: dict[str, Necessity] = {}

    plan: list = []
    for trial in range(trials):
        size = Fraction(rng.choice([1, 1, 2, 3]), rng.choice([1, 2, 4]))
        with Context(f"necessity:{entry.ref}"):
            try:
                arguments = list(entry.sample(rng))
            except Exception:  # pragma: no cover - a sampler that cannot run
                continue
            if not arguments:
                continue
            if not plan:
                plan = _moves(arguments)
            move = plan[trial % len(plan)]
            if move[1] >= len(arguments) or (move[2] is not None
                                             and move[2] >= len(arguments)):
                continue
            moved = _apply(arguments, move, rng, size)
            if moved is None:
                continue
            arguments[move[1]] = moved

            with relaxed_hypotheses() as violations:
                outcome = SURVIVED
                try:
                    entry.wrapped(*arguments)
                except ProofFailure:
                    outcome = NEEDED
                except (GeometryError, BadConfiguration, ValueError,
                        ZeroDivisionError, IndexError, ArithmeticError):
                    outcome = WELL_DEFINED
                except Exception:  # pragma: no cover - anything else is a bug
                    continue

            # Only a run that broke exactly one hypothesis says anything about
            # that hypothesis; with two broken the outcome cannot be attributed.
            mine = [(text, guard) for ref, text, guard in violations
                    if ref == entry.ref]
            if len({text for text, _ in mine}) != 1 or len(violations) != len(mine):
                continue
            text, is_guard = mine[0]
            record = found.setdefault(text, Necessity(entry.ref, text, guard=is_guard))
            record.broken += 1
            setattr(record, {NEEDED: "needed", WELL_DEFINED: "well_defined",
                             SURVIVED: "survived"}[outcome],
                    getattr(record, {NEEDED: "needed", WELL_DEFINED: "well_defined",
                                     SURVIVED: "survived"}[outcome]) + 1)
    return sorted(found.values(), key=lambda item: item.text)


@dataclass
class NecessityReport:
    """The corpus-wide picture, with its own coverage stated."""

    results: list[Necessity] = field(default_factory=list)
    propositions_tried: int = 0
    hypotheses_total: int = 0

    @property
    def tested(self) -> list[Necessity]:
        return [item for item in self.results if item.broken]

    @property
    def candidates(self) -> list[Necessity]:
        """Euclid's hypotheses that were broken and whose conclusions held anyway.

        Guards are left out.  Breaking "the ratio is not 1" and finding the
        conclusion intact says something about our input handling, and standing
        it beside a real surviving hypothesis made the count read as much more
        than it was.
        """
        return [item for item in self.tested
                if item.verdict == SURVIVED and not item.guard]

    @property
    def surviving_guards(self) -> list[Necessity]:
        """Well-formedness conditions of our own that the code tolerates."""
        return [item for item in self.tested
                if item.verdict == SURVIVED and item.guard]

    @property
    def coverage(self) -> float:
        if not self.hypotheses_total:
            return 0.0
        return len(self.tested) / self.hypotheses_total

    def summary(self) -> str:
        counts = defaultdict(int)
        for item in self.tested:
            counts[item.verdict] += 1
        return (
            f"{self.propositions_tried} propositions, "
            f"{self.hypotheses_total} hypotheses stated, "
            f"{len(self.tested)} of them broken cleanly enough to judge "
            f"({100 * self.coverage:.0f}% coverage)\n"
            f"  needed             : {counts[NEEDED]}\n"
            f"  keeps construction : {counts[WELL_DEFINED]}\n"
            f"  survived breaking  : {len(self.candidates)}  <- candidates, not results\n"
            f"  our own guards     : {len(self.surviving_guards)}  "
            "(well-formedness we added, tolerated by the code)"
        )


def necessity_report(entries=None, trials: int = 24) -> NecessityReport:
    """Run the analysis over the corpus."""
    chosen = list(entries) if entries is not None else all_propositions()
    report = NecessityReport()
    for entry in chosen:
        if entry.sample is None:
            continue
        report.propositions_tried += 1
        stated = _count_hypotheses(entry)
        report.hypotheses_total += stated
        report.results.extend(hypothesis_necessity(entry, trials=trials))
    return report


def _count_hypotheses(entry: Proposition, trials: int = 4) -> int:
    """How many hypotheses a proposition states, counted by running it.

    This used to be ``entry.source().count("hypothesis(")`` -- a text search over
    source code, which counts the word in a comment or a docstring and misses a
    hypothesis raised inside a helper or a loop.  The coverage figure this
    project publishes is a fraction with this number underneath it, so it should
    come from the same place every other number does: a trace.

    Taken as the maximum over a few configurations, because a proposition that
    branches can state a different number of hypotheses on different figures.
    """
    rng = random.Random(f"hypotheses:{entry.ref}")
    most = 0
    # A sampler that often violates its own hypothesis takes several attempts to
    # yield a run that completes -- VII.24 wants three pairwise-coprime numbers
    # and rarely gets them first go. Four bare attempts gave it no completed run
    # at all, so it reported zero hypotheses: worse than the text search it
    # replaced.
    successes = 0
    for _ in range(trials * 6):
        if successes >= trials:
            break
        with Context(f"hypotheses:{entry.ref}"):
            try:
                run = run_sampled(entry.ref, rng)
            except Exception:
                continue
            successes += 1
            most = max(most, sum(1 for claim in run.trace.claims
                                 if claim.by == ("hypothesis",)))
    return most
