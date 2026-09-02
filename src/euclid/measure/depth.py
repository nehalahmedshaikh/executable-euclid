"""How algebraically deep each proposition goes.

Every magnitude a construction produces is an exact element of a tower of
quadratic extensions of Q, so it has a degree, and :func:`minpoly.degree`
returns it.  Running the whole corpus and recording the highest degree each
proposition reaches gives a map of the *Elements* by algebraic complexity --
where the second square root first becomes necessary, where the fourth, and
which books never leave the rationals at all.

Nothing about this is available from the text.  It is a property of what the
constructions *do*, and it can only be read off a corpus that runs exactly.

One trap, which caught the first version: walking point coordinates alone
reports Books V and VII to X as degree 1, because those propositions argue
about magnitudes and construct no points.  The magnitudes are in what the
proposition returns, so the walk has to go through ``Out`` as well.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Iterator, Optional

from ..elements.registry import Out, Proposition, all_propositions, run_sampled
from ..kernel.field import Surd
from ..kernel.minpoly import degree
from ..plane.objects import Circle, Line, Point
from ..solid.objects import Line3, Plane, Point3, Sphere

__all__ = ["Depth", "algebraic_depth", "depth_profile", "first_appearances"]


def _magnitudes(value, seen: Optional[set] = None) -> Iterator:
    """Every exact magnitude reachable from a value, however it is wrapped."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return
    seen.add(id(value))
    if isinstance(value, (Fraction, Surd)):
        yield value
    elif isinstance(value, Point):
        yield value.x
        yield value.y
    elif isinstance(value, Line):
        yield value.a
        yield value.b
        yield value.c
    elif isinstance(value, Circle):
        yield from _magnitudes(value.centre, seen)
        yield value.r2
    elif isinstance(value, Point3):
        yield value.x
        yield value.y
        yield value.z
    elif isinstance(value, Plane):
        yield value.a
        yield value.b
        yield value.c
        yield value.d
    elif isinstance(value, Line3):
        yield from _magnitudes(value.p, seen)
        yield from _magnitudes(value.q, seen)
    elif isinstance(value, Sphere):
        yield from _magnitudes(value.centre, seen)
        yield value.r2
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _magnitudes(item, seen)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _magnitudes(item, seen)
    elif isinstance(value, Out):
        for name, item in vars(value).items():
            if name not in ("trace", "proposition"):
                yield from _magnitudes(item, seen)


@dataclass
class Depth:
    ref: str
    degree: int = 1
    where: str = ""          # the labelled point or result that reaches it
    tower_height: int = 0    # how many square roots deep the context went
    configurations: int = 0  # how many runs the degree is the maximum over
    unmeasured: int = 0      # magnitudes whose degree could not be computed

    def __str__(self) -> str:
        note = f"  ({self.unmeasured} unmeasured)" if self.unmeasured else ""
        return f"{self.ref:<8} degree {self.degree:>3}   {self.where}{note}"


def algebraic_depth(entry: Proposition, seed: int = 0, tries: int = 8) -> Optional[Depth]:
    """The highest degree over Q that one proposition's construction reaches.

    Over every configuration that runs, not the first.  The first version had
    its ``return`` inside the loop, so ``tries`` only bought a retry when a
    sample was rejected and every published ceiling rested on one figure.  A
    proposition can reach different degrees on different configurations, and the
    ceiling is the highest of them.
    """
    if entry.sample is None:
        return None
    rng = random.Random(f"depth:{entry.ref}:{seed}")
    found: Optional[Depth] = None

    for _ in range(tries):
        try:
            run = run_sampled(entry.ref, rng)
        except Exception:
            continue
        if found is None:
            found = Depth(entry.ref)
        found.configurations += 1
        found.tower_height = max(found.tower_height, run.context.tower.depth)

        def consider(magnitude, where: str) -> None:
            try:
                order = degree(magnitude)
            except Exception:
                # A magnitude whose minimal polynomial cannot be computed --
                # above MAX_TOWER_DEPTH_FOR_DEGREE the basis would have 2^depth
                # entries. This used to be skipped in silence, which lets a
                # ceiling be under-reported with nothing to show for it.
                found.unmeasured += 1
                return
            if order > found.degree:
                found.degree = order
                found.where = where

        for move in run.trace.moves:
            for magnitude in _magnitudes(move.obj):
                consider(magnitude, move.label or move.kind)
        for magnitude in _magnitudes(run.value):
            consider(magnitude, "the magnitude it produces")

    return found


def depth_profile(entries=None) -> dict:
    """Every proposition's depth, keyed by ref."""
    chosen = list(entries) if entries is not None else all_propositions()
    found = {}
    for entry in chosen:
        depth = algebraic_depth(entry)
        if depth is not None:
            found[entry.ref] = depth
    return found


def first_appearances(profile: dict) -> dict:
    """Where in the Elements each degree is first reached.

    Propositions are visited in Euclid's own order, so the answer is the
    earliest place the book demands that much algebra.
    """
    order = [entry.ref for entry in all_propositions()]
    first: dict[int, str] = {}
    for ref in order:
        depth = profile.get(ref)
        if depth is None:
            continue
        first.setdefault(depth.degree, ref)
    return dict(sorted(first.items()))


def ceilings(profile: dict) -> dict:
    """The highest degree each book reaches."""
    highest: dict[str, int] = {}
    for ref, depth in profile.items():
        book = ref.split(".")[0]
        highest[book] = max(highest.get(book, 1), depth.degree)
    return highest
