"""Euclid's number theory, shared by Books VII to IX.

These are the operations the arithmetical books are built from -- the Euclidean
algorithm and what follows from it. They lived inside the book module until
three books were split apart and it became clear that sixteen of its helpers
belonged to none of them in particular.

Numbers here are Euclid's: positive integers, with the unit not counted as a
number. Nothing rounds, so nothing needs to.
"""

from __future__ import annotations

__all__ = [
    "common_measure",
    "continued_proportion",
    "coprime",
    "coprime_pair",
    "gcd",
    "in_continued_proportion",
    "is_cube",
    "is_prime",
    "is_square",
    "lcm",
    "least_terms",
    "measures",
    "prime_factors",
    "progression",
    "similar_planes",
    "three_numbers",
]


def measures(a: int, b: int) -> bool:
    """``a`` measures ``b``: it goes into it a whole number of times."""
    return a != 0 and b % a == 0


def gcd(a: int, b: int) -> int:
    """The greatest common measure, by the algorithm of VII.2."""
    while b:
        a, b = b, a % b
    return abs(a)


def lcm(a: int, b: int) -> int:
    """The least number the two measure, by VII.34."""
    return abs(a * b) // gcd(a, b)


def coprime(a: int, b: int) -> bool:
    """Euclid's 'prime to one another': no common measure but a unit."""
    return gcd(a, b) == 1


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


def least_terms(a: int, b: int) -> tuple[int, int]:
    """The least pair having the same ratio, by VII.33."""
    measure = gcd(a, b)
    return a // measure, b // measure


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


def coprime_pair(rng):
    while True:
        a, b = rng.randint(2, 200), rng.randint(2, 200)
        if coprime(a, b) and a != b:
            return a, b


def three_numbers(rng):
    return rng.randint(2, 200), rng.randint(2, 200), rng.randint(2, 200)


def progression(rng):
    """A continued proportion in least terms, and how many terms it has."""
    while True:
        p, q = rng.randint(2, 6), rng.randint(2, 6)
        if coprime(p, q) and p != q:
            return p, q, rng.randint(3, 5)


def similar_planes(rng):
    """Two plane numbers whose sides are proportional.

    All four sides are handed over.  Giving two and a scale, and letting the
    proposition multiply, leaves it checking that ``a * (b * scale)`` equals
    ``b * (a * scale)`` -- which is commutativity, and true whatever the sides
    are, so it says nothing about their being proportional.
    """
    a, b = rng.randint(2, 9), rng.randint(2, 9)
    scale = rng.randint(2, 5)
    return a, b, a * scale, b * scale
