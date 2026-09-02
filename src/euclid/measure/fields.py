"""Which propositions survive when the number field is made smaller.

Hilbert's method, executed: build a model where an axiom fails and see what
breaks.  The field a construction is allowed to build in is restricted, the
corpus is run again, and each proposition either completes or names the step
where it could not.

Three rungs:

``Q``
    the rational plane.  No square root at all beyond what the rationals
    already contain.
``Q^pyth``
    Hilbert's Pythagorean field: roots of sums of two squares, which is exactly
    what a straightedge and a segment-transferrer produce.  A length may be
    measured; two circles may not be crossed.
``Q^eucl``
    the constructible numbers, which is what the rest of this project uses.

The rung that carries the result is the middle one.  Every square root the
corpus takes is either a **hypotenuse** -- measuring a length, normalising an
angle -- or a **circle intersection**, and those are different acts.  Only the
second is continuity.  Splitting them is what this module is for; the Q column
alone would restate :mod:`euclid.verify.ledger`, which already records every
intersection a proposition performs.

Two disciplines keep it honest.

**Sampling is done outside the restriction.**  A sampler that needs an
irrational coordinate would otherwise fail for a reason that says nothing about
Euclid, so configurations are built with the policy off, checked for
rationality, and only then handed to a restricted run.  A proposition with no
rational configuration is recorded ``untestable`` -- never ``needs-root``.

**A success is not validity in the rational plane.**  It means no counterexample
among the configurations tried, in the same register :mod:`euclid.measure.necessity`
uses.  Propositions that verify on some rational configurations and not others
are reported as ``configuration-dependent``, with the count.
"""

from __future__ import annotations

import random
import traceback
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional

from ..elements.registry import (
    BadConfiguration,
    ProofFailure,
    Proposition,
    all_propositions,
    get,
)
from ..kernel.field import (
    Context,
    FieldPolicy,
    Pythagorean,
    Rational,
    RootNotInField,
    Surd,
    fmt,
)
from ..plane.construct import GeometryError
from ..plane.objects import Circle, Line, Point
from ..solid.objects import Line3, Plane, Point3, Sphere

__all__ = [
    "FieldVerdict",
    "LADDER",
    "field_profile",
    "field_verdict",
    "partition",
]

LADDER = (("Q", Rational), ("Q^pyth", Pythagorean))

# what the root was wanted for
CONTINUITY = "continuity"    # two circles, or a line and a circle, had to meet
MEASUREMENT = "measurement"  # a length or an angle was measured
MAGNITUDE = "magnitude"      # the proposition's own subject is irrational

ALWAYS = "always"
NEVER = "never"
SOMETIMES = "configuration-dependent"
UNTESTABLE = "untestable"


def _is_rational(value, seen: Optional[set] = None) -> bool:
    """Does this configuration avoid square roots entirely?"""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return True
    seen.add(id(value))
    if isinstance(value, Surd):
        return False
    if isinstance(value, Point):
        return _is_rational(value.x, seen) and _is_rational(value.y, seen)
    if isinstance(value, Point3):
        return all(_is_rational(part, seen) for part in (value.x, value.y, value.z))
    if isinstance(value, Plane):
        return all(_is_rational(part, seen)
                   for part in (value.a, value.b, value.c, value.d))
    if isinstance(value, Line3):
        return _is_rational(value.p, seen) and _is_rational(value.q, seen)
    if isinstance(value, Sphere):
        return _is_rational(value.centre, seen) and _is_rational(value.r2, seen)
    if isinstance(value, Line):
        return all(_is_rational(c, seen) for c in (value.a, value.b, value.c))
    if isinstance(value, Circle):
        return _is_rational(value.centre, seen) and _is_rational(value.r2, seen)
    if isinstance(value, (list, tuple, set, frozenset)):
        return all(_is_rational(item, seen) for item in value)
    return True


def _blame(error: RootNotInField) -> tuple[str, str]:
    """What asked for the root, from the innermost frame outside the kernel."""
    for frame in reversed(traceback.extract_tb(error.__traceback__)):
        where = frame.filename.replace("\\", "/")
        if "/kernel/" in where:
            continue
        site = f"{where.rsplit('/', 1)[-1]}:{frame.name}:{frame.lineno}"
        # Measuring a length is one act and crossing two circles is another,
        # and the whole of this analysis is telling them apart. Space has its
        # own pair of modules doing the same two jobs.
        if where.endswith(("plane/angles.py", "solid/angles.py")):
            return MEASUREMENT, site
        if where.endswith(("plane/construct.py", "solid/construct.py")):
            return CONTINUITY, site
        if "/elements/" in where:
            # The proposition's own subject is irrational -- Book X asks for
            # roots directly, and that is not a debt of the instrument.
            return MAGNITUDE, site
        raise AssertionError(
            f"a root was asked for at {site}, which this analysis does not "
            f"classify. Falling through to '{MAGNITUDE}' is how a whole module "
            f"of square roots gets filed as somebody else's problem: give the "
            f"frame a cause here instead.")
    return MAGNITUDE, "?"


@dataclass
class FieldVerdict:
    """How one proposition fared over one restricted field."""

    ref: str
    field_name: str
    configurations: int = 0   # rational configurations actually run
    verified: int = 0
    needs_root: int = 0
    other_failure: int = 0
    cause: str = ""
    site: str = ""
    radicand: str = ""

    @property
    def verdict(self) -> str:
        if not self.configurations:
            return UNTESTABLE
        if self.verified == self.configurations:
            return ALWAYS
        if self.verified:
            return SOMETIMES
        return NEVER

    def __str__(self) -> str:
        detail = f"  {self.cause} at {self.site}" if self.cause else ""
        return (f"{self.ref:<8} {self.field_name:<8} {self.verdict:<24}"
                f"({self.verified}/{self.configurations}){detail}")


def field_verdict(
    entry: Proposition,
    policy: FieldPolicy,
    trials: int = 12,
    seed: int = 0,
) -> FieldVerdict:
    """Run one proposition over a restricted field on rational configurations."""
    result = FieldVerdict(entry.ref, policy.name)
    if entry.sample is None:
        return result
    rng = random.Random(f"fields:{entry.ref}:{seed}")

    attempts = 0
    while result.configurations < trials and attempts < trials * 6:
        attempts += 1
        # Sample with the restriction off, so a sampler's own square roots are
        # never mistaken for the construction's.
        with Context(f"fields:sample:{entry.ref}") as scratch:
            try:
                arguments = list(entry.sample(rng))
            except Exception:
                continue
            if scratch.tower.depth or not _is_rational(arguments):
                continue

        result.configurations += 1
        with Context(f"fields:{entry.ref}", policy=policy):
            try:
                entry.wrapped(*arguments)
                result.verified += 1
            except RootNotInField as error:
                result.needs_root += 1
                if not result.cause:
                    result.cause, result.site = _blame(error)
                    result.radicand = fmt(error.radicand)
            except (ProofFailure, BadConfiguration, GeometryError, ValueError,
                    ZeroDivisionError, IndexError, ArithmeticError):
                result.other_failure += 1
    return result


def field_profile(policy: FieldPolicy, entries=None, trials: int = 12) -> dict:
    """Every proposition over one restricted field."""
    chosen = list(entries) if entries is not None else all_propositions()
    return {e.ref: field_verdict(e, policy, trials=trials)
            for e in chosen if e.sample is not None}


def partition(trials: int = 12) -> dict:
    """What each rung of the ladder buys, and which gains are real.

    A proposition that fails over Q and completes over Q^pyth needed a length
    measured.  One that fails over both needed two circles to meet, or is about
    an irrational magnitude to begin with.

    The gain has to be checked against the assumption ledger, because a
    proposition can pass over Q^pyth for two quite different reasons.  Either it
    never intersects a circle -- in which case measuring is genuinely all it
    needs -- or it does, and the intersection happened to land on a point the
    field already held.  I.23, I.31, I.32 and I.43 are the second kind: their
    samplers hand them rational triangles, so the circles meet where the
    configuration already was.  Reporting those as Pythagorean would be a
    finding about ``samples.triangle``.
    """
    from ..verify.ledger import audit

    rational = field_profile(Rational(), trials=trials)
    pythagorean = field_profile(Pythagorean(), trials=trials)

    buckets: dict[str, list[str]] = {
        "rational": [],           # completes over Q
        "measuring_only": [],     # Q^pyth is enough, and it crosses no circle
        "discharged_luckily": [], # Q^pyth is enough, but it does cross one
        "needs_continuity": [],
        "needs_magnitude": [],
        "configuration_dependent": [],
        "untestable": [],
    }
    for ref, over_q in rational.items():
        over_pyth = pythagorean.get(ref)
        if over_q.verdict == UNTESTABLE:
            buckets["untestable"].append(ref)
        elif over_q.verdict == ALWAYS:
            buckets["rational"].append(ref)
        elif over_q.verdict == SOMETIMES:
            buckets["configuration_dependent"].append(ref)
        elif over_pyth is not None and over_pyth.verdict == ALWAYS:
            indebted = audit(ref, trials=6).continuity_debt
            buckets["discharged_luckily" if indebted else "measuring_only"].append(ref)
        elif over_pyth is not None and over_pyth.verdict == SOMETIMES:
            buckets["configuration_dependent"].append(ref)
        elif over_pyth is not None and over_pyth.cause == CONTINUITY:
            buckets["needs_continuity"].append(ref)
        else:
            buckets["needs_magnitude"].append(ref)
    return {"buckets": buckets, "rational": rational, "pythagorean": pythagorean}
