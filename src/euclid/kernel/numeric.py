"""Adaptive-precision interval arithmetic over exact rationals.

This module knows nothing about the constructible-number tower; it only
provides rigorous enclosures so that :mod:`euclid.kernel.field` can decide the
*sign* of a nonzero element.  Every bound produced here is exact: an interval
returned by these routines is guaranteed to contain the true value.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt

__all__ = ["Interval", "sqrt_bounds"]


def sqrt_bounds(q: Fraction, prec: int) -> tuple[Fraction, Fraction]:
    """Rigorous rational bounds ``lo <= sqrt(q) <= hi`` with ``hi - lo <= 2**-prec``.

    Writing ``q = num/den`` we have ``sqrt(q) = sqrt(num*den)/den``, so a single
    integer square root at scale ``2**prec`` gives exact bounds.
    """
    if q < 0:
        raise ValueError(f"sqrt_bounds of negative rational {q}")
    num, den = q.numerator, q.denominator
    scale = 1 << prec
    root = isqrt(num * den * scale * scale)
    return Fraction(root, scale * den), Fraction(root + 1, scale * den)


class Interval:
    """A closed rational interval ``[lo, hi]`` guaranteed to contain a value."""

    __slots__ = ("lo", "hi")

    def __init__(self, lo: Fraction, hi: Fraction) -> None:
        if lo > hi:
            raise ValueError(f"malformed interval [{lo}, {hi}]")
        self.lo = lo
        self.hi = hi

    @classmethod
    def exact(cls, q: Fraction) -> "Interval":
        return cls(q, q)

    def __add__(self, other: "Interval") -> "Interval":
        return Interval(self.lo + other.lo, self.hi + other.hi)

    def __sub__(self, other: "Interval") -> "Interval":
        return Interval(self.lo - other.hi, self.hi - other.lo)

    def __neg__(self) -> "Interval":
        return Interval(-self.hi, -self.lo)

    def __mul__(self, other: "Interval") -> "Interval":
        products = (
            self.lo * other.lo,
            self.lo * other.hi,
            self.hi * other.lo,
            self.hi * other.hi,
        )
        return Interval(min(products), max(products))

    def sqrt(self, prec: int) -> "Interval":
        """Enclosure of the square root; the lower end is clamped at zero."""
        lo = self.lo if self.lo > 0 else Fraction(0)
        if self.hi < 0:
            raise ValueError("sqrt of a strictly negative interval")
        return Interval(sqrt_bounds(lo, prec)[0], sqrt_bounds(self.hi, prec)[1])

    @property
    def excludes_zero(self) -> bool:
        return self.lo > 0 or self.hi < 0

    @property
    def width(self) -> Fraction:
        return self.hi - self.lo

    def midpoint(self) -> Fraction:
        return (self.lo + self.hi) / 2

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Interval({float(self.lo)!r}, {float(self.hi)!r})"
