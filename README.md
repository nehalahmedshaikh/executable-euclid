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

**The complete Elements is executable.** The generated site is at
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

The executable corpus covers every book in full. The generated site's
index is the authoritative coverage report; it derives its totals directly from
the proposition registry rather than repeating them here.

Book XI is where Euclid stops having postulates: the five are postulates of the
plane, and Book XI opens with definitions and then argues. Constructions in space
therefore expose assumptions in the ledger that planar constructions do not.
Books V and VII to X argue about ratios, numbers, and magnitudes, so they draw
nothing, as Euclid draws nothing there; what they check is exact all the same.

## What "checked" means

Each proposition runs on many figures that fit its assumptions, and every step is
tested exactly against the figure that was built. So a conclusion is confirmed
true of the figure. Whether it *follows from the postulates by Euclid's rules of
inference* is a separate question, and the machine is silent on it.

**Dependencies are recorded in two forms.** An executed edge carries out the
proposition it appeals to on the current figure, enforcing its hypotheses and
checking its conclusions. A cited edge records Heath's marginal reference and
checks only that it names an existing, earlier proposition. The generated graph
reports the current provenance and dependency totals directly from those records.

**The necessity analysis is empirical.** It bends each stated hypothesis and
watches the conclusion. A separating configuration is evidence; failure to find
one may mean the remaining hypotheses imply the one being bent. The generated
findings page is the authoritative report of trial strength, coverage, candidates,
and implied verdicts.

**Certified and actually tested are not the same.** A claim that cannot come out
false, or a hypothesis no sampled figure can satisfy, passes every run while
checking nothing, and some claims did: Book X applied an area to the
rational line, gave the result a second name, and compared the two names.
[`tests/test_corpus.py`](tests/test_corpus.py) follows each name back to what it
was assigned, and sorts sums and products, before comparing the two sides of a
claim — which is what makes that shape visible where reading the line does not.
A claim can also be forced for a reason no rewriting reaches, so
`euclid measure --unfalsified` bends the figure underneath every claim in the
corpus and reports the ones that no bend of it made false.

## Where the words come from

Proposition statements are Thomas L. Heath's 1908 translation, out of copyright,
parsed from a local epub by [`tools/fetch_heath.py`](tools/fetch_heath.py) — one source for the complete corpus. The scanning errors found so
far are corrected and listed, with the method that caught them, on the
[text page](https://nehalahmedshaikh.github.io/executable-euclid/text.html).

## Running it

Python 3.11 or newer. **No dependencies at all.**

On Linux and macOS, create an isolated environment first:

```console
$ python3 -m venv .venv
$ source .venv/bin/activate
$ python -m pip install -e ".[dev]"
$ pytest
$ euclid list I
$ euclid run I.47              # construct it and check every step
$ euclid why I.47              # what it rests on
$ euclid ngon 17               # constructible; 7 is not, and it says why
$ euclid classify "sqrt(3)+sqrt(5)"   # Book X's name for a magnitude
$ euclid measure --depth       # algebraic degree, book by book
$ euclid site --out docs       # build the website locally (docs/ is ignored)
```

On Windows, create the same environment with `py -m venv .venv` and activate it
with `.venv\Scripts\Activate.ps1`. GitHub Actions builds the site once, audits
that exact output, and deploys it to GitHub Pages; generated HTML is not kept in
Git.

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
docs/        a local website build (generated and ignored)
```

## Licence

MIT for the code. Heath's translation is public domain.
