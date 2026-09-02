"""Ways of bending a configuration, and the vocabulary they are named in.

Two analyses need to put a proposition on a figure it was not meant for.
:mod:`euclid.measure.necessity` bends one given and asks which of Euclid's
hypotheses the conclusion was leaning on; :mod:`euclid.measure.mutation` bends
one given and asks which of the proposition's own claims noticed.  They want
the same perturbations for opposite reasons, so the perturbations live here.

Every bend is exact.  A rotation uses the rational parametrisation of the
circle, a stretch multiplies by a rational, and an offset adds one, so a bent
configuration stays inside the field the original was built in and the arithmetic
downstream is as exact as it ever was.

The vocabulary matters more than it looks.  A blind offset moves a point's
distance and its direction from every other point at once, so on a proposition
with several hypotheses over several points it breaks two of them together and
the run says nothing about either.  Turning a point about another keeps the
distance and moves the angle; sliding it along the ray keeps the angle and moves
the distance.  Between them a hypothesis about a length and a hypothesis about
an angle come apart.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Optional

from ..kernel.field import Surd
from ..plane.objects import Point

__all__ = ["apply", "moves"]

# A magnitude the bends below can act on arithmetically. Book X hands its
# propositions surds rather than points, and until these were included every
# proposition from X.21 onward was unbendable: the analyses ran, found nothing
# to perturb, and reported no coverage rather than reporting the gap.
_MAGNITUDE = (int, Fraction, Surd)


def _is_magnitude(value) -> bool:
    return isinstance(value, _MAGNITUDE) and not isinstance(value, bool)


def _jitter(value, rng, size: Fraction):
    """Move a given a little, so that something about it stops being true."""
    if isinstance(value, Point):
        return Point(value.x + size * rng.choice([-1, 1]),
                     value.y + size * rng.choice([-1, 1, 0]))
    if isinstance(value, (list, tuple)):
        index = rng.randrange(len(value)) if value else 0
        moved = list(value)
        if moved and (isinstance(moved[index], Point) or _is_magnitude(moved[index])):
            moved[index] = _jitter(moved[index], rng, size)
            return type(value)(moved) if isinstance(value, tuple) else moved
    if isinstance(value, int) and not isinstance(value, bool):
        return value + rng.choice([-1, 1])
    if _is_magnitude(value):
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


def moves(arguments: list) -> list:
    """Every perturbation worth trying on one configuration."""
    places = [i for i, value in enumerate(arguments) if isinstance(value, Point)]
    plan = [("offset", i, None) for i in range(len(arguments))]
    for i, value in enumerate(arguments):
        # Scaling a magnitude changes its ratio to every other magnitude in the
        # figure, which is the whole subject of Books V and X; adding to it
        # changes the ratio and the value together.
        if _is_magnitude(value):
            plan.append(("scale", i, None))
    for i in places:
        for anchor in places:
            if i != anchor:
                plan.append(("turn", i, anchor))
                plan.append(("stretch", i, anchor))
    return plan


def apply(arguments: list, move, rng, size: Fraction) -> Optional[object]:
    """Carry out one perturbation, or return None if it does not apply."""
    kind, index, anchor = move
    if kind == "offset":
        return _jitter(arguments[index], rng, size)
    if kind == "scale":
        value = arguments[index]
        if not _is_magnitude(value):
            return None
        factor = 1 + size / 4
        return value * factor
    point, pivot = arguments[index], arguments[anchor]
    if not (isinstance(point, Point) and isinstance(pivot, Point)):
        return None
    if point == pivot:
        return None
    if kind == "turn":
        return _turned(point, pivot, size / 4)
    return _stretched(point, pivot, 1 + size / 4)
