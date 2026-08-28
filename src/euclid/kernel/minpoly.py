"""Minimal polynomials, algebraic degree, and the impossibility oracle.

Every element of a quadratic tower ``K_n`` lives in a Q-vector space with the
basis ``{ prod_{i in S} sqrt(r_i) : S subset {1..n} }`` of dimension ``2^n``.
Expanding an element into that basis turns "what is the degree of this number?"
into linear algebra over the rationals, which we do exactly with Fractions.

That degree is what powers the classical impossibility results.  A constructible
number always has degree a power of two, so any target whose minimal polynomial
has degree 3 -- doubling the cube, trisecting 60 degrees, the regular heptagon --
is out of reach of straightedge and compass, and we can *say why* rather than
gesture at it.

Note the direction of the implication.  Degree not a power of two proves
impossibility outright.  Degree a power of two does **not** by itself prove
constructibility (the Galois closure has to cooperate too), so this module
never claims it does; when the machine asserts something is constructible it is
because :mod:`euclid.search` or :mod:`euclid.elements` actually built it.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Iterable, Optional

from .field import Constructible, Surd, is_zero

__all__ = [
    "FERMAT_PRIMES",
    "Verdict",
    "basis_expand",
    "cube_duplication_verdict",
    "degree",
    "heptagon_verdict",
    "min_poly",
    "ngon_verdict",
    "poly_str",
    "rational_roots",
    "trisection_verdict",
]

MAX_TOWER_DEPTH_FOR_DEGREE = 8

FERMAT_PRIMES = (3, 5, 17, 257, 65537)


# ---------------------------------------------------------------------------
# expansion into the rational basis of the tower
# ---------------------------------------------------------------------------


def basis_expand(x: Constructible) -> dict[frozenset[int], Fraction]:
    """Coordinates of ``x`` in the basis of square-root products.

    ``Surd(k, a, b)`` expands as ``expand(a) + expand(b) * sqrt(r_k)``; because
    ``a`` and ``b`` live strictly below level ``k`` their index sets never
    contain ``k``, so the two halves cannot collide.
    """
    if isinstance(x, Fraction):
        return {} if x == 0 else {frozenset(): x}
    result = dict(basis_expand(x.a))
    for indices, coefficient in basis_expand(x.b).items():
        result[indices | {x.level}] = coefficient
    return result


def _vector(x: Constructible, keys: list[frozenset[int]]) -> list[Fraction]:
    expansion = basis_expand(x)
    return [expansion.get(key, Fraction(0)) for key in keys]


def _all_keys(depth: int) -> list[frozenset[int]]:
    keys: list[frozenset[int]] = [frozenset()]
    for level in range(1, depth + 1):
        keys += [key | {level} for key in keys]
    return keys


def min_poly(x: Constructible) -> list[Fraction]:
    """Monic minimal polynomial of ``x`` over Q, as ascending coefficients.

    Powers of ``x`` are pushed through Gaussian elimination until one falls in
    the span of its predecessors; the dependency *is* the minimal polynomial.
    """
    if isinstance(x, Fraction):
        return [-x, Fraction(1)]
    depth = x.tower.depth
    if depth > MAX_TOWER_DEPTH_FOR_DEGREE:
        raise ValueError(
            f"tower depth {depth} exceeds the degree-computation limit "
            f"of {MAX_TOWER_DEPTH_FOR_DEGREE} (basis would have 2^{depth} entries)"
        )
    keys = _all_keys(depth)

    pivots: list[tuple[int, list[Fraction], list[Fraction]]] = []
    power: Constructible = Fraction(1)
    for exponent in range(len(keys) + 1):
        vector = _vector(power, keys)
        combination = [Fraction(0)] * (exponent + 1)
        combination[exponent] = Fraction(1)

        for index, pivot_row, pivot_combo in pivots:
            if vector[index]:
                factor = vector[index]
                vector = [v - factor * p for v, p in zip(vector, pivot_row)]
                for position, value in enumerate(pivot_combo):
                    combination[position] -= factor * value

        nonzero = next((i for i, value in enumerate(vector) if value), None)
        if nonzero is None:
            leading = combination[-1]
            return [c / leading for c in combination]

        scale = vector[nonzero]
        normalised_row = [v / scale for v in vector]
        normalised_combo = [c / scale for c in combination]
        pivots.append((nonzero, normalised_row, normalised_combo))
        power = power * x

    raise AssertionError("no linear dependence found within the tower dimension")


def degree(x: Constructible) -> int:
    """Degree of ``x`` over Q."""
    return len(min_poly(x)) - 1


def poly_str(coefficients: Iterable[Fraction], variable: str = "x") -> str:
    """Render ascending coefficients as a readable polynomial."""
    terms: list[str] = []
    for exponent, coefficient in reversed(list(enumerate(coefficients))):
        if coefficient == 0:
            continue
        magnitude = abs(coefficient)
        if exponent == 0:
            body = str(magnitude)
        else:
            power = variable if exponent == 1 else f"{variable}^{exponent}"
            body = power if magnitude == 1 else f"{magnitude}*{power}"
        sign_text = "-" if coefficient < 0 else "+"
        terms.append(f"{sign_text} {body}" if terms else (f"-{body}" if coefficient < 0 else body))
    return " ".join(terms) if terms else "0"


# ---------------------------------------------------------------------------
# integer polynomial helpers, enough for the classical impossibilities
# ---------------------------------------------------------------------------


def _divisors(n: int) -> list[int]:
    n = abs(n)
    found = []
    candidate = 1
    while candidate * candidate <= n:
        if n % candidate == 0:
            found.append(candidate)
            if candidate != n // candidate:
                found.append(n // candidate)
        candidate += 1
    return sorted(found)


def rational_roots(coefficients: list[int]) -> list[Fraction]:
    """All rational roots of an integer polynomial, by the rational root theorem."""
    while coefficients and coefficients[-1] == 0:
        coefficients = coefficients[:-1]
    if not coefficients:
        raise ValueError("the zero polynomial has every rational as a root")
    shift = 0
    while coefficients[shift] == 0:
        shift += 1
    roots = [Fraction(0)] if shift else []
    trimmed = coefficients[shift:]
    for numerator in _divisors(trimmed[0]):
        for denominator in _divisors(trimmed[-1]):
            for candidate in (Fraction(numerator, denominator), Fraction(-numerator, denominator)):
                if candidate in roots:
                    continue
                value = sum(c * candidate**i for i, c in enumerate(trimmed))
                if value == 0:
                    roots.append(candidate)
    return sorted(roots)


def _is_irreducible_cubic(coefficients: list[int]) -> bool:
    """A cubic over Q is irreducible exactly when it has no rational root."""
    assert len(coefficients) == 4 and coefficients[-1] != 0
    return not rational_roots(coefficients)


class Verdict:
    """The result of an impossibility question, with its reasoning."""

    __slots__ = ("question", "possible", "reason", "polynomial", "algebraic_degree")

    def __init__(
        self,
        question: str,
        possible: bool,
        reason: str,
        polynomial: Optional[str] = None,
        algebraic_degree: Optional[int] = None,
    ) -> None:
        self.question = question
        self.possible = possible
        self.reason = reason
        self.polynomial = polynomial
        self.algebraic_degree = algebraic_degree

    def __repr__(self) -> str:
        verdict = "CONSTRUCTIBLE" if self.possible else "IMPOSSIBLE"
        return f"<{verdict}: {self.question}>"

    def report(self) -> str:
        lines = [f"{self.question}", ""]
        lines.append("  verdict   : " + ("constructible" if self.possible else "impossible"))
        if self.polynomial:
            lines.append(f"  minimal   : {self.polynomial} = 0")
        if self.algebraic_degree is not None:
            lines.append(f"  degree    : {self.algebraic_degree} over Q")
        lines.append(f"  reason    : {self.reason}")
        return "\n".join(lines)


def _cubic_verdict(question: str, coefficients: list[int], target: str) -> Verdict:
    irreducible = _is_irreducible_cubic(coefficients)
    polynomial = poly_str([Fraction(c) for c in coefficients])
    if not irreducible:
        return Verdict(question, True, f"{target} satisfies a reducible cubic", polynomial, None)
    return Verdict(
        question,
        False,
        f"{target} has degree 3 over Q (the cubic is irreducible, having no rational root), "
        "and 3 is not a power of 2; every constructible number has degree a power of 2, "
        "because each straightedge-and-compass step adjoins at most a square root",
        polynomial,
        3,
    )


def cube_duplication_verdict() -> Verdict:
    return _cubic_verdict(
        "Can a cube be doubled with straightedge and compass?",
        [-2, 0, 0, 1],
        "the edge ratio cbrt(2)",
    )


def trisection_verdict() -> Verdict:
    return _cubic_verdict(
        "Can an arbitrary angle be trisected with straightedge and compass?",
        [-1, -6, 0, 8],
        "cos(20 degrees), a third of the constructible 60-degree angle,",
    )


def heptagon_verdict() -> Verdict:
    return _cubic_verdict(
        "Can a regular heptagon be constructed with straightedge and compass?",
        [-1, -2, 1, 1],
        "2*cos(2*pi/7)",
    )


# ---------------------------------------------------------------------------
# Gauss-Wantzel: regular polygons
# ---------------------------------------------------------------------------


def _prime_factors(n: int) -> dict[int, int]:
    factors: dict[int, int] = {}
    remaining = n
    divisor = 2
    while divisor * divisor <= remaining:
        while remaining % divisor == 0:
            factors[divisor] = factors.get(divisor, 0) + 1
            remaining //= divisor
        divisor += 1
    if remaining > 1:
        factors[remaining] = factors.get(remaining, 0) + 1
    return factors


def ngon_verdict(n: int) -> Verdict:
    """Gauss-Wantzel: the regular n-gon is constructible iff n = 2^k times a
    product of distinct Fermat primes.  Unlike the degree test this is an
    equivalence, so both answers are conclusive."""
    question = f"Is the regular {n}-gon constructible with straightedge and compass?"
    if n < 3:
        return Verdict(question, False, f"{n} sides is not a polygon")

    factors = _prime_factors(n)
    odd_primes = {p: e for p, e in factors.items() if p != 2}
    repeated = [p for p, e in odd_primes.items() if e > 1]
    non_fermat = [p for p in odd_primes if p not in FERMAT_PRIMES]

    twos = factors.get(2, 0)
    shape = " * ".join(
        ([f"2^{twos}"] if twos else []) + [str(p) if e == 1 else f"{p}^{e}" for p, e in sorted(odd_primes.items())]
    ) or "1"

    if repeated:
        culprit = repeated[0]
        return Verdict(
            question,
            False,
            f"{n} = {shape}, and the odd prime {culprit} is repeated; Gauss-Wantzel requires "
            "the odd part to be a product of *distinct* Fermat primes",
        )
    if non_fermat:
        culprit = sorted(non_fermat)[0]
        return Verdict(
            question,
            False,
            f"{n} = {shape}, and {culprit} is not a Fermat prime "
            f"(the known ones are {', '.join(map(str, FERMAT_PRIMES))}); "
            "Gauss-Wantzel therefore rules the polygon out",
        )
    used = ", ".join(str(p) for p in sorted(odd_primes)) or "none"
    return Verdict(
        question,
        True,
        f"{n} = {shape}: a power of two times distinct Fermat primes ({used}), "
        "so Gauss-Wantzel guarantees a construction exists",
    )
