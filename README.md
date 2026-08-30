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

The [findings page](docs/findings.html) has these written up, each with the
command that reproduces it. Three kinds of claim appear, and they are not equally
strong: **exhaustive** means every possibility was enumerated, so a negative is a
theorem; **measured** means computed exactly from the constructions as they run;
**empirical** means sampled over configurations, so it is evidence, and it says
how much.

Nothing here is read off the `cites` annotations. Those are written by hand
beside each step, following Heath's marginal references, so a finding drawn from
them would be a finding about our own typing. See [what is *not*
here](#what-this-is-not) below.

**Measured — the *Elements* leaves the rationals on its first page.** Every
magnitude these constructions produce is an exact element of a tower of quadratic
extensions of the rationals, so it has a degree, and the kernel can state it.
Running all 390 propositions gives a map of the work by algebraic depth:

| Book | I | II | III | IV | V | VI | VII | VIII | IX | X |
|---|---|---|---|---|---|---|---|---|---|---|
| **Highest degree** | 4 | 4 | 2 | 8 | 4 | 2 | 1 | 1 | 1 | 32 |

I.1 already needs √3, and I.2 already needs a second square root standing on the
first. Yet Books III and VI — all those circles, all that similarity — never
exceed degree 2, and Books VII to IX never leave the rationals at all, which is
what arithmetic ought to look like. The deepest point in the work is **X.115, at
degree 32**. The text cannot tell you this; it is a property of what the
constructions *do*.

```console
$ euclid measure --depth
```

**Exhaustive — Book X cannot name every constructible number.** Book X sorts the
irrationals into thirteen named species and is often described as though that
were all of them. Searching constructible numbers by increasing complexity, the
first one Euclid has no word for is

```console
$ euclid gap
1 + sqrt2 + sqrt3   ~ 4.1462643699
  Book X calls this : an irrational outside Euclid's thirteen species
  because           : it resolves into 3 terms, where Book X's definitions
                      treat two
  degree over Q     : 4
  minimal polynomial: x^4 - 4*x^3 - 4*x^2 + 16*x - 8 = 0
```

It is constructible with straightedge and compass. Euclid classifies what comes
out of applying areas — sums and differences of *two* terms — so a number needing
three falls outside however constructible it is.

**Empirical — II.9 and II.10 are one proposition, written twice.** Both say the
squares on the two segments of a divided line are double the square on the half
together with the square on the piece between the points of section. II.9 states
it for a point taken *between* the ends; II.10 for a point taken beyond them.
Break that hypothesis and run anyway: the conclusion holds either way, in every
configuration tried. The identity does not care where the point falls. Euclid
needs two propositions because he has no negative length to let one cover both;
in exact arithmetic the distinction disappears.

**Empirical — breaking Euclid's hypotheses on purpose.** A proposition says
nothing about the configurations its hypotheses exclude, so those are normally
thrown away and one question goes unasked: *would the conclusion have held
anyway?* Move one given until a hypothesis breaks, then run without enforcing it.

Across the corpus 729 hypotheses are stated; **260 could be broken cleanly enough
to judge (36% coverage)** — a run that breaks two at once says nothing about
either and is discarded. Of those, **162 proved necessary** and 21 turned out to
be holding the construction together rather than the conclusion up. **77 survived
being broken.** Those are *candidates*, not results, and the honest first reading
of one is that our claims are too weak to notice the difference — which is
exactly what happened the first time this ran: seven propositions of Book III
were checking things true of any four points, circle or no circle. They were
strengthened, and their hypotheses became necessary.

```console
$ euclid measure --needless
```

**Measured — Euclid uses something his own rules do not give him.** His
postulates let you draw a circle. None of them says two circles ever cross. He
needs them to cross in I.1, on the first page, and simply takes it. Every step
using an intersection the postulates do not license is counted as it happens:
**355 places** across Books I to X.

**Measured — four proofs take more than one route through the diagram.** Each
proposition is run on many configurations and the runs compared, looking for a
step that holds in one figure and fails in another. **Four do: III.23, III.32,
III.34 and VI.9.** Three evaluate a different number of facts depending on where
the points fall — III.34 checks between four and nine things about the same
theorem — so the argument is branching on the picture. III.32 is the sharper
case: a step asserting two points lie on the same side of a line is true in some
configurations and false in others, which is the shape of the gap Pasch's axiom
was later written to close.

The other 386 do take the same route through every figure. That negative half
earns a caveat: as the corpus grew, more samplers came to be *built* to satisfy
their hypotheses rather than stumbling into them, so the configurations are less
adversarial than they were in Book I.

**Exhaustive — I.1 cannot be beaten, and the compass alone costs seven circles.**

| Problem | Euclid | His moves | Fewest possible |
|---|---|---|---|
| equilateral triangle | I.1 | 4 | **2** |
| perpendicular bisector | I.10 | 15 | **3** |
| midpoint | I.10 | 15 | **4** |
| perpendicular at a point | I.11 | 7 | **5** |
| square on a segment | I.46 | 10 | **5** |
| midpoint, *compass alone* | — | — | **7** |

Every construction up to the stated length was enumerated, so *fewest possible*
is a theorem and not a search that gave up. That last row is the interesting one:
Mohr (1672) and Mascheroni (1797) proved the compass alone can find anything a
straightedge and compass can, and enumeration puts a price on it. Six circles are
not enough, and all of them were tried. Some of Euclid's own constructions are
far longer than they need to be, because he builds them out of results already
proved rather than reaching for the quickest route.

### What this is not

The dependency graph has two kinds of edge and the difference matters. **53 are
executed** — one proposition calls another as a function and the call is recorded
as it happens. **383 are cited** — a reference written by hand beside a step,
following Heath's margins. Citations are checked (every one must name a
proposition that exists, and no proposition may cite a later one) but they are
transcription, not discovery, and **only 12% of the graph is executed**.

So statements like *"136 propositions depend on I.1"* or *"the parallel postulate
first appears at I.29"* are true, and are Euclid's own cross-references read back
in a tidy order. They used to be listed above as findings. They are not findings,
and they have been removed.

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
the reference names a proposition that does not exist, or one that comes *later*
in the book, which are different and much smaller guarantees. This is why nothing
in [What came out of it](#what-came-out-of-it) is derived from citations.

The **necessity analysis is empirical and partial**, and both words matter. A
hypothesis that survives being broken is a candidate, not a theorem: it means no
counterexample turned up among the configurations tried. Coverage is 36%, and the
missing 64% is mostly propositions like I.4, where moving any one point breaks
two hypotheses at once so no outcome can be attributed to either. Those are
reported as untested, never as unneeded — the difference is the whole credibility
of the analysis, and [`tests/test_measure.py`](tests/test_measure.py) pins it
down.

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
