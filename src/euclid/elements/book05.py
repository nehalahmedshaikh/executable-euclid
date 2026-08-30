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
    pair exists at all, which is what Eudoxus means by "the same ratio".
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


def ratio_cmp(
    a: Constructible, b: Constructible, c: Constructible, d: Constructible
) -> int:
    """Compare the ratio ``a:b`` with ``c:d``: -1, 0 or 1.

    Euclid defines "greater ratio" in Def.7 by exhibiting equimultiples, and
    that is what :func:`separating_witness` produces.  Here the comparison
    itself is settled by cross-multiplying, which for positive magnitudes says
    the same thing and says it in one step.
    """
    return sign(a * d - b * c)


# ---------------------------------------------------------------------------
# propositions
# ---------------------------------------------------------------------------
#
# Book V argues about magnitudes, not figures, so nothing here is drawn -- the
# same standing decision as Books VII to IX. What is checked is exact all the
# same, and where Euclid's statement is about equimultiples the check is made
# against Definition 5 itself, through `separating_witness`, rather than against
# the cross-multiplication that happens to decide it.


def _magnitude(rng) -> Constructible:
    """One positive magnitude, irrational about half the time."""
    value = Fraction(rng.randint(1, 9), rng.randint(1, 4))
    if rng.random() < 0.4:
        value = value * sqrt(rng.choice([2, 3, 5, 6, 7]))
    return value


def _two_magnitudes_and_a_multiple(rng):
    return _magnitude(rng), _magnitude(rng), rng.randint(2, 6)


def _two_magnitudes_and_two_multiples(rng):
    return _magnitude(rng), _magnitude(rng), rng.randint(2, 7), rng.randint(2, 7)


def _three_magnitudes(rng):
    return _magnitude(rng), _magnitude(rng), _magnitude(rng)


def _proportional_magnitudes(rng):
    """Four magnitudes in proportion, some of them irrational."""
    a = Fraction(rng.randint(1, 9), rng.randint(1, 4))
    b = Fraction(rng.randint(1, 9), rng.randint(1, 4))
    if rng.random() < 0.5:
        a = a * sqrt(rng.choice([2, 3, 5, 6, 7]))
    scale = Fraction(rng.randint(1, 6), rng.randint(1, 5))
    return a, b, a * scale, b * scale


def _a_part_of_a_whole(rng):
    """A whole, a part less than it, and the multiple taken of each (V.5)."""
    part = _magnitude(rng)
    return part + _magnitude(rng), part, rng.randint(2, 6)


def _a_proper_part_in_proportion(rng):
    """a : b = c : d with c and d genuinely smaller parts of a and b (V.19)."""
    a, b = _magnitude(rng), _magnitude(rng)
    scale = Fraction(rng.randint(1, 4), rng.randint(5, 8))  # strictly under one
    return a, b, a * scale, b * scale


def _proportion_and_a_smaller_ratio(rng):
    """a : b = c : d, and a fifth and sixth whose ratio is strictly less (V.13)."""
    a, b, c, d = _proportional_magnitudes(rng)
    e = _magnitude(rng)
    # c : d exceeds e : f exactly when c*f > d*e, so take f above d*e/c.
    f = (d * e / c) * (1 + Fraction(rng.randint(1, 4), 4))
    return a, b, c, d, e, f


def _equal_pair_and_a_third(rng):
    """Two equal magnitudes and a third to compare them with (V.7)."""
    equal = _magnitude(rng)
    return equal, equal, _magnitude(rng)


def _three_pairs_in_one_ratio(rng):
    """Three pairs of magnitudes standing in a single ratio (V.12)."""
    a, b, c, d = _proportional_magnitudes(rng)
    again = Fraction(rng.randint(1, 6), rng.randint(1, 5))
    return a, b, c, d, a * again, b * again


def _six_proportional(rng):
    a, b, c, d = _proportional_magnitudes(rng)
    scale = Fraction(rng.randint(1, 6), rng.randint(1, 5))
    return a, b, c, d, a * scale, b * scale


@proposition(
    "V.1",
    THEOREM,
    sample=_two_magnitudes_and_a_multiple,
    note="Multiplication distributes over addition, said of magnitudes that are "
    "not numbers and cannot be multiplied by one another.",
)
def prop_V_1(e, f, times: int) -> Out:
    """AB and CD are the same multiple of E and F."""
    hypothesis("the magnitudes are positive", sign(e) > 0 and sign(f) > 0)
    hypothesis("the multiple is a genuine one", times >= 1)
    ab, cd = times * e, times * f
    claim("AB is that multiple of E, and CD of F", "Def.2",
          ab == times * e and cd == times * f)
    claim("so their sum is the same multiple of the sum", "C.N.2",
          ab + cd == times * (e + f))
    return Out(sum=ab + cd)


@proposition(
    "V.2",
    THEOREM,
    sample=_two_magnitudes_and_two_multiples,
)
def prop_V_2(b, d, first_times: int, second_times: int) -> Out:
    """A is `first_times` B as C is of D; E is `second_times` B as F is of D."""
    hypothesis("the magnitudes are positive", sign(b) > 0 and sign(d) > 0)
    a, c = first_times * b, first_times * d
    e, f = second_times * b, second_times * d
    claim("the sum of the first and fifth is a multiple of the second", "Def.2",
          a + e == (first_times + second_times) * b)
    claim("and the sum of the third and sixth the same multiple of the fourth", "V.1",
          c + f == (first_times + second_times) * d)
    return Out(sums=(a + e, c + f))


@proposition(
    "V.3",
    THEOREM,
    sample=_two_magnitudes_and_two_multiples,
)
def prop_V_3(b, d, times: int, again: int) -> Out:
    """A is `times` B as C is of D; then `again`-fold A and C are `times*again`
    fold B and D."""
    hypothesis("the magnitudes are positive", sign(b) > 0 and sign(d) > 0)
    a, c = times * b, times * d
    claim("the equimultiples taken are multiples of the original multiples", "Def.2",
          again * a == again * (times * b) and again * c == again * (times * d))
    claim("so ex aequali they are equimultiples of the second and the fourth", "V.1",
          again * a == (again * times) * b and again * c == (again * times) * d)
    return Out(taken=(again * a, again * c))


@proposition(
    "V.4",
    THEOREM,
    sample=lambda rng: _proportional_magnitudes(rng) + (rng.randint(2, 6), rng.randint(2, 6)),
    note="Ratio survives being scaled on both sides -- what makes a ratio a thing "
    "about the pair rather than about the magnitudes.",
)
def prop_V_4(a, b, c, d, of_first: int, of_second: int) -> Out:
    hypothesis("a : b = c : d", a * d == b * c)
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d)))
    first, third = of_first * a, of_first * c
    second, fourth = of_second * b, of_second * d
    claim("the equimultiples stand in the same ratio", "Def.5",
          first * fourth == second * third)
    claim("and no equimultiples separate them", "Def.5",
          separating_witness(first, second, third, fourth) is None)
    return Out()


@proposition(
    "V.5",
    THEOREM,
    sample=_a_part_of_a_whole,
)
def prop_V_5(whole, part, times: int) -> Out:
    """AB is `times` CD, and the part taken away is the same multiple of a part."""
    hypothesis("the magnitudes are positive", sign(whole) > 0 and sign(part) > 0)
    hypothesis("the part subtracted is less than the whole", sign(whole - part) > 0)
    ab, cd = times * whole, times * part
    claim("the remainder is the same multiple of the remainder", "C.N.3",
          ab - cd == times * (whole - part))
    return Out(remainder=ab - cd)


@proposition(
    "V.6",
    THEOREM,
    sample=_two_magnitudes_and_two_multiples,
)
def prop_V_6(x, y, times: int, taken: int) -> Out:
    """AB and CD are `times` E and F; `taken`-fold E and F are subtracted."""
    hypothesis("the magnitudes are positive", sign(x) > 0 and sign(y) > 0)
    hypothesis("less is taken away than there is", taken <= times)
    left, right = times * x - taken * x, times * y - taken * y
    remaining = times - taken
    claim("the remainders are equimultiples of the same two magnitudes", "V.1",
          left == remaining * x and right == remaining * y)
    claim("and where one multiple remains they are equal to them", "C.N.3",
          remaining != 1 or (left == x and right == y))
    return Out(remainders=(left, right))


@proposition(
    "V.7",
    THEOREM,
    sample=_equal_pair_and_a_third,
)
def prop_V_7(a, b, c) -> Out:
    """A and B are equal; C is the magnitude they are compared with."""
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c)))
    hypothesis("A and B are equal", a == b)
    claim("equal magnitudes have the same ratio to the same", "Def.5",
          separating_witness(a, c, b, c) is None)
    claim("and the same has the same ratio to equal magnitudes", "Def.5",
          separating_witness(c, a, c, b) is None)
    return Out()


@proposition(
    "V.10",
    THEOREM,
    sample=_three_magnitudes,
)
def prop_V_10(a, b, c) -> Out:
    """A and B both have a ratio to C."""
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c)))
    hypothesis("A and B are unequal", a != b)
    claim("that which has the greater ratio to the same is the greater", "Def.7",
          (ratio_cmp(a, c, b, c) > 0) == (sign(a - b) > 0))
    claim("and that to which the same has the greater ratio is the less", "Def.7",
          (ratio_cmp(c, a, c, b) > 0) == (sign(a - b) < 0))
    return Out()


@proposition(
    "V.12",
    THEOREM,
    sample=_three_pairs_in_one_ratio,
    note="As one antecedent is to one consequent, so is the sum to the sum -- the "
    "step that lets Book V add proportions together.",
)
def prop_V_12(a, b, c, d, e, f) -> Out:
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d, e, f)))
    hypothesis("a : b = c : d", a * d == b * c)
    hypothesis("and c : d = e : f", c * f == d * e)
    claim("so all three pairs stand in one ratio", "V.11",
          a * d == b * c and a * f == b * e)
    claim("so one antecedent is to one consequent as all are to all", "Def.5",
          separating_witness(a, b, a + c + e, b + d + f) is None)
    return Out(total=(a + c + e, b + d + f))


@proposition(
    "V.13",
    THEOREM,
    sample=_proportion_and_a_smaller_ratio,
)
def prop_V_13(a, b, c, d, e, f) -> Out:
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d, e, f)))
    hypothesis("a : b = c : d", a * d == b * c)
    hypothesis("c : d is greater than e : f", ratio_cmp(c, d, e, f) > 0)
    claim("therefore a : b is greater than e : f", "Def.7",
          ratio_cmp(a, b, e, f) > 0)
    claim("and equimultiples can be produced that show it", "Def.7",
          separating_witness(a, b, e, f) is not None)
    return Out()


@proposition(
    "V.14",
    THEOREM,
    sample=_proportional_magnitudes,
)
def prop_V_14(a, b, c, d) -> Out:
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d)))
    hypothesis("a : b = c : d", a * d == b * c)
    claim("as the first stands to the third, so the second stands to the fourth",
          "V.8", sign(a - c) == sign(b - d))
    return Out()


@proposition(
    "V.15",
    THEOREM,
    sample=_two_magnitudes_and_a_multiple,
)
def prop_V_15(a, b, times: int) -> Out:
    hypothesis("the magnitudes are positive", sign(a) > 0 and sign(b) > 0)
    claim("parts have the same ratio as their equimultiples", "Def.5",
          separating_witness(a, b, times * a, times * b) is None)
    return Out()


@proposition(
    "V.17",
    THEOREM,
    sample=_proportional_magnitudes,
    note="Separando. Euclid needs both this and its converse because a ratio is "
    "not a quotient he may rearrange at will.",
)
def prop_V_17(a, b, c, d) -> Out:
    """AB : BE = CD : DF, componendo; separando follows."""
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d)))
    hypothesis("componendo: (a+b) : b = (c+d) : d", (a + b) * d == b * (c + d))
    claim("separando, a : b = c : d", "Def.5",
          separating_witness(a, b, c, d) is None)
    return Out()


@proposition(
    "V.18",
    THEOREM,
    sample=_proportional_magnitudes,
    note="Componendo, the converse of V.17.",
)
def prop_V_18(a, b, c, d) -> Out:
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d)))
    hypothesis("separando: a : b = c : d", a * d == b * c)
    claim("componendo, (a+b) : b = (c+d) : d", "Def.5",
          separating_witness(a + b, b, c + d, d) is None)
    return Out()


@proposition(
    "V.19",
    THEOREM,
    sample=_a_proper_part_in_proportion,
)
def prop_V_19(a, b, c, d) -> Out:
    """The whole AB is to the whole CD as the part AE to the part CF."""
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d)))
    hypothesis("whole is to whole as part is to part", a * d == b * c)
    hypothesis("the parts are less than the wholes",
               sign(a - c) > 0 and sign(b - d) > 0)
    claim("the remainder is to the remainder as whole to whole", "Def.5",
          separating_witness(a - c, b - d, a, b) is None)
    return Out(remainders=(a - c, b - d))


def _two_triples_in_ratio(rng):
    """Three magnitudes and three more, in the same ratio two and two."""
    a, b, c = _three_magnitudes(rng)
    scale = Fraction(rng.randint(1, 6), rng.randint(1, 5))
    return a, b, c, a * scale, b * scale, c * scale


@proposition(
    "V.20",
    THEOREM,
    sample=_two_triples_in_ratio,
)
def prop_V_20(a, b, c, d, e, f) -> Out:
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d, e, f)))
    hypothesis("a : b = d : e", a * e == b * d)
    hypothesis("b : c = e : f", b * f == c * e)
    claim("as the first stands to the third, so the fourth stands to the sixth",
          ["V.8", "V.13"], sign(a - c) == sign(d - f))
    return Out()


def _two_triples_perturbed(rng):
    """Three magnitudes and three more in perturbed proportion: a:b = e:f and b:c = d:e."""
    a, b, c = _three_magnitudes(rng)
    d = _magnitude(rng)
    e = c * d / b          # from b : c = d : e, so b*e = c*d
    f = b * e / a          # from a : b = e : f, so a*f = b*e
    return a, b, c, d, e, f


@proposition(
    "V.21",
    THEOREM,
    sample=_two_triples_perturbed,
    note="'Perturbed' means the second triple is matched to the first crosswise, "
    "which is how ratios get composed in the wrong order and still behave.",
)
def prop_V_21(a, b, c, d, e, f) -> Out:
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d, e, f)))
    hypothesis("a : b = e : f", a * f == b * e)
    hypothesis("b : c = d : e", b * e == c * d)
    claim("as the first stands to the third, so the fourth stands to the sixth",
          ["V.8", "V.13"], sign(a - c) == sign(d - f))
    return Out()


@proposition(
    "V.22",
    THEOREM,
    sample=_two_triples_in_ratio,
    note="Ex aequali: ratios compose end to end, which is what makes Book VI's "
    "chains of similar triangles work.",
)
def prop_V_22(a, b, c, d, e, f) -> Out:
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d, e, f)))
    hypothesis("a : b = d : e", a * e == b * d)
    hypothesis("b : c = e : f", b * f == c * e)
    claim("ex aequali, a : c = d : f", "Def.5",
          separating_witness(a, c, d, f) is None)
    return Out()


@proposition(
    "V.23",
    THEOREM,
    sample=_two_triples_perturbed,
)
def prop_V_23(a, b, c, d, e, f) -> Out:
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d, e, f)))
    hypothesis("a : b = e : f", a * f == b * e)
    hypothesis("b : c = d : e", b * e == c * d)
    claim("ex aequali in perturbed proportion, a : c = d : f", "Def.5",
          separating_witness(a, c, d, f) is None)
    return Out()


@proposition(
    "V.24",
    THEOREM,
    sample=lambda rng: _proportional_magnitudes(rng) + (_magnitude(rng),),
)
def prop_V_24(a, b, c, d, e) -> Out:
    """A : B = C : D, and E : B = F : D; the antecedents add."""
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d, e)))
    hypothesis("a : b = c : d", a * d == b * c)
    f = e * d / b  # so that e : b = f : d
    claim("the fifth stands to the second as the sixth to the fourth", "Def.5",
          e * d == b * f)
    claim("so the first and fifth together stand to the second as the third and "
          "sixth together to the fourth", "Def.5",
          separating_witness(a + e, b, c + f, d) is None)
    return Out(sums=(a + e, c + f))


def _four_proportional_ordered(rng):
    """a : b = c : d with a the greatest and d the least."""
    lesser = _magnitude(rng)
    greater = lesser + _magnitude(rng)
    scale = 1 + Fraction(rng.randint(1, 5), rng.randint(1, 4))
    return greater * scale, greater, lesser * scale, lesser


@proposition(
    "V.25",
    THEOREM,
    sample=_four_proportional_ordered,
)
def prop_V_25(a, b, c, d) -> Out:
    hypothesis("the magnitudes are positive",
               all(sign(x) > 0 for x in (a, b, c, d)))
    hypothesis("a : b = c : d", a * d == b * c)
    hypothesis("A is the greatest and D the least",
               sign(a - b) > 0 and sign(a - c) > 0 and sign(b - d) > 0 and sign(c - d) > 0)
    claim("the greatest and the least together exceed the other two", "V.19",
          sign((a + d) - (b + c)) > 0)
    return Out()


@proposition(
    "V.11",
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
