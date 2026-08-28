"""Books VII-IX: the arithmetical books, as the algorithms they always were.

These books have no diagrams worth drawing, but they do have running code in
them.  VII.1-2 is the Euclidean algorithm, stated as repeated subtraction.
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


@proposition(
    "VII.2",
    "To find the greatest common measure of two given numbers not relatively prime.",
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
    "Any composite number is measured by some prime number.",
    THEOREM,
    sample=lambda rng: (rng.randint(4, 500) | 1 if rng.random() < 0.3 else 2 * rng.randint(2, 250),),
)
def prop_VII_31(n: int) -> Out:
    hypothesis("the number is composite", n > 3 and not is_prime(n))
    factors = prime_factors(n)
    claim("a prime factor was found", "VII.31", bool(factors) and is_prime(factors[0]))
    claim("and it measures the number", "Def.VII.3", n % factors[0] == 0)
    return Out(prime=factors[0])


def _prime_list(rng):
    primes = [p for p in range(2, 60) if is_prime(p)]
    rng.shuffle(primes)
    return (sorted(primes[: rng.randint(1, 5)]),)


@proposition(
    "IX.20",
    "Prime numbers are more than any assigned multitude of prime numbers.",
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
    "If as many numbers as we please beginning from a unit are set out continuously in "
    "double proportion until the sum of all becomes prime, and if the sum multiplied into "
    "the last makes some number, then the product is perfect.",
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
