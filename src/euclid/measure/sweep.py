"""Running a proposition on figures it was not written for.

Two questions are asked of a bent figure and they are the same experiment.
*Which hypothesis was holding this up?* -- bend a given, note which hypothesis
that broke, and see whether the conclusion followed anyway.  *Which claim would
notice?* -- bend a given and see which claims came out false.  One run answers
both, so there is one run: :mod:`euclid.measure.necessity` and
:mod:`euclid.measure.mutation` are two readings of what this module observes.

They were separate passes at first, and separate passes over four hundred
propositions at forty-eight configurations each is twenty minutes that buys
nothing -- the second pass bends the same givens the same way and runs the same
constructions.

The run is made under two suspensions.  Hypotheses are recorded rather than
enforced, because a bent figure violates them by design and the point is to see
past the exclusion.  False claims are recorded rather than raised, because a
proposition stops at its first failed step and that would leave every later
claim unjudged -- one bend would say one thing instead of saying something about
all of them.

Nothing run here proves anything.  The proposition is being carried out on a
figure it does not hold for, and the values it computes on the way are
meaningless.  What is being watched is which of its own checks noticed.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Iterator

from ..elements.registry import (
    BadConfiguration,
    Proposition,
    relaxed_hypotheses,
    surveyed_claims,
)
from ..kernel.field import Context
from ..plane.construct import GeometryError
from ..plane.trace import Claim, Trace, pop_trace, push_trace
from .bend import apply as _apply
from .bend import moves as _moves

__all__ = ["BUDGET", "Observation", "bend_sweep", "ran_every_trial"]

HYPOTHESIS = ("hypothesis",)

# Seconds one proposition may spend being bent. Chosen so that the corpus sweep
# is minutes rather than an hour: at eight bends apiece the corpus took 450
# seconds and Book IV was 250 of them, because inscribing a circle in a pentagon
# is ten seconds a bend and no bend of it stops early any more.
BUDGET = 2.0

# Which propositions got all the bends they were asked for, last time they were
# swept. A trial can be skipped without producing an observation -- a bend that
# does not apply to the given it lands on -- so the caller cannot tell a
# truncated sweep from a complete one by counting what came back.
_COMPLETED: dict[str, bool] = {}


def ran_every_trial(ref: str) -> bool:
    """Whether the last sweep of this proposition spent all its trials."""
    return _COMPLETED.get(ref, True)

# A bend that breaks the construction rather than the conclusion. Anything
# outside this set is a bug in the encoding, not an outcome, and is discarded.
_BROKEN = (GeometryError, BadConfiguration, ValueError, ZeroDivisionError,
           IndexError, ArithmeticError)


@dataclass
class Observation:
    """One run of one proposition on one figure."""

    trial: int                                    # -1 is the unbent inventory run
    bent: bool                                    # False for the unbent inventory run
    violations: list = field(default_factory=list)  # (ref, text, guard) hypotheses broken
    own: list[Claim] = field(default_factory=list)  # the proposition's own claims
    hypotheses: list[Claim] = field(default_factory=list)  # ...and what it assumed
    inherited: list[Claim] = field(default_factory=list)  # those of the ones it cites
    collapsed: bool = False                       # the construction broke

    @property
    def refuted(self) -> bool:
        """One of the proposition's own claims came out false: its conclusion is
        not true of this figure."""
        return any(not c.holds for c in self.own)

    @property
    def appeal_failed(self) -> bool:
        """A proposition this one appeals to came out false on this figure.

        Kept apart from :attr:`refuted`, because they answer different questions.
        The conclusion of II.9 holds on every bent figure its analysis reaches;
        what fails there is I.47, whose betweenness the bend destroys.  Reading
        that as "the conclusion needed the hypothesis" would have overturned a
        finding the site publishes, on evidence that says only that the argument
        stopped going through.
        """
        return any(not c.holds for c in self.inherited)


def _split(outer: Trace) -> tuple[list[Claim], list[Claim], list[Claim]]:
    """The proposition's own claims and hypotheses, and the claims it inherited."""
    if not outer.children:
        return [], [], []
    mine = outer.children[0]
    own = [c for c in mine.claims if c.by != HYPOTHESIS]
    stated = [c for c in mine.claims if c.by == HYPOTHESIS]
    inherited = [c for child in mine.descendants() for c in child.claims
                 if c.by != HYPOTHESIS]
    return own, stated, inherited


def bend_sweep(
    entry: Proposition, trials: int = 24, seed: int = 0, tag: str = "sweep",
    budget: float = BUDGET,
) -> Iterator[Observation]:
    """Bend one proposition's figure repeatedly and report what each run did.

    The first observation is unbent: it is the inventory of what the proposition
    states on a figure it was written for, and without it a claim that no bend
    ever reaches would simply be absent rather than counted as unreached.

    ``budget`` is seconds, and a proposition that runs out of it stops early with
    fewer bends behind its verdict.  It is needed because a bent run is not a
    cheap run: the proposition is carried out to the end rather than stopping at
    its first false step, and on the heavy constructions of Book IV that is ten
    seconds a bend -- IV.13 alone was a quarter of the corpus sweep.  Every count
    this module feeds is a count of bends actually run, so a truncated sweep
    reports less evidence rather than the same evidence more cheaply.
    """
    if entry.sample is None:
        return
    rng = random.Random(f"{tag}:{entry.ref}:{seed}")
    started = time.monotonic()
    last = 0.0  # what the previous bend cost, as the estimate for the next
    _COMPLETED[entry.ref] = True
    plan: list = []
    for trial in range(-1, trials):
        # The unbent inventory run is never skipped; it is what the claims are
        # counted against.
        #
        # The check is predictive, not merely elapsed. Asking only whether the
        # budget is spent bounds how many trials *start* late and not how long
        # any one of them runs, so a single slow bend sails past it: IX.36 bends
        # the exponent of a perfect number, and counting the divisors of the
        # number that results took thirty seconds against a budget of two. The
        # last trial's cost is the estimate for the next one.
        spent = time.monotonic() - started
        if trial >= 0 and spent + last > budget:
            _COMPLETED[entry.ref] = False
            return
        began = time.monotonic()
        size = Fraction(rng.choice([1, 1, 2, 3]), rng.choice([1, 2, 4]))
        with Context(f"{tag}:{entry.ref}"):
            try:
                arguments = list(entry.sample(rng))
            except Exception:  # pragma: no cover - a sampler that cannot run
                continue
            if not arguments:
                continue
            if not plan:
                plan = _moves(arguments)
            if trial >= 0:
                move = plan[trial % len(plan)]
                if move[1] >= len(arguments) or (move[2] is not None
                                                 and move[2] >= len(arguments)):
                    continue
                bent = _apply(arguments, move, rng, size)
                if bent is None:
                    continue
                arguments[move[1]] = bent

            outer = push_trace(Trace(proposition=f"{tag}:{entry.ref}"))
            collapsed, unexplained = False, False
            broken: list = []
            try:
                with relaxed_hypotheses() as violations, surveyed_claims():
                    try:
                        entry.wrapped(*arguments)
                    except _BROKEN:
                        collapsed = True
                    except Exception:  # pragma: no cover - anything else is a bug
                        unexplained = True
                    broken = list(violations)
            finally:
                pop_trace()
            if unexplained:
                continue

            last = max(last, time.monotonic() - began)
            own, stated, inherited = _split(outer)
            yield Observation(trial=trial, bent=trial >= 0, violations=broken,
                              own=own, hypotheses=stated, inherited=inherited,
                              collapsed=collapsed)
