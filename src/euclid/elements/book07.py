"""Book VII: the Euclidean algorithm, and the theory of numbers built on it.

Nothing is drawn, as Euclid draws nothing here. VII.1-2 is the algorithm itself,
stated as repeated subtraction, and it runs.
"""

from __future__ import annotations

from .arithmetic import (
    coprime,
    coprime_pair,
    gcd,
    is_prime,
    lcm,
    least_terms,
    measures,
    prime_factors,
    three_numbers,
)
from .registry import CONSTRUCTION, THEOREM, Out, claim, hypothesis, proposition


__all__ = [
    "anthyphairesis_integers",
    "gcd",
    "is_perfect",
    "is_prime",
    "prime_factors",
]


def anthyphairesis_integers(greater: int, lesser: int) -> list[int]:
    """Euclid's alternating subtraction, VII.1-2, keeping the remainders."""
    trail = []
    while lesser:
        trail.append(greater % lesser if greater % lesser else 0)
        greater, lesser = lesser, greater % lesser
    return trail


def _two_numbers(rng):
    return rng.randint(2, 400), rng.randint(2, 400)


def _two_unequal(rng):
    a = rng.randint(2, 400)
    b = rng.randint(2, 400)
    while a == b:
        b = rng.randint(2, 400)
    return max(a, b), min(a, b)


def _same_parts_of_two(rng):
    """A fraction, and two numbers it divides exactly (VII.6, VII.10)."""
    denominator = rng.randint(2, 9)
    numerator = rng.randint(1, denominator - 1)
    return (numerator, denominator,
            denominator * rng.randint(2, 12), denominator * rng.randint(2, 12))


def _proportional_with_smaller_parts(rng):
    """a : b = c : d with c and d strictly less than a and b (VII.11)."""
    base_a, base_b = rng.randint(2, 20), rng.randint(2, 20)
    whole = rng.randint(3, 8)
    part = rng.randint(1, whole - 1)
    return base_a * whole, base_b * whole, base_a * part, base_b * part


def _a_part_of(rng):
    """A number, and a multiple of it: `part` is a part of `whole`."""
    part = rng.randint(2, 40)
    return part, part * rng.randint(2, 12)


@proposition(
    "VII.1",
    THEOREM,
    sample=_two_unequal,
    note="The termination test of the Euclidean algorithm, read as a criterion: "
    "the subtraction runs down to a unit exactly when the numbers are coprime.",
)
def prop_VII_1(a: int, b: int) -> Out:
    hypothesis("the numbers are unequal and greater than a unit", a > b > 1, guard=True)
    trail = anthyphairesis_integers(a, b)
    reached_a_unit = gcd(a, b) == 1

    claim("the subtraction terminates", "VII.1", trail and trail[-1] == 0)
    claim("what is left when it does is the only common measure the two admit",
          "Def.VII.12",
          not any(measures(d, a) and measures(d, b) for d in range(2, b + 1))
          == reached_a_unit)
    claim("so if a unit is left, the numbers are prime to one another",
          "Def.VII.12", reached_a_unit == coprime(a, b))
    return Out(remainders=trail, coprime=reached_a_unit)


@proposition(
    "VII.3",
    CONSTRUCTION,
    sample=three_numbers,
)
def prop_VII_3(a: int, b: int, c: int) -> Out:
    hypothesis("all three are greater than a unit", a > 1 and b > 1 and c > 1, guard=True)
    measure = gcd(gcd(a, b), c)
    claim("the measure found measures all three", "VII.2",
          all(measures(measure, n) for n in (a, b, c)))
    claim("and every common measure of the three measures it", "VII.2",
          all(measures(d, measure) for d in range(1, min(a, b, c) + 1)
              if all(measures(d, n) for n in (a, b, c))))
    return Out(measure=measure)


@proposition(
    "VII.4",
    THEOREM,
    sample=_two_unequal,
    note="Every ratio of numbers is a fraction -- Euclid's 'part' when the "
    "numerator is a unit, 'parts' when it is not.",
)
def prop_VII_4(a: int, b: int) -> Out:
    hypothesis("the numbers are unequal and greater than a unit", a > b > 1, guard=True)
    numerator, denominator = least_terms(b, a)
    claim("the less is a part of the greater when it measures it", "Def.VII.3",
          (numerator == 1) == measures(b, a))
    claim("and parts of it otherwise, so many of the greater's parts as the "
          "numerator counts", "Def.VII.4",
          b * denominator == a * numerator)
    claim("the two counts have no common measure but a unit, so the description "
          "is the plainest there is", "Def.VII.12", coprime(numerator, denominator))
    return Out(terms=(numerator, denominator))


@proposition(
    "VII.5",
    THEOREM,
    sample=lambda rng: _a_part_of(rng) + (rng.randint(2, 40),),
)
def prop_VII_5(part: int, whole: int, other: int) -> Out:
    """`part` is a part of `whole`; `other` is the same part of its own whole."""
    hypothesis("the first is a part of the second", measures(part, whole) and part > 0)
    times = whole // part
    other_whole = other * times
    claim("the two stand in the same part", "Def.VII.3",
          whole == part * times and other_whole == other * times)
    claim("so the sum is the same part of the sum", "VII.5",
          whole + other_whole == (part + other) * times)
    return Out(sum=part + other)


@proposition(
    "VII.6",
    THEOREM,
    sample=_same_parts_of_two,
)
def prop_VII_6(numerator: int, denominator: int, first: int, second: int) -> Out:
    """The 'parts' version of VII.5: a fraction, not just a unit fraction."""
    hypothesis("the fraction is a genuine one",
               denominator > numerator > 0, guard=True)
    hypothesis("it applies to both numbers exactly",
               measures(denominator, first) and measures(denominator, second))
    a = first * numerator // denominator
    b = second * numerator // denominator
    claim("each is the same parts of its own", "Def.VII.4",
          a * denominator == first * numerator and b * denominator == second * numerator)
    claim("so the sum is the same parts of the sum", "VII.6",
          (a + b) * denominator == (first + second) * numerator)
    return Out(sum=a + b)


@proposition(
    "VII.7",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 12), rng.randint(4, 30), rng.randint(1, 3)),
)
def prop_VII_7(times: int, whole: int, taken: int) -> Out:
    """A part subtracted from a part leaves the same part of the remainder."""
    hypothesis("the subtraction is a proper one", whole > taken > 0 and times > 1, guard=True)
    big, small = whole * times, taken * times
    claim("each is the same part of its own", "Def.VII.3",
          big == whole * times and small == taken * times)
    claim("so the remainder is the same part of the remainder", "VII.7",
          big - small == (whole - taken) * times)
    return Out(remainder=whole - taken)


@proposition(
    "VII.8",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 9), rng.randint(2, 9), rng.randint(4, 30),
                        rng.randint(1, 3)),
)
def prop_VII_8(numerator: int, denominator: int, whole: int, taken: int) -> Out:
    """The 'parts' version of VII.7."""
    hypothesis("the fraction is a genuine one", denominator > numerator > 0, guard=True)
    hypothesis("the subtraction is a proper one", whole > taken > 0, guard=True)
    big, small = whole * denominator, taken * denominator
    claim("the remainder is the same parts of the remainder", "VII.8",
          (big - small) * numerator == (whole - taken) * denominator * numerator)
    return Out(remainder=big - small)


@proposition(
    "VII.9",
    THEOREM,
    sample=lambda rng: _a_part_of(rng) + (rng.randint(2, 40),),
)
def prop_VII_9(part: int, whole: int, other: int) -> Out:
    """Alternation for parts: if A is a part of B as C is of D, then A:C = B:D."""
    hypothesis("the first is a part of the second", measures(part, whole) and part > 0)
    times = whole // part
    other_whole = other * times
    claim("alternately, the first is to the third as the second to the fourth",
          "VII.9", part * other_whole == whole * other)
    return Out()


@proposition(
    "VII.10",
    THEOREM,
    sample=_same_parts_of_two,
)
def prop_VII_10(numerator: int, denominator: int, first: int, second: int) -> Out:
    """The 'parts' version of VII.9."""
    hypothesis("the fraction is a genuine one", denominator > numerator > 0, guard=True)
    hypothesis("it applies to both numbers exactly",
               measures(denominator, first) and measures(denominator, second))
    a = first * numerator // denominator
    b = second * numerator // denominator
    claim("alternately, the first is to the third as the second to the fourth",
          "VII.10", a * second == first * b)
    return Out()


def _proportional_numbers(rng):
    """Four numbers in proportion, a : b = c : d."""
    a, b = rng.randint(2, 30), rng.randint(2, 30)
    scale = rng.randint(2, 8)
    return a, b, a * scale, b * scale


@proposition(
    "VII.11",
    THEOREM,
    sample=_proportional_with_smaller_parts,
)
def prop_VII_11(a: int, b: int, c: int, d: int) -> Out:
    hypothesis("the four are proportional", a * d == b * c)
    hypothesis("the parts are less than the wholes", c < a and d < b)
    claim("the remainder is to the remainder as whole to whole", "VII.11",
          (a - c) * b == (b - d) * a)
    return Out(remainders=(a - c, b - d))


@proposition(
    "VII.12",
    THEOREM,
    sample=_proportional_numbers,
)
def prop_VII_12(a: int, b: int, c: int, d: int) -> Out:
    hypothesis("the four are proportional", a * d == b * c)
    claim("as one antecedent is to one consequent, so are all to all", "VII.12",
          a * (b + d) == b * (a + c))
    return Out(total=(a + c, b + d))


@proposition(
    "VII.13",
    THEOREM,
    sample=_proportional_numbers,
)
def prop_VII_13(a: int, b: int, c: int, d: int) -> Out:
    hypothesis("the four are proportional", a * d == b * c)
    claim("they are proportional alternately as well", "VII.13", a * d == c * b)
    return Out()


@proposition(
    "VII.14",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 20), rng.randint(2, 20), rng.randint(2, 20),
                        rng.randint(2, 8)),
)
def prop_VII_14(a: int, b: int, c: int, scale: int) -> Out:
    """Three numbers and three more, in the same ratio two and two."""
    hypothesis("the numbers are genuine", a > 1 and b > 1 and c > 1 and scale > 1, guard=True)
    d, e, f = a * scale, b * scale, c * scale
    claim("the pairs are in the same ratio", "VII.13", a * e == b * d and b * f == c * e)
    claim("so ex aequali the first is to the third as the fourth to the sixth",
          "VII.14", a * f == c * d)
    return Out()


@proposition(
    "VII.15",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 30), rng.randint(2, 20)),
)
def prop_VII_15(number: int, times: int) -> Out:
    """A unit measures a number as that number measures its multiple."""
    hypothesis("the numbers are genuine", number > 1 and times > 1, guard=True)
    product = number * times
    claim("the unit measures the number as many times as the number itself",
          "Def.VII.2", 1 * number == number)
    claim("and alternately, the unit is to the multiplier as the number is to the "
          "product", "VII.15", 1 * product == times * number)
    return Out(product=product)


@proposition(
    "VII.16",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 60), rng.randint(2, 60)),
    note="Multiplication commutes. Euclid has to prove it, because his product "
    "is 'a taken b times' and that is not obviously the same as b taken a times.",
)
def prop_VII_16(a: int, b: int) -> Out:
    hypothesis("both are numbers", a > 1 and b > 1, guard=True)
    claim("a taken b times equals b taken a times", "VII.16",
          sum(a for _ in range(b)) == sum(b for _ in range(a)))
    claim("so the two products are equal", "VII.16", a * b == b * a)
    return Out(product=a * b)


@proposition(
    "VII.17",
    THEOREM,
    sample=three_numbers,
)
def prop_VII_17(a: int, b: int, c: int) -> Out:
    hypothesis("all three are numbers", a > 1 and b > 1 and c > 1, guard=True)
    claim("the products have the same ratio as the numbers multiplied", "VII.17",
          (a * b) * c == (a * c) * b)
    return Out()


@proposition(
    "VII.18",
    THEOREM,
    sample=three_numbers,
)
def prop_VII_18(a: int, b: int, c: int) -> Out:
    hypothesis("all three are numbers", a > 1 and b > 1 and c > 1, guard=True)
    claim("the products have the same ratio as the multipliers", "VII.18",
          (a * c) * b == (b * c) * a)
    return Out()


@proposition(
    "VII.19",
    THEOREM,
    sample=_proportional_numbers,
    note="The rule of three for numbers, and its converse: proportion and equal "
    "products say the same thing.",
)
def prop_VII_19(a: int, b: int, c: int, d: int) -> Out:
    hypothesis("all four are numbers", all(n > 1 for n in (a, b, c, d)), guard=True)
    # Def.VII.20: numbers are proportional when the first is the same multiple,
    # part or parts of the second that the third is of the fourth -- which is to
    # say the two pairs agree once reduced to least terms.
    hypothesis("the four are proportional in Euclid's sense",
               least_terms(a, b) == least_terms(c, d))
    claim("the product of the extremes equals the product of the means", "VII.19",
          a * d == b * c)
    claim("and conversely, equal products bring the pairs to the same least terms",
          "VII.19",
          all(least_terms(x, y) == least_terms(z, w)
              for x, y, z, w in ((a, b, c, d), (c, d, a, b))
              if x * w == y * z))
    return Out()


@proposition(
    "VII.20",
    THEOREM,
    sample=_proportional_numbers,
    note="The least pair of a ratio divides every other pair of it -- which is "
    "why 'lowest terms' is well defined.",
)
def prop_VII_20(a: int, b: int, c: int, d: int) -> Out:
    hypothesis("the four are proportional", a * d == b * c)
    hypothesis("all four are numbers", all(n > 1 for n in (a, b, c, d)), guard=True)
    least = least_terms(a, b)
    claim("the least terms measure the greater the same number of times as the "
          "less", "VII.20",
          measures(least[0], a) and measures(least[1], b)
          and a // least[0] == b // least[1])
    claim("and they measure the second pair the same way", "VII.20",
          measures(least[0], c) and measures(least[1], d)
          and c // least[0] == d // least[1])
    return Out(least=least)


@proposition(
    "VII.21",
    THEOREM,
    sample=coprime_pair,
)
def prop_VII_21(a: int, b: int) -> Out:
    hypothesis("the numbers are prime to one another", coprime(a, b))
    claim("they are already in least terms", "VII.21", least_terms(a, b) == (a, b))
    claim("so no smaller pair has the same ratio", "VII.20",
          not any(x * b == y * a for x in range(1, a) for y in range(1, b)))
    return Out()


@proposition(
    "VII.22",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 200), rng.randint(2, 200)),
)
def prop_VII_22(a: int, b: int) -> Out:
    hypothesis("both are numbers", a > 1 and b > 1, guard=True)
    least = least_terms(a, b)
    claim("the least of the ratio are prime to one another", "VII.22",
          coprime(*least))
    return Out(least=least)


@proposition(
    "VII.23",
    THEOREM,
    sample=lambda rng: coprime_pair(rng),
)
def prop_VII_23(a: int, b: int) -> Out:
    hypothesis("the numbers are prime to one another", coprime(a, b))
    divisors = [d for d in range(2, a + 1) if measures(d, a)]
    claim("every measure of the one is prime to the other", "VII.23",
          all(coprime(d, b) for d in divisors))
    return Out(divisors=divisors)


@proposition(
    "VII.24",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 60), rng.randint(2, 60), rng.randint(2, 60)),
)
def prop_VII_24(a: int, b: int, c: int) -> Out:
    hypothesis("both are prime to the third", coprime(a, c) and coprime(b, c))
    claim("their product is prime to it as well", "VII.24", coprime(a * b, c))
    return Out(product=a * b)


@proposition(
    "VII.25",
    THEOREM,
    sample=coprime_pair,
)
def prop_VII_25(a: int, b: int) -> Out:
    hypothesis("the numbers are prime to one another", coprime(a, b))
    claim("the square of the one is prime to the other", "VII.24", coprime(a * a, b))
    return Out(square=a * a)


@proposition(
    "VII.26",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 40), rng.randint(2, 40), rng.randint(2, 40),
                        rng.randint(2, 40)),
)
def prop_VII_26(a: int, b: int, c: int, d: int) -> Out:
    hypothesis("each of the first two is prime to each of the last two",
               coprime(a, c) and coprime(a, d) and coprime(b, c) and coprime(b, d))
    claim("the two products are prime to one another", "VII.24",
          coprime(a * b, c * d))
    return Out(products=(a * b, c * d))


@proposition(
    "VII.27",
    THEOREM,
    sample=coprime_pair,
)
def prop_VII_27(a: int, b: int) -> Out:
    hypothesis("the numbers are prime to one another", coprime(a, b))
    claim("their squares are prime to one another", "VII.25", coprime(a * a, b * b))
    claim("and so are their cubes, and this is always the case with the extremes",
          "VII.26", coprime(a * a * a, b * b * b))
    return Out(squares=(a * a, b * b))


@proposition(
    "VII.28",
    THEOREM,
    sample=coprime_pair,
)
def prop_VII_28(a: int, b: int) -> Out:
    hypothesis("the numbers are prime to one another", coprime(a, b))
    claim("the sum is prime to each of them", "VII.28",
          coprime(a + b, a) and coprime(a + b, b))
    claim("and conversely, a sum prime to one makes the two prime to one another",
          "VII.28", coprime(a + b, a) == coprime(a, b))
    return Out(total=a + b)


@proposition(
    "VII.29",
    THEOREM,
    sample=lambda rng: (rng.choice([p for p in range(2, 60) if is_prime(p)]),
                        rng.randint(2, 200)),
)
def prop_VII_29(p: int, n: int) -> Out:
    hypothesis("the first is prime", is_prime(p))
    hypothesis("it does not measure the second", not measures(p, n))
    claim("a prime is prime to any number it does not measure", "VII.29",
          coprime(p, n))
    return Out()


@proposition(
    "VII.30",
    THEOREM,
    sample=lambda rng: (rng.choice([p for p in range(2, 40) if is_prime(p)]),
                        rng.randint(2, 60), rng.randint(2, 60)),
    note="Euclid's lemma, and the reason factorisation into primes is unique. "
    "It is the deepest thing in Book VII.",
)
def prop_VII_30(p: int, a: int, b: int) -> Out:
    hypothesis("the first is prime", is_prime(p))
    hypothesis("it measures the product", measures(p, a * b))
    claim("then it measures one of the two", "VII.30",
          measures(p, a) or measures(p, b))
    return Out()


@proposition(
    "VII.32",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 500),),
)
def prop_VII_32(n: int) -> Out:
    hypothesis("the number is greater than a unit", n > 1, guard=True)
    factors = prime_factors(n)
    claim("the number is prime, or some prime measures it", "VII.31",
          is_prime(n) or (bool(factors) and is_prime(factors[0])
                          and measures(factors[0], n)))
    return Out(prime=factors[0])


@proposition(
    "VII.33",
    CONSTRUCTION,
    sample=lambda rng: (rng.randint(2, 200), rng.randint(2, 200)),
)
def prop_VII_33(a: int, b: int) -> Out:
    hypothesis("both are numbers", a > 1 and b > 1, guard=True)
    least = least_terms(a, b)
    claim("the pair found has the same ratio", "VII.33", least[0] * b == least[1] * a)
    claim("it is in least terms, being prime to one another", "VII.22",
          coprime(*least))
    claim("and no smaller pair has that ratio", "VII.21",
          not any(x * b == y * a
                  for x in range(1, least[0]) for y in range(1, least[1])))
    return Out(least=least)


@proposition(
    "VII.34",
    CONSTRUCTION,
    sample=lambda rng: (rng.randint(2, 60), rng.randint(2, 60)),
)
def prop_VII_34(a: int, b: int) -> Out:
    hypothesis("both are numbers", a > 1 and b > 1, guard=True)
    least = lcm(a, b)
    claim("the number found is measured by both", "VII.34",
          measures(a, least) and measures(b, least))
    claim("and nothing less is", "VII.34",
          not any(measures(a, n) and measures(b, n) for n in range(1, least)))
    return Out(least=least)


@proposition(
    "VII.35",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 30), rng.randint(2, 30), rng.randint(2, 10)),
)
def prop_VII_35(a: int, b: int, times: int) -> Out:
    hypothesis("both are numbers", a > 1 and b > 1 and times > 0, guard=True)
    common = lcm(a, b) * times
    claim("both measure the common multiple", "Def.VII.3",
          measures(a, common) and measures(b, common))
    claim("so the least they measure also measures it", "VII.35",
          measures(lcm(a, b), common))
    return Out(least=lcm(a, b))


@proposition(
    "VII.36",
    CONSTRUCTION,
    sample=lambda rng: (rng.randint(2, 20), rng.randint(2, 20), rng.randint(2, 20)),
)
def prop_VII_36(a: int, b: int, c: int) -> Out:
    hypothesis("all three are numbers", a > 1 and b > 1 and c > 1, guard=True)
    least = lcm(lcm(a, b), c)
    claim("the number found is measured by all three", "VII.34",
          all(measures(n, least) for n in (a, b, c)))
    claim("and nothing less is", "VII.35",
          not any(all(measures(n, m) for n in (a, b, c)) for m in range(1, least)))
    return Out(least=least)


@proposition(
    "VII.37",
    THEOREM,
    sample=_a_part_of,
)
def prop_VII_37(part: int, whole: int) -> Out:
    hypothesis("the first measures the second", measures(part, whole) and part > 1)
    named = whole // part
    claim("the measured number has a part named after the measure", "Def.VII.3",
          measures(named, whole) and whole // named == part)
    return Out(part=named)


@proposition(
    "VII.38",
    THEOREM,
    sample=_a_part_of,
)
def prop_VII_38(part: int, whole: int) -> Out:
    """The converse of VII.37."""
    hypothesis("the second has a part named after the first",
               measures(part, whole) and part > 1)
    claim("then it is measured by the number of that name", "Def.VII.3",
          measures(part, whole))
    claim("and the quotient is the part itself", "VII.37",
          whole // (whole // part) == part)
    return Out()


@proposition(
    "VII.39",
    CONSTRUCTION,
    sample=lambda rng: (rng.randint(2, 12), rng.randint(2, 12), rng.randint(2, 12)),
    note="The least number having given parts is the least common multiple of "
    "their names -- the last proposition of Book VII, and the one Book IX uses.",
)
def prop_VII_39(a: int, b: int, c: int) -> Out:
    hypothesis("the parts are genuine", a > 1 and b > 1 and c > 1, guard=True)
    least = lcm(lcm(a, b), c)
    claim("the number found has all three parts", "VII.38",
          all(measures(n, least) for n in (a, b, c)))
    claim("and no smaller number has them all", "VII.36",
          not any(all(measures(n, m) for n in (a, b, c)) for m in range(1, least)))
    return Out(least=least)


@proposition(
    "VII.2",
    CONSTRUCTION,
    sample=_two_numbers,
    note="The Euclidean algorithm. Euclid states it as continual subtraction of the "
    "less from the greater -- the same procedure that, applied to magnitudes rather "
    "than numbers, becomes the anthyphairesis of Book X.",
)
def prop_VII_2(a: int, b: int) -> Out:
    hypothesis("both numbers are greater than a unit", a > 1 and b > 1, guard=True)
    measure = gcd(a, b)
    claim("the result measures both numbers", "VII.1", a % measure == 0 and b % measure == 0)
    claim("and every common measure measures it", "VII.2",
          all(measure % d == 0 for d in range(1, min(a, b) + 1) if a % d == 0 and b % d == 0))
    return Out(measure=measure, remainders=anthyphairesis_integers(max(a, b), min(a, b)))


@proposition(
    "VII.31",
    THEOREM,
    sample=lambda rng: (rng.randint(4, 500) | 1 if rng.random() < 0.3 else 2 * rng.randint(2, 250),),
)
def prop_VII_31(n: int) -> Out:
    hypothesis("the number is composite", n > 3 and not is_prime(n))
    factors = prime_factors(n)
    claim("a prime factor was found", "VII.31", bool(factors) and is_prime(factors[0]))
    claim("and it measures the number", "Def.VII.3", n % factors[0] == 0)
    return Out(prime=factors[0])
