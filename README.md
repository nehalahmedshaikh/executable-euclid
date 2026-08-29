# Executable Euclid

**Euclid's *Elements*, turned into software that runs.**

Every other Euclid project renders the *Elements* as something to look at — a
nicer web edition, coloured diagrams, interactive applets. This one runs it.

Each proposition is a small program. It draws its own figure with a straightedge
and compass, checks its own conclusion, and reports what it needed to get there.
Nothing is measured, rounded, or approximated. The books that argue about
numbers and magnitudes rather than figures — V, VII to IX, and most of X — draw
nothing, as Euclid draws nothing there; what they check is exact all the same.

```console
$ euclid run I.47
I.47  In right-angled triangles the square on the side subtending the right angle
      is equal to the squares on the sides containing the right angle.
        (Heath, 1908)

  given  the angle ABC is right
  step   the squares are described on the three sides            [I.46]
  step   the perpendicular from B divides the square on AC …     [I.4, I.41, I.31]
  step   therefore the square on AC equals the squares on AB and BC together

  15 lines and circles drawn, 12 steps, all checked exactly.
```

---

## The one idea everything rests on

A straightedge and compass can only produce certain lengths: the ones you reach
from whole numbers by adding, subtracting, multiplying, dividing, and taking
square roots. This project stores those lengths **exactly** — as square roots
piled on square roots — and never as decimals.

That sounds like a small choice. It is the whole project. Two lengths are either
equal or they are not. There is no tolerance to set, no rounding, and no near
miss that might be mistaken for a theorem.

The hard part is keeping the representation tidy. Before inventing a new square
root, the machine checks whether the answer is already expressible with the ones
it has:

```python
>>> with Context() as ctx:
...     r2, r3 = sqrt(2), sqrt(3)
...     sqrt(8) == 2 * r2                  # 8 is not new: it is 4 × 2
True
...     sqrt(5 + 2 * sqrt(6)) == r2 + r3   # untangles by itself
True
...     ctx.tower.depth                    # still only two roots in play
2
```

---

## What came out of it

There is a [findings page](docs/findings.html) with all of these written up.

**The first proposition holds up the whole book.** Of the 390 propositions written
out here, **136 depend on I.1**, the equilateral triangle. Nothing else comes
close. That ranking was not assigned by anyone — it is what the call graph looks
like after every proposition has run.

**The parallel postulate announces itself.** Euclid holds his fifth and most
argued-over rule back until I.29. Nobody told the machine that. It reads the
references each proof cites, and the line lands exactly where historians say it
does: I.27 and I.28 manage without it, everything from I.29 on needs it.

**Pythagoras needs a quarter of the book.** Follow I.47 back through everything
it uses and **25 propositions** remain out of 390. Delete the rest and it still
stands.

**Euclid uses something his own rules do not give him.** His postulates let you
draw a circle. None of them says two circles ever cross. He needs them to cross
in I.1, on the first page, and simply takes it. Counting every such step gives
**355 places** where a point is used that no rule promises exists.

**Nothing in the book quietly changes its mind.** Each proposition is run on many
different figures and the runs compared, looking for a step that holds in one
picture but not another. There are none. That is a negative result, but a real
one, and the detector that produced it is tested directly.

**Euclid's first construction cannot be beaten.** Trying every construction of
two moves or fewer confirms the two circles of I.1 are the shortest way to build
an equilateral triangle.

| Problem | Euclid | His moves | Fewest possible |
|---|---|---|---|
| equilateral triangle | I.1 | 4 | **2** |
| perpendicular bisector | I.10 | 15 | **3** |
| midpoint | I.10 | 15 | **4** |
| perpendicular at a point | I.11 | 7 | **5** |
| square on a segment | I.46 | 10 | **5** |
| midpoint, *compass alone* | — | — | **7** |

That last row is the interesting one. Mohr (1672) and Mascheroni (1797) proved
the compass alone can find anything a straightedge and compass can. Searching
every possibility confirms it and puts a price on it: with no straight line
permitted, finding the middle of a segment takes **exactly seven circles**. Six
is not enough, and every six-circle construction was checked.

**A bug the mathematics caught.** Partway through Book II a length came out
negative. Every square root has two answers, and the routine that looks for one
inside the existing numbers had returned the wrong one. A version working in
decimals would never have noticed — an ordinary square root function always
hands back the positive answer.

---

## Book X, running

Book X is the longest in the *Elements*, 115 propositions, and the one everyone
skips. It sorts irrational lengths into thirteen named kinds. It reads as
impenetrable because it is written about things nobody could calculate with.

Each of Euclid's definitions turns out to be a yes-or-no question about whether
some sum or product is rational — exactly what the exact arithmetic can answer.
So the whole classification becomes one function:

```console
$ euclid classify "sqrt(3)+sqrt(5)"
  Book X calls this : sixth binomial
  because           : it is the sum of two rational lines commensurable in
                      square only; neither term is commensurable in length with
                      the assigned line, and sqrt(a² − b²) is incommensurable
                      with the greater

$ euclid classify "(1+sqrt(5))/2"      # the golden ratio: a fifth binomial
$ euclid classify "sqrt(18)+sqrt(2)"   # not a binomial — it is really 4·sqrt(2)
```

All thirteen names are implemented. The last six — *major*, *minor*, and the
four whose names are whole sentences — are the awkward ones: their two terms are
the roots of a single quadratic, so neither can be written without the other and
the sum has no seam to split it at. Squaring puts the seam back, and the pair
that comes out is checked by adding it up again.

## Impossible things

```console
$ euclid ngon 17        # constructible
$ euclid ngon 7         # impossible, and here is why
$ euclid impossible     # trisecting an angle, doubling the cube, the heptagon
```

Constructible lengths always have a degree that is a power of two. Doubling the
cube needs degree three, so it cannot be done. The machine works out the degree
rather than taking it on faith.

---

## What is covered

| Book | Encoded | |
|---|---|---|
| **I** | **48 / 48** | congruence, parallels, area, Pythagoras |
| **II** | **14 / 14** | geometric algebra, the golden section |
| **III** | **37 / 37** | circles, tangents, the power of a point |
| **IV** | **16 / 16** | inscribed and circumscribed figures |
| **V** | **25 / 25** | Eudoxus on proportion |
| **VI** | **33 / 33** | similar figures, application of areas |
| **VII** | **39 / 39** | the Euclidean algorithm, primes, proportion |
| **VIII** | **27 / 27** | continued proportions, squares and cubes |
| **IX** | **36 / 36** | primes, parity, perfect numbers |
| **X** | **115 / 115** | incommensurables, the thirteen irrationals |
| XI | 0 / 39 | solid geometry |
| XII | 0 / 18 | the method of exhaustion |
| XIII | 0 / 18 | the regular solids |

**390 propositions**, 6207 checked steps. **Books I to X are complete** — every
proposition of plane geometry, the theory of proportion, the arithmetical books,
and the whole of Book X. Books XI–XIII are solid geometry and the kernel is
planar by design, so they wait on a decision about that.

**Book V is worth a note.** Its famous Definition 5 asks about *all* pairs of
multiples at once, so it cannot be tested by trying them. But it can be settled
from the other side: two ratios differ exactly when some pair of multiples tells
them apart, and that pair can be *found*. The machine finds it, which turns a
definition into a procedure.

## Where the words come from

Proposition statements are Thomas L. Heath's 1908 translation, which is out of
copyright. They are parsed by [`tools/fetch_heath.py`](tools/fetch_heath.py),
not retyped or reworded — so what ships here is the published text.

One source, all thirteen books, **465 enunciations** — every proposition of the
*Elements*. The script reads a local epub and touches no network. Only the
enunciations are taken; a modern edition's introductions and notes are a
copyrighted compilation and are neither extracted nor committed.

**Nothing is paraphrased, anywhere.** There is no second kind of statement to
fall back to: a proposition has no parameter for its own wording, and looking up
one that is missing raises rather than inventing a stand-in. A summary cannot
reach a page by accident because there is no code path that would put one there.

Where the scan misprints Heath, the correction is published rather than hidden.
Three so far — `acutc` for `acute`, `cach` for `each`, and one lost full stop —
each listed on the site with what the scan says, what it was corrected to, and
why. The parser refuses to run if a correction stops applying, so a stale one
cannot sit there doing nothing.

Two of those three substitute a single letter and still spell a real word, so no
spell check would find them. What finds them is that Euclid's vocabulary is tiny
and endlessly repetitive — about four hundred distinct words across all 465
enunciations — so the script lists every word used *exactly once*. A misprint
has nowhere to hide in a list that short, and everything else in it is a genuine
term of art (`polyhedral`, `eventimes`, `anthyphairesis`).

## What "checked" means

Worth being straight about, since it is the main thing to poke at.

Each proposition runs on many figures that fit its assumptions, and every step is
tested exactly against the figure that was built. Because the arithmetic is
exact, there is nowhere for an error to hide.

But this tests the constructions, not Euclid's reasoning. It confirms the
conclusions are true of the figures; it does not confirm they follow by his rules
of inference. The references each step cites are recorded but not relied on — so
a step with the wrong reference attached still cannot slip a false statement past,
though the machine will not tell you the reference is wrong. It will tell you if
the reference names a proposition that does not exist, which is a different and
much smaller guarantee.

A second thing worth being straight about: *certified* and *actually tested* are
not the same. A claim that cannot come out false, or a hypothesis no sampled
figure can satisfy, passes every run while checking nothing. Both have happened
here, and both are now caught — [`tests/test_corpus.py`](tests/test_corpus.py)
reads every claim in the corpus looking for the shapes that cannot fail.

For the shortest-construction searches: where the result says *fewest possible*,
every construction of that length was examined, so it really is shortest and a
failure really does prove none exists. Where the search ran out of budget it says
so. Two limits apply throughout — points straying far outside the figure are
ignored, and figures with more than twenty points are abandoned — and either
could in principle hide something.

---

## Running it

Python 3.11 or newer. **No dependencies at all.**

```console
$ pip install -e ".[dev]"
$ pytest                      # 172 tests
$ euclid list I
$ euclid verify I
$ euclid why I.47
$ euclid site --out docs      # rebuild the website
```

## How it is put together

```
src/euclid/
  kernel/    exact arithmetic; degrees; which polygons are possible
  plane/     points, lines, circles; the postulates as operations;
             exact tests and exact angles; a record of what was drawn
  elements/  the propositions, one module per book
  verify/    running propositions on many figures; the assumptions table
  graph/     the map of what depends on what
  search/    the shortest-construction search and its instruction sets
  render/    diagrams from records, and the website
tools/       fetch_heath.py — downloads and parses the translation
docs/        the generated website
```

## Licence

MIT for the code. Heath's translation is public domain.
