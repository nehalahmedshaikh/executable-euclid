"""Book X: Euclid's taxonomy of irrational magnitudes, as a working classifier.

Book X is the longest book in the *Elements*, 115 propositions, and the one
everyone skips.  Its subject is a classification of the irrational magnitudes
that straightedge and compass produce -- thirteen named species, built up from
sums and differences of square roots, each with its own construction and its
own theorem.  Stephen Barrow called it "the cross of mathematicians"; most
modern editions summarise it in a paragraph and move on.

The reason it reads as impenetrable prose is that it is written about objects
nobody could compute with.  We can.  The kernel already represents exactly the
magnitudes Book X is about -- iterated square roots over the rationals -- so
Euclid's definitions become predicates and his taxonomy becomes a function.

The scheme, with the assigned rational line taken as 1:

* **rational** -- commensurable in length with the assigned line, or (Euclid's
  wider use) in square only, so that its square is rational;
* **medial** (X.21) -- the mean proportional between two rational lines
  commensurable in square only, so ``x^2`` is irrational but ``x^4`` rational;
* **binomial** (X.36) and **apotome** (X.73) -- the sum and difference of two
  rational lines commensurable in square only, each falling into one of six
  species (X.48-53, X.85-90) according to which term is commensurable with the
  assigned line and whether ``sqrt(a^2 - b^2)`` is commensurable with the
  greater;
* the medial-based species -- **first and second bimedial** (X.37-38), **major**
  (X.39), **the side of a rational plus a medial area** (X.40), **the side of
  the sum of two medial areas** (X.41), and the corresponding apotomes.

Every one of those conditions is a question about rationality of a product or a
sum, and the kernel decides each one exactly.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Optional

from ..kernel.field import Constructible, Surd, is_zero, sign, sqrt
from ..kernel.minpoly import basis_expand, degree
from .registry import THEOREM, Out, claim, hypothesis, proposition

__all__ = [
    "Classification",
    "classify",
    "commensurable",
    "commensurable_in_square",
    "is_medial",
    "is_rational_line",
    "is_rational_in_square",
    "terms_of",
]


# ---------------------------------------------------------------------------
# Book X's basic predicates, with the assigned rational line taken as 1
# ---------------------------------------------------------------------------


def is_rational_line(x: Constructible) -> bool:
    """Commensurable in length with the assigned line."""
    return isinstance(x, Fraction)


def is_rational_in_square(x: Constructible) -> bool:
    """Euclid's wider 'rational': the square is commensurable with the assigned square."""
    return isinstance(x * x, Fraction)


def is_medial(x: Constructible) -> bool:
    """X.21: the side of a medial area -- ``x^2`` irrational but ``x^4`` rational."""
    square = x * x
    return not isinstance(square, Fraction) and isinstance(square * square, Fraction)


def commensurable(x: Constructible, y: Constructible) -> bool:
    if is_zero(y):
        return False
    return isinstance(x / y, Fraction)


def commensurable_in_square(x: Constructible, y: Constructible) -> bool:
    if is_zero(y):
        return False
    return isinstance((x * x) / (y * y), Fraction)


# ---------------------------------------------------------------------------
# decomposing a magnitude into its terms
# ---------------------------------------------------------------------------


def terms_of(x: Constructible) -> list[Constructible]:
    """Split ``x`` into the terms of its expansion over the tower's rational basis.

    A binomial such as ``3 + sqrt 7`` comes back as two terms; ``sqrt 2 + sqrt 3``
    also comes back as two, even though neither is rational.  This is exactly
    the decomposition Book X's definitions are phrased in terms of.
    """
    if isinstance(x, Fraction):
        return [x] if x != 0 else []
    tower = x.tower
    pieces: list[Constructible] = []
    for indices, coefficient in basis_expand(x).items():
        value: Constructible = coefficient
        for level in sorted(indices):
            value = value * Surd(tower, level, Fraction(0), Fraction(1))
        pieces.append(value)
    pieces.sort(key=lambda term: (sign(term) < 0, -abs(float(term))))
    return pieces


# ---------------------------------------------------------------------------
# the classification
# ---------------------------------------------------------------------------

BINOMIAL_SPECIES = ("first", "second", "third", "fourth", "fifth", "sixth")


class Classification:
    """What Book X calls a magnitude, and why."""

    __slots__ = ("value", "name", "family", "species", "reason", "terms", "algebraic_degree")

    def __init__(
        self,
        value: Constructible,
        name: str,
        family: str,
        reason: str,
        terms: Optional[list] = None,
        species: Optional[str] = None,
        algebraic_degree: Optional[int] = None,
    ) -> None:
        self.value = value
        self.name = name
        self.family = family
        self.species = species
        self.reason = reason
        self.terms = terms or []
        self.algebraic_degree = algebraic_degree

    def __repr__(self) -> str:
        return f"<{self.name}>"

    def report(self) -> str:
        from ..kernel.field import fmt, to_float

        lines = [f"{fmt(self.value)}   ~ {to_float(self.value):.10f}", ""]
        lines.append(f"  Book X calls this : {self.name}")
        if self.species:
            lines.append(f"  species           : {self.species}")
        if self.algebraic_degree:
            lines.append(f"  degree over Q     : {self.algebraic_degree}")
        if self.terms:
            joined = "   and   ".join(fmt(term) for term in self.terms)
            lines.append(f"  terms             : {joined}")
        lines.append(f"  because           : {self.reason}")
        return "\n".join(lines)


def _binomial_species(greater: Constructible, lesser: Constructible) -> tuple[str, str]:
    """Which of the six species (X.48-53) this binomial or apotome belongs to."""
    difference = greater * greater - lesser * lesser
    root = sqrt(difference) if sign(difference) > 0 else Fraction(0)
    aligned = commensurable(root, greater)

    if is_rational_line(greater):
        index = 0 if aligned else 3
        which = "the greater term is commensurable in length with the assigned line"
    elif is_rational_line(lesser):
        index = 1 if aligned else 4
        which = "the lesser term is commensurable in length with the assigned line"
    else:
        index = 2 if aligned else 5
        which = "neither term is commensurable in length with the assigned line"

    tail = (
        "and sqrt(a^2 - b^2) is commensurable in length with the greater"
        if aligned
        else "and sqrt(a^2 - b^2) is incommensurable with the greater"
    )
    return BINOMIAL_SPECIES[index], f"{which}, {tail}"


def _two_term_classification(
    value: Constructible, greater: Constructible, lesser: Constructible, subtractive: bool
) -> Classification:
    magnitude = -lesser if subtractive else lesser
    squares_sum = greater * greater + magnitude * magnitude
    rectangle = greater * magnitude

    both_rational_in_square = is_rational_in_square(greater) and is_rational_in_square(magnitude)
    both_medial = is_medial(greater) and is_medial(magnitude)

    if both_rational_in_square and not commensurable(greater, magnitude):
        species, why = _binomial_species(greater, magnitude)
        family = "apotome" if subtractive else "binomial"
        article = f"{species} {family}"
        reference = "X.73, X.85-90" if subtractive else "X.36, X.48-53"
        return Classification(
            value,
            article,
            family,
            f"it is the {'difference' if subtractive else 'sum'} of two rational lines "
            f"commensurable in square only ({reference}); {why}",
            [greater, magnitude],
            species,
        )

    if both_medial and not commensurable(greater, magnitude):
        if is_rational_line(rectangle):
            name = "first apotome of a medial line" if subtractive else "first bimedial"
            why = "the rectangle they contain is rational (X.37, X.74)"
        elif is_medial(rectangle):
            name = "second apotome of a medial line" if subtractive else "second bimedial"
            why = "the rectangle they contain is medial (X.38, X.75)"
        else:
            name = "a medial-based irrational outside Euclid's named species"
            why = "the rectangle they contain is neither rational nor medial"
        return Classification(
            value, name, "medial-based", f"both terms are medial and {why}",
            [greater, magnitude],
        )

    if not commensurable_in_square(greater, magnitude):
        rational_sum = isinstance(squares_sum, Fraction)
        medial_sum = is_medial(sqrt(squares_sum)) if sign(squares_sum) > 0 else False
        rational_rect = is_rational_line(rectangle)
        medial_rect = is_medial(rectangle)

        if rational_sum and medial_rect:
            name = "minor" if subtractive else "major"
            why = "the sum of their squares is rational and the rectangle medial (X.39, X.76)"
        elif medial_sum and rational_rect:
            name = (
                "that which produces with a rational area a medial whole"
                if subtractive
                else "the side of a rational plus a medial area"
            )
            why = "the sum of their squares is medial and the rectangle rational (X.40, X.77)"
        elif medial_sum and medial_rect:
            name = (
                "that which produces with a medial area a medial whole"
                if subtractive
                else "the side of the sum of two medial areas"
            )
            why = "both the sum of their squares and the rectangle are medial (X.41, X.78)"
        else:
            name = "an irrational outside Euclid's thirteen species"
            why = "the sum of the squares and the rectangle fit none of the patterns"
        return Classification(
            value, name, "medial-based", f"the terms are incommensurable in square, and {why}",
            [greater, magnitude],
        )

    return Classification(
        value,
        "an irrational outside Euclid's thirteen species",
        "unclassified",
        "the two terms are commensurable, so the magnitude is not one of the "
        "compound irrationals Book X names",
        [greater, magnitude],
    )


def classify(x: Constructible) -> Classification:
    """Name a magnitude in Euclid's own vocabulary."""
    if sign(x) <= 0:
        raise ValueError("Book X classifies magnitudes, which are positive")

    if is_rational_line(x):
        return Classification(
            x, "rational", "rational",
            "it is commensurable in length with the assigned rational line", [x],
            algebraic_degree=1,
        )

    order = degree(x)

    if is_rational_in_square(x):
        return Classification(
            x, "rational (commensurable in square only)", "rational",
            "its square is commensurable with the square on the assigned line, though "
            "the line itself is not -- Euclid still calls such a line rational (X.Def.3)",
            [x], algebraic_degree=order,
        )

    if is_medial(x):
        return Classification(
            x, "medial", "medial",
            "its square is a medial area: irrational, but with rational square in turn, "
            "so the line is the mean proportional between two rational lines "
            "commensurable in square only (X.21)",
            [x], algebraic_degree=order,
        )

    pieces = terms_of(x)
    if len(pieces) == 2:
        greater, lesser = pieces
        result = _two_term_classification(x, greater, lesser, sign(lesser) < 0)
        result.algebraic_degree = order
        return result

    return Classification(
        x,
        "an irrational outside Euclid's thirteen species",
        "unclassified",
        f"it resolves into {len(pieces)} terms, where Book X's definitions treat two",
        pieces,
        algebraic_degree=order,
    )


# ---------------------------------------------------------------------------
# propositions
# ---------------------------------------------------------------------------


def _rational_pair_in_square_only(rng):
    first = Fraction(rng.randint(1, 6), rng.randint(1, 3))
    radicand = rng.choice([2, 3, 5, 6, 7, 10, 11])
    second = Fraction(rng.randint(1, 4), rng.randint(1, 3)) * sqrt(radicand)
    return first, second


@proposition(
    "X.21",
    "The rectangle contained by rational straight lines commensurable in square only is "
    "irrational, and the side of the square equal to it is irrational; let it be called "
    "medial.",
    THEOREM,
    sample=_rational_pair_in_square_only,
)
def prop_X_21(a, b) -> Out:
    hypothesis("both lines are rational in square", is_rational_in_square(a) and is_rational_in_square(b))
    hypothesis("they are commensurable in square only", not commensurable(a, b))
    rectangle = a * b
    side = sqrt(rectangle)
    claim("the rectangle they contain is irrational", "X.Def.4",
          not isinstance(rectangle, Fraction))
    claim("the side of the equal square is medial", "X.21", is_medial(side))
    claim("and the classifier names it so", "X.21", classify(side).name == "medial")
    return Out(medial=side)


@proposition(
    "X.36",
    "If two rational straight lines commensurable in square only are added together, then "
    "the whole is irrational; let it be called binomial.",
    THEOREM,
    sample=_rational_pair_in_square_only,
)
def prop_X_36(a, b) -> Out:
    hypothesis("both lines are rational in square", is_rational_in_square(a) and is_rational_in_square(b))
    hypothesis("they are commensurable in square only", not commensurable(a, b))
    whole = a + b
    claim("the whole is irrational", "X.36", not isinstance(whole, Fraction))
    named = classify(whole)
    claim("Book X calls it a binomial", "X.36", named.family == "binomial")
    claim("and assigns it one of the six species", "X.48-53",
          named.species in ("first", "second", "third", "fourth", "fifth", "sixth"))
    return Out(binomial=whole, species=named.species)


@proposition(
    "X.73",
    "If from a rational straight line there is subtracted a rational straight line "
    "commensurable with the whole in square only, then the remainder is irrational; let "
    "it be called an apotome.",
    THEOREM,
    sample=_rational_pair_in_square_only,
)
def prop_X_73(a, b) -> Out:
    hypothesis("both lines are rational in square", is_rational_in_square(a) and is_rational_in_square(b))
    hypothesis("they are commensurable in square only", not commensurable(a, b))
    greater, lesser = (a, b) if sign(a - b) > 0 else (b, a)
    remainder = greater - lesser
    claim("the remainder is irrational", "X.73", not isinstance(remainder, Fraction))
    named = classify(remainder)
    claim("Book X calls it an apotome", "X.73", named.family == "apotome")
    claim("and assigns it one of the six species", "X.85-90",
          named.species in ("first", "second", "third", "fourth", "fifth", "sixth"))
    return Out(apotome=remainder, species=named.species)


def _medial_pair(rng):
    """Two medials commensurable in square only, containing a rational rectangle.

    Taking ``k^(1/4)`` and ``k^(3/4)`` does it: each is medial, their ratio is
    the irrational ``sqrt k`` so they are incommensurable in length, their
    squares are in rational ratio, and their rectangle is the rational ``k``.
    """
    radicand = rng.choice([2, 3, 5, 7])
    quarter = sqrt(sqrt(radicand))
    first = Fraction(rng.randint(1, 4), rng.randint(1, 3)) * quarter
    second = Fraction(rng.randint(1, 4), rng.randint(1, 3)) * sqrt(radicand) * quarter
    return first, second


@proposition(
    "X.37",
    "If two medial straight lines commensurable in square only and containing a rational "
    "rectangle are added together, then the whole is irrational; let it be called a first "
    "bimedial straight line.",
    THEOREM,
    sample=_medial_pair,
)
def prop_X_37(a, b) -> Out:
    hypothesis("both lines are medial", is_medial(a) and is_medial(b))
    hypothesis("they are commensurable in square only", not commensurable(a, b))
    hypothesis("the rectangle they contain is rational", is_rational_line(a * b))
    whole = a + b
    claim("the whole is irrational", "X.37", not isinstance(whole, Fraction))
    claim("and it is a first bimedial", "X.37", classify(whole).name == "first bimedial")
    return Out(bimedial=whole)
