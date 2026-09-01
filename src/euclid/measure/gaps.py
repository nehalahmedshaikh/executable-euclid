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
from ..kernel.field import Context, fmt, sign, sqrt, to_float
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


SQUAREFREE = (2, 3, 5, 6, 7, 10, 11)
COEFFICIENT = 2


def _squarefree_pairs():
    for i, m in enumerate(SQUAREFREE):
        for n in SQUAREFREE[i + 1:]:
            yield m, n


def candidates() -> Iterator[tuple[str, Callable]]:
    """Every biquadratic constructible of bounded height, in order of height.

    A number of degree at most four over Q that a straightedge and compass can
    reach lies in some ``Q(sqrt m, sqrt n)``, where it is
    ``a + b sqrt m + c sqrt n + d sqrt(mn)`` with rational coefficients.  Fixing
    ``m < n`` squarefree up to 11 and integer coefficients up to 2 in size gives
    a finite set, and this walks all of it ordered by height -- the coefficients
    and the radicands together -- so "the simplest thing Book X cannot name"
    means least height in a set that was enumerated, not first hit in a list
    somebody wrote out.

    The bound is stated rather than hidden: a constructible of degree 8, or one
    with a larger radicand, is outside this and could in principle be simpler on
    some other measure.  Within the set the search is exhaustive.
    """
    rows: list[tuple[int, str, Callable]] = []
    span = range(-COEFFICIENT, COEFFICIENT + 1)
    for m, n in _squarefree_pairs():
        for a in span:
            for b in span:
                for c in span:
                    for d in span:
                        if b == c == d == 0:
                            continue  # a rational: Book X is not about these
                        height = abs(a) + abs(b) + abs(c) + abs(d) + m + n
                        parts = ([str(a)] if a else [])
                        for coefficient, radicand in ((b, m), (c, n), (d, m * n)):
                            if coefficient:
                                head = "" if coefficient == 1 else (
                                    "-" if coefficient == -1 else f"{coefficient}*")
                                parts.append(f"{head}sqrt{radicand}")
                        name = " + ".join(parts).replace("+ -", "- ")
                        subtractions = sum(1 for k in (a, b, c, d) if k < 0)
                        rows.append((
                            height, subtractions, name,
                            (lambda a=a, b=b, c=c, d=d, m=m, n=n:
                             a + b * sqrt(m) + c * sqrt(n) + d * sqrt(m * n)),
                        ))
    # Height first, then fewest subtractions, then the name for determinism.
    # Many numbers tie on height alone -- at the minimum they are all three-term
    # -- and preferring the one written without a minus sign picks the form a
    # reader would state.
    rows.sort(key=lambda row: (row[0], row[1], row[2]))
    for _height, _subtractions, name, build in rows:
        yield name, build


def _examine(name: str, build: Callable) -> Optional[Gap]:
    """Classify one candidate, in its own context so towers never mix."""
    with Context("gap"):
        try:
            value = build()
        except Exception:  # pragma: no cover - a negative under a root
            return None
        # Book X classifies magnitudes, so a lattice point that comes out
        # negative or zero is not a candidate at all. Enumerating a whole
        # coefficient box produces plenty of them.
        if sign(value) <= 0:
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
            if sign(value) <= 0:
                continue  # Book X classifies magnitudes, so these are not candidates
            if classify(value).name == UNNAMED:
                unnamed += 1
            else:
                named += 1
    return named, unnamed
