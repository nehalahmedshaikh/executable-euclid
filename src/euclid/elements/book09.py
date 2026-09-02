"""Book IX: primes, parity, and the perfect numbers.

IX.20 is a construction, not a counting argument: given any list of primes it
builds one more. IX.36 pairs the perfect numbers with the Mersenne primes, and
it carries the oldest open question in mathematics -- whether an odd perfect
number exists.
"""

from __future__ import annotations

from .book07 import (
    prop_VII_19,
    prop_VII_20,
    prop_VII_28,
    prop_VII_30,
    prop_VII_31,
    prop_VII_36,
)
from .book08 import prop_VIII_6
from .arithmetic import (
    common_measure,
    continued_proportion,
    coprime,
    coprime_pair,
    gcd,
    in_continued_proportion,
    is_cube,
    is_prime,
    is_square,
    measures,
    prime_factors,
    progression,
    similar_planes,
    three_numbers,
)
from .registry import (
    CONSTRUCTION,
    THEOREM,
    Out,
    because,
    claim,
    hypothesis,
    proposition,
)


def _third_proportional_case(rng):
    """Two numbers, half the time ones a third proportional exists for.

    Left to chance the answer was almost always "impossible", so the branch that
    finds the third proportional -- and the appeal to VII.19 inside it -- went
    unrun. Sampling it sometimes was worse than either: whether the edge counted
    as executed then depended on the draw, and the corpus reported 457 edges on
    one run and 458 on the next. The impossible case is still covered, by the
    biconditional the claim states rather than by the luck of the sampler.
    """
    b = rng.randint(2, 30)
    if True:  # always: an edge that appears only sometimes is not a measurement
        divisors = [d for d in range(2, b * b) if b * b % d == 0 and b * b // d > 1]
        if divisors:
            return rng.choice(divisors), b
    return rng.randint(2, 30), b


def _fourth_proportional_case(rng):
    """Three numbers, half the time ones a fourth proportional exists for."""
    b, c = rng.randint(2, 20), rng.randint(2, 20)
    if True:  # always, for the same reason as the third proportional
        divisors = [d for d in range(2, b * c) if b * c % d == 0 and b * c // d > 1]
        if divisors:
            return rng.choice(divisors), b, c
    return rng.randint(2, 20), b, c


def proper_divisors(n: int) -> list[int]:
    return [d for d in range(1, n) if n % d == 0]


def is_perfect(n: int) -> bool:
    """Euclid's definition VII.22: a number equal to the sum of its own parts."""
    return n > 1 and sum(proper_divisors(n)) == n


def _from_a_unit(rng):
    """A progression beginning from a unit: 1, r, r^2, ... (IX.8-IX.13)."""
    return rng.randint(2, 7), rng.randint(4, 9)


@proposition(
    "IX.1",
    THEOREM,
    sample=similar_planes,
)
def prop_IX_1(a: int, b: int, c: int, d: int) -> Out:
    hypothesis("the sides are genuine numbers",
               a > 1 and b > 1 and c > 1 and d > 1, guard=True)
    hypothesis("the two are similar plane numbers, their sides proportional",
               a * d == b * c)
    first, second = a * b, c * d
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
    hypothesis("the numbers are genuine", a > 1 and b > 1, guard=True)
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
    hypothesis("the number is genuine", a > 1, guard=True)
    cube = a ** 3
    claim("a cube multiplied by itself makes a cube", "IX.3", is_cube(cube * cube))
    return Out(product=cube * cube)


@proposition(
    "IX.4",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 8), rng.randint(2, 8)),
)
def prop_IX_4(a: int, b: int) -> Out:
    hypothesis("the numbers are genuine", a > 1 and b > 1, guard=True)
    claim("cube multiplied by cube makes a cube", "IX.4", is_cube(a ** 3 * b ** 3))
    return Out(product=a ** 3 * b ** 3)


@proposition(
    "IX.5",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 8), rng.randint(2, 8)),
)
def prop_IX_5(a: int, b: int) -> Out:
    hypothesis("the numbers are genuine", a > 1 and b > 1, guard=True)
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
    hypothesis("the number is genuine", a > 1, guard=True)
    hypothesis("its square is cube", is_cube(a * a))
    claim("the number itself is cube", "IX.6", is_cube(a))
    claim("and no number whose square is cube fails to be one", "IX.6",
          all(is_cube(n) for n in range(2, 300) if is_cube(n * n)))
    return Out()


@proposition(
    "IX.7",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 10) * rng.randint(2, 10), rng.randint(2, 20)),
)
def prop_IX_7(composite: int, other: int) -> Out:
    """A composite number multiplied by any number makes a solid number.

    The composite is given, and its two sides are found rather than handed over.
    Given the sides and multiplying them out, the conclusion compared the
    product with the expression it had just been built from.
    """
    hypothesis("the first is composite", composite > 1 and not is_prime(composite))
    hypothesis("the second is a number", other > 1, guard=True)
    a = next(d for d in range(2, composite) if measures(d, composite))
    b = composite // a
    solid = composite * other
    claim("the composite is measured by some number, and so has two sides",
          "Def.VII.13", a > 1 and b > 1 and a * b == composite)
    claim("its product with any number is solid, having three sides", "Def.VII.17",
          a > 1 and b > 1 and other > 1 and a * b * other == solid)
    return Out(solid=solid, sides=(a, b, other))


@proposition(
    "IX.8",
    THEOREM,
    sample=_from_a_unit,
    note="Reading a progression from a unit as powers: the third term is a "
    "square, the fourth a cube, the seventh both -- because 2, 3 and 6 are.",
)
def prop_IX_8(ratio: int, count: int) -> Out:
    hypothesis("the progression is genuine", ratio > 1 and count >= 7, guard=True)
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
    hypothesis("the progression is genuine", ratio > 1 and count >= 4, guard=True)
    squares = [(ratio * ratio) ** k for k in range(count)]
    because(prop_IX_8, ratio, max(count, 7))

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
    hypothesis("the progression is genuine", ratio > 1 and count >= 5, guard=True)
    hypothesis("the number after the unit is not square", not is_square(ratio))
    terms = [ratio ** k for k in range(count)]
    because(prop_IX_8, ratio, max(count, 7))

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
    hypothesis("the progression is genuine", ratio > 1 and count >= 4, guard=True)
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
    hypothesis("the progression is genuine", ratio > 1 and count >= 4, guard=True)
    terms = [ratio ** k for k in range(count)]
    last_primes = sorted(set(prime_factors(terms[-1])))
    # The last is the second taken as often as the progression is long, so a
    # prime measuring it measures a product of the second with the rest, and
    # VII.30 puts it into one of the two.
    for _p in last_primes:
        because(prop_VII_30, _p, terms[1], terms[-1] // terms[1])

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
    hypothesis("the progression is genuine", count >= 4, guard=True)
    terms = [prime ** k for k in range(count)]
    because(prop_IX_12, prime, count) if prime > 1 and count >= 4 else None

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
    because(prop_VII_36, 2, 3, 5)
    for _p in primes:
        because(prop_VII_30, _p, primes[0], least // primes[0])

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
    sample=progression,
)
def prop_IX_15(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is a genuine one", p > 1 and q > 1, guard=True)
    terms = [q * q, p * q, p * p]
    hypothesis("the three are the least in their ratio", common_measure(terms) == 1)
    because(prop_VII_28, p, q) if coprime(p, q) else None

    claim("any two added together are prime to the remaining one", "VII.28",
          coprime(terms[0] + terms[1], terms[2])
          and coprime(terms[1] + terms[2], terms[0])
          and coprime(terms[0] + terms[2], terms[1]))
    return Out(terms=terms)


@proposition(
    "IX.16",
    THEOREM,
    sample=coprime_pair,
)
def prop_IX_16(a: int, b: int) -> Out:
    hypothesis("the numbers are prime to one another", coprime(a, b))
    hypothesis("the first does not measure the second", not measures(a, b))
    because(prop_VII_20, a, b, a, b)

    claim("the second is to no other number as the first is to the second", "VII.20",
          not any(a * c == b * b for c in range(1, b * b + 1)))
    return Out()


@proposition(
    "IX.17",
    THEOREM,
    sample=progression,
)
def prop_IX_17(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is a genuine one", p > 1 and q > 1, guard=True)
    hypothesis("a genuine progression is asked for", count >= 3, guard=True)
    terms = continued_proportion(1, (p, q), count)
    hypothesis("the extremes are prime to one another", coprime(terms[0], terms[-1]))
    because(prop_IX_16, terms[0], terms[-1])
    because(prop_VIII_6, p, q, count)

    claim("the first does not measure the second", "VIII.6",
          not measures(terms[0], terms[1]))
    claim("so the last is to no other number as the first is to the second", "IX.16",
          not any(terms[0] * c == terms[1] * terms[-1]
                  for c in range(1, terms[1] * terms[-1] + 1)))
    return Out()


@proposition(
    "IX.18",
    CONSTRUCTION,
    sample=_third_proportional_case,
    note="Euclid asks when a problem is *possible*, and answers with a test -- "
    "a decision procedure, not a construction.",
)
def prop_IX_18(a: int, b: int) -> Out:
    hypothesis("both are numbers", a > 1 and b > 1, guard=True)
    possible = measures(a, b * b)
    if possible and b * b // a > 1:
        # A is to B as B is to the third, so VII.19 speaks of these four.
        because(prop_VII_19, a, b, b, b * b // a)

    claim("a third proportional exists exactly when the first measures the square "
          "of the second", "VII.19", possible == (b * b % a == 0))
    claim("and when it does, it is that quotient", "VII.19",
          not possible or a * (b * b // a) == b * b)
    return Out(possible=possible, third=(b * b // a) if possible else None)


@proposition(
    "IX.19",
    CONSTRUCTION,
    sample=_fourth_proportional_case,
)
def prop_IX_19(a: int, b: int, c: int) -> Out:
    hypothesis("all three are numbers", a > 1 and b > 1 and c > 1, guard=True)
    possible = measures(a, b * c)
    if possible and b * c // a > 1:
        because(prop_VII_19, a, b, c, b * c // a)

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
    because(prop_IX_21, [2 * n for n in given])

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
    because(prop_IX_22, given + [given[0]]) if len(given) % 2 else None

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
    hypothesis("the subtraction is a proper one", a > b, guard=True)
    because(prop_IX_21, [a, b]) if all(measures(2, n) for n in (a, b)) else None

    claim("the remainder is even", "IX.21", measures(2, a - b))
    return Out(remainder=a - b)


@proposition("IX.25", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, True, False))
def prop_IX_25(a: int, b: int) -> Out:
    hypothesis("an even number has an odd subtracted",
               measures(2, a) and not measures(2, b))
    hypothesis("the subtraction is a proper one", a > b, guard=True)
    because(prop_IX_23, [b]) if not measures(2, b) else None

    claim("the remainder is odd", "IX.23", not measures(2, a - b))
    return Out(remainder=a - b)


@proposition("IX.26", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, False, False))
def prop_IX_26(a: int, b: int) -> Out:
    hypothesis("an odd number has an odd subtracted",
               not measures(2, a) and not measures(2, b))
    hypothesis("the subtraction is a proper one", a > b, guard=True)
    because(prop_IX_22, [a, b]) if all(not measures(2, n) for n in (a, b)) else None

    claim("the remainder is even", "IX.22", measures(2, a - b))
    return Out(remainder=a - b)


@proposition("IX.27", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, False, True))
def prop_IX_27(a: int, b: int) -> Out:
    hypothesis("an odd number has an even subtracted",
               not measures(2, a) and measures(2, b))
    hypothesis("the subtraction is a proper one", a > b, guard=True)
    because(prop_IX_25, a, b) if measures(2, a) and not measures(2, b) and a > b else None

    because(prop_IX_25, a + b, b) if measures(2, a + b) and not measures(2, b) else None

    claim("the remainder is odd", "IX.25", not measures(2, a - b))
    return Out(remainder=a - b)


@proposition("IX.28", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, False, True))
def prop_IX_28(a: int, b: int) -> Out:
    hypothesis("an odd number multiplies an even one",
               not measures(2, a) and measures(2, b))
    because(prop_IX_21, [a]) if measures(2, a) else None

    because(prop_IX_21, [a * b]) if measures(2, a * b) else None

    claim("the product is even", "IX.21", measures(2, a * b))
    return Out(product=a * b)


@proposition("IX.29", THEOREM,
             sample=lambda rng: _pair_by_parity(rng, False, False))
def prop_IX_29(a: int, b: int) -> Out:
    hypothesis("an odd number multiplies an odd one",
               not measures(2, a) and not measures(2, b))
    because(prop_IX_23, [a, b, a]) if all(not measures(2, n) for n in (a, b)) else None

    claim("the product is odd", "IX.23", not measures(2, a * b))
    return Out(product=a * b)


@proposition("IX.30", THEOREM,
             sample=lambda rng: (2 * rng.randint(1, 15) + 1, rng.randint(1, 20)))
def prop_IX_30(number: int, multiple: int) -> Out:
    # The multiple is arbitrary and the evenness is a hypothesis, so oddness has
    # something to do. Building the even number as ``number * 2 * multiple``
    # instead makes the half divisible whatever the parity, and the proposition
    # then holds for reasons of its own construction: 4 measures 12 and does not
    # measure 6, and no such case could arise.
    product = number * multiple
    hypothesis("the number is odd", not measures(2, number))
    hypothesis("it measures an even number", measures(2, product))
    claim("it measures the half of it as well", "IX.30", measures(number, product // 2))
    return Out(half=product // 2)


@proposition("IX.31", THEOREM,
             sample=lambda rng: (2 * rng.randint(1, 30) + 1, rng.randint(2, 40)))
def prop_IX_31(odd: int, other: int) -> Out:
    hypothesis("the number is odd", not measures(2, odd))
    hypothesis("it is prime to the other", coprime(odd, other))
    because(prop_IX_30, odd, other)

    claim("it is prime to the double of it also", "IX.30", coprime(odd, 2 * other))
    return Out()


@proposition("IX.32", THEOREM, sample=lambda rng: (2 ** rng.randint(2, 12),),
             note="'Even-times even only' means a power of two: divisible by two "
             "down to two itself and never by an odd number.")
def prop_IX_32(number: int) -> Out:
    hypothesis("a genuine doubling is asked for", number >= 4, guard=True)
    # The doubling is carried out rather than named by an exponent. Written as
    # ``number = 2 ** power``, the claim that the number is reached by doubling
    # compared it with the expression it was assigned, and a number that is no
    # power of two could not have been offered to refute it. Here the chain
    # overshoots when it is not, and the claim fails.
    chain = [2]
    while chain[-1] < number:
        chain.append(chain[-1] + chain[-1])
    claim("the number is reached by continual doubling from a dyad", "Def.VII.8",
          chain[-1] == number and in_continued_proportion(chain))
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
    hypothesis("the progression is genuine", ratio > 1 and count >= 3, guard=True)
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

    # Euclid's step is about the number with the unit added, not the product:
    # if it is not itself prime, VII.31 finds the prime that measures it. The
    # appeal was written on the product, where it says nothing.
    if candidate > 3 and not is_prime(candidate):
        because(prop_VII_31, candidate)

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

    because(prop_IX_35, 2, exponent) if exponent >= 3 else None

    claim("the doubling series sums to the stated total", "IX.35",
          sum(2**k for k in range(exponent)) == total)
    claim("the product of the sum and the last term is perfect", "IX.36",
          is_perfect(candidate))
    claim("it equals the sum of its own proper parts", "Def.VII.22",
          sum(proper_divisors(candidate)) == candidate)
    return Out(perfect=candidate, mersenne=total)
