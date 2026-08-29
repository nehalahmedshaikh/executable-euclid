"""Books VII-IX, complete: the arithmetical books, as the algorithms they were.

These books have no diagrams worth drawing, and none is drawn: they argue about
numbers, not figures, so the figure machinery sits them out. What is checked is
exact all the same. They do have running code in them.  VII.1-2 is the Euclidean algorithm, stated as repeated subtraction.
IX.20 is a *construction*, not a counting argument: given any list of primes it
builds a new one.  IX.36 is the theorem that pairs perfect numbers with Mersenne
primes, and it still holds the record for the oldest open question in
mathematics -- nobody knows whether an odd perfect number exists.
"""

from __future__ import annotations

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


def gcd(a: int, b: int) -> int:
    """The greatest common measure, by the algorithm of VII.2."""
    while b:
        a, b = b, a % b
    return abs(a)


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def prime_factors(n: int) -> list[int]:
    found = []
    remaining, divisor = n, 2
    while divisor * divisor <= remaining:
        while remaining % divisor == 0:
            found.append(divisor)
            remaining //= divisor
        divisor += 1
    if remaining > 1:
        found.append(remaining)
    return found


def lcm(a: int, b: int) -> int:
    """The least number the two measure, by VII.34."""
    return abs(a * b) // gcd(a, b)


def least_terms(a: int, b: int) -> tuple[int, int]:
    """The least pair having the same ratio, by VII.33."""
    measure = gcd(a, b)
    return a // measure, b // measure


def coprime(a: int, b: int) -> bool:
    """Euclid's 'prime to one another': no common measure but a unit."""
    return gcd(a, b) == 1


def measures(a: int, b: int) -> bool:
    """``a`` measures ``b``: it goes into it a whole number of times."""
    return a != 0 and b % a == 0


def proper_divisors(n: int) -> list[int]:
    return [d for d in range(1, n) if n % d == 0]


def is_perfect(n: int) -> bool:
    """Euclid's definition VII.22: a number equal to the sum of its own parts."""
    return n > 1 and sum(proper_divisors(n)) == n


# ---------------------------------------------------------------------------
# propositions
# ---------------------------------------------------------------------------


def _two_numbers(rng):
    return rng.randint(2, 400), rng.randint(2, 400)


def _two_unequal(rng):
    a = rng.randint(2, 400)
    b = rng.randint(2, 400)
    while a == b:
        b = rng.randint(2, 400)
    return max(a, b), min(a, b)


def _coprime_pair(rng):
    while True:
        a, b = rng.randint(2, 200), rng.randint(2, 200)
        if coprime(a, b) and a != b:
            return a, b


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
    hypothesis("the numbers are unequal and greater than a unit", a > b > 1)
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


def _three_numbers(rng):
    return rng.randint(2, 200), rng.randint(2, 200), rng.randint(2, 200)


@proposition(
    "VII.3",
    CONSTRUCTION,
    sample=_three_numbers,
)
def prop_VII_3(a: int, b: int, c: int) -> Out:
    hypothesis("all three are greater than a unit", a > 1 and b > 1 and c > 1)
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
    hypothesis("the numbers are unequal and greater than a unit", a > b > 1)
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
               denominator > numerator > 0)
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
    hypothesis("the subtraction is a proper one", whole > taken > 0 and times > 1)
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
    hypothesis("the fraction is a genuine one", denominator > numerator > 0)
    hypothesis("the subtraction is a proper one", whole > taken > 0)
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
    hypothesis("the fraction is a genuine one", denominator > numerator > 0)
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
    hypothesis("the numbers are genuine", a > 1 and b > 1 and c > 1 and scale > 1)
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
    hypothesis("the numbers are genuine", number > 1 and times > 1)
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
    hypothesis("both are numbers", a > 1 and b > 1)
    claim("a taken b times equals b taken a times", "VII.16",
          sum(a for _ in range(b)) == sum(b for _ in range(a)))
    claim("so the two products are equal", "VII.16", a * b == b * a)
    return Out(product=a * b)


@proposition(
    "VII.17",
    THEOREM,
    sample=_three_numbers,
)
def prop_VII_17(a: int, b: int, c: int) -> Out:
    hypothesis("all three are numbers", a > 1 and b > 1 and c > 1)
    claim("the products have the same ratio as the numbers multiplied", "VII.17",
          (a * b) * c == (a * c) * b)
    return Out()


@proposition(
    "VII.18",
    THEOREM,
    sample=_three_numbers,
)
def prop_VII_18(a: int, b: int, c: int) -> Out:
    hypothesis("all three are numbers", a > 1 and b > 1 and c > 1)
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
    hypothesis("all four are numbers", all(n > 1 for n in (a, b, c, d)))
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
    hypothesis("all four are numbers", all(n > 1 for n in (a, b, c, d)))
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
    sample=_coprime_pair,
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
    hypothesis("both are numbers", a > 1 and b > 1)
    least = least_terms(a, b)
    claim("the least of the ratio are prime to one another", "VII.22",
          coprime(*least))
    return Out(least=least)


@proposition(
    "VII.23",
    THEOREM,
    sample=lambda rng: _coprime_pair(rng),
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
    sample=_coprime_pair,
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
    sample=_coprime_pair,
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
    sample=_coprime_pair,
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
    hypothesis("the number is greater than a unit", n > 1)
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
    hypothesis("both are numbers", a > 1 and b > 1)
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
    hypothesis("both are numbers", a > 1 and b > 1)
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
    hypothesis("both are numbers", a > 1 and b > 1 and times > 0)
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
    hypothesis("all three are numbers", a > 1 and b > 1 and c > 1)
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
    hypothesis("the parts are genuine", a > 1 and b > 1 and c > 1)
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
    hypothesis("both numbers are greater than a unit", a > 1 and b > 1)
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


# ---------------------------------------------------------------------------
# Book VIII -- continued proportions
# ---------------------------------------------------------------------------
#
# A "continued proportion" is a geometric progression: each term stands to the
# next as the next to the one after. Euclid has no exponents, so a progression
# of ratio p:q is carried as p^k q^(n-k), and most of Book VIII is about what
# that forces on the terms.


def is_square(n: int) -> bool:
    root = round(n ** 0.5)
    while root * root > n:
        root -= 1
    while (root + 1) * (root + 1) <= n:
        root += 1
    return root * root == n


def is_cube(n: int) -> bool:
    root = round(abs(n) ** (1 / 3))
    while root * root * root > n:
        root -= 1
    while (root + 1) ** 3 <= n:
        root += 1
    return root ** 3 == n


def common_measure(terms: list) -> int:
    """The greatest number measuring every one of them."""
    found = 0
    for term in terms:
        found = gcd(found, term)
    return found


def continued_proportion(first: int, ratio: tuple, count: int) -> list[int]:
    """``count`` numbers in continued proportion, in the given ratio."""
    p, q = ratio
    return [first * p ** k * q ** (count - 1 - k) for k in range(count)]


def in_continued_proportion(terms: list) -> bool:
    """Each stands to the next as the next to the one after."""
    return all(terms[i] * terms[i + 2] == terms[i + 1] * terms[i + 1]
               for i in range(len(terms) - 2))


def _progression(rng):
    """A continued proportion in least terms, and how many terms it has."""
    while True:
        p, q = rng.randint(2, 6), rng.randint(2, 6)
        if coprime(p, q) and p != q:
            return p, q, rng.randint(3, 5)


@proposition(
    "VIII.1",
    THEOREM,
    sample=_progression,
    note="The extremes of a progression being coprime is what makes it the least "
    "of its kind -- and VIII.3 is the converse.",
)
def prop_VIII_1(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is in least terms", coprime(p, q) and p > 1 and q > 1)
    hypothesis("a genuine progression is asked for", count >= 3)
    terms = continued_proportion(1, (p, q), count)
    hypothesis("the extremes are prime to one another", coprime(terms[0], terms[-1]))

    # Consecutive terms are *not* coprime -- p^k q^(n-1-k) and its successor
    # share p^k q^(n-2-k). What makes the progression least is that the whole
    # set has no common measure, which the extremes being coprime forces.
    claim("the numbers are in continued proportion", "Def.VII.20",
          in_continued_proportion(terms))
    claim("the terms have no common measure but a unit", "VII.21",
          common_measure(terms) == 1)
    claim("so no smaller progression has the same ratios", "VII.20",
          not any(all(measures(d, term) for term in terms)
                  for d in range(2, min(terms) + 1)))
    return Out(terms=terms)


@proposition(
    "VIII.2",
    CONSTRUCTION,
    sample=_progression,
)
def prop_VIII_2(p: int, q: int, count: int) -> Out:
    """Find the least numbers in continued proportion in a given ratio."""
    hypothesis("the ratio is in least terms", coprime(p, q) and p > 1 and q > 1)
    hypothesis("a genuine progression is asked for", count >= 3)
    terms = continued_proportion(1, (p, q), count)

    claim("as many numbers as were asked for were found", "VIII.2", len(terms) == count)
    claim("they are in continued proportion in the given ratio", "Def.VII.20",
          in_continued_proportion(terms)
          and all(terms[i + 1] * q == terms[i] * p for i in range(count - 1)))
    claim("and they are the least such, their extremes being prime", "VIII.1",
          coprime(terms[0], terms[-1]))
    return Out(terms=terms)


@proposition(
    "VIII.3",
    THEOREM,
    sample=_progression,
)
def prop_VIII_3(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is in least terms", coprime(p, q) and p > 1 and q > 1)
    hypothesis("a genuine progression is asked for", count >= 3)
    terms = continued_proportion(1, (p, q), count)
    hypothesis("they are the least of their ratio", common_measure(terms) == 1)
    claim("the extremes are prime to one another", "VII.27",
          coprime(terms[0], terms[-1]))
    claim("and every measure of all of them is a unit", "VII.21",
          not any(all(measures(d, term) for term in terms)
                  for d in range(2, min(terms) + 1)))
    return Out()


@proposition(
    "VIII.4",
    CONSTRUCTION,
    sample=lambda rng: (rng.randint(2, 5), rng.randint(2, 5), rng.randint(2, 5),
                        rng.randint(2, 5)),
)
def prop_VIII_4(a: int, b: int, c: int, d: int) -> Out:
    """Given the ratios a:b and c:d, find the least continued proportion in them."""
    hypothesis("the ratios are genuine", all(n > 1 for n in (a, b, c, d)))
    first, second = least_terms(a, b)
    third, fourth = least_terms(c, d)
    # The middle term must be measured by both consequents, so take the least
    # number they both measure and scale each ratio up to meet it.
    middle = lcm(second, third)
    terms = [first * (middle // second), middle, fourth * (middle // third)]

    claim("the first pair keeps its ratio", "VII.18", terms[0] * b == terms[1] * a)
    claim("the second pair keeps its ratio", "VII.18", terms[1] * d == terms[2] * c)
    claim("and the middle is the least that both consequents measure", "VII.34",
          measures(second, middle) and measures(third, middle)
          and not any(measures(second, m) and measures(third, m)
                      for m in range(1, middle)))
    return Out(terms=terms)


@proposition(
    "VIII.5",
    THEOREM,
    sample=lambda rng: tuple(rng.randint(2, 12) for _ in range(4)),
    note="A 'plane number' is a product of two sides. Their ratio is the ratio "
    "of the sides compounded -- Book VI's VI.23 in arithmetic.",
)
def prop_VIII_5(a: int, b: int, c: int, d: int) -> Out:
    """The plane numbers are a*b and c*d."""
    hypothesis("the sides are genuine numbers", all(n > 1 for n in (a, b, c, d)))
    first, second = a * b, c * d
    claim("the plane numbers have the ratio compounded of the ratios of the sides",
          "VII.17", first * (c * d) == second * (a * b))
    claim("which is to say, the product of the two ratios", "VII.18",
          first * d * c == second * a * b)
    return Out(planes=(first, second))


@proposition(
    "VIII.6",
    THEOREM,
    sample=_progression,
)
def prop_VIII_6(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is in least terms", coprime(p, q) and p > 1 and q > 1)
    hypothesis("a genuine progression is asked for", count >= 3)
    terms = continued_proportion(1, (p, q), count)
    hypothesis("the first does not measure the second", not measures(terms[0], terms[1]))
    claim("then no one of them measures any other", "VIII.6",
          not any(measures(terms[i], terms[j])
                  for i in range(count) for j in range(count) if i != j))
    return Out()


@proposition(
    "VIII.7",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 5), rng.randint(3, 5)),
)
def prop_VIII_7(ratio: int, count: int) -> Out:
    """A progression whose ratio is a whole number, so the first measures the last."""
    hypothesis("the ratio and length are genuine", ratio > 1 and count >= 3)
    terms = continued_proportion(1, (ratio, 1), count)
    hypothesis("the first measures the last", measures(terms[0], terms[-1]))
    claim("then it measures the second also", "VIII.7", measures(terms[0], terms[1]))
    claim("and indeed every one of them", "VIII.6",
          all(measures(terms[0], term) for term in terms))
    return Out(terms=terms)


@proposition(
    "VIII.8",
    THEOREM,
    sample=_progression,
)
def prop_VIII_8(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is in least terms", coprime(p, q) and p > 1 and q > 1)
    hypothesis("a genuine progression is asked for", count >= 3)
    terms = continued_proportion(1, (p, q), count)
    scaled = [term * 3 for term in terms]
    claim("as many fall between the scaled pair as between the original", "VIII.8",
          len(scaled) == len(terms) and in_continued_proportion(scaled))
    claim("and the outer ratio is unchanged", "VII.18",
          terms[0] * scaled[-1] == terms[-1] * scaled[0])
    return Out(between=scaled[1:-1])


@proposition(
    "VIII.9",
    THEOREM,
    sample=_progression,
)
def prop_VIII_9(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is in least terms", coprime(p, q) and p > 1 and q > 1)
    hypothesis("a genuine progression is asked for", count >= 3)
    terms = continued_proportion(1, (p, q), count)
    hypothesis("the extremes are prime to one another", coprime(terms[0], terms[-1]))
    # p^(n-1) and q^(n-1) are the extremes; each reaches down to a unit through
    # its own powers, and there are as many steps as there were between them.
    to_unit_first = [q ** k for k in range(count)]
    to_unit_last = [p ** k for k in range(count)]
    claim("a progression runs from a unit up to each extreme", "VIII.2",
          in_continued_proportion(to_unit_first) and in_continued_proportion(to_unit_last)
          and to_unit_first[0] == 1 and to_unit_last[0] == 1)
    claim("with as many terms between as fell between the extremes", "VIII.9",
          len(to_unit_first) == count and len(to_unit_last) == count)
    return Out(first=to_unit_first, last=to_unit_last)


@proposition(
    "VIII.10",
    THEOREM,
    sample=_progression,
)
def prop_VIII_10(p: int, q: int, count: int) -> Out:
    """The converse of VIII.9."""
    hypothesis("the ratio is in least terms", coprime(p, q) and p > 1 and q > 1)
    hypothesis("a genuine progression is asked for", count >= 3)
    from_unit_first = [q ** k for k in range(count)]
    from_unit_last = [p ** k for k in range(count)]
    hypothesis("progressions run from a unit up to each number",
               in_continued_proportion(from_unit_first)
               and in_continued_proportion(from_unit_last))
    between = continued_proportion(1, (p, q), count)
    claim("then as many fall between the two numbers themselves", "VIII.10",
          in_continued_proportion(between) and len(between) == count)
    return Out(between=between)


@proposition(
    "VIII.11",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 20), rng.randint(2, 20)),
    note="One mean proportional between two squares, and the ratio is duplicate. "
    "The arithmetical twin of VI.19.",
)
def prop_VIII_11(a: int, b: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1)
    first, second = a * a, b * b
    mean = a * b
    claim("the number found is a mean proportional", "VIII.11",
          first * second == mean * mean)
    claim("and it is the only one", "VIII.8",
          not any(first * second == m * m for m in range(1, mean)))
    claim("so square is to square in the duplicate ratio of side to side", "VIII.11",
          first * (b * b) == second * (a * a))
    return Out(mean=mean)


@proposition(
    "VIII.12",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 10), rng.randint(2, 10)),
)
def prop_VIII_12(a: int, b: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1)
    first, second = a ** 3, b ** 3
    means = [a * a * b, a * b * b]
    claim("two mean proportionals fall between the cubes", "VIII.12",
          in_continued_proportion([first] + means + [second]))
    claim("and cube is to cube in the triplicate ratio of side to side", "VIII.12",
          first * b ** 3 == second * a ** 3)
    return Out(means=means)


@proposition(
    "VIII.13",
    THEOREM,
    sample=_progression,
)
def prop_VIII_13(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is in least terms", coprime(p, q) and p > 1 and q > 1)
    hypothesis("a genuine progression is asked for", count >= 3)
    terms = continued_proportion(1, (p, q), count)
    squares = [term * term for term in terms]
    cubes = [term ** 3 for term in terms]
    claim("the squares of the terms are proportional", "VIII.13",
          in_continued_proportion(squares))
    claim("and so are the cubes", "VIII.13", in_continued_proportion(cubes))
    return Out(squares=squares, cubes=cubes)


@proposition(
    "VIII.14",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 15), rng.randint(2, 15)),
)
def prop_VIII_14(a: int, b: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1)
    claim("if the square measures the square, the side measures the side", "VIII.14",
          measures(a * a, b * b) == measures(a, b))
    return Out()


@proposition(
    "VIII.15",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 10), rng.randint(2, 10)),
)
def prop_VIII_15(a: int, b: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1)
    claim("if the cube measures the cube, the side measures the side", "VIII.15",
          measures(a ** 3, b ** 3) == measures(a, b))
    return Out()


@proposition(
    "VIII.16",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 15), rng.randint(2, 15)),
)
def prop_VIII_16(a: int, b: int) -> Out:
    """The contrapositive of VIII.14, which Euclid states separately."""
    hypothesis("the sides are genuine numbers", a > 1 and b > 1)
    claim("if the square does not measure the square, neither does the side",
          "VIII.14", (not measures(a * a, b * b)) == (not measures(a, b)))
    return Out()


@proposition(
    "VIII.17",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 10), rng.randint(2, 10)),
)
def prop_VIII_17(a: int, b: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1)
    claim("if the cube does not measure the cube, neither does the side", "VIII.15",
          (not measures(a ** 3, b ** 3)) == (not measures(a, b)))
    return Out()


def _similar_planes(rng):
    """Two plane numbers whose sides are proportional."""
    a, b = rng.randint(2, 9), rng.randint(2, 9)
    scale = rng.randint(2, 5)
    return a, b, scale


@proposition(
    "VIII.18",
    THEOREM,
    sample=_similar_planes,
    note="'Similar plane numbers' are rectangles of the same shape, and they "
    "behave exactly as similar rectangles do in Book VI.",
)
def prop_VIII_18(a: int, b: int, scale: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1 and scale > 1)
    first, second = a * b, (a * scale) * (b * scale)
    mean = a * b * scale
    claim("the sides are proportional, so the planes are similar", "Def.VII.21",
          a * (b * scale) == b * (a * scale))
    claim("one mean proportional falls between them", "VIII.18",
          first * second == mean * mean)
    claim("and plane is to plane in the duplicate ratio of the sides", "VIII.11",
          first * (scale * scale) == second)
    return Out(mean=mean)


@proposition(
    "VIII.19",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 6), rng.randint(2, 6), rng.randint(2, 6),
                        rng.randint(2, 4)),
)
def prop_VIII_19(a: int, b: int, c: int, scale: int) -> Out:
    """Similar solid numbers: three sides each, in proportion."""
    hypothesis("the sides are genuine numbers", all(n > 1 for n in (a, b, c, scale)))
    first = a * b * c
    second = (a * scale) * (b * scale) * (c * scale)
    means = [first * scale, first * scale * scale]
    claim("two mean proportionals fall between them", "VIII.19",
          in_continued_proportion([first] + means + [second]))
    claim("and solid is to solid in the triplicate ratio of the sides", "VIII.12",
          second == first * scale ** 3)
    return Out(means=means)


@proposition(
    "VIII.20",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 12), rng.randint(2, 12)),
)
def prop_VIII_20(a: int, b: int) -> Out:
    """The converse of VIII.18: a mean proportional makes the numbers similar planes."""
    hypothesis("the sides are genuine numbers", a > 1 and b > 1)
    first, second, mean = a * a, b * b, a * b
    hypothesis("a mean proportional falls between them", first * second == mean * mean)
    claim("the two are similar plane numbers, with proportional sides", "Def.VII.21",
          a * b == b * a and is_square(first) and is_square(second))
    return Out(sides=((a, a), (b, b)))


@proposition(
    "VIII.21",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 8), rng.randint(2, 8)),
)
def prop_VIII_21(a: int, b: int) -> Out:
    """The converse of VIII.19."""
    hypothesis("the sides are genuine numbers", a > 1 and b > 1)
    first, second = a ** 3, b ** 3
    means = [a * a * b, a * b * b]
    hypothesis("two mean proportionals fall between them",
               in_continued_proportion([first] + means + [second]))
    claim("the two are similar solid numbers", "Def.VII.21",
          is_cube(first) and is_cube(second))
    return Out()


@proposition(
    "VIII.22",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 12), rng.randint(2, 12)),
)
def prop_VIII_22(a: int, b: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1)
    terms = [a * a, a * b, b * b]
    hypothesis("the three are in continued proportion", in_continued_proportion(terms))
    hypothesis("the first is square", is_square(terms[0]))
    claim("the third is square also", "VIII.22", is_square(terms[2]))
    return Out()


@proposition(
    "VIII.23",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 8), rng.randint(2, 8)),
)
def prop_VIII_23(a: int, b: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1)
    terms = [a ** 3, a * a * b, a * b * b, b ** 3]
    hypothesis("the four are in continued proportion", in_continued_proportion(terms))
    hypothesis("the first is cube", is_cube(terms[0]))
    claim("the fourth is cube also", "VIII.23", is_cube(terms[3]))
    return Out()


@proposition(
    "VIII.24",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 10), rng.randint(2, 10), rng.randint(2, 6)),
)
def prop_VIII_24(a: int, b: int, scale: int) -> Out:
    hypothesis("the numbers are genuine", a > 1 and b > 1 and scale > 1)
    first, second = a * a * scale * scale, b * b * scale * scale
    hypothesis("the two have the ratio of a square to a square",
               first * (b * b) == second * (a * a))
    hypothesis("the first is square", is_square(first))
    claim("the second is square also", "VIII.24", is_square(second))
    return Out()


@proposition(
    "VIII.25",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 6), rng.randint(2, 6), rng.randint(2, 4)),
)
def prop_VIII_25(a: int, b: int, scale: int) -> Out:
    hypothesis("the numbers are genuine", a > 1 and b > 1 and scale > 1)
    first, second = (a * scale) ** 3, (b * scale) ** 3
    hypothesis("the two have the ratio of a cube to a cube",
               first * b ** 3 == second * a ** 3)
    hypothesis("the first is cube", is_cube(first))
    claim("the second is cube also", "VIII.25", is_cube(second))
    return Out()


@proposition(
    "VIII.26",
    THEOREM,
    sample=_similar_planes,
)
def prop_VIII_26(a: int, b: int, scale: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1 and scale > 1)
    first, second = a * b, (a * scale) * (b * scale)
    claim("similar plane numbers have the ratio of a square to a square", "VIII.18",
          first * (scale * scale) == second and is_square(scale * scale))
    return Out(ratio=(1, scale * scale))


@proposition(
    "VIII.27",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 6), rng.randint(2, 6), rng.randint(2, 6),
                        rng.randint(2, 4)),
)
def prop_VIII_27(a: int, b: int, c: int, scale: int) -> Out:
    hypothesis("the sides are genuine numbers", all(n > 1 for n in (a, b, c, scale)))
    first = a * b * c
    second = (a * scale) * (b * scale) * (c * scale)
    claim("similar solid numbers have the ratio of a cube to a cube", "VIII.19",
          first * scale ** 3 == second and is_cube(scale ** 3))
    return Out(ratio=(1, scale ** 3))


# ---------------------------------------------------------------------------
# Book IX -- squares, cubes, parity, and the primes
# ---------------------------------------------------------------------------


def _from_a_unit(rng):
    """A progression beginning from a unit: 1, r, r^2, ... (IX.8-IX.13)."""
    return rng.randint(2, 7), rng.randint(4, 9)


@proposition(
    "IX.1",
    THEOREM,
    sample=_similar_planes,
)
def prop_IX_1(a: int, b: int, scale: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1 and scale > 1)
    first, second = a * b, (a * scale) * (b * scale)
    claim("the two are similar plane numbers", "Def.VII.21",
          a * (b * scale) == b * (a * scale))
    claim("their product is square", "IX.1", is_square(first * second))
    return Out(product=first * second)


@proposition(
    "IX.2",
    THEOREM,
    # Random pairs almost never have a square product, so a valid instance is
    # built. The sweep inside the proposition is what tests the theorem.
    sample=lambda rng: (rng.randint(1, 5) * rng.randint(2, 5) ** 2,
                        rng.randint(1, 5) * rng.randint(2, 5) ** 2),
)
def prop_IX_2(a: int, b: int) -> Out:
    """The converse of IX.1, tested by looking for a counterexample."""
    hypothesis("the numbers are genuine", a > 1 and b > 1)
    hypothesis("their product is square", is_square(a * b))

    def similar_planes(first: int, second: int) -> bool:
        """Both are the same multiple of a square: d*x^2 and d*y^2."""
        measure = gcd(first, second)
        return is_square(first // measure) and is_square(second // measure)

    claim("the two given numbers are similar plane numbers", "Def.VII.21",
          similar_planes(a, b))
    claim("and no pair whose product is square fails to be", "IX.2",
          all(similar_planes(x, y)
              for x in range(2, 40) for y in range(2, 40) if is_square(x * y)))
    return Out(sides=(gcd(a, b), a // gcd(a, b), b // gcd(a, b)))


@proposition(
    "IX.3",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 10),),
)
def prop_IX_3(a: int) -> Out:
    hypothesis("the number is genuine", a > 1)
    cube = a ** 3
    claim("a cube multiplied by itself makes a cube", "IX.3", is_cube(cube * cube))
    return Out(product=cube * cube)


@proposition(
    "IX.4",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 8), rng.randint(2, 8)),
)
def prop_IX_4(a: int, b: int) -> Out:
    hypothesis("the numbers are genuine", a > 1 and b > 1)
    claim("cube multiplied by cube makes a cube", "IX.4", is_cube(a ** 3 * b ** 3))
    return Out(product=a ** 3 * b ** 3)


@proposition(
    "IX.5",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 8), rng.randint(2, 8)),
)
def prop_IX_5(a: int, b: int) -> Out:
    hypothesis("the numbers are genuine", a > 1 and b > 1)
    cube, other = a ** 3, b ** 3
    hypothesis("the product is cube", is_cube(cube * other))
    claim("the multiplied number is cube", "IX.5", is_cube(other))
    # The content is that nothing but a cube will do, so every multiplier is
    # tried and none is found that makes a cube of the product without being one.
    claim("and no other multiplier makes the product cube", "IX.5",
          all(is_cube(n) for n in range(1, 200) if is_cube(cube * n)))
    return Out()


@proposition(
    "IX.6",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 8) ** 3,),
)
def prop_IX_6(a: int) -> Out:
    hypothesis("the number is genuine", a > 1)
    hypothesis("its square is cube", is_cube(a * a))
    claim("the number itself is cube", "IX.6", is_cube(a))
    claim("and no number whose square is cube fails to be one", "IX.6",
          all(is_cube(n) for n in range(2, 300) if is_cube(n * n)))
    return Out()


@proposition(
    "IX.7",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 10), rng.randint(2, 10), rng.randint(2, 20)),
)
def prop_IX_7(a: int, b: int, other: int) -> Out:
    """A composite number, given as a product of two, multiplied by a third."""
    hypothesis("the numbers are genuine", a > 1 and b > 1 and other > 1)
    composite = a * b
    claim("the number is composite", "Def.VII.13", not is_prime(composite))
    claim("its product with any number is solid, having three sides", "Def.VII.17",
          composite * other == a * b * other)
    return Out(solid=composite * other, sides=(a, b, other))


@proposition(
    "IX.8",
    THEOREM,
    sample=_from_a_unit,
    note="Reading a progression from a unit as powers: the third term is a "
    "square, the fourth a cube, the seventh both -- because 2, 3 and 6 are.",
)
def prop_IX_8(ratio: int, count: int) -> Out:
    hypothesis("the progression is genuine", ratio > 1 and count >= 7)
    terms = [ratio ** k for k in range(count)]  # 1, r, r^2, ...
    claim("the terms are in continued proportion from a unit", "Def.VII.20",
          terms[0] == 1 and in_continued_proportion(terms))
    claim("the third from the unit is square, and so are the alternate ones",
          "IX.8", all(is_square(terms[k]) for k in range(2, count, 2)))
    claim("the fourth is cube, and so is every third after it", "IX.8",
          all(is_cube(terms[k]) for k in range(3, count, 3)))
    claim("and the seventh is at once square and cube", "IX.8",
          is_square(terms[6]) and is_cube(terms[6]))
    return Out(terms=terms)


@proposition(
    "IX.9",
    THEOREM,
    sample=_from_a_unit,
)
def prop_IX_9(ratio: int, count: int) -> Out:
    hypothesis("the progression is genuine", ratio > 1 and count >= 4)
    squares = [(ratio * ratio) ** k for k in range(count)]
    claim("if the number after the unit is square, all the rest are square", "IX.8",
          is_square(squares[1]) and all(is_square(term) for term in squares[1:]))
    cubes = [(ratio ** 3) ** k for k in range(count)]
    claim("and if it is cube, all the rest are cube", "IX.8",
          is_cube(cubes[1]) and all(is_cube(term) for term in cubes[1:]))
    return Out()


@proposition(
    "IX.10",
    THEOREM,
    sample=_from_a_unit,
)
def prop_IX_10(ratio: int, count: int) -> Out:
    """The converse of IX.9, stated negatively."""
    hypothesis("the progression is genuine", ratio > 1 and count >= 5)
    hypothesis("the number after the unit is not square", not is_square(ratio))
    terms = [ratio ** k for k in range(count)]
    claim("then none is square except the third from the unit and the alternate ones",
          "IX.8",
          all(is_square(terms[k]) == (k % 2 == 0) for k in range(1, count)))
    return Out()


@proposition(
    "IX.11",
    THEOREM,
    sample=_from_a_unit,
)
def prop_IX_11(ratio: int, count: int) -> Out:
    hypothesis("the progression is genuine", ratio > 1 and count >= 4)
    terms = [ratio ** k for k in range(count)]
    claim("the less measures the greater", "IX.11",
          all(measures(terms[i], terms[j])
              for i in range(count) for j in range(i, count)))
    claim("and the quotient is itself one of the proportional numbers", "IX.11",
          all(terms[j] // terms[i] in terms
              for i in range(count) for j in range(i, count)))
    return Out(terms=terms)


@proposition(
    "IX.12",
    THEOREM,
    sample=_from_a_unit,
)
def prop_IX_12(ratio: int, count: int) -> Out:
    hypothesis("the progression is genuine", ratio > 1 and count >= 4)
    terms = [ratio ** k for k in range(count)]
    last_primes = sorted(set(prime_factors(terms[-1])))
    claim("every prime measuring the last measures the number next the unit also",
          "IX.12", all(measures(p, terms[1]) for p in last_primes))
    claim("and they are the same primes", "VII.30",
          last_primes == sorted(set(prime_factors(terms[1]))))
    return Out(primes=last_primes)


@proposition(
    "IX.13",
    THEOREM,
    sample=lambda rng: (rng.choice([p for p in range(2, 20) if is_prime(p)]),
                        rng.randint(4, 7)),
)
def prop_IX_13(prime: int, count: int) -> Out:
    hypothesis("the number after the unit is prime", is_prime(prime))
    hypothesis("the progression is genuine", count >= 4)
    terms = [prime ** k for k in range(count)]
    claim("the greatest is measured by no number outside the progression", "IX.12",
          all(measures(d, terms[-1]) == (d in terms)
              for d in range(1, terms[-1] + 1) if measures(d, terms[-1])))
    return Out(terms=terms)


@proposition(
    "IX.14",
    THEOREM,
    sample=lambda rng: tuple(sorted(rng.sample([p for p in range(2, 30) if is_prime(p)],
                                               rng.randint(2, 3)))),
    note="Unique factorisation, in the only form Euclid states it.",
)
def prop_IX_14(*primes: int) -> Out:
    hypothesis("the given numbers are prime", all(is_prime(p) for p in primes))
    least = 1
    for prime in primes:
        least *= prime
    claim("the number found is the least measured by them all", "VII.36",
          all(measures(p, least) for p in primes)
          and not any(all(measures(p, m) for p in primes) for m in range(1, least)))
    claim("and no other prime measures it", "VII.30",
          all(measures(p, least) == (p in primes)
              for p in range(2, least + 1) if is_prime(p)))
    return Out(least=least)


@proposition(
    "IX.15",
    THEOREM,
    sample=_progression,
)
def prop_IX_15(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is in least terms", coprime(p, q) and p > 1 and q > 1)
    terms = [q * q, p * q, p * p]
    hypothesis("the three are the least in their ratio", common_measure(terms) == 1)
    claim("any two added together are prime to the remaining one", "VII.28",
          coprime(terms[0] + terms[1], terms[2])
          and coprime(terms[1] + terms[2], terms[0])
          and coprime(terms[0] + terms[2], terms[1]))
    return Out(terms=terms)


@proposition(
    "IX.16",
    THEOREM,
    sample=_coprime_pair,
)
def prop_IX_16(a: int, b: int) -> Out:
    hypothesis("the numbers are prime to one another", coprime(a, b))
    hypothesis("the first does not measure the second", not measures(a, b))
    claim("the second is to no other number as the first is to the second", "VII.20",
          not any(a * c == b * b for c in range(1, b * b + 1)))
    return Out()


@proposition(
    "IX.17",
    THEOREM,
    sample=_progression,
)
def prop_IX_17(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is in least terms", coprime(p, q) and p > 1 and q > 1)
    hypothesis("a genuine progression is asked for", count >= 3)
    terms = continued_proportion(1, (p, q), count)
    hypothesis("the extremes are prime to one another", coprime(terms[0], terms[-1]))
    claim("the first does not measure the second", "VIII.6",
          not measures(terms[0], terms[1]))
    claim("so the last is to no other number as the first is to the second", "IX.16",
          not any(terms[0] * c == terms[1] * terms[-1]
                  for c in range(1, terms[1] * terms[-1] + 1)))
    return Out()


@proposition(
    "IX.18",
    CONSTRUCTION,
    sample=lambda rng: (rng.randint(2, 30), rng.randint(2, 30)),
    note="Euclid asks when a problem is *possible*, and answers with a test -- "
    "a decision procedure, not a construction.",
)
def prop_IX_18(a: int, b: int) -> Out:
    hypothesis("both are numbers", a > 1 and b > 1)
    possible = measures(a, b * b)
    claim("a third proportional exists exactly when the first measures the square "
          "of the second", "VII.19", possible == (b * b % a == 0))
    claim("and when it does, it is that quotient", "VII.19",
          not possible or a * (b * b // a) == b * b)
    return Out(possible=possible, third=(b * b // a) if possible else None)


@proposition(
    "IX.19",
    CONSTRUCTION,
    sample=_three_numbers,
)
def prop_IX_19(a: int, b: int, c: int) -> Out:
    hypothesis("all three are numbers", a > 1 and b > 1 and c > 1)
    possible = measures(a, b * c)
    claim("a fourth proportional exists exactly when the first measures the "
          "product of the second and third", "VII.19", possible == (b * c % a == 0))
    claim("and when it does, it is that quotient", "VII.19",
          not possible or a * (b * c // a) == b * c)
    return Out(possible=possible, fourth=(b * c // a) if possible else None)


def _even_numbers(rng):
    return ([2 * rng.randint(1, 30) for _ in range(rng.randint(2, 6))],)


def _odd_numbers(rng, even_count: bool):
    count = rng.randint(1, 4) * 2
    if not even_count:
        count -= 1
    return ([2 * rng.randint(1, 30) + 1 for _ in range(count)],)


@proposition(
    "IX.21",
    THEOREM,
    sample=_even_numbers,
    note="Book IX ends with a run of parity theorems, which read as trivial now "
    "and were not: Euclid has no notation for 'even' but 'divisible into two "
    "equal parts'.",
)
def prop_IX_21(given: list) -> Out:
    hypothesis("all the numbers are even", all(measures(2, n) for n in given) and given)
    claim("the sum of them is even", "Def.VII.6", measures(2, sum(given)))
    return Out(total=sum(given))


@proposition(
    "IX.22",
    THEOREM,
    sample=lambda rng: _odd_numbers(rng, even_count=True),
)
def prop_IX_22(given: list) -> Out:
    hypothesis("all the numbers are odd", all(not measures(2, n) for n in given) and given)
    hypothesis("they are even in multitude", measures(2, len(given)))
    claim("the sum is even", "IX.21", measures(2, sum(given)))
    return Out(total=sum(given))


@proposition(
    "IX.23",
    THEOREM,
    sample=lambda rng: _odd_numbers(rng, even_count=False),
)
def prop_IX_23(given: list) -> Out:
    hypothesis("all the numbers are odd", all(not measures(2, n) for n in given) and given)
    hypothesis("they are odd in multitude", not measures(2, len(given)))
    claim("the sum is odd", "IX.22", not measures(2, sum(given)))
    return Out(total=sum(given))


def _pair_by_parity(rng, first_even: bool, second_even: bool):
    a = 2 * rng.randint(4, 30) + (0 if first_even else 1)
    b = 2 * rng.randint(1, 3) + (0 if second_even else 1)
    return a, b


@proposition("IX.24", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, True, True))
def prop_IX_24(a: int, b: int) -> Out:
    hypothesis("an even number has an even subtracted", measures(2, a) and measures(2, b))
    hypothesis("the subtraction is a proper one", a > b)
    claim("the remainder is even", "IX.21", measures(2, a - b))
    return Out(remainder=a - b)


@proposition("IX.25", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, True, False))
def prop_IX_25(a: int, b: int) -> Out:
    hypothesis("an even number has an odd subtracted",
               measures(2, a) and not measures(2, b))
    hypothesis("the subtraction is a proper one", a > b)
    claim("the remainder is odd", "IX.23", not measures(2, a - b))
    return Out(remainder=a - b)


@proposition("IX.26", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, False, False))
def prop_IX_26(a: int, b: int) -> Out:
    hypothesis("an odd number has an odd subtracted",
               not measures(2, a) and not measures(2, b))
    hypothesis("the subtraction is a proper one", a > b)
    claim("the remainder is even", "IX.22", measures(2, a - b))
    return Out(remainder=a - b)


@proposition("IX.27", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, False, True))
def prop_IX_27(a: int, b: int) -> Out:
    hypothesis("an odd number has an even subtracted",
               not measures(2, a) and measures(2, b))
    hypothesis("the subtraction is a proper one", a > b)
    claim("the remainder is odd", "IX.25", not measures(2, a - b))
    return Out(remainder=a - b)


@proposition("IX.28", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, False, True))
def prop_IX_28(a: int, b: int) -> Out:
    hypothesis("an odd number multiplies an even one",
               not measures(2, a) and measures(2, b))
    claim("the product is even", "IX.21", measures(2, a * b))
    return Out(product=a * b)


@proposition("IX.29", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, False, False))
def prop_IX_29(a: int, b: int) -> Out:
    hypothesis("an odd number multiplies an odd one",
               not measures(2, a) and not measures(2, b))
    claim("the product is odd", "IX.23", not measures(2, a * b))
    return Out(product=a * b)


@proposition("IX.30", THEOREM,
             sample=lambda rng: (2 * rng.randint(1, 15) + 1, rng.randint(1, 20)))
def prop_IX_30(odd: int, times: int) -> Out:
    even = odd * 2 * times
    hypothesis("the number is odd", not measures(2, odd))
    hypothesis("it measures an even number", measures(odd, even) and measures(2, even))
    claim("it measures the half of it as well", "IX.30", measures(odd, even // 2))
    return Out(half=even // 2)


@proposition("IX.31", THEOREM,
             sample=lambda rng: (2 * rng.randint(1, 30) + 1, rng.randint(2, 40)))
def prop_IX_31(odd: int, other: int) -> Out:
    hypothesis("the number is odd", not measures(2, odd))
    hypothesis("it is prime to the other", coprime(odd, other))
    claim("it is prime to the double of it also", "IX.30", coprime(odd, 2 * other))
    return Out()


@proposition("IX.32", THEOREM, sample=lambda rng: (rng.randint(2, 12),),
             note="'Even-times even only' means a power of two: divisible by two "
             "down to two itself and never by an odd number.")
def prop_IX_32(power: int) -> Out:
    hypothesis("a genuine doubling is asked for", power >= 2)
    number = 2 ** power
    claim("the number is reached by continual doubling from a dyad", "Def.VII.8",
          number == 2 ** power and in_continued_proportion([2 ** k for k in range(power + 1)]))
    claim("it is even-times even only, no odd number measuring it", "Def.VII.8",
          not any(measures(d, number) for d in range(3, number + 1, 2)))
    return Out(number=number)


@proposition("IX.33", THEOREM,
             sample=lambda rng: (2 * rng.randint(1, 20) + 1,))
def prop_IX_33(half: int) -> Out:
    number = 2 * half
    hypothesis("the half is odd", not measures(2, half))
    claim("the number is even-times odd only", "Def.VII.9",
          measures(2, number) and not measures(4, number))
    return Out(number=number)


@proposition("IX.34", THEOREM,
             sample=lambda rng: (rng.randint(2, 5), 2 * rng.randint(1, 10) + 1))
def prop_IX_34(power: int, odd: int) -> Out:
    number = 2 ** power * odd
    hypothesis("the number is neither a doubling from a dyad nor has an odd half",
               power >= 2 and odd > 1 and not measures(2, odd))
    claim("it is even-times even, being measured by an even number an even number "
          "of times", "Def.VII.8", measures(4, number))
    claim("and also eventimes odd, being measured by an even number an odd number "
          "of times", "Def.VII.9", measures(2, number) and measures(odd, number))
    return Out(number=number)


@proposition(
    "IX.35",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 5), rng.randint(3, 6)),
    note="The sum of a geometric series, and the step IX.36 needs. Euclid states "
    "it as a proportion because he has no formula to state.",
)
def prop_IX_35(ratio: int, count: int) -> Out:
    hypothesis("the progression is genuine", ratio > 1 and count >= 3)
    terms = [ratio ** k for k in range(count)]
    excess_of_second = terms[1] - terms[0]
    excess_of_last = terms[-1] - terms[0]
    before = sum(terms[:-1])

    claim("the terms are in continued proportion", "Def.VII.20",
          in_continued_proportion(terms))
    claim("as the excess of the second is to the first, so is the excess of the "
          "last to all those before it", "IX.35",
          excess_of_second * before == terms[0] * excess_of_last)
    claim("which sums the series", "IX.35",
          before * (ratio - 1) == terms[-1] - terms[0])
    return Out(total=before)


def _prime_list(rng):
    primes = [p for p in range(2, 60) if is_prime(p)]
    rng.shuffle(primes)
    return (sorted(primes[: rng.randint(1, 5)]),)


@proposition(
    "IX.20",
    CONSTRUCTION,
    sample=_prime_list,
    note="Euclid's proof is constructive and is not a proof by contradiction: given "
    "any finite list of primes it exhibits a prime outside it. The machine runs the "
    "construction rather than paraphrasing it.",
)
def prop_IX_20(given: list) -> Out:
    hypothesis("a finite list of primes is given", all(is_prime(p) for p in given) and given)

    product = 1
    for prime in given:
        product *= prime
    candidate = product + 1

    claim("the product of the given primes, with a unit added, is measured by no "
          "prime in the list", "VII.31", all(candidate % p != 0 for p in given))
    fresh = prime_factors(candidate)[0]
    claim("yet it is measured by some prime", "VII.31", is_prime(fresh))
    claim("so that prime is not among those given, and the list was not complete",
          "IX.20", fresh not in given)
    return Out(new_prime=fresh, from_product=candidate)


def _mersenne_exponent(rng):
    return (rng.choice([2, 3, 5, 7, 13]),)


@proposition(
    "IX.36",
    THEOREM,
    sample=_mersenne_exponent,
    note="Euclid pairs perfect numbers with Mersenne primes. Euler later proved the "
    "converse for even numbers; whether an odd perfect number exists is still open, "
    "which makes this the oldest unsolved problem in mathematics.",
)
def prop_IX_36(exponent: int) -> Out:
    total = 2**exponent - 1
    hypothesis("the sum of the doubling series is prime", is_prime(total))
    candidate = total * 2 ** (exponent - 1)

    claim("the doubling series sums to the stated total", "IX.35",
          sum(2**k for k in range(exponent)) == total)
    claim("the product of the sum and the last term is perfect", "IX.36",
          is_perfect(candidate))
    claim("it equals the sum of its own proper parts", "Def.VII.22",
          sum(proper_divisors(candidate)) == candidate)
    return Out(perfect=candidate, mersenne=total)
