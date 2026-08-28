"""Book V: Eudoxus' theory of proportion, made executable.

Definition 5 is the most admired sentence in Greek mathematics and the least
usable one:

    Magnitudes are said to be in the same ratio, the first to the second and
    the third to the fourth, when, if any equimultiples whatever are taken of
    the first and third, and any equimultiples whatever of the second and
    fourth, the former equimultiples alike exceed, are alike equal to, or alike
    fall short of, the latter equimultiples respectively.

It quantifies over *all* pairs of multiples, so it cannot be checked by
enumeration.  But it can be checked constructively in the other direction: two
ratios differ exactly when some pair ``(m, n)`` separates them, and that pair
can be *found*.  :func:`separating_witness` finds it, which turns Eudoxus'
definition from a description into a decision procedure.

Alongside it sits :func:`anthyphairesis`, Euclid's own alternating subtraction
(the engine of VII.1-2 and X.2): it terminates exactly when two magnitudes are
commensurable, and its quotients are the continued fraction of their ratio.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Optional

from ..kernel.field import Constructible, is_zero, sign, sqrt, to_float
from . import samples
from .registry import THEOREM, Out, claim, hypothesis, proposition

__all__ = [
    "anthyphairesis",
    "commensurable",
    "eudoxus_same_ratio",
    "separating_witness",
]


def _floor(x: Constructible) -> int:
    """Exact floor of a constructible number."""
    guess = int(to_float(x) // 1)
    while sign(x - guess) < 0:
        guess -= 1
    while sign(x - (guess + 1)) >= 0:
        guess += 1
    return guess


def _simplest_between(
    low: Constructible, high: Optional[Constructible], depth: int = 0
) -> tuple[int, int]:
    """The simplest fraction strictly between ``low`` and ``high``.

    ``high`` of ``None`` means unbounded above.  This is the continued-fraction
    construction: if an integer fits in the gap, take it; otherwise both ends
    share an integer part, so strip it and recurse on the reciprocals of the
    fractional parts.  The recursion is as deep as the continued fraction is
    long, which is why it finds a witness between ratios a millionth apart
    without a millionth of a search.
    """
    if depth > 200:  # pragma: no cover - would mean the ends were not distinct
        raise ArithmeticError("simplest-between failed to converge")
    whole = _floor(low)
    if high is None or sign((whole + 1) - high) < 0:
        return whole + 1, 1
    low_part, high_part = low - whole, high - whole
    upper = None if is_zero(low_part) else 1 / low_part
    numerator, denominator = _simplest_between(1 / high_part, upper, depth + 1)
    return whole * numerator + denominator, numerator


def separating_witness(
    a: Constructible, b: Constructible, c: Constructible, d: Constructible
) -> Optional[tuple[int, int]]:
    """Find equimultiples that tell the ratios ``a:b`` and ``c:d`` apart.

    Returns ``(m, n)`` such that ``m*a`` and ``n*b`` compare one way while
    ``m*c`` and ``n*d`` compare the other -- the concrete witness Definition 5
    asks about.  Returns ``None`` when the ratios agree, in which case no such
    pair exists at all, which is exactly what Eudoxus means by "the same ratio".
    """
    if a * d == b * c:
        return None
    (low_a, low_b), (high_c, high_d) = (
        ((a, b), (c, d)) if a * d < b * c else ((c, d), (a, b))
    )
    numerator, denominator = _simplest_between(low_a / low_b, high_c / high_d)
    return denominator, numerator


def eudoxus_same_ratio(
    a: Constructible, b: Constructible, c: Constructible, d: Constructible, bound: int = 60
) -> bool:
    """Definition 5 itself, tested over all equimultiples up to ``bound``."""
    for m in range(1, bound + 1):
        for n in range(1, bound + 1):
            if sign(m * a - n * b) != sign(m * c - n * d):
                return False
    return True


def anthyphairesis(
    greater: Constructible, lesser: Constructible, steps: int = 24
) -> tuple[list[int], bool]:
    """Euclid's alternating subtraction; returns the quotients and whether it ended.

    Termination means the magnitudes are commensurable -- they have a common
    measure -- and the quotients are the continued fraction of their ratio.
    """
    quotients: list[int] = []
    first, second = greater, lesser
    for _ in range(steps):
        if is_zero(second):
            return quotients, True
        quotient = _floor(first / second)
        quotients.append(quotient)
        first, second = second, first - quotient * second
    return quotients, is_zero(second)


def commensurable(x: Constructible, y: Constructible) -> bool:
    """Do two magnitudes have a common measure?  Decided exactly, not by search.

    Anthyphairesis answers this by running, and may run forever; the kernel
    answers it by looking, because a ratio is rational precisely when it comes
    out of the field as a Fraction.
    """
    return isinstance(x / y, Fraction)


# ---------------------------------------------------------------------------
# propositions
# ---------------------------------------------------------------------------


def _proportional_magnitudes(rng):
    """Four magnitudes in proportion, some of them irrational."""
    a = Fraction(rng.randint(1, 9), rng.randint(1, 4))
    b = Fraction(rng.randint(1, 9), rng.randint(1, 4))
    if rng.random() < 0.5:
        a = a * sqrt(rng.choice([2, 3, 5, 6, 7]))
    scale = Fraction(rng.randint(1, 6), rng.randint(1, 5))
    return a, b, a * scale, b * scale


def _six_proportional(rng):
    a, b, c, d = _proportional_magnitudes(rng)
    scale = Fraction(rng.randint(1, 6), rng.randint(1, 5))
    return a, b, c, d, a * scale, b * scale


@proposition(
    "V.11",
    "Ratios which are the same with the same ratio are also the same with one another.",
    THEOREM,
    sample=_six_proportional,
    note="Transitivity of proportion -- which Eudoxus has to prove, because his "
    "ratios are not numbers.",
)
def prop_V_11(a, b, c, d, e, f) -> Out:
    hypothesis("a : b = c : d", a * d == b * c)
    hypothesis("c : d = e : f", c * f == d * e)
    claim("therefore a : b = e : f", "Def.5", a * f == b * e)
    claim("and no equimultiples separate them", "Def.5",
          separating_witness(a, b, e, f) is None)
    return Out()


@proposition(
    "V.16",
    "If four magnitudes are proportional, then they are also proportional alternately.",
    THEOREM,
    sample=_proportional_magnitudes,
)
def prop_V_16(a, b, c, d) -> Out:
    hypothesis("a : b = c : d", a * d == b * c)
    hypothesis("the magnitudes are of the same kind and nonzero",
               not is_zero(a) and not is_zero(b) and not is_zero(c) and not is_zero(d))
    claim("alternately, a : c = b : d -- no equimultiples separate the alternated "
          "ratios either", "Def.5", separating_witness(a, c, b, d) is None)
    return Out()


def _unequal_ratios(rng):
    a = Fraction(rng.randint(1, 9), rng.randint(1, 4))
    b = Fraction(rng.randint(1, 9), rng.randint(1, 4))
    c = Fraction(rng.randint(1, 9), rng.randint(1, 4))
    d = Fraction(rng.randint(1, 9), rng.randint(1, 4))
    while a * d == b * c:
        d = d + 1
    return a, b, c, d


@proposition(
    "V.8",
    "Of unequal magnitudes, the greater has to the same a greater ratio than the less "
    "has; and the same has to the less a greater ratio than it has to the greater.",
    THEOREM,
    sample=_unequal_ratios,
    note="The constructive core of Book V: when two ratios differ, a pair of "
    "equimultiples can be produced that proves it.",
)
def prop_V_8(a, b, c, d) -> Out:
    hypothesis("the ratios a : b and c : d are unequal", a * d != b * c)
    witness = separating_witness(a, b, c, d)
    claim("equimultiples can be found which separate the two ratios", "Def.5",
          witness is not None)
    m, n = witness
    claim(f"with m = {m} and n = {n} the multiples fall on opposite sides", "Def.5",
          sign(m * a - n * b) != sign(m * c - n * d))
    return Out(witness=witness)


@proposition(
    "V.9",
    "Magnitudes which have the same ratio to the same equal one another; and magnitudes "
    "to which the same has the same ratio are equal.",
    THEOREM,
    sample=_proportional_magnitudes,
    note="Definition 5 executed in both directions: equal ratios admit no separating "
    "equimultiples, and unequal magnitudes always do.",
)
def prop_V_9(a, b, c, d) -> Out:
    hypothesis("a : b = c : d", a * d == b * c)
    claim("no equimultiples up to the searched bound separate the ratios", "Def.5",
          eudoxus_same_ratio(a, b, c, d, bound=20))
    claim("and none exist at all", "Def.5", separating_witness(a, b, c, d) is None)
    claim("so a magnitude having this ratio to b is determined uniquely", "Def.5",
          separating_witness(a, b, a * 2, b * 2) is None)
    return Out()
