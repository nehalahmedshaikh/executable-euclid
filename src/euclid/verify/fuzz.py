"""Randomised certification.

Each proposition is run on many configurations that satisfy its hypotheses
exactly, and every claim is checked against the constructed model.  Two things
are worth being precise about, since the value of the whole project rests on
them.

**What this establishes.**  For a conclusion that is a polynomial identity in
the coordinates -- which covers the equalities of length, area and angle that
Book I trades in -- agreement at randomly chosen rational parameters is strong
evidence of an identity, in the Schwartz-Zippel sense: a nonzero polynomial of
low degree vanishes on only a thin set of samples.  Because the arithmetic is
exact there is no numerical slack to hide behind; a claim either holds or it
does not.

**What it does not establish.**  This is a model check, not a synthetic
derivation.  We verify that the conclusion holds of the figure the construction
built, not that it follows from the postulates by Euclid's rules of inference.
Configurations the sampler never visits are not covered, which is exactly why
:mod:`euclid.verify.ledger` exists: it looks for the places where the
construction's behaviour depends on which configuration it was handed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable, Optional

from ..elements.registry import (
    BadConfiguration,
    ProofFailure,
    Proposition,
    all_propositions,
    get,
    run_sampled,
)
from ..plane.construct import GeometryError

__all__ = ["Failure", "Report", "certify", "certify_all", "warm_up"]

DEFAULT_TRIALS = 20


@dataclass
class Failure:
    kind: str
    message: str
    trial: int


@dataclass
class Report:
    ref: str
    title: str
    trials: int = 0
    verified: int = 0
    rejected: int = 0
    claims_checked: int = 0
    failures: list[Failure] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures and self.verified > 0

    @property
    def status(self) -> str:
        if self.failures:
            return "FAILED"
        if self.verified == 0:
            return "no valid inputs"
        return "certified"

    def line(self) -> str:
        return (
            f"{self.ref:<7} {self.status:<12} "
            f"{self.verified:>3} verified, {self.rejected:>2} rejected, "
            f"{self.claims_checked:>3} claims"
        )


def certify(ref: str, trials: int = DEFAULT_TRIALS, seed: int = 0) -> Report:
    """Run one proposition on ``trials`` sampled configurations."""
    entry = get(ref)
    report = Report(ref=ref, title=entry.statement, trials=trials)
    if entry.sample is None:
        return report
    rng = random.Random(f"{ref}:{seed}")
    for trial in range(trials):
        try:
            result = run_sampled(ref, rng)
        except BadConfiguration:
            report.rejected += 1
        except GeometryError as exc:
            report.failures.append(Failure("degenerate", str(exc), trial))
        except ProofFailure as exc:
            report.failures.append(Failure("claim", str(exc), trial))
        except Exception as exc:  # pragma: no cover - genuine bugs surface here
            report.failures.append(Failure(type(exc).__name__, str(exc), trial))
        else:
            report.verified += 1
            report.claims_checked += len(result.trace.claims)
    return report


def certify_all(
    book: Optional[str] = None,
    trials: int = DEFAULT_TRIALS,
    seed: int = 0,
    propositions: Optional[Iterable[Proposition]] = None,
) -> list[Report]:
    chosen = list(propositions) if propositions is not None else all_propositions()
    if book is not None:
        chosen = [entry for entry in chosen if entry.book == book]
    return [certify(entry.ref, trials=trials, seed=seed) for entry in chosen]


def warm_up(seed: int = 0) -> None:
    """Execute every proposition once so the dependency graph is populated.

    Calls and citations are recorded as they happen, so nothing knows what
    depends on what until the code has actually run.
    """
    for entry in all_propositions():
        if entry.sample is None:
            continue
        rng = random.Random(f"{entry.ref}:{seed}")
        for _ in range(8):
            try:
                run_sampled(entry.ref, rng)
                break
            except (BadConfiguration, GeometryError):
                continue
            except ProofFailure:
                break
