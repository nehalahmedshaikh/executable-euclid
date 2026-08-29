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


def hypothesis_necessity(
    entry: Proposition, trials: int = 24, seed: int = 0
) -> list[Necessity]:
    """Break each hypothesis of one proposition in turn and see what follows."""
    if entry.sample is None:
        return []
    rng = random.Random(f"necessity:{entry.ref}:{seed}")
    found: dict[str, Necessity] = {}

    for trial in range(trials):
        size = Fraction(rng.choice([1, 1, 2, 3]), rng.choice([1, 2, 4]))
        with Context(f"necessity:{entry.ref}"):
            try:
                arguments = list(entry.sample(rng))
            except Exception:  # pragma: no cover - a sampler that cannot run
                continue
            if not arguments:
                continue
            index = trial % len(arguments)
            moved = _jitter(arguments[index], rng, size)
            if moved is None:
                continue
            arguments[index] = moved

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
            mine = [text for ref, text in violations if ref == entry.ref]
            if len(set(mine)) != 1 or len(violations) != len(mine):
                continue
            text = mine[0]
            record = found.setdefault(text, Necessity(entry.ref, text))
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
        """Hypotheses that were broken and whose conclusions held anyway."""
        return [item for item in self.tested if item.verdict == SURVIVED]

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
            f"  survived breaking  : {counts[SURVIVED]}  <- candidates, not results"
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


def _count_hypotheses(entry: Proposition) -> int:
    """How many hypotheses a proposition states, read from its own source."""
    return entry.source().count("hypothesis(")
