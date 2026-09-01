# Executable Euclid

**Euclid's *Elements*, turned into software that runs.**

Other Euclid projects render the *Elements* as something to look at — a nicer web
edition, coloured diagrams, interactive applets. This one runs it. Each
proposition is a small program that draws its own figure with a straightedge and
compass, checks its own conclusion, and reports what it needed to get there.
Nothing is measured, rounded, or approximated.

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

**Books I to X are complete: 390 propositions.** The generated site is at
[**nehalahmedshaikh.github.io/executable-euclid**](https://nehalahmedshaikh.github.io/executable-euclid/).

---

## The one idea everything rests on

A straightedge and compass can only produce certain lengths: the ones you reach
from whole numbers by adding, subtracting, multiplying, dividing, and taking
square roots. This project stores those lengths **exactly** — as square roots
piled on square roots — never as decimals. That sounds like a small choice and it
is the whole project: two lengths are either equal or they are not, so there is
no tolerance to set, no rounding, and no near miss that might be mistaken for a
theorem.

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

## What it found

Running the corpus answers questions the text cannot: how algebraically deep each
book goes, which of Euclid's stated hypotheses his conclusions turn out not to
need, where Book X's taxonomy of irrationals stops naming things, and how short
his constructions could have been. Each is written up on the
**[findings page](https://nehalahmedshaikh.github.io/executable-euclid/findings.html)**
with the command that reproduces it, graded by how strong the claim is.

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
| XIII | **12 / 18** | the golden section, the pentagon, the regular solids |

**402 propositions**, 6453 checked steps. Book XIII divides at its twelfth
proposition: everything before that is plane geometry and is done, and
everything after it, with Books XI and XII, is solid and waits on a kernel that
leaves the plane. Books V and VII to X argue about numbers and magnitudes, so
they draw nothing, as Euclid draws nothing there; what they check is exact all
the same.

## What "checked" means

Each proposition runs on many figures that fit its assumptions, and every step is
tested exactly against the figure that was built. So a conclusion is confirmed
true of the figure. Whether it *follows from the postulates by Euclid's rules of
inference* is a separate question, and the machine is silent on it.

**Dependencies are two different things, and only one is an observation.** 68
edges are **executed** — one proposition calls another and the call is recorded
as it happens. 400 are **cited** — a reference written by hand beside a step,
following Heath's margins. A citation is checked for naming a proposition that
exists and for not naming a later one, and that is all: `claim` records its
warrant without consulting it, so a step could cite the wrong result and stay
green. **15% of the graph is executed**, and the work of raising that is under
way — a cited step becomes an executed one by calling the proposition it appeals
to, which makes the appeal itself checkable. Nothing on the findings page rests
on the rest: *"148 propositions depend on I.1"* is true, and it reads Euclid's
own cross-references back.

**The necessity analysis is empirical and partial.** A hypothesis that survives
being broken is reported as a candidate, with the number of configurations behind
it. Coverage is 45%: a run that breaks two hypotheses at once cannot attribute
the outcome to either, so it is discarded, and what cannot be broken alone is
reported as untested.

**Certified and actually tested are not the same.** A claim that cannot come out
false, or a hypothesis no sampled figure can satisfy, passes every run while
checking nothing. Both have happened here;
[`tests/test_corpus.py`](tests/test_corpus.py) reads every claim in the corpus
for the shapes that cannot fail.

## Where the words come from

Proposition statements are Thomas L. Heath's 1908 translation, out of copyright,
parsed from a local epub by [`tools/fetch_heath.py`](tools/fetch_heath.py) — one
source, all thirteen books, **465 enunciations**. The scanning errors found so
far are corrected and listed, with the method that caught them, on the
[text page](https://nehalahmedshaikh.github.io/executable-euclid/text.html).

## Running it

Python 3.11 or newer. **No dependencies at all.**

```console
$ pip install -e ".[dev]"
$ pytest
$ euclid list I
$ euclid run I.47              # construct it and check every step
$ euclid why I.47              # what it rests on
$ euclid ngon 17               # constructible; 7 is not, and it says why
$ euclid classify "sqrt(3)+sqrt(5)"   # Book X's name for a magnitude
$ euclid measure --depth       # algebraic degree, book by book
$ euclid site --out docs       # rebuild the website
```

## How it is put together

```
src/euclid/
  kernel/    exact arithmetic; degrees; which polygons are possible
  plane/     points, lines, circles; the postulates as operations;
             exact tests and exact angles; a record of what was drawn
  elements/  the propositions, one module per book; arithmetic.py and
             figures.py hold what more than one book needs
  verify/    running propositions on many figures; the assumptions table
  measure/   the analyses behind the findings, and the file they are recorded in
  graph/     the map of what depends on what
  search/    the shortest-construction search and its instruction sets
  render/    diagrams from records, and the website
tools/       fetch_heath.py — parses the translation from a local epub
docs/        the generated website
```

## Licence

MIT for the code. Heath's translation is public domain.
