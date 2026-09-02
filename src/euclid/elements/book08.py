"""Book VIII: numbers in continued proportion, and the squares and cubes.

What a geometric progression of whole numbers can and cannot do -- the
arithmetical half of the similar-figures argument of Book VI.
"""

from __future__ import annotations

from .book07 import (
    prop_VII_17,
    prop_VII_18,
    prop_VII_20,
    prop_VII_21,
    prop_VII_27,
    prop_VII_34,
)
from .arithmetic import (
    common_measure,
    continued_proportion,
    coprime,
    in_continued_proportion,
    is_cube,
    is_square,
    lcm,
    least_terms,
    measures,
    progression,
    similar_planes,
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


@proposition(
    "VIII.1",
    THEOREM,
    sample=progression,
    note="The extremes of a progression being coprime is what makes it the least "
    "of its kind -- and VIII.3 is the converse.",
)
def prop_VIII_1(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is a genuine one", p > 1 and q > 1, guard=True)
    hypothesis("a genuine progression is asked for", count >= 3, guard=True)
    terms = continued_proportion(1, (p, q), count)
    hypothesis("the extremes are prime to one another", coprime(terms[0], terms[-1]))

    # Consecutive terms are *not* coprime -- p^k q^(n-1-k) and its successor
    # share p^k q^(n-2-k). What makes the progression least is that the whole
    # set has no common measure, which the extremes being coprime forces.
    because(prop_VII_20, terms[0], terms[-1], terms[0], terms[-1])
    because(prop_VII_21, terms[0], terms[-1]) if coprime(terms[0], terms[-1]) else None

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
    sample=progression,
)
def prop_VIII_2(p: int, q: int, count: int) -> Out:
    """Find the least numbers in continued proportion in a given ratio."""
    hypothesis("the ratio is a genuine one", p > 1 and q > 1, guard=True)
    # Leastness is what this proposition sets out to produce, and the
    # construction delivers it only for a ratio already in least terms. Euclid's
    # own enunciation says "the least that are in a given ratio", so this is his
    # condition and not our bookkeeping.
    hypothesis("the given ratio is in least terms", coprime(p, q))
    hypothesis("a genuine progression is asked for", count >= 3, guard=True)
    terms = continued_proportion(1, (p, q), count)

    because(prop_VIII_1, p, q, count) if coprime(p, q) else None

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
    sample=progression,
)
def prop_VIII_3(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is a genuine one", p > 1 and q > 1, guard=True)
    hypothesis("a genuine progression is asked for", count >= 3, guard=True)
    terms = continued_proportion(1, (p, q), count)
    hypothesis("they are the least of their ratio", common_measure(terms) == 1)
    because(prop_VII_21, p, q) if coprime(p, q) else None
    because(prop_VII_27, p, q) if coprime(p, q) else None

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
    hypothesis("the ratios are genuine", all(n > 1 for n in (a, b, c, d)), guard=True)
    first, second = least_terms(a, b)
    third, fourth = least_terms(c, d)
    # The middle term must be measured by both consequents, so take the least
    # number they both measure and scale each ratio up to meet it.
    middle = lcm(second, third)
    terms = [first * (middle // second), middle, fourth * (middle // third)]

    because(prop_VII_18, a, b, c)
    because(prop_VII_34, a, b)

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
    hypothesis("the sides are genuine numbers", all(n > 1 for n in (a, b, c, d)), guard=True)
    first, second = a * b, c * d
    because(prop_VII_17, a, b, c)
    because(prop_VII_18, a, b, c)

    claim("the plane numbers have the ratio compounded of the ratios of the sides",
          "VII.17", first * (c * d) == second * (a * b))
    claim("which is to say, the product of the two ratios", "VII.18",
          first * d * c == second * a * b)
    return Out(planes=(first, second))


@proposition(
    "VIII.6",
    THEOREM,
    sample=progression,
)
def prop_VIII_6(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is a genuine one", p > 1 and q > 1, guard=True)
    hypothesis("a genuine progression is asked for", count >= 3, guard=True)
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
    hypothesis("the ratio and length are genuine", ratio > 1 and count >= 3, guard=True)
    terms = continued_proportion(1, (ratio, 1), count)
    hypothesis("the first measures the last", measures(terms[0], terms[-1]))

    claim("then it measures the second also", "VIII.7", measures(terms[0], terms[1]))
    claim("and indeed every one of them", "VIII.6",
          all(measures(terms[0], term) for term in terms))
    return Out(terms=terms)


@proposition(
    "VIII.8",
    THEOREM,
    sample=progression,
)
def prop_VIII_8(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is a genuine one", p > 1 and q > 1, guard=True)
    hypothesis("a genuine progression is asked for", count >= 3, guard=True)
    terms = continued_proportion(1, (p, q), count)
    scaled = [term * 3 for term in terms]
    because(prop_VII_18, p, q, count)

    claim("as many fall between the scaled pair as between the original", "VIII.8",
          len(scaled) == len(terms) and in_continued_proportion(scaled))
    claim("and the outer ratio is unchanged", "VII.18",
          terms[0] * scaled[-1] == terms[-1] * scaled[0])
    return Out(between=scaled[1:-1])


@proposition(
    "VIII.9",
    THEOREM,
    sample=progression,
)
def prop_VIII_9(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is a genuine one", p > 1 and q > 1, guard=True)
    hypothesis("a genuine progression is asked for", count >= 3, guard=True)
    terms = continued_proportion(1, (p, q), count)
    hypothesis("the extremes are prime to one another", coprime(terms[0], terms[-1]))
    # p^(n-1) and q^(n-1) are the extremes; each reaches down to a unit through
    # its own powers, and there are as many steps as there were between them.
    to_unit_first = [q ** k for k in range(count)]
    to_unit_last = [p ** k for k in range(count)]
    because(prop_VIII_2, p, q, count) if coprime(p, q) else None

    claim("a progression runs from a unit up to each extreme", "VIII.2",
          in_continued_proportion(to_unit_first) and in_continued_proportion(to_unit_last)
          and to_unit_first[0] == 1 and to_unit_last[0] == 1)
    claim("with as many terms between as fell between the extremes", "VIII.9",
          len(to_unit_first) == count and len(to_unit_last) == count)
    return Out(first=to_unit_first, last=to_unit_last)


@proposition(
    "VIII.10",
    THEOREM,
    sample=progression,
)
def prop_VIII_10(p: int, q: int, count: int) -> Out:
    """The converse of VIII.9."""
    hypothesis("the ratio is a genuine one", p > 1 and q > 1, guard=True)
    hypothesis("a genuine progression is asked for", count >= 3, guard=True)
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
    hypothesis("the sides are genuine numbers", a > 1 and b > 1, guard=True)
    first, second = a * a, b * b
    mean = a * b
    because(prop_VIII_8, a, b, 3)

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
    hypothesis("the sides are genuine numbers", a > 1 and b > 1, guard=True)
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
    sample=progression,
)
def prop_VIII_13(p: int, q: int, count: int) -> Out:
    hypothesis("the ratio is a genuine one", p > 1 and q > 1, guard=True)
    hypothesis("a genuine progression is asked for", count >= 3, guard=True)
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
    hypothesis("the sides are genuine numbers", a > 1 and b > 1, guard=True)
    claim("if the square measures the square, the side measures the side", "VIII.14",
          measures(a * a, b * b) == measures(a, b))
    return Out()


@proposition(
    "VIII.15",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 10), rng.randint(2, 10)),
)
def prop_VIII_15(a: int, b: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1, guard=True)
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
    hypothesis("the sides are genuine numbers", a > 1 and b > 1, guard=True)
    because(prop_VIII_14, a, b)

    claim("if the square does not measure the square, neither does the side",
          "VIII.14", (not measures(a * a, b * b)) == (not measures(a, b)))
    return Out()


@proposition(
    "VIII.17",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 10), rng.randint(2, 10)),
)
def prop_VIII_17(a: int, b: int) -> Out:
    hypothesis("the sides are genuine numbers", a > 1 and b > 1, guard=True)
    because(prop_VIII_15, a, b)

    claim("if the cube does not measure the cube, neither does the side", "VIII.15",
          (not measures(a ** 3, b ** 3)) == (not measures(a, b)))
    return Out()


@proposition(
    "VIII.18",
    THEOREM,
    sample=similar_planes,
    note="'Similar plane numbers' are rectangles of the same shape, and they "
    "behave exactly as similar rectangles do in Book VI.",
)
def prop_VIII_18(a: int, b: int, c: int, d: int) -> Out:
    """The planes are AB and CD; the sides are given, not multiplied out."""
    hypothesis("the sides are genuine numbers",
               a > 1 and b > 1 and c > 1 and d > 1, guard=True)
    hypothesis("the sides are proportional, so the planes are similar",
               a * d == b * c)
    first, second = a * b, c * d
    mean = a * d
    because(prop_VIII_11, a, b)

    claim("one mean proportional falls between them", "VIII.18",
          first * second == mean * mean)
    claim("and plane is to plane in the duplicate ratio of the sides", "VIII.11",
          first * (c * c) == second * (a * a))
    return Out(mean=mean)


@proposition(
    "VIII.19",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 6), rng.randint(2, 6), rng.randint(2, 6),
                        rng.randint(2, 4)),
)
def prop_VIII_19(a: int, b: int, c: int, scale: int) -> Out:
    """Similar solid numbers: three sides each, in proportion."""
    hypothesis("the sides are genuine numbers", all(n > 1 for n in (a, b, c, scale)), guard=True)
    first = a * b * c
    second = (a * scale) * (b * scale) * (c * scale)
    means = [first * scale, first * scale * scale]
    because(prop_VIII_12, a, b)

    claim("two mean proportionals fall between them", "VIII.19",
          in_continued_proportion([first] + means + [second]))
    claim("and solid is to solid in the triplicate ratio of the sides", "VIII.12",
          second == first * scale ** 3)
    return Out(means=means)


def _with_a_mean_proportional(rng):
    """Two numbers with one mean proportional between them, all three given."""
    a, b = rng.randint(2, 12), rng.randint(2, 12)
    return a * a, b * b, a * b


@proposition(
    "VIII.20",
    THEOREM,
    sample=lambda rng: _with_a_mean_proportional(rng),
)
def prop_VIII_20(first: int, second: int, mean: int) -> Out:
    """The converse of VIII.18: a mean proportional makes the numbers similar planes.

    The two numbers and their mean are given.  Building them from a pair of
    sides made the conclusion -- that sides can be found -- true of the sides
    already in hand, so the search below never had to succeed.
    """
    hypothesis("the numbers are genuine", first > 1 and second > 1, guard=True)
    hypothesis("a mean proportional falls between them", first * second == mean * mean)
    # Def. VII.21 asks for sides in proportion, so they have to be produced.
    # A side is a number, so neither may be a unit.
    sides = None
    for width in range(2, first):
        if first % width:
            continue
        length = first // width
        for other in range(2, second):
            if second % other:
                continue
            partner = second // other
            if length > 1 and partner > 1 and width * partner == length * other:
                sides = ((width, length), (other, partner))
                break
        if sides:
            break
    claim("the two are similar plane numbers, with proportional sides", "Def.VII.21",
          sides is not None
          and sides[0][0] * sides[0][1] == first
          and sides[1][0] * sides[1][1] == second
          and sides[0][0] * sides[1][1] == sides[0][1] * sides[1][0])
    return Out(sides=sides)


@proposition(
    "VIII.21",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 8), rng.randint(2, 8)),
)
def prop_VIII_21(a: int, b: int) -> Out:
    """The converse of VIII.19."""
    hypothesis("the sides are genuine numbers", a > 1 and b > 1, guard=True)
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
    hypothesis("the sides are genuine numbers", a > 1 and b > 1, guard=True)
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
    hypothesis("the sides are genuine numbers", a > 1 and b > 1, guard=True)
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
    hypothesis("the numbers are genuine", a > 1 and b > 1 and scale > 1, guard=True)
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
    hypothesis("the numbers are genuine", a > 1 and b > 1 and scale > 1, guard=True)
    first, second = (a * scale) ** 3, (b * scale) ** 3
    hypothesis("the two have the ratio of a cube to a cube",
               first * b ** 3 == second * a ** 3)
    hypothesis("the first is cube", is_cube(first))
    claim("the second is cube also", "VIII.25", is_cube(second))
    return Out()


@proposition(
    "VIII.26",
    THEOREM,
    sample=similar_planes,
)
def prop_VIII_26(a: int, b: int, c: int, d: int) -> Out:
    hypothesis("the sides are genuine numbers",
               a > 1 and b > 1 and c > 1 and d > 1, guard=True)
    hypothesis("the sides are proportional, so the planes are similar",
               a * d == b * c)
    first, second = a * b, c * d
    because(prop_VIII_18, a, b, c, d)

    claim("similar plane numbers have the ratio of a square to a square", "VIII.18",
          first * (c * c) == second * (a * a)
          and is_square(a * a) and is_square(c * c))
    return Out(ratio=(a * a, c * c))


@proposition(
    "VIII.27",
    THEOREM,
    sample=lambda rng: (rng.randint(2, 6), rng.randint(2, 6), rng.randint(2, 6),
                        rng.randint(2, 4)),
)
def prop_VIII_27(a: int, b: int, c: int, scale: int) -> Out:
    hypothesis("the sides are genuine numbers", all(n > 1 for n in (a, b, c, scale)), guard=True)
    first = a * b * c
    second = (a * scale) * (b * scale) * (c * scale)
    because(prop_VIII_19, a, b, c, scale)

    claim("similar solid numbers have the ratio of a cube to a cube", "VIII.19",
          first * scale ** 3 == second and is_cube(scale ** 3))
    return Out(ratio=(1, scale ** 3))
