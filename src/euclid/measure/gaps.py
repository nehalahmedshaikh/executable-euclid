"""Where Book X's taxonomy stops naming things.

Book X sorts the irrational magnitudes that straightedge and compass produce
into thirteen named species.  It is often described as if that were an
exhaustive classification of the constructible irrationals.  It is not, and the
classifier can be made to show exactly where it runs out: search the simple
constructible numbers in order of complexity and report the first one Euclid has
no name for.

The witness is small and checkable by hand.  It matters because it marks the
boundary of the book's ambition: Euclid classifies the magnitudes that arise
from *applying areas* -- sums and differences of two terms -- and a number
needing three terms falls outside that, however constructible it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Iterator, Optional

from ..elements.book10 import classify
from ..kernel.field import Context, fmt, sqrt, to_float
from ..kernel.minpoly import degree, min_poly, poly_str

__all__ = ["Gap", "candidates", "simplest_gap", "taxonomy_gaps"]

UNNAMED = "an irrational outside Euclid's thirteen species"


@dataclass
class Gap:
    expression: str
    value_float: float
    degree: int
    minimal_polynomial: str
    terms: int          # how many terms it resolves into
    reason: str

    def __str__(self) -> str:
        return (f"{self.expression}\n"
                f"  ~ {self.value_float:.10f}\n"
                f"  degree over Q     : {self.degree}\n"
                f"  minimal polynomial: {self.minimal_polynomial}\n"
                f"  Book X calls this : {UNNAMED}\n"
                f"  because           : {self.reason}")


def candidates() -> Iterator[tuple[str, Callable]]:
    """Constructible numbers in rough order of complexity.

    Built the way Euclid builds: rationals, then square roots of rationals,
    then sums of those, then nested roots.  The order is deliberately naive --
    the point is to find the *simplest* thing the taxonomy misses, so the search
    must not be steered toward a clever example.
    """
    smalls = [1, 2, 3, 5, 6, 7]
    # Two terms: these are the binomials and apotomes, and are all named.
    for a in (1, 2, 3):
        for b in smalls:
            yield f"{a} + sqrt{b}", (lambda a=a, b=b: a + sqrt(b))
    # Two irrational terms.
    for b in smalls:
        for c in smalls:
            if b < c:
                yield f"sqrt{b} + sqrt{c}", (lambda b=b, c=c: sqrt(b) + sqrt(c))
    # Three terms: a rational and two roots.
    for a in (1, 2, 3):
        for b in smalls:
            for c in smalls:
                if b < c:
                    yield (f"{a} + sqrt{b} + sqrt{c}",
                           (lambda a=a, b=b, c=c: a + sqrt(b) + sqrt(c)))
    # Three irrational terms.
    for b in smalls:
        for c in smalls:
            for d in smalls:
                if b < c < d:
                    yield (f"sqrt{b} + sqrt{c} + sqrt{d}",
                           (lambda b=b, c=c, d=d: sqrt(b) + sqrt(c) + sqrt(d)))
    # Nested roots, which Book X does reach: some of these are named.
    for a in (1, 2, 3):
        for b in smalls:
            yield f"sqrt({a} + sqrt{b})", (lambda a=a, b=b: sqrt(a + sqrt(b)))


def _examine(name: str, build: Callable) -> Optional[Gap]:
    """Classify one candidate, in its own context so towers never mix."""
    with Context("gap"):
        try:
            value = build()
        except Exception:  # pragma: no cover - a negative under a root
            return None
        named = classify(value)
        if named.name != UNNAMED:
            return None
        return Gap(
            expression=name,
            value_float=to_float(value),
            degree=degree(value),
            minimal_polynomial=poly_str(min_poly(value)) + " = 0",
            terms=len(named.terms),
            reason=named.reason,
        )


def taxonomy_gaps(limit: int = 12) -> list[Gap]:
    """Constructible numbers Book X has no name for, simplest first."""
    found: list[Gap] = []
    for name, build in candidates():
        gap = _examine(name, build)
        if gap is not None:
            found.append(gap)
            if len(found) >= limit:
                break
    return found


def simplest_gap() -> Optional[Gap]:
    """The first constructible number the thirteen species fail to name."""
    gaps = taxonomy_gaps(limit=1)
    return gaps[0] if gaps else None


def named_count() -> tuple[int, int]:
    """How many of the candidates tried do fall inside the thirteen."""
    named = unnamed = 0
    for name, build in candidates():
        with Context("gap"):
            try:
                value = build()
            except Exception:  # pragma: no cover
                continue
            if classify(value).name == UNNAMED:
                unnamed += 1
            else:
                named += 1
    return named, unnamed
