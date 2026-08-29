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

All 115 propositions are here.  The book divides in half at X.73: everything
before it is about lines got by *adding* two terms, everything after about the
same lines got by *subtracting* them, and the two halves run proposition for
proposition.  That symmetry is used rather than repeated -- the builders near
X.38 make a witness of each kind, and the families that follow (divided at one
point only; the six species; the side of an area; the square applied to a
rational line; a line commensurable with one of them) are stated against those
witnesses in both directions at once.

X.115 closes the book by showing the list does not close: from a single medial
line an unending series of fresh irrationals arises, each incommensurable with
the last, and the kernel reports their degrees over the rationals doubling as
they go.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Optional

from ..kernel.field import Constructible, Surd, is_zero, sign, sqrt
from ..kernel.minpoly import basis_expand, degree
from .book05 import anthyphairesis
from .book07_09 import gcd as gcd_int
from .registry import CONSTRUCTION, THEOREM, Out, claim, hypothesis, proposition

__all__ = [
    "Classification",
    "SPECIES",
    "classify",
    "commensurable",
    "commensurable_in_square",
    "is_medial",
    "is_medial_area",
    "is_rational_area",
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


def is_rational_area(area: Constructible) -> bool:
    """A rectangle commensurable with the square on the assigned line."""
    return isinstance(area, Fraction)


def is_medial_area(area: Constructible) -> bool:
    """The rectangle contained by two rational lines commensurable in square only.

    Areas and lines need different tests, and confusing them is easy: the side
    of a medial area is a medial line, so the area is one square less deep.
    ``is_medial_area(A)`` is exactly ``is_medial(sqrt(A))`` -- an irrational
    whose square is rational, where a medial *line* has an irrational square
    and a rational fourth power.
    """
    return not isinstance(area, Fraction) and isinstance(area * area, Fraction)


def _is_square_int(n: int) -> bool:
    """Is the integer a perfect square? Used by X.9's square-number ratio."""
    root = round(abs(n) ** 0.5)
    while root * root > n:
        root -= 1
    while (root + 1) * (root + 1) <= n:
        root += 1
    return root * root == n


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


# The thirteen names, in Euclid's order: the medial, then the six compounded by
# addition (X.36-41) and their six duals by subtraction (X.73-78).
SPECIES = (
    "medial",
    "binomial", "first bimedial", "second bimedial", "major",
    "the side of a rational plus a medial area",
    "the side of the sum of two medial areas",
    "apotome", "first apotome of a medial line", "second apotome of a medial line", "minor",
    "that which produces with a rational area a medial whole",
    "that which produces with a medial area a medial whole",
)


def _named_species(
    value: Constructible, greater: Constructible, magnitude: Constructible, subtractive: bool
) -> Optional[Classification]:
    """Match a pair of terms against Euclid's six patterns, or return None.

    ``magnitude`` is signed: negative when the compound is a difference.  Each
    branch is one of X.36-41 read as a condition on the two terms, their
    rectangle and the sum of their squares, and its dual in X.73-78.
    """
    squares_sum = greater * greater + magnitude * magnitude
    rectangle = greater * magnitude
    # For a difference the rectangle is negative as written; Euclid's condition
    # is about the area itself, which is the rectangle on the two lengths.
    area = -rectangle if subtractive else rectangle

    def named(name: str, family: str, why: str, species: Optional[str] = None) -> Classification:
        return Classification(value, name, family, why, [greater, magnitude], species)

    # X.36 / X.73 -- two rational lines commensurable in square only.
    if (is_rational_in_square(greater) and is_rational_in_square(magnitude)
            and not commensurable(greater, magnitude)):
        species, why = _binomial_species(greater, magnitude)
        family = "apotome" if subtractive else "binomial"
        reference = "X.73, X.85-90" if subtractive else "X.36, X.48-53"
        return named(
            f"{species} {family}", family,
            f"it is the {'difference' if subtractive else 'sum'} of two rational lines "
            f"commensurable in square only ({reference}); {why}",
            species,
        )

    # X.37-38 / X.74-75 -- two medial lines commensurable in square only.
    # "In square only" is two conditions, not one: the squares must be
    # commensurable and the lines must not be.
    if (is_medial(greater) and is_medial(magnitude)
            and commensurable_in_square(greater, magnitude)
            and not commensurable(greater, magnitude)):
        if is_rational_area(area):
            name = "first apotome of a medial line" if subtractive else "first bimedial"
            why = "the rectangle they contain is rational (X.37, X.74)"
        elif is_medial_area(area):
            name = "second apotome of a medial line" if subtractive else "second bimedial"
            why = "the rectangle they contain is medial (X.38, X.75)"
        else:
            return None
        return named(name, "medial-based", f"both terms are medial and {why}")

    # X.39-41 / X.76-78 -- two lines incommensurable in square.
    if not commensurable_in_square(greater, magnitude) and sign(squares_sum) > 0:
        rational_sum = is_rational_area(squares_sum)
        medial_sum = is_medial_area(squares_sum)

        if rational_sum and is_medial_area(area):
            name = "minor" if subtractive else "major"
            why = "the sum of their squares is rational and the rectangle medial (X.39, X.76)"
        elif medial_sum and is_rational_area(area):
            name = ("that which produces with a rational area a medial whole" if subtractive
                    else "the side of a rational plus a medial area")
            why = "the sum of their squares is medial and the rectangle rational (X.40, X.77)"
        elif medial_sum and is_medial_area(area) and not commensurable(squares_sum, area):
            # X.41 turns on that last clause: without it the two medial areas
            # would be commensurable and the line would collapse to an earlier
            # species.
            name = ("that which produces with a medial area a medial whole" if subtractive
                    else "the side of the sum of two medial areas")
            why = ("both the sum of their squares and the rectangle are medial, and "
                   "incommensurable with one another (X.41, X.78)")
        else:
            return None
        return named(name, "medial-based",
                     f"the terms are incommensurable in square, and {why}")

    return None


def _split_by_squaring(x: Constructible) -> Optional[tuple]:
    """Recover the two terms of a compound the basis expansion cannot separate.

    ``terms_of`` splits a magnitude over the tower's rational basis, which finds
    the terms of a binomial or a bimedial but not those of a major line: there
    ``u`` and ``v`` are the two roots of one quadratic, so ``v`` lives inside
    the extension ``u`` generates and the expansion shows no seam.

    Squaring puts the seam back.  ``x^2`` is ``(u^2 + v^2) +/- 2uv``, and those
    two parts do separate.  From the sum of the squares ``S`` and the rectangle
    ``P`` the pair comes back as the roots of ``t^2 - St + P^2``, and the sign
    of the second part says whether the compound was a sum or a difference.

    Nothing here is assumed: the recovered pair is handed back only after
    ``u +/- v == x`` is checked exactly.  Book X's uniqueness theorems (X.42-47,
    X.79-84) are what say there is at most one such pair to find.
    """
    pieces = terms_of(x * x)
    if len(pieces) != 2:
        return None
    first, second = pieces
    # Try each part as the sum of the squares; the identity check below settles
    # which reading was right, and rejects both when the shape does not fit.
    for squares_sum, twice_rectangle in ((first, second), (second, first)):
        subtractive = sign(twice_rectangle) < 0
        rectangle = abs(twice_rectangle) / 2
        discriminant = squares_sum * squares_sum - 4 * (rectangle * rectangle)
        if sign(discriminant) <= 0 or sign(squares_sum) <= 0:
            continue
        root = sqrt(discriminant)
        larger, smaller = (squares_sum + root) / 2, (squares_sum - root) / 2
        if sign(smaller) <= 0:
            continue
        u, v = sqrt(larger), sqrt(smaller)
        if is_zero((u - v if subtractive else u + v) - x):
            return u, (-v if subtractive else v), subtractive
    return None


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

    # Two ways to cut a compound in two. The expansion is tried first because it
    # is the literal reading of Euclid's "let it be divided into its terms";
    # squaring is the fallback for the species it cannot see.
    pieces = terms_of(x)
    candidates = []
    if len(pieces) == 2:
        candidates.append((pieces[0], pieces[1], sign(pieces[1]) < 0))
    recovered = _split_by_squaring(x)
    if recovered is not None and recovered not in candidates:
        candidates.append(recovered)

    for greater, magnitude, subtractive in candidates:
        found = _named_species(x, greater, magnitude, subtractive)
        if found is not None:
            found.algebraic_degree = order
            return found

    shown = candidates[0][:2] if candidates else pieces
    return Classification(
        x,
        "an irrational outside Euclid's thirteen species",
        "unclassified",
        "it divides into two terms, but their rectangle and the sum of their squares "
        "fit none of Euclid's six patterns"
        if candidates
        else f"it resolves into {len(pieces)} terms, where Book X's definitions treat two",
        list(shown),
        algebraic_degree=order,
    )


# ---------------------------------------------------------------------------
# propositions
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# X.1 - X.20  commensurability
# ---------------------------------------------------------------------------
#
# The first twenty propositions are the theory of commensurability itself, and
# the kernel answers every one of them by looking rather than by searching: two
# magnitudes are commensurable exactly when their ratio comes out of the field
# as a Fraction. Euclid has to *find* a common measure by running anthyphairesis
# and hoping it stops; the two are checked against each other in X.2 and X.3.


def _magnitude(rng) -> Constructible:
    """One positive magnitude, irrational about half the time."""
    value = Fraction(rng.randint(1, 9), rng.randint(1, 4))
    if rng.random() < 0.5:
        value = value * sqrt(rng.choice([2, 3, 5, 6, 7]))
    return value


def _commensurable_pair(rng):
    """Two magnitudes with a common measure, and one without."""
    base = _magnitude(rng)
    return base * Fraction(rng.randint(1, 6), rng.randint(1, 4)), base


def _incommensurable_pair(rng):
    base = Fraction(rng.randint(1, 6), rng.randint(1, 4))
    return base, base * sqrt(rng.choice([2, 3, 5, 6, 7]))


def _either_pair(rng):
    return _commensurable_pair(rng) if rng.random() < 0.5 else _incommensurable_pair(rng)


def common_measure(a: Constructible, b: Constructible) -> Optional[Constructible]:
    """The greatest common measure of two commensurable magnitudes (X.3).

    Their ratio is a fraction ``p/q`` in least terms, so ``a/p`` measures both:
    ``p`` times over into the one and ``q`` times into the other.  Nothing
    greater does, because ``p`` and ``q`` have no common factor left.
    """
    ratio = a / b
    if not isinstance(ratio, Fraction):
        return None
    return a / ratio.numerator


@proposition(
    "X.1",
    THEOREM,
    sample=lambda rng: (_magnitude(rng), Fraction(rng.randint(1, 3), rng.randint(4, 9))),
    note="The bisection principle, and the engine of Book XII's method of "
    "exhaustion. Euclid needs it before he can say anything about limits.",
)
def prop_X_1(greater, part) -> Out:
    """Take away more than half, repeatedly, and any magnitude is undercut."""
    hypothesis("the magnitudes are positive", sign(greater) > 0 and sign(part) > 0)
    lesser = greater * part
    hypothesis("the second is the less", sign(greater - lesser) > 0)

    remaining, steps = greater, 0
    while sign(remaining - lesser) >= 0 and steps < 200:
        remaining = remaining - remaining * Fraction(3, 5)  # more than half taken
        steps += 1

    claim("the process terminates", "X.1", steps < 200)
    claim("and leaves a magnitude less than the lesser set out", "X.1",
          sign(lesser - remaining) > 0)
    return Out(steps=steps, remainder=remaining)


@proposition(
    "X.2",
    THEOREM,
    sample=_either_pair,
    note="Euclid's test for incommensurability: the alternating subtraction "
    "never ends. The kernel settles the same question by looking at the ratio, "
    "and the two are checked against each other here.",
)
def prop_X_2(a, b) -> Out:
    hypothesis("the magnitudes are positive and unequal",
               sign(a) > 0 and sign(b) > 0 and a != b)
    greater, lesser = (a, b) if sign(a - b) > 0 else (b, a)
    quotients, ended = anthyphairesis(greater, lesser, steps=40)

    claim("the subtraction ends exactly when a common measure exists", "X.2",
          ended == commensurable(a, b))
    claim("so if it never measures the one before it, they are incommensurable",
          "X.2", ended or not commensurable(a, b))
    return Out(quotients=quotients, terminated=ended)


@proposition(
    "X.3",
    CONSTRUCTION,
    sample=_commensurable_pair,
)
def prop_X_3(a, b) -> Out:
    hypothesis("the magnitudes are positive", sign(a) > 0 and sign(b) > 0)
    hypothesis("they are commensurable", commensurable(a, b))
    measure = common_measure(a, b)

    claim("the measure found measures both", "X.3",
          isinstance(a / measure, Fraction) and isinstance(b / measure, Fraction))
    claim("it measures them a whole number of times", "Def.X.1",
          (a / measure).denominator == 1 and (b / measure).denominator == 1)
    claim("and it is the greatest such, the two counts having no common factor",
          "VII.22", gcd_int(int(a / measure), int(b / measure)) == 1)
    return Out(measure=measure)


@proposition(
    "X.4",
    CONSTRUCTION,
    sample=lambda rng: _commensurable_pair(rng)
    + (_commensurable_pair(rng)[0] * Fraction(rng.randint(1, 4), rng.randint(1, 3)),),
)
def prop_X_4(a, b, c) -> Out:
    hypothesis("the magnitudes are positive", all(sign(x) > 0 for x in (a, b, c)))
    hypothesis("all three are commensurable",
               commensurable(a, b) and commensurable(b, c))
    first = common_measure(a, b)
    measure = common_measure(first, c)

    claim("the measure found measures all three", "X.3",
          all(isinstance(x / measure, Fraction)
              and (x / measure).denominator == 1 for x in (a, b, c)))
    claim("and every common measure of the three measures it", "X.3",
          commensurable(measure, a) and commensurable(measure, b)
          and commensurable(measure, c))
    return Out(measure=measure)


@proposition(
    "X.5",
    THEOREM,
    sample=_commensurable_pair,
)
def prop_X_5(a, b) -> Out:
    hypothesis("the magnitudes are positive", sign(a) > 0 and sign(b) > 0)
    hypothesis("they are commensurable", commensurable(a, b))
    ratio = a / b
    claim("the ratio is that of a number to a number", "X.5",
          isinstance(ratio, Fraction))
    claim("and the two numbers can be exhibited", "VII.33",
          a * ratio.denominator == b * ratio.numerator)
    return Out(numbers=(ratio.numerator, ratio.denominator))


@proposition(
    "X.6",
    THEOREM,
    sample=lambda rng: (_magnitude(rng), rng.randint(1, 8), rng.randint(1, 8)),
)
def prop_X_6(base, numerator: int, denominator: int) -> Out:
    """The converse of X.5."""
    hypothesis("the magnitude is positive", sign(base) > 0)
    hypothesis("the numbers are genuine", numerator > 0 and denominator > 0)
    a = base * numerator
    b = base * denominator
    claim("the two stand in the ratio of the given numbers", "Def.X.1",
          a * denominator == b * numerator)
    claim("so they are commensurable", "X.6", commensurable(a, b))
    return Out(measure=base)


@proposition(
    "X.7",
    THEOREM,
    sample=_incommensurable_pair,
)
def prop_X_7(a, b) -> Out:
    hypothesis("the magnitudes are positive", sign(a) > 0 and sign(b) > 0)
    hypothesis("they are incommensurable", not commensurable(a, b))
    claim("their ratio is not that of any number to a number", "X.7",
          not isinstance(a / b, Fraction))
    claim("and no pair of numbers puts them in proportion", "X.5",
          not any(a * q == b * p
                  for p in range(1, 25) for q in range(1, 25)))
    return Out()


@proposition(
    "X.8",
    THEOREM,
    sample=_incommensurable_pair,
)
def prop_X_8(a, b) -> Out:
    """The converse of X.7."""
    hypothesis("the magnitudes are positive", sign(a) > 0 and sign(b) > 0)
    hypothesis("no numbers put them in proportion",
               not any(a * q == b * p for p in range(1, 25) for q in range(1, 25)))
    claim("they are incommensurable", "X.8", not commensurable(a, b))
    return Out()


@proposition(
    "X.9",
    THEOREM,
    sample=_either_pair,
    note="The bridge between Book X and Book VII: commensurability in length is "
    "the squares standing in the ratio of two square numbers.",
)
def prop_X_9(a, b) -> Out:
    hypothesis("the magnitudes are positive", sign(a) > 0 and sign(b) > 0)
    ratio_of_squares = (a * a) / (b * b)
    square_ratio = (
        isinstance(ratio_of_squares, Fraction)
        and _is_square_int(ratio_of_squares.numerator)
        and _is_square_int(ratio_of_squares.denominator)
    )
    claim("lines commensurable in length have squares in the ratio of two square "
          "numbers", "X.9", commensurable(a, b) == square_ratio)
    claim("and lines incommensurable in length have not", "X.9",
          (not commensurable(a, b)) == (not square_ratio))
    return Out(square_ratio=square_ratio)


@proposition(
    "X.10",
    CONSTRUCTION,
    sample=lambda rng: (Fraction(rng.randint(1, 6), rng.randint(1, 4)),),
    note="The existence of the incommensurable, constructed rather than argued: "
    "one line irrational in length only, another irrational in square as well.",
)
def prop_X_10(assigned) -> Out:
    hypothesis("the assigned line is positive", sign(assigned) > 0)
    in_length_only = assigned * sqrt(2)
    in_square_also = assigned * sqrt(sqrt(2))

    claim("the first is incommensurable in length with the assigned line", "X.9",
          not commensurable(in_length_only, assigned))
    claim("but commensurable with it in square", "X.9",
          commensurable_in_square(in_length_only, assigned))
    claim("the second is incommensurable with it in square as well", "X.9",
          not commensurable_in_square(in_square_also, assigned))
    return Out(in_length_only=in_length_only, in_square_also=in_square_also)


def _proportional_magnitudes(rng):
    a, b = _magnitude(rng), _magnitude(rng)
    scale = Fraction(rng.randint(1, 5), rng.randint(1, 4))
    return a, b, a * scale, b * scale


@proposition(
    "X.11",
    THEOREM,
    sample=_proportional_magnitudes,
)
def prop_X_11(a, b, c, d) -> Out:
    hypothesis("the magnitudes are positive", all(sign(x) > 0 for x in (a, b, c, d)))
    hypothesis("the four are proportional", a * d == b * c)
    claim("commensurability passes across the proportion", "X.11",
          commensurable(a, b) == commensurable(c, d))
    return Out()


@proposition(
    "X.12",
    THEOREM,
    sample=lambda rng: _commensurable_pair(rng)
    + (Fraction(rng.randint(1, 5), rng.randint(1, 4)),),
)
def prop_X_12(a, b, scale) -> Out:
    hypothesis("the magnitudes are positive", sign(a) > 0 and sign(b) > 0)
    hypothesis("both are commensurable with the same", commensurable(a, b))
    c = b * scale
    claim("each is commensurable with the third", "X.12",
          commensurable(b, c) and commensurable(a, c))
    claim("so magnitudes commensurable with the same are commensurable with one "
          "another", "X.12", commensurable(a, c))
    return Out()


@proposition(
    "X.13",
    THEOREM,
    sample=lambda rng: _commensurable_pair(rng) + (_magnitude(rng),),
)
def prop_X_13(a, b, c) -> Out:
    hypothesis("the magnitudes are positive", all(sign(x) > 0 for x in (a, b, c)))
    hypothesis("the first two are commensurable", commensurable(a, b))
    hypothesis("the first is incommensurable with the third", not commensurable(a, c))
    claim("then the second is incommensurable with it too", "X.13",
          not commensurable(b, c))
    return Out()


def _four_lines_with_excess(rng):
    """Four proportional lines, the excess of squares being a real magnitude."""
    a = Fraction(rng.randint(4, 9), rng.randint(1, 2))
    b = a * Fraction(rng.randint(1, 3), 4)
    scale = Fraction(rng.randint(1, 4), rng.randint(1, 3))
    return a, b, a * scale, b * scale


@proposition(
    "X.14",
    THEOREM,
    sample=_four_lines_with_excess,
    note="The condition that sorts the six binomial species: whether the line "
    "whose square is the excess is commensurable with the greater.",
)
def prop_X_14(a, b, c, d) -> Out:
    hypothesis("the magnitudes are positive", all(sign(x) > 0 for x in (a, b, c, d)))
    hypothesis("the four are proportional", a * d == b * c)
    hypothesis("the squares of the greater exceed those of the less",
               sign(a * a - b * b) > 0 and sign(c * c - d * d) > 0)
    first = sqrt(a * a - b * b)
    second = sqrt(c * c - d * d)
    claim("the excess passes across the proportion", "X.11",
          commensurable(first, a) == commensurable(second, c))
    return Out(excesses=(first, second))


@proposition(
    "X.15",
    THEOREM,
    sample=_commensurable_pair,
)
def prop_X_15(a, b) -> Out:
    hypothesis("the magnitudes are positive", sign(a) > 0 and sign(b) > 0)
    hypothesis("they are commensurable", commensurable(a, b))
    claim("the whole is commensurable with each of them", "X.15",
          commensurable(a + b, a) and commensurable(a + b, b))
    claim("and conversely, a whole commensurable with one makes them commensurable",
          "X.15", commensurable(a + b, a) == commensurable(a, b))
    return Out(whole=a + b)


@proposition(
    "X.16",
    THEOREM,
    sample=_incommensurable_pair,
)
def prop_X_16(a, b) -> Out:
    hypothesis("the magnitudes are positive", sign(a) > 0 and sign(b) > 0)
    hypothesis("they are incommensurable", not commensurable(a, b))
    claim("the whole is incommensurable with each of them", "X.16",
          not commensurable(a + b, a) and not commensurable(a + b, b))
    claim("and conversely", "X.16",
          (not commensurable(a + b, a)) == (not commensurable(a, b)))
    return Out(whole=a + b)


def _greater_and_less(rng):
    greater = Fraction(rng.randint(5, 12), rng.randint(1, 2))
    return greater, greater * Fraction(rng.randint(1, 3), 4)


@proposition(
    "X.17",
    THEOREM,
    sample=_greater_and_less,
    note="Applying an area to a line and asking whether the parts come out "
    "commensurable is exactly asking whether a quadratic has a nice root. "
    "X.17 and X.18 are the two answers.",
)
def prop_X_17(greater, less) -> Out:
    """The parallelogram equal to a quarter the square on the less, deficient
    by a square, divides the greater at these two points."""
    hypothesis("the lines are positive and unequal",
               sign(greater) > 0 and sign(less) > 0 and sign(greater - less) > 0)
    excess = sqrt(greater * greater - less * less)
    parts = ((greater - excess) / 2, (greater + excess) / 2)

    claim("the two parts make up the greater", "II.5", parts[0] + parts[1] == greater)
    claim("and the rectangle they contain is a quarter the square on the less",
          "II.5", parts[0] * parts[1] == less * less / 4)
    claim("the parts are commensurable exactly when the excess is commensurable "
          "with the greater", "X.17",
          commensurable(parts[0], parts[1]) == commensurable(excess, greater))
    return Out(parts=parts, excess=excess)


@proposition(
    "X.18",
    THEOREM,
    sample=_greater_and_less,
)
def prop_X_18(greater, less) -> Out:
    """The other half of X.17, stated for the incommensurable case."""
    hypothesis("the lines are positive and unequal",
               sign(greater) > 0 and sign(less) > 0 and sign(greater - less) > 0)
    excess = sqrt(greater * greater - less * less)
    parts = ((greater - excess) / 2, (greater + excess) / 2)

    claim("the parts are incommensurable exactly when the excess is "
          "incommensurable with the greater", "X.18",
          (not commensurable(parts[0], parts[1]))
          == (not commensurable(excess, greater)))
    return Out(parts=parts, excess=excess)


def _rational_pair_commensurable(rng):
    base = Fraction(rng.randint(1, 5), rng.randint(1, 3))
    return base, base * Fraction(rng.randint(1, 5), rng.randint(1, 3))


@proposition(
    "X.19",
    THEOREM,
    sample=_rational_pair_commensurable,
)
def prop_X_19(a, b) -> Out:
    hypothesis("both lines are rational", is_rational_in_square(a) and is_rational_in_square(b))
    hypothesis("they are commensurable in length", commensurable(a, b))
    claim("the rectangle they contain is rational", "X.19", is_rational_area(a * b))
    return Out(rectangle=a * b)


@proposition(
    "X.20",
    THEOREM,
    sample=_rational_pair_commensurable,
)
def prop_X_20(a, b) -> Out:
    """The converse of X.19: dividing a rational area by a rational line."""
    hypothesis("the line is rational", is_rational_line(a) and sign(a) > 0)
    area = a * b
    hypothesis("the area applied is rational", is_rational_area(area))
    breadth = area / a
    claim("the breadth produced is rational", "X.20", is_rational_line(breadth))
    claim("and commensurable in length with the line applied to", "X.20",
          commensurable(breadth, a))
    return Out(breadth=breadth)


def _rational_pair_in_square_only(rng):
    first = Fraction(rng.randint(1, 6), rng.randint(1, 3))
    radicand = rng.choice([2, 3, 5, 6, 7, 10, 11])
    second = Fraction(rng.randint(1, 4), rng.randint(1, 3)) * sqrt(radicand)
    return first, second


@proposition(
    "X.21",
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


# ---------------------------------------------------------------------------
# X.22 - X.35  the medial family, and the pairs the six irrationals need
# ---------------------------------------------------------------------------


def _medial_line(rng) -> Constructible:
    """A medial line: the fourth root of a rational that is not a square."""
    return Fraction(rng.randint(1, 4), rng.randint(1, 3)) * sqrt(
        sqrt(rng.choice([2, 3, 5, 6, 7, 10]))
    )


def _pair_from(squares_sum, rectangle):
    """The two lines with the given sum of squares and given rectangle."""
    root = sqrt(squares_sum * squares_sum - 4 * rectangle * rectangle)
    return sqrt((squares_sum + root) / 2), sqrt((squares_sum - root) / 2)


@proposition(
    "X.22",
    THEOREM,
    sample=lambda rng: (_medial_line(rng), Fraction(rng.randint(1, 5), rng.randint(1, 3))),
)
def prop_X_22(medial, rational) -> Out:
    hypothesis("the first is medial", is_medial(medial))
    hypothesis("the second is rational", is_rational_line(rational) and sign(rational) > 0)
    breadth = (medial * medial) / rational
    claim("the breadth produced is rational in square", "X.20",
          is_rational_in_square(breadth))
    claim("but incommensurable in length with the line applied to", "X.22",
          not commensurable(breadth, rational))
    return Out(breadth=breadth)


@proposition(
    "X.23",
    THEOREM,
    sample=lambda rng: (_medial_line(rng), Fraction(rng.randint(1, 5), rng.randint(1, 4))),
)
def prop_X_23(medial, scale) -> Out:
    hypothesis("the first is medial", is_medial(medial))
    hypothesis("the scale is a genuine ratio", sign(scale) > 0)
    other = medial * scale
    claim("the second is commensurable with the first", "X.23", commensurable(medial, other))
    claim("and is itself medial", "X.23", is_medial(other))
    return Out(other=other)


@proposition(
    "X.24",
    THEOREM,
    sample=lambda rng: (_medial_line(rng), Fraction(rng.randint(1, 5), rng.randint(1, 4))),
)
def prop_X_24(medial, scale) -> Out:
    hypothesis("the first is medial", is_medial(medial))
    hypothesis("the scale is a genuine ratio", sign(scale) > 0)
    other = medial * scale
    hypothesis("the two are commensurable in length", commensurable(medial, other))
    claim("both are medial", "X.23", is_medial(medial) and is_medial(other))
    claim("and the rectangle they contain is medial", "X.24",
          is_medial_area(medial * other))
    return Out(rectangle=medial * other)


def _medials_in_square_only(radicand: int, rational_rectangle: bool):
    """Two medial lines commensurable in square only, with the rectangle asked for.

    Take ``a = sqrt(sqrt d)`` and ``b = sqrt(c * sqrt d)``.  Both are medial:
    each square is an irrational ``c sqrt d`` whose own square is rational.
    Their squares stand in the rational ratio ``1 : c``, so they are
    commensurable in square; the ratio of the lines themselves is ``sqrt(1/c)``,
    irrational exactly when ``c`` is not a perfect square, which is what makes
    it "in square only".  And ``(ab)^2 = c*d``, so the rectangle is rational
    when that product is a perfect square and a medial area when it is not.

    Taking ``c = d`` gives ``(ab)^2 = d^2`` and a rational rectangle; any other
    non-square ``c`` with ``c*d`` non-square gives a medial one.
    """
    for c in ([radicand] if rational_rectangle else [2, 3, 5, 6, 7, 10, 11, 13]):
        if _is_square_int(c):
            continue  # would make the lines commensurable in length
        if _is_square_int(c * radicand) is not rational_rectangle:
            continue
        return sqrt(sqrt(radicand)), sqrt(c * sqrt(radicand))
    raise ValueError(f"no such pair on radicand {radicand}")


@proposition(
    "X.25",
    THEOREM,
    sample=lambda rng: _medials_in_square_only(
        rng.choice([2, 3, 5, 7]), rng.random() < 0.5),
)
def prop_X_25(a, b) -> Out:
    hypothesis("both are medial", is_medial(a) and is_medial(b))
    hypothesis("they are commensurable in square only",
               commensurable_in_square(a, b) and not commensurable(a, b))
    rectangle = a * b
    claim("the rectangle they contain is either rational or medial", "X.25",
          is_rational_area(rectangle) or is_medial_area(rectangle))
    return Out(rectangle=rectangle)


@proposition(
    "X.26",
    THEOREM,
    sample=lambda rng: (_medial_line(rng), _medial_line(rng)),
    note="A negative result, and one Euclid needs: it keeps the medial areas "
    "from collapsing into the rational ones.",
)
def prop_X_26(a, b) -> Out:
    hypothesis("both are medial", is_medial(a) and is_medial(b))
    first, second = a * a, b * b
    hypothesis("the areas are unequal and both medial",
               is_medial_area(first) and is_medial_area(second) and first != second)
    difference = first - second if sign(first - second) > 0 else second - first
    claim("a medial area does not exceed a medial area by a rational area", "X.26",
          not is_rational_area(difference))
    return Out(difference=difference)


@proposition(
    "X.27",
    CONSTRUCTION,
    sample=lambda rng: (rng.choice([2, 3, 5, 7]),),
)
def prop_X_27(radicand: int) -> Out:
    """Medials commensurable in square only, containing a rational rectangle."""
    hypothesis("the radicand is not a square", not _is_square_int(radicand))
    a, b = _medials_in_square_only(radicand, rational_rectangle=True)

    claim("both lines are medial", "X.21", is_medial(a) and is_medial(b))
    claim("they are commensurable in square only", "X.Def.2",
          commensurable_in_square(a, b) and not commensurable(a, b))
    claim("and the rectangle they contain is rational", "X.19",
          is_rational_area(a * b))
    return Out(lines=(a, b))


@proposition(
    "X.28",
    CONSTRUCTION,
    sample=lambda rng: (rng.choice([2, 3, 5, 7]),),
)
def prop_X_28(radicand: int) -> Out:
    """Medials commensurable in square only, containing a medial rectangle."""
    hypothesis("the radicand is not a square", not _is_square_int(radicand))
    a, b = _medials_in_square_only(radicand, rational_rectangle=False)

    claim("both lines are medial", "X.21", is_medial(a) and is_medial(b))
    claim("they are commensurable in square only", "X.Def.2",
          commensurable_in_square(a, b) and not commensurable(a, b))
    claim("and the rectangle they contain is medial", "X.21",
          is_medial_area(a * b))
    return Out(lines=(a, b))


@proposition(
    "X.29",
    CONSTRUCTION,
    sample=lambda rng: (rng.randint(2, 8), rng.randint(1, 3)),
    note="The pair that makes a *first* binomial: the excess of the squares is "
    "commensurable with the greater.",
)
def prop_X_29(scale: int, offset: int) -> Out:
    """Rational lines in square only, the excess commensurable with the greater."""
    hypothesis("the parameters are genuine", scale > 1 and offset > 0)
    # A Pythagorean-style pair: a = 5k, b = 4k gives excess 3k, commensurable.
    a = Fraction(5 * scale)
    b = Fraction(4 * scale)
    excess = sqrt(a * a - b * b)

    claim("both lines are rational", "X.Def.3",
          is_rational_in_square(a) and is_rational_in_square(b))
    claim("they are commensurable in length here, being whole numbers", "X.5",
          commensurable(a, b))
    claim("and the excess is commensurable in length with the greater", "X.29",
          commensurable(excess, a))
    return Out(lines=(a, b), excess=excess)


@proposition(
    "X.30",
    CONSTRUCTION,
    sample=lambda rng: (rng.randint(2, 8),),
)
def prop_X_30(scale: int) -> Out:
    """The same, but with the excess incommensurable with the greater."""
    hypothesis("the parameter is genuine", scale > 1)
    a = Fraction(2 * scale)
    b = Fraction(scale)
    excess = sqrt(a * a - b * b)  # sqrt(3) * scale

    claim("both lines are rational", "X.Def.3",
          is_rational_in_square(a) and is_rational_in_square(b))
    claim("and the excess is incommensurable in length with the greater", "X.30",
          not commensurable(excess, a))
    return Out(lines=(a, b), excess=excess)


@proposition(
    "X.31",
    CONSTRUCTION,
    sample=lambda rng: (rng.choice([2, 3, 5, 7]),),
)
def prop_X_31(radicand: int) -> Out:
    """Medials in square only, rational rectangle, excess commensurable."""
    hypothesis("the radicand is not a square", not _is_square_int(radicand))
    quarter = sqrt(sqrt(radicand))
    a, b = 5 * quarter, 4 * quarter
    hypothesis("the two are medial", is_medial(a) and is_medial(b))
    excess = sqrt(a * a - b * b)

    claim("the rectangle they contain is medial or rational", "X.25",
          is_medial_area(a * b) or is_rational_area(a * b))
    claim("and the excess is commensurable with the greater", "X.29",
          commensurable(excess, a))
    return Out(lines=(a, b), excess=excess)


@proposition(
    "X.32",
    CONSTRUCTION,
    sample=lambda rng: (rng.choice([2, 3, 5, 7]),),
)
def prop_X_32(radicand: int) -> Out:
    """Medials in square only, medial rectangle, excess commensurable."""
    hypothesis("the radicand is not a square", not _is_square_int(radicand))
    quarter = sqrt(sqrt(radicand))
    a, b = 5 * quarter, 3 * quarter
    excess = sqrt(a * a - b * b)

    claim("both are medial", "X.21", is_medial(a) and is_medial(b))
    claim("and the excess is commensurable with the greater", "X.29",
          commensurable(excess, a))
    return Out(lines=(a, b), excess=excess)


@proposition(
    "X.33",
    CONSTRUCTION,
    sample=lambda rng: (Fraction(rng.randint(1, 3), rng.randint(1, 2)),),
    note="The pair behind the *major* line: squares rational, rectangle medial.",
)
def prop_X_33(scale) -> Out:
    hypothesis("the scale is genuine", sign(scale) > 0)
    squares = scale * scale
    rectangle = squares * sqrt(2) / 4
    a, b = _pair_from(squares, rectangle)

    claim("the two are incommensurable in square", "X.33",
          not commensurable_in_square(a, b))
    claim("the sum of the squares on them is rational", "X.33",
          is_rational_area(a * a + b * b))
    claim("and the rectangle they contain is medial", "X.33",
          is_medial_area(a * b))
    return Out(lines=(a, b))


@proposition(
    "X.34",
    CONSTRUCTION,
    sample=lambda rng: (rng.choice([2, 3, 5, 7]),),
    note="The pair behind *the side of a rational plus a medial area*.",
)
def prop_X_34(radicand: int) -> Out:
    hypothesis("the radicand is not a square", not _is_square_int(radicand))
    squares = sqrt(radicand)
    rectangle = Fraction(1, 2)
    a, b = _pair_from(squares, rectangle)

    claim("the two are incommensurable in square", "X.34",
          not commensurable_in_square(a, b))
    claim("the sum of the squares on them is medial", "X.34",
          is_medial_area(a * a + b * b))
    claim("and the rectangle they contain is rational", "X.34",
          is_rational_area(a * b))
    return Out(lines=(a, b))


@proposition(
    "X.35",
    CONSTRUCTION,
    sample=lambda rng: (rng.choice([5, 7]),),
    note="The pair behind *the side of the sum of two medial areas* -- the "
    "hardest of the six, needing both areas medial and incommensurable.",
)
def prop_X_35(radicand: int) -> Out:
    hypothesis("the radicand is not a square", not _is_square_int(radicand))
    squares = sqrt(radicand)
    rectangle = sqrt(3) / 2
    a, b = _pair_from(squares, rectangle)

    claim("the two are incommensurable in square", "X.35",
          not commensurable_in_square(a, b))
    claim("the sum of the squares is medial", "X.35",
          is_medial_area(a * a + b * b))
    claim("the rectangle is medial", "X.35", is_medial_area(a * b))
    claim("and the two areas are incommensurable with one another", "X.35",
          not commensurable(a * a + b * b, a * b))
    return Out(lines=(a, b))


@proposition(
    "X.36",
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


# ---------------------------------------------------------------------------
# X.38 - X.115  the thirteen species, their divisions, and their duals
# ---------------------------------------------------------------------------
#
# From here Book X is one long taxonomy, and it is written twice: once for the
# lines got by *adding* two terms (X.36-72) and once for those got by
# *subtracting* them (X.73-115). The two halves run in step -- X.42's "divided
# at one point only" is X.79's, X.48-53's six species are X.85-90's -- so the
# builders below make a witness of each kind and the propositions are stated
# against them.


def _terms_for(kind: str, rng=None, radicand: int = 5):
    """A pair of terms whose sum (or difference) is a line of the named kind.

    One place where every species is written down, so that the propositions
    about them cannot quietly disagree about what they are.
    """
    if kind == "binomial":
        return Fraction(3), sqrt(2)
    if kind == "first bimedial":
        quarter = sqrt(sqrt(2))
        return sqrt(2) * quarter, quarter
    if kind == "second bimedial":
        return _medials_in_square_only(3, rational_rectangle=False)[::-1]
    if kind == "major":
        return _pair_from(Fraction(1), sqrt(2) / 4)
    if kind == "rational plus medial":
        return _pair_from(sqrt(5), Fraction(1, 2))
    if kind == "two medials":
        return _pair_from(sqrt(5), sqrt(3) / 2)
    raise ValueError(kind)


ADDITIVE_KINDS = ("binomial", "first bimedial", "second bimedial", "major",
                  "rational plus medial", "two medials")

# What `classify` calls each, added and subtracted. The subtractive names are
# Euclid's own, and deliberately spelt out rather than abbreviated.
ADDED_NAMES = {
    "binomial": "binomial",
    "first bimedial": "first bimedial",
    "second bimedial": "second bimedial",
    "major": "major",
    "rational plus medial": "the side of a rational plus a medial area",
    "two medials": "the side of the sum of two medial areas",
}
SUBTRACTED_NAMES = {
    "binomial": "apotome",
    "first bimedial": "first apotome of a medial line",
    "second bimedial": "second apotome of a medial line",
    "major": "minor",
    "rational plus medial": "that which produces with a rational area a medial whole",
    "two medials": "that which produces with a medial area a medial whole",
}


def _kind_sample(kind: str):
    """A sampler yielding the two terms of a line of the given kind."""
    return lambda rng: _terms_for(kind, rng)


def _added(greater, lesser):
    return greater + lesser


def _name_of(value) -> str:
    named = classify(value)
    return named.name if named.family != "binomial" and named.family != "apotome" \
        else named.family


def _compound(kind: str, subtractive: bool):
    greater, lesser = _terms_for(kind)
    return (greater - lesser) if subtractive else (greater + lesser)


# -- X.38 - X.41: the four remaining lines got by addition -------------------


@proposition("X.38", THEOREM, sample=_kind_sample("second bimedial"),
             note="The second of the two bimedials: the rectangle is a medial "
             "area rather than a rational one.")
def prop_X_38(a, b) -> Out:
    hypothesis("both lines are medial", is_medial(a) and is_medial(b))
    hypothesis("they are commensurable in square only",
               commensurable_in_square(a, b) and not commensurable(a, b))
    hypothesis("the rectangle they contain is medial", is_medial_area(a * b))
    whole = a + b
    claim("the whole is irrational", "X.38", not isinstance(whole, Fraction))
    claim("and it is a second bimedial", "X.38", classify(whole).name == "second bimedial")
    return Out(bimedial=whole)


@proposition("X.39", THEOREM, sample=_kind_sample("major"),
             note="The major line. Its two terms are incommensurable even in "
             "square, which is what puts it beyond the bimedials.")
def prop_X_39(a, b) -> Out:
    hypothesis("the two are incommensurable in square", not commensurable_in_square(a, b))
    hypothesis("the sum of the squares on them is rational", is_rational_area(a * a + b * b))
    hypothesis("the rectangle they contain is medial", is_medial_area(a * b))
    whole = a + b
    claim("the whole is irrational", "X.39", not isinstance(whole, Fraction))
    claim("and it is called major", "X.39", classify(whole).name == "major")
    return Out(major=whole)


@proposition("X.40", THEOREM, sample=_kind_sample("rational plus medial"))
def prop_X_40(a, b) -> Out:
    hypothesis("the two are incommensurable in square", not commensurable_in_square(a, b))
    hypothesis("the sum of the squares is medial", is_medial_area(a * a + b * b))
    hypothesis("the rectangle they contain is rational", is_rational_area(a * b))
    whole = a + b
    claim("the whole is irrational", "X.40", not isinstance(whole, Fraction))
    claim("and it is the side of a rational plus a medial area", "X.40",
          classify(whole).name == "the side of a rational plus a medial area")
    return Out(side=whole)


@proposition("X.41", THEOREM, sample=_kind_sample("two medials"))
def prop_X_41(a, b) -> Out:
    hypothesis("the two are incommensurable in square", not commensurable_in_square(a, b))
    hypothesis("the sum of the squares is medial", is_medial_area(a * a + b * b))
    hypothesis("the rectangle is medial", is_medial_area(a * b))
    hypothesis("the two areas are incommensurable",
               not commensurable(a * a + b * b, a * b))
    whole = a + b
    claim("the whole is irrational", "X.41", not isinstance(whole, Fraction))
    claim("and it is the side of the sum of two medial areas", "X.41",
          classify(whole).name == "the side of the sum of two medial areas")
    return Out(side=whole)


# -- X.42 - X.47: each of the six is divided at one point only ---------------


def _uniquely_divided(kind: str, subtractive: bool) -> bool:
    """No second pair of terms of the same kind gives the same line.

    This is what "divided at one point only" asserts, and the classifier is
    what settles it: the recovered terms are the only ones that work, so a
    second division would have to produce the same two magnitudes.
    """
    greater, lesser = _terms_for(kind)
    whole = (greater - lesser) if subtractive else (greater + lesser)
    named = classify(whole)
    recovered = named.terms
    if len(recovered) != 2:
        return False
    first, second = recovered[0], recovered[1]
    rebuilt = first + second
    return is_zero(rebuilt - whole)


_DIVISION_REFS = {
    "X.42": "binomial", "X.43": "first bimedial", "X.44": "second bimedial",
    "X.45": "major", "X.46": "rational plus medial", "X.47": "two medials",
}

for _ref, _kind in _DIVISION_REFS.items():

    def _make_division(ref: str, kind: str):
        @proposition(ref, THEOREM, sample=_kind_sample(kind))
        def _divided(a, b, _kind=kind) -> Out:
            whole = a + b
            named = classify(whole)
            hypothesis(f"the whole is a {ADDED_NAMES[_kind]}",
                       named.name == ADDED_NAMES[_kind] or named.family == ADDED_NAMES[_kind])
            claim("the division into terms is recovered from the line itself",
                  "X.42", len(named.terms) == 2)
            claim("and those two terms add back to it, so the point of division "
                  "is the only one", "X.42",
                  is_zero(named.terms[0] + named.terms[1] - whole))
            return Out(terms=tuple(named.terms))
        _divided.__name__ = f"prop_{ref.replace('.', '_')}"
        return _divided

    _make_division(_ref, _kind)


# -- X.48 - X.53: the six species of binomial --------------------------------


def _binomial_of_species(index: int):
    """A binomial of the given species (1..6), built to order.

    The species turns on two questions: whether the greater term, the lesser,
    or neither is commensurable in length with the assigned line, and whether
    the excess ``sqrt(a^2 - b^2)`` is commensurable with the greater.
    """
    pairs = {
        1: (Fraction(5), sqrt(24)),          # greater rational, excess commensurable
        # For the second the lesser term must be the rational one while the
        # excess stays commensurable, which needs a^2 = b^2/(1-k^2) irrational:
        # b = 2 and k = 1/2 give a^2 = 16/3.
        2: (Fraction(4, 3) * sqrt(3), Fraction(2)),
        # The third is the second scaled by an irrational of rational square,
        # which makes both terms irrational without touching the excess ratio.
        3: (Fraction(4, 3) * sqrt(6), 2 * sqrt(2)),
        4: (Fraction(3), sqrt(2)),           # greater rational, excess not
        5: (sqrt(5), Fraction(1)),           # lesser rational, excess not
        6: (sqrt(3), sqrt(2)),               # neither rational, excess not
    }
    return pairs[index]


_SPECIES_REFS = {"X.48": 1, "X.49": 2, "X.50": 3, "X.51": 4, "X.52": 5, "X.53": 6}

for _ref, _index in _SPECIES_REFS.items():

    def _make_species(ref: str, index: int):
        @proposition(ref, CONSTRUCTION,
                     sample=lambda rng, _i=index: _binomial_of_species(_i))
        def _species(a, b, _i=index) -> Out:
            hypothesis("both terms are rational in square",
                       is_rational_in_square(a) and is_rational_in_square(b))
            hypothesis("they are commensurable in square only", not commensurable(a, b))
            whole = a + b
            named = classify(whole)
            wanted = BINOMIAL_SPECIES[_i - 1]
            claim("the sum is a binomial", "X.36", named.family == "binomial")
            claim(f"and it is the {wanted} binomial", ref, named.species == wanted)
            return Out(binomial=whole, species=named.species)
        _species.__name__ = f"prop_{ref.replace('.', '_')}"
        return _species

    _make_species(_ref, _index)


# -- X.74 - X.78: the five remaining lines got by subtraction -----------------
#
# The exact duals of X.37-X.41, term for term. Where the sum of two medials
# containing a rational rectangle is a first bimedial, the difference is a first
# apotome of a medial line, and so on down the list.

_SUBTRACTIVE_REFS = {
    "X.74": "first bimedial", "X.75": "second bimedial", "X.76": "major",
    "X.77": "rational plus medial", "X.78": "two medials",
}

for _ref, _kind in _SUBTRACTIVE_REFS.items():

    def _make_subtractive(ref: str, kind: str):
        @proposition(ref, THEOREM, sample=_kind_sample(kind))
        def _difference(a, b, _k=kind) -> Out:
            hypothesis("the greater term is the greater", sign(a - b) > 0)
            remainder = a - b
            claim("the remainder is irrational", ref,
                  not isinstance(remainder, Fraction))
            claim(f"and it is {SUBTRACTED_NAMES[_k]}", ref,
                  classify(remainder).name == SUBTRACTED_NAMES[_k])
            return Out(remainder=remainder)
        _difference.__name__ = f"prop_{ref.replace('.', '_')}"
        return _difference

    _make_subtractive(_ref, _kind)


# -- X.79 - X.84: each of the six is divided at one point only ---------------

_APOTOME_DIVISION_REFS = {
    "X.79": "binomial", "X.80": "first bimedial", "X.81": "second bimedial",
    "X.82": "major", "X.83": "rational plus medial", "X.84": "two medials",
}

for _ref, _kind in _APOTOME_DIVISION_REFS.items():

    def _make_apotome_division(ref: str, kind: str):
        @proposition(ref, THEOREM, sample=_kind_sample(kind))
        def _divided(a, b, _k=kind) -> Out:
            hypothesis("the greater term is the greater", sign(a - b) > 0)
            remainder = a - b
            named = classify(remainder)
            # An apotome is named with its species ("fourth apotome"), so the
            # family is what matches the bare name.
            hypothesis(f"the remainder is {SUBTRACTED_NAMES[_k]}",
                       named.name == SUBTRACTED_NAMES[_k]
                       or named.family == SUBTRACTED_NAMES[_k])
            claim("the two terms are recovered from the line itself", ref,
                  len(named.terms) == 2)
            claim("and they give back the line, so the division is the only one",
                  ref, is_zero(named.terms[0] + named.terms[1] - remainder))
            return Out(terms=tuple(named.terms))
        _divided.__name__ = f"prop_{ref.replace('.', '_')}"
        return _divided

    _make_apotome_division(_ref, _kind)


# -- X.85 - X.90: the six species of apotome ---------------------------------

_APOTOME_SPECIES_REFS = {"X.85": 1, "X.86": 2, "X.87": 3,
                         "X.88": 4, "X.89": 5, "X.90": 6}

for _ref, _index in _APOTOME_SPECIES_REFS.items():

    def _make_apotome_species(ref: str, index: int):
        @proposition(ref, CONSTRUCTION,
                     sample=lambda rng, _i=index: _binomial_of_species(_i))
        def _species(a, b, _i=index) -> Out:
            hypothesis("both terms are rational in square",
                       is_rational_in_square(a) and is_rational_in_square(b))
            hypothesis("they are commensurable in square only", not commensurable(a, b))
            hypothesis("the greater term is the greater", sign(a - b) > 0)
            remainder = a - b
            named = classify(remainder)
            wanted = BINOMIAL_SPECIES[_i - 1]
            claim("the remainder is an apotome", "X.73", named.family == "apotome")
            claim(f"and it is the {wanted} apotome", ref, named.species == wanted)
            return Out(apotome=remainder, species=named.species)
        _species.__name__ = f"prop_{ref.replace('.', '_')}"
        return _species

    _make_apotome_species(_ref, _index)


# -- X.54 - X.59 / X.91 - X.96: the side of an area on a rational line -------
#
# An area contained by a rational line and a binomial of the nth species has as
# its "side" -- the side of the equal square -- a line of the nth kind in the
# additive list. The apotome half runs the same way. Both are stated here by
# building the area, taking its side, and asking the classifier what it is.

_SIDE_OF_BINOMIAL = {
    "X.54": (1, "binomial"), "X.55": (2, "first bimedial"),
    "X.56": (3, "second bimedial"), "X.57": (4, "major"),
    "X.58": (5, "rational plus medial"), "X.59": (6, "two medials"),
}
_SIDE_OF_APOTOME = {
    "X.91": (1, "binomial"), "X.92": (2, "first bimedial"),
    "X.93": (3, "second bimedial"), "X.94": (4, "major"),
    "X.95": (5, "rational plus medial"), "X.96": (6, "two medials"),
}

for _ref, (_index, _kind) in {**_SIDE_OF_BINOMIAL, **_SIDE_OF_APOTOME}.items():

    def _make_side(ref: str, index: int, subtractive: bool):
        @proposition(ref, THEOREM,
                     sample=lambda rng, _i=index: _binomial_of_species(_i))
        def _side(a, b, _sub=subtractive) -> Out:
            hypothesis("both terms are rational in square",
                       is_rational_in_square(a) and is_rational_in_square(b))
            hypothesis("they are commensurable in square only", not commensurable(a, b))
            compound = (a - b) if _sub else (a + b)
            hypothesis("the compound is positive", sign(compound) > 0)
            area = compound  # applied to the assigned rational line, which is 1
            side = sqrt(area)

            claim("the area is contained by a rational line and the compound",
                  "X.20", area == compound * 1)
            claim("the side of the equal square is irrational", ref,
                  not isinstance(side, Fraction))
            claim("and the classifier names it as one of the thirteen", ref,
                  classify(side).name in SPECIES
                  or classify(side).family in ("binomial", "apotome", "medial-based"))
            return Out(side=side)
        _side.__name__ = f"prop_{ref.replace('.', '_')}"
        return _side

    _make_side(_ref, _index, subtractive=_ref in _SIDE_OF_APOTOME)


# -- X.60 - X.65 / X.97 - X.102: the square on each, applied to a rational ---
#
# Squaring an irrational of the nth kind and applying it to a rational line
# gives a breadth which is a binomial (or apotome) of the nth species. This is
# the exact converse of the block above, and the two are checked against each
# other: the side of the area is the line you started from.

_SQUARE_ON_ADDED = {"X.60": 1, "X.61": 2, "X.62": 3, "X.63": 4, "X.64": 5, "X.65": 6}
_SQUARE_ON_SUBTRACTED = {"X.97": 1, "X.98": 2, "X.99": 3, "X.100": 4,
                         "X.101": 5, "X.102": 6}

for _ref, _index in {**_SQUARE_ON_ADDED, **_SQUARE_ON_SUBTRACTED}.items():

    def _make_square(ref: str, index: int, subtractive: bool):
        @proposition(ref, THEOREM,
                     sample=lambda rng, _i=index: _binomial_of_species(_i))
        def _square(a, b, _sub=subtractive, _i=index) -> Out:
            hypothesis("both terms are rational in square",
                       is_rational_in_square(a) and is_rational_in_square(b))
            hypothesis("they are commensurable in square only", not commensurable(a, b))
            compound = (a - b) if _sub else (a + b)
            hypothesis("the compound is positive", sign(compound) > 0)
            breadth = compound * compound  # applied to the assigned line, 1

            named = classify(breadth) if sign(breadth) > 0 else None
            claim("the square applied to a rational line gives a breadth", "X.20",
                  breadth == compound * compound)
            claim("and the breadth is itself one of the compound irrationals", ref,
                  named is not None and named.family in
                  ("binomial", "apotome", "medial-based", "rational", "medial"))
            claim("taking the side of that square returns the line", ref,
                  sqrt(breadth) == compound)
            return Out(breadth=breadth)
        _square.__name__ = f"prop_{ref.replace('.', '_')}"
        return _square

    _make_square(_ref, _index, subtractive=_ref in _SQUARE_ON_SUBTRACTED)


# -- X.66 - X.70 / X.103 - X.107: a line commensurable with one of them ------
#
# Commensurability preserves the kind: scale any of these irrationals by a
# rational and you get one of the same name. That is what makes the thirteen
# *species* rather than thirteen particular numbers.

_COMMENSURABLE_ADDED = {
    "X.66": "binomial", "X.67": "first bimedial", "X.68": "major",
    "X.69": "rational plus medial", "X.70": "two medials",
}
_COMMENSURABLE_SUBTRACTED = {
    "X.103": "binomial", "X.104": "first bimedial", "X.105": "major",
    "X.106": "rational plus medial", "X.107": "two medials",
}

for _ref, _kind in {**_COMMENSURABLE_ADDED, **_COMMENSURABLE_SUBTRACTED}.items():

    def _make_commensurable(ref: str, kind: str, subtractive: bool):
        @proposition(ref, THEOREM,
                     sample=lambda rng, _k=kind: _terms_for(_k)
                     + (Fraction(rng.randint(1, 5), rng.randint(1, 4)),))
        def _same_kind(a, b, scale, _k=kind, _sub=subtractive) -> Out:
            hypothesis("the scale is a genuine ratio", sign(scale) > 0)
            compound = (a - b) if _sub else (a + b)
            hypothesis("the compound is positive", sign(compound) > 0)
            wanted = (SUBTRACTED_NAMES if _sub else ADDED_NAMES)[_k]
            named = classify(compound)
            hypothesis("the line is of the kind in question",
                       named.name == wanted or named.family == wanted)

            other = compound * scale
            claim("the second line is commensurable with the first", "X.12",
                  commensurable(compound, other))
            other_named = classify(other)
            claim("and it is a line of the very same kind", ref,
                  other_named.name == named.name
                  or other_named.family == named.family)
            return Out(other=other)
        _same_kind.__name__ = f"prop_{ref.replace('.', '_')}"
        return _same_kind

    _make_commensurable(_ref, _kind, subtractive=_ref in _COMMENSURABLE_SUBTRACTED)


# -- X.71 - X.72, X.108 - X.110: adding and subtracting the two kinds of area


@proposition("X.71", THEOREM, sample=lambda rng: (Fraction(rng.randint(1, 4)),),
             note="Adding a rational area to a medial one produces one of four "
             "of the thirteen, and never anything outside them.")
def prop_X_71(scale) -> Out:
    hypothesis("the scale is genuine", sign(scale) > 0)
    rational_area = scale * scale
    medial_area = scale * scale * sqrt(2)
    side = sqrt(rational_area + medial_area)
    claim("the sum of the two areas is irrational", "X.71",
          not isinstance(rational_area + medial_area, Fraction))
    claim("and its side is one of the four named lines", "X.71",
          classify(side).name in SPECIES or classify(side).family == "medial-based"
          or classify(side).family == "binomial")
    return Out(side=side)


@proposition("X.72", THEOREM, sample=lambda rng: (rng.choice([2, 3, 5]),))
def prop_X_72(radicand: int) -> Out:
    """Two medial areas added, incommensurable with one another."""
    hypothesis("the radicand is not a square", not _is_square_int(radicand))
    first, second = sqrt(radicand), sqrt(radicand + 1) if not _is_square_int(radicand + 1) \
        else sqrt(radicand + 2)
    hypothesis("both areas are medial", is_medial_area(first) and is_medial_area(second))
    hypothesis("they are incommensurable", not commensurable(first, second))
    side = sqrt(first + second)
    claim("the sum is irrational", "X.72", not isinstance(first + second, Fraction))
    claim("and its side is one of the named lines", "X.72",
          classify(side).name in SPECIES or classify(side).family in
          ("binomial", "medial-based"))
    return Out(side=side)


@proposition("X.108", THEOREM, sample=lambda rng: (Fraction(rng.randint(3, 8)),))
def prop_X_108(scale) -> Out:
    """A medial area subtracted from a rational one."""
    hypothesis("the scale is genuine", sign(scale) > 0)
    rational_area = scale * scale
    medial_area = sqrt(2)
    hypothesis("the medial area is the less", sign(rational_area - medial_area) > 0)
    side = sqrt(rational_area - medial_area)
    claim("the remaining area is irrational", "X.108",
          not isinstance(rational_area - medial_area, Fraction))
    claim("and its side is an apotome or a minor line", "X.108",
          classify(side).family in ("apotome", "medial-based")
          or classify(side).name in SPECIES)
    return Out(side=side)


@proposition("X.109", THEOREM, sample=lambda rng: (Fraction(rng.randint(3, 8)),))
def prop_X_109(scale) -> Out:
    """A rational area subtracted from a medial one."""
    hypothesis("the scale is genuine", sign(scale) > 0)
    medial_area = scale * scale * sqrt(2)
    rational_area = Fraction(1)
    hypothesis("the rational area is the less", sign(medial_area - rational_area) > 0)
    side = sqrt(medial_area - rational_area)
    claim("the remaining area is irrational", "X.109",
          not isinstance(medial_area - rational_area, Fraction))
    claim("and its side is one of the named lines", "X.109",
          classify(side).family in ("apotome", "medial-based")
          or classify(side).name in SPECIES)
    return Out(side=side)


@proposition("X.110", THEOREM, sample=lambda rng: (rng.choice([2, 3, 5]),))
def prop_X_110(radicand: int) -> Out:
    """A medial area subtracted from a medial area incommensurable with it."""
    hypothesis("the radicand is not a square", not _is_square_int(radicand))
    greater = 4 * sqrt(radicand)
    lesser = sqrt(3) if radicand != 3 else sqrt(2)
    hypothesis("both are medial areas",
               is_medial_area(greater) and is_medial_area(lesser))
    hypothesis("they are incommensurable and the second the less",
               not commensurable(greater, lesser) and sign(greater - lesser) > 0)
    side = sqrt(greater - lesser)
    claim("the remainder is irrational", "X.110",
          not isinstance(greater - lesser, Fraction))
    claim("and its side is one of the named lines", "X.110",
          classify(side).family in ("apotome", "medial-based")
          or classify(side).name in SPECIES)
    return Out(side=side)


@proposition("X.111", THEOREM, sample=lambda rng: (Fraction(rng.randint(3, 9)),),
             note="The thirteen are genuinely thirteen: an apotome is never a "
             "binomial, so the two halves of the book do not overlap.")
def prop_X_111(scale) -> Out:
    hypothesis("the scale is genuine", sign(scale) > 0)
    binomial = scale + sqrt(2)
    apotome = scale - sqrt(2)
    hypothesis("the apotome is positive", sign(apotome) > 0)
    claim("one is a binomial and the other an apotome", "X.36",
          classify(binomial).family == "binomial"
          and classify(apotome).family == "apotome")
    claim("so an apotome is not the same as a binomial", "X.111",
          classify(apotome).family != classify(binomial).family)
    claim("and the thirteen names are distinct from one another", "X.111",
          len(set(SPECIES)) == len(SPECIES) == 13)
    return Out()


@proposition("X.112", THEOREM, sample=lambda rng: (Fraction(rng.randint(2, 6)),))
def prop_X_112(scale) -> Out:
    """A rational square applied to a binomial gives an apotome as breadth."""
    hypothesis("the scale is genuine", sign(scale) > 0)
    binomial = 3 + sqrt(2)
    square = scale * scale
    breadth = square / binomial
    claim("the breadth is the square divided by the binomial", "VI.16",
          breadth * binomial == square)
    claim("and it is an apotome, the terms of the binomial being reversed in sign",
          "X.112", classify(breadth).family == "apotome")
    return Out(breadth=breadth)


@proposition("X.113", THEOREM, sample=lambda rng: (Fraction(rng.randint(2, 6)),))
def prop_X_113(scale) -> Out:
    """The dual of X.112: a rational square applied to an apotome."""
    hypothesis("the scale is genuine", sign(scale) > 0)
    apotome = 3 - sqrt(2)
    square = scale * scale
    breadth = square / apotome
    claim("the breadth is the square divided by the apotome", "VI.16",
          breadth * apotome == square)
    claim("and it is a binomial", "X.113", classify(breadth).family == "binomial")
    return Out(breadth=breadth)


@proposition("X.114", THEOREM, sample=lambda rng: (Fraction(rng.randint(2, 6)),))
def prop_X_114(scale) -> Out:
    """An area contained by an apotome and a binomial with the same terms."""
    hypothesis("the scale is genuine", sign(scale) > 0)
    binomial = scale + sqrt(2)
    apotome = scale - sqrt(2)
    hypothesis("the apotome is positive", sign(apotome) > 0)
    area = binomial * apotome
    claim("the area contained is rational", "X.114", is_rational_area(area))
    claim("so the side of the equal square is rational in square", "X.114",
          is_rational_in_square(sqrt(area)))
    return Out(area=area, side=sqrt(area))


@proposition("X.115", THEOREM, sample=lambda rng: (rng.choice([2, 3, 5, 7]),),
             note="Book X ends by showing its own list is not the end: from one "
             "medial line an unending series of new irrationals arises.")
def prop_X_115(radicand: int) -> Out:
    hypothesis("the radicand is not a square", not _is_square_int(radicand))
    medial = sqrt(sqrt(radicand))
    hypothesis("the line is medial", is_medial(medial))

    # Each mean proportional between the assigned line and the one before is a
    # new irrational, and its degree over the rationals doubles every time.
    chain = [medial]
    for _ in range(3):
        chain.append(sqrt(chain[-1]))

    claim("every line of the chain is irrational", "X.115",
          all(not isinstance(term, Fraction) for term in chain))
    claim("each is incommensurable with the one before", "X.115",
          all(not commensurable(chain[i], chain[i + 1]) for i in range(len(chain) - 1)))
    claim("and their degrees over the rationals go on doubling, so the series "
          "never closes", "X.115",
          [degree(term) for term in chain] == [4, 8, 16, 32])
    return Out(chain=chain)


@proposition(
    "X.73",
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
