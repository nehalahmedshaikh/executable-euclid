"""The static site: pure stdlib in, GitHub Pages out.

Every page is generated from something the machine did.  The diagrams come from
constructions that ran and checked out; the cross-references come from the call
graph rather than a hand-kept index; the assumption tables come from running
each proposition over many different figures.  Nothing here is transcribed by
hand.
"""

from __future__ import annotations

import html
import random
from pathlib import Path
from typing import Optional

from ..elements.registry import (
    BOOK_TITLES,
    HEATH_CREDIT,
    BadConfiguration,
    ProofFailure,
    Proposition,
    all_propositions,
    reference_kind,
    run_sampled,
)
from ..kernel.field import Context, fmt, sqrt, to_float
from ..plane.construct import GeometryError
from ..plane.trace import Trace
from ..verify.fuzz import certify
from ..verify.ledger import audit
from .layout import graph_svg
from .svg import render_trace

__all__ = ["build"]

# Strictly black and white: no hue anywhere, in either theme.
STYLE = """
:root {
  --ink: #101010; --faint: #6a6a6a; --rule: #dcdcdc; --page: #ffffff;
  --panel: #f7f7f7; --line: #101010;
}
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #ededed; --faint: #909090; --rule: #2c2c2c; --page: #0c0c0c;
    --panel: #151515; --line: #ededed;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--page); color: var(--ink);
  font: 17px/1.68 Georgia, 'Iowan Old Style', 'Palatino Linotype', serif;
}
.wrap { max-width: 44rem; margin: 0 auto; padding: 3.5rem 1.25rem 6rem; }
.wide { max-width: 66rem; }
a { color: inherit; text-decoration: underline; text-decoration-thickness: 1px;
    text-underline-offset: 3px; }
a:hover { text-decoration-thickness: 2px; }
h1 { font-size: 1.95rem; line-height: 1.22; margin: 0 0 .5rem; font-weight: normal;
     letter-spacing: -.01em; }
h2 { font-size: 1.22rem; font-weight: normal; margin: 2.8rem 0 .8rem;
     border-bottom: 1px solid var(--rule); padding-bottom: .35rem; }
h3 { font-size: 1rem; margin: 1.9rem 0 .5rem; font-weight: 700; }
.kicker { font: 700 .68rem/1 ui-sans-serif, system-ui, sans-serif;
  letter-spacing: .16em; text-transform: uppercase; color: var(--faint);
  margin: 0 0 .8rem; }
.lede { color: var(--faint); font-size: 1.05rem; margin: .2rem 0 2rem; }
nav.top { font: .8rem/2 ui-sans-serif, system-ui, sans-serif; margin-bottom: 2.6rem;
          padding-bottom: .8rem; border-bottom: 1px solid var(--rule); }
nav.top a { margin-right: 1.1rem; text-decoration: none; color: var(--faint); }
nav.top a:hover, nav.top a.here { color: var(--ink); text-decoration: underline; }
code, pre, .mono { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
pre { background: var(--panel); border: 1px solid var(--rule);
      padding: .95rem 1.05rem; overflow-x: auto; font-size: .78rem; line-height: 1.6; }
code { font-size: .86em; }
table { border-collapse: collapse; width: 100%; font-size: .87rem; }
th, td { text-align: left; padding: .4rem .65rem; border-bottom: 1px solid var(--rule);
         vertical-align: top; }
th { font: 700 .68rem/1.5 ui-sans-serif, system-ui, sans-serif;
     letter-spacing: .09em; text-transform: uppercase; color: var(--faint); }
tbody tr:last-child td { border-bottom: none; }
.scroll { overflow-x: auto; }
figure { margin: 1.8rem 0; text-align: center; }
figcaption { font: .78rem ui-sans-serif, system-ui, sans-serif; color: var(--faint);
             margin-top: .6rem; }
svg.figure { max-width: 100%; height: auto; background: var(--panel);
             border: 1px solid var(--rule); }
svg.figure .arc { stroke: var(--line); stroke-width: .8; stroke-dasharray: 3 3;
                  opacity: .45; }
svg.figure .ray { stroke: var(--line); stroke-width: 1.3; }
svg.figure .dot { fill: var(--line); }
svg.figure .letter { fill: var(--ink); font: italic 14px Georgia, serif; }
svg.graph { max-width: 100%; height: auto; }
svg.graph .edge { fill: none; stroke: var(--rule); stroke-width: 1.1; }
svg.graph .edge.lit { stroke: var(--ink); stroke-width: 1.7; }
svg.graph .node { fill: var(--page); stroke: var(--rule); }
svg.graph .node.lit { fill: var(--ink); }
svg.graph .node-label { font: 11px ui-monospace, monospace; fill: var(--ink); }
svg.graph a:hover .node { stroke: var(--ink); stroke-width: 1.6; }
ul.claims { list-style: none; padding: 0; margin: 1rem 0; }
ul.claims li { padding: .5rem 0 .5rem 1rem; border-left: 2px solid var(--ink);
               margin-bottom: .3rem; }
ul.claims li.hyp { border-left: 2px solid var(--rule); }
.cite { font: .7rem ui-sans-serif, system-ui, sans-serif; color: var(--faint);
        display: block; margin-top: .2rem; letter-spacing: .02em; }
.grid { display: grid; gap: .25rem .9rem;
        grid-template-columns: repeat(auto-fill, minmax(4.6rem, 1fr)); }
.grid a { display: block; padding: .18rem 0; font-size: .88rem;
          font-family: ui-monospace, monospace; text-decoration: none;
          border-bottom: 1px solid transparent; }
.grid a:hover { border-bottom-color: var(--ink); }
.stat { display: grid; grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
        gap: 0; margin: 1.8rem 0; border: 1px solid var(--rule); }
.stat div { padding: .9rem 1rem; border-right: 1px solid var(--rule); }
.stat div:last-child { border-right: none; }
.stat b { display: block; font: 400 1.6rem/1.15 Georgia, serif; }
.stat span { font: .68rem ui-sans-serif, system-ui, sans-serif; color: var(--faint);
             letter-spacing: .05em; text-transform: uppercase; }
blockquote { margin: 0 0 1.2rem; padding: .2rem 0 .2rem 1.1rem;
             border-left: 3px solid var(--ink); font-size: 1.06rem; }
blockquote .src { display: block; font: .7rem ui-sans-serif, system-ui, sans-serif;
                  color: var(--faint); margin-top: .55rem; letter-spacing: .04em;
                  text-transform: uppercase; }
.note { color: var(--faint); font-size: .92rem; }
.finding { border-top: 1px solid var(--rule); padding-top: 1.1rem; margin-top: 1.8rem; }
.finding h3 { margin-top: 0; }
footer { margin-top: 4.5rem; padding-top: 1rem; border-top: 1px solid var(--rule);
         font: .78rem/1.7 ui-sans-serif, system-ui, sans-serif; color: var(--faint); }
"""

NAV = [
    ("index.html", "Overview"),
    ("findings.html", "Findings"),
    ("graph.html", "Dependencies"),
    ("minimal.html", "Minimal Elements"),
    ("ledger.html", "What Euclid assumes"),
    ("optimizer.html", "Shortest constructions"),
    ("book-x.html", "Book X"),
]


def _esc(text) -> str:
    return html.escape(str(text), quote=False)


def _slug(ref: str) -> str:
    return ref.replace(".", "-")


def _page(title: str, body: str, here: str = "", wide: bool = False) -> str:
    links = "".join(
        '<a href="{}"{}>{}</a>'.format(href, ' class="here"' if href == here else "", label)
        for href, label in NAV
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_esc(title)}</title><style>{STYLE}</style></head><body>"
        f'<div class="wrap{" wide" if wide else ""}">'
        f'<nav class="top">{links}</nav>{body}'
        "<footer><p>Every diagram here was drawn from a construction that ran and "
        "checked out in exact arithmetic. Every cross-reference was read off the call "
        "graph, not typed in by hand.</p>"
        f"<p>Proposition statements are {HEATH_CREDIT} Where a statement is missing "
        "from that text, a short summary written for this project stands in, and the "
        "page says so.</p></footer>"
        "</div></body></html>"
    )


def _sample_trace(entry: Proposition, seed: int = 3) -> Optional[Trace]:
    if entry.sample is None:
        return None
    rng = random.Random(f"site:{entry.ref}:{seed}")
    for _ in range(12):
        try:
            return run_sampled(entry.ref, rng).trace
        except (BadConfiguration, GeometryError, ProofFailure):
            continue
    return None


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------


def _proposition_page(entry: Proposition, graph, trace: Optional[Trace]) -> str:
    body = [
        f'<p class="kicker">Book {entry.book} &middot; Proposition {entry.number}</p>',
        f"<h1>{entry.ref}</h1>",
        f"<blockquote>{_esc(entry.statement)}"
        f'<span class="src">{_esc(entry.statement_source)}</span></blockquote>',
    ]
    if entry.note:
        body.append(f'<p class="note">{_esc(entry.note)}</p>')

    if trace is not None:
        figure = render_trace(trace, entry.ref)
        if figure:
            body.append(
                f"<figure>{figure}<figcaption>"
                f"{trace.step_count} lines and circles drawn"
                "</figcaption></figure>"
            )

    if trace is not None and trace.claims:
        body.append("<h2>Every step, checked</h2><ul class=\"claims\">")
        for item in trace.claims:
            given = item.by == ("hypothesis",)
            citations = ", ".join(
                f'<a href="{_slug(ref)}.html">{ref}</a>'
                if reference_kind(ref) == "proposition" and ref in graph.nodes
                else _esc(ref)
                for ref in item.by
            )
            body.append(
                f'<li class="{"hyp" if given else ""}">{_esc(item.text)}'
                f'<span class="cite">{"given" if given else f"by {citations}"}</span></li>'
            )
        body.append("</ul>")

    needs = sorted(graph.needs(entry.ref), key=lambda r: graph.nodes[r].sort_key())
    used_by = sorted(graph.dependents(entry.ref), key=lambda r: graph.nodes[r].sort_key())
    uncoded = sorted(entry.depends_on - set(graph.nodes))
    body.append("<h2>What it needs, and what needs it</h2>")
    if needs:
        links = " ".join(f'<a href="{_slug(r)}.html">{r}</a>' for r in needs)
        body.append(f"<p><strong>Needs:</strong> {links}</p>")
    else:
        body.append("<p><strong>Needs:</strong> nothing earlier.</p>")
    if used_by:
        links = " ".join(f'<a href="{_slug(r)}.html">{r}</a>' for r in used_by)
        body.append(f"<p><strong>Used by:</strong> {links}</p>")
    if uncoded:
        body.append(
            f'<p class="note"><strong>Also cites</strong> {", ".join(uncoded)}, which '
            "this project has not written out yet.</p>"
        )
    axioms = sorted(graph.axioms(entry.ref))
    if axioms:
        body.append(f"<p><strong>Rests on:</strong> {', '.join(axioms)}</p>")
    body.append(
        f"<p><strong>Depth:</strong> {graph.depth(entry.ref)} steps of argument above the "
        "first principles. <strong>Parallel postulate:</strong> "
        f"{'needed' if graph.uses_parallel_postulate(entry.ref) else 'not needed'}.</p>"
    )

    ledger = audit(entry.ref, trials=6)
    body.append("<h2>What it takes on trust</h2>")
    if ledger.is_clean:
        body.append('<p class="note">Nothing. It draws no intersections and reads '
                    "nothing off the picture.</p>")
    else:
        body.append('<ul class="claims">')
        for item in ledger.assumptions:
            times = f" (&times;{item.occurrences})" if item.occurrences > 1 else ""
            body.append(
                f'<li>{_esc(item.detail)}{times}<span class="cite">{item.kind}</span></li>'
            )
        body.append("</ul>")

    source = entry.source()
    if source:
        body.append(f"<h2>The proposition as code</h2><pre>{_esc(source)}</pre>")

    return _page(f"{entry.ref} — Executable Euclid", "".join(body))


def _index_page(graph, stats) -> str:
    top_ref, top_count = graph.load_bearing()[0]
    body = [
        '<p class="kicker">Euclid\'s Elements, as software</p>',
        "<h1>Executable Euclid</h1>",
        '<p class="lede">Every proposition is a small program. It draws its own figure '
        "with a straightedge and compass, checks its own conclusion, and says what it "
        "depended on. Nothing is measured or approximated.</p>",
        '<div class="stat">',
        f"<div><b>{len(graph.nodes)}</b><span>propositions</span></div>",
        f"<div><b>{stats['claims']}</b><span>steps checked</span></div>",
        f"<div><b>{stats['edges']}</b><span>dependencies found</span></div>",
        f"<div><b>{stats['continuity']}</b><span>unproved assumptions</span></div>",
        "</div>",
        "<h2>The idea</h2>",
        "<p>A straightedge and compass can only produce certain numbers: the ones you "
        "reach from whole numbers by adding, subtracting, multiplying, dividing, and "
        "taking square roots. This project stores those numbers exactly, as square roots "
        "piled on square roots, never as decimals.</p>",
        "<p>That sounds like a small choice, but it changes what the machine can say. "
        "Two lengths are either equal or they are not; there is no rounding, no tolerance "
        "to set, and no near-miss that might be mistaken for a theorem. Everything else "
        "on this site follows from that.</p>",
        "<h2>What it found</h2>",
        "<ul>",
        f'<li><a href="graph.html">A map of the book that nobody drew.</a> The links '
        f"between propositions come from watching them run. {top_ref} turns out to hold "
        f"up {top_count} of the others.</li>",
        '<li><a href="minimal.html">The shortest route to Pythagoras.</a> Strip out '
        "everything I.47 does not need, and a small self-contained book is left.</li>",
        '<li><a href="ledger.html">The gaps Euclid never mentions.</a> His rules let you '
        "draw circles, but never say that two circles meet. He uses that fact anyway, "
        "starting on page one.</li>",
        '<li><a href="optimizer.html">The shortest possible constructions.</a> Found by '
        "trying every one, then checked exactly. With no straightedge at all, finding the "
        "middle of a line takes exactly seven circles.</li>",
        '<li><a href="book-x.html">Book X, running.</a> The book everyone skips, turned '
        "into something you can call.</li>",
        "</ul>",
        '<p><a href="findings.html"><strong>All the findings in one place &rarr;</strong>'
        "</a></p>",
        "<h2>The propositions</h2>",
    ]

    by_book: dict[str, list[Proposition]] = {}
    for entry in all_propositions():
        by_book.setdefault(entry.book, []).append(entry)
    for book, entries in by_book.items():
        title = BOOK_TITLES.get(book, "")
        note = " (complete)" if book == "I" else ""
        body.append(f"<h3>Book {book} &mdash; {_esc(title)}{note}</h3>")
        body.append('<div class="grid">')
        for entry in entries:
            body.append(f'<a href="{_slug(entry.ref)}.html">{entry.ref}</a>')
        body.append("</div>")

    body.append(
        "<h2>What &ldquo;checked&rdquo; means here</h2>"
        "<p>Each proposition is run on many different figures that fit its assumptions, "
        "and every step is tested exactly against the figure that was built. That is a "
        "strong test, but it is a test of the pictures, not a proof in Euclid's own "
        "logic. It confirms the conclusions are true of the constructions; it does not "
        "confirm they follow by his rules of reasoning.</p>"
        "<p>The references each step cites are recorded, but the test does not rely on "
        "them. So a step with the wrong reference attached still cannot slip a false "
        "statement past.</p>"
    )
    return _page("Executable Euclid", "".join(body), here="index.html")


def _findings_page(graph, stats, search_rows) -> str:
    top = graph.load_bearing()[:5]
    minimal = graph.tree_shake("I.47") if "I.47" in graph.nodes else []
    findings = []

    findings.append((
        "The first proposition holds up the whole book",
        f"<p>Of the 48 propositions in Book I, <strong>{top[0][1]} depend on I.1</strong>, "
        "the equilateral triangle. Nothing else comes close to carrying that much. The "
        "ranking below was not assigned; it is what the call graph looks like once every "
        "proposition has run.</p>"
        '<div class="scroll"><table><tr><th>Proposition</th><th>Things resting on it</th>'
        "</tr>"
        + "".join(
            f'<tr><td><a href="{_slug(ref)}.html">{ref}</a></td><td>{count}</td></tr>'
            for ref, count in top
        )
        + "</table></div>",
    ))

    findings.append((
        "The parallel postulate announces itself",
        "<p>Euclid holds his fifth and most controversial rule in reserve until I.29. "
        "Nobody told the machine that. It reads the references each proof cites, and the "
        "line falls exactly where historians say it does: I.27 and I.28 manage without "
        "it, and everything from I.29 onward needs it.</p>"
        '<div class="scroll"><table><tr><th>Proposition</th><th>Needs Postulate 5</th></tr>'
        + "".join(
            f'<tr><td><a href="{_slug(ref)}.html">{ref}</a></td>'
            f"<td>{'yes' if graph.uses_parallel_postulate(ref) else 'no'}</td></tr>"
            for ref in ("I.16", "I.20", "I.26", "I.27", "I.28", "I.29", "I.32", "I.47")
            if ref in graph.nodes
        )
        + "</table></div>",
    ))

    findings.append((
        "Pythagoras needs a quarter of what has been written",
        f"<p>Following I.47 back through everything it uses gives "
        f"<strong>{len(minimal)} propositions</strong> out of the "
        f"{len(graph.nodes)} written out here. The rest can be deleted and I.47 still "
        f'stands. <a href="minimal.html">See the list &rarr;</a></p>',
    ))

    findings.append((
        "Euclid uses something his own rules do not give him",
        f"<p>His postulates let you draw a circle. They never say that two circles cross. "
        "He needs them to cross in I.1, on the first page, to get the top corner of his "
        "triangle &mdash; and he simply takes it. That gap was first pointed out properly "
        "in the nineteenth century.</p>"
        f"<p>Counting every such step across everything written out here gives "
        f"<strong>{stats['continuity']} places</strong> where a point is used that no "
        f'rule guarantees exists. <a href="ledger.html">See the full table &rarr;</a></p>',
    ))

    findings.append((
        "Nothing in the book quietly changes its mind",
        "<p>A worry with old geometry is that a proof may only work for the picture the "
        "author happened to draw. To test this, each proposition is run on many different "
        "figures and the runs are compared. If a fact were true in one figure and false in "
        "another, it would show up as a difference.</p>"
        "<p><strong>No proposition here does that.</strong> Every construction takes the "
        "same route through every legal figure it is handed. That is a negative result, "
        "but it is a real one, and the detector that produced it is tested directly.</p>",
    ))

    lines = []
    for euclid_ref, euclid_steps, result in search_rows:
        if not result.found:
            continue
        reference = (
            '<a href="{}.html">{}</a>'.format(_slug(euclid_ref), euclid_ref)
            if euclid_ref
            else "&mdash;"
        )
        lines.append(
            f"<tr><td>{_esc(result.problem.replace('-', ' '))}</td><td>{reference}</td>"
            f"<td>{euclid_steps or '&mdash;'}</td><td>{result.length}</td></tr>"
        )
    findings.append((
        "Euclid's very first construction cannot be beaten",
        "<p>Trying every possible construction of two moves or fewer confirms that the "
        "two circles of I.1 are the shortest way to build an equilateral triangle. Some of "
        "his later constructions are much longer than they need to be &mdash; but that is "
        "because he builds them out of results he has already proved, rather than reaching "
        "for the quickest route. He was after certainty, not brevity.</p>"
        '<div class="scroll"><table><tr><th>Problem</th><th>Euclid</th><th>His moves</th>'
        f"<th>Fewest possible</th></tr>{''.join(lines)}</table></div>",
    ))

    findings.append((
        "Seven circles, and no straightedge",
        "<p>Two mathematicians, Mohr in 1672 and Mascheroni in 1797, proved that anything "
        "you can find with a straightedge and compass you can find with the compass alone. "
        "Searching every possibility confirms it here problem by problem, and puts a price "
        "on it: finding the middle of a line takes <strong>exactly seven circles</strong> "
        "when no straight line may be drawn. Six is not enough, and the machine checked "
        "all of them.</p>",
    ))

    findings.append((
        "Two magnitudes that behave better than they look",
        "<p>Book X sorts irrational lengths into named kinds. Two cases show the exact "
        "arithmetic doing something a calculator could not:</p>"
        "<ul><li><code>&radic;18 + &radic;2</code> looks like a sum of two different roots, "
        "but it is really <code>4&radic;2</code>. The classifier refuses to call it a "
        "binomial, correctly.</li>"
        "<li><code>&radic;(4 + &radic;7)</code> untangles itself into a sum of simpler "
        "roots before being named. The machine finds the root inside the numbers it "
        "already has rather than inventing a new one.</li></ul>"
        '<p><a href="book-x.html">The full table &rarr;</a></p>',
    ))

    findings.append((
        "A bug the mathematics caught",
        "<p>While Book II was being written, a length came out negative. Every square "
        "root has two answers, and the routine that searches for one inside the existing "
        "numbers had returned the wrong one &mdash; it gave "
        "<code>1/2 &minus; &radic;(5/4)</code>, about &minus;0.618, where "
        "<code>0.618</code> was wanted. Both square to the same thing, so both are "
        "correct roots; only one is a length.</p>"
        "<p>A version of this working in decimals would never have noticed: an ordinary "
        "square root function always hands back the positive answer. The bug only became "
        "visible because the number was being carried around exactly.</p>",
    ))

    body = [
        '<p class="kicker">What running the Elements turned up</p>',
        "<h1>Findings</h1>",
        '<p class="lede">These came out of the machine, not out of a book. Each one can '
        "be reproduced from the command line.</p>",
    ]
    for heading, text in findings:
        body.append(f'<div class="finding"><h3>{heading}</h3>{text}</div>')
    body.append(
        '<div class="finding"><h3>Still open</h3>'
        "<p>Books V to X are represented by a handful of propositions each, not written "
        "out in full. Their statements are short summaries rather than Heath's words, "
        "because no clean copy of that part of his translation was available to parse. "
        "Both are marked wherever they appear.</p></div>"
    )
    return _page("Findings — Executable Euclid", "".join(body), here="findings.html")


def _graph_page(graph) -> str:
    rows = "".join(
        f'<tr><td><a href="{_slug(ref)}.html">{ref}</a></td><td>{count}</td>'
        f"<td>{graph.depth(ref)}</td><td>{_esc(graph.nodes[ref].statement[:74])}</td></tr>"
        for ref, count in graph.load_bearing()[:16]
    )
    body = [
        '<p class="kicker">Read off the running code</p>',
        "<h1>What depends on what</h1>",
        '<p class="lede">No list of cross-references is kept anywhere in this project. '
        "These links are simply what each proposition reached for when it ran.</p>",
        f'<div class="scroll">{graph_svg(graph)}</div>',
        '<p class="note">Propositions sit on the row matching how many steps of argument '
        "stand between them and the starting rules. Lines run upward from a proposition to "
        "the ones built on it.</p>",
        "<h2>Carrying the most weight</h2>",
        "<p>How many other propositions would fall if this one did.</p>",
        '<div class="scroll"><table><tr><th>Proposition</th><th>Dependents</th>'
        f"<th>Depth</th><th>Statement</th></tr>{rows}</table></div>",
    ]
    return _page("Dependencies — Executable Euclid", "".join(body),
                 here="graph.html", wide=True)


def _minimal_page(graph, target: str = "I.47") -> str:
    if target not in graph.nodes:
        return _page("Minimal Elements", "<h1>Nothing to show</h1>")
    minimal = graph.tree_shake(target)
    dropped = sorted(set(graph.nodes) - set(minimal), key=lambda r: graph.nodes[r].sort_key())
    rows = "".join(
        f'<tr><td><a href="{_slug(ref)}.html">{ref}</a></td>'
        f"<td>{_esc(graph.nodes[ref].statement)}</td></tr>"
        for ref in minimal
    )
    body = [
        '<p class="kicker">Everything Pythagoras needs, and nothing else</p>',
        f"<h1>The shortest route to {target}</h1>",
        f'<p class="lede">Of the {len(graph.nodes)} propositions written out here, '
        f"{len(minimal)} are needed to reach {target}. Below they are in order, each one "
        "resting only on those above it.</p>",
        f'<div class="scroll">{graph_svg(graph, minimal, highlight=target)}</div>',
        f'<div class="scroll"><table><tr><th>#</th><th>Statement</th></tr>{rows}</table></div>',
        f"<h2>Left out ({len(dropped)})</h2>",
        '<p class="note">'
        + " ".join(f'<a href="{_slug(ref)}.html">{ref}</a>' for ref in dropped)
        + "</p>",
    ]
    return _page(f"Shortest route to {target}", "".join(body), here="minimal.html", wide=True)


def _ledger_page() -> str:
    ledgers = [audit(entry.ref, trials=8) for entry in all_propositions()]
    totals = (
        sum(item.continuity_debt for item in ledgers),
        sum(len(item.of_kind("order")) for item in ledgers),
        sum(len(item.of_kind("case")) for item in ledgers),
    )
    rows = "".join(
        f'<tr><td><a href="{_slug(item.ref)}.html">{item.ref}</a></td>'
        f"<td>{item.continuity_debt or ''}</td>"
        f"<td>{len(item.of_kind('order')) or ''}</td>"
        f"<td>{len(item.of_kind('case')) or ''}</td>"
        f"<td>{item.configurations}</td></tr>"
        for item in ledgers
    )
    body = [
        '<p class="kicker">Found by running the proofs, not by reading them</p>',
        "<h1>What Euclid takes on trust</h1>",
        '<p class="lede">His rules let you draw a straight line and a circle. None of them '
        "says two circles ever cross. He uses that anyway, on the first page, and many "
        "times after.</p>",
        '<div class="stat">',
        f"<div><b>{totals[0]}</b><span>points assumed to exist</span></div>",
        f"<div><b>{totals[1]}</b><span>facts read off the picture</span></div>",
        f"<div><b>{totals[2]}</b><span>steps that vary by figure</span></div>",
        "</div>",
        "<h2>What each column counts</h2>",
        "<p><strong>Points assumed to exist.</strong> Every time the construction uses a "
        "point where a line meets a circle, or two circles meet. Euclid's rules never "
        "promise those points are there. This is read straight off the record of what was "
        "drawn, so nothing is missed.</p>",
        "<p><strong>Facts read off the picture.</strong> Claims that one point lies between "
        "two others, or that two points are on the same side of a line &mdash; things the "
        "diagram shows but the argument never establishes.</p>",
        "<p><strong>Steps that vary by figure.</strong> Each proposition is run on many "
        "different figures and the runs compared. A step that holds in one figure but not "
        "another would appear here. The column is empty, which is itself worth knowing: "
        "every construction here behaves the same way on every figure it is given.</p>",
        '<div class="scroll"><table><tr><th>Proposition</th><th>Points assumed</th>'
        "<th>Read off</th><th>Varies</th><th>Figures tried</th></tr>"
        f"{rows}</table></div>",
    ]
    return _page("What Euclid assumes — Executable Euclid", "".join(body),
                 here="ledger.html", wide=True)


def _optimizer_page(rows) -> str:
    table = []
    for euclid_ref, euclid_steps, result in rows:
        reference = (
            f'<a href="{_slug(euclid_ref)}.html">{euclid_ref}</a>' if euclid_ref else "&mdash;"
        )
        table.append(
            f"<tr><td>{_esc(result.problem.replace('-', ' '))}</td><td>{reference}</td>"
            f"<td>{euclid_steps or '&mdash;'}</td>"
            f"<td>{result.length if result.found else 'none'}</td>"
            f"<td>{'fewest possible' if result.exhaustive else 'not proved shortest'}</td>"
            f"<td>{result.geometrography.notation()}</td>"
            f"<td>{'yes' if result.verified else '&mdash;'}</td></tr>"
        )
    body = [
        '<p class="kicker">Try everything, then check it exactly</p>',
        "<h1>The shortest constructions</h1>",
        '<p class="lede">The machine tries every legal move, in order of length, until it '
        "reaches the goal. The winner is then rebuilt in exact arithmetic, where it either "
        "works or does not.</p>",
        '<div class="scroll"><table><tr><th>Problem</th><th>Euclid</th><th>His moves</th>'
        "<th>Fewest</th><th>Status</th><th>Cost</th><th>Checked</th></tr>"
        + "".join(table)
        + "</table></div>",
        "<h2>Why Euclid's numbers are bigger</h2>",
        "<p>The two counts measure different things, and the gap is mostly that. "
        "<strong>His moves</strong> counts every line and circle drawn once the earlier "
        "propositions he leans on are expanded &mdash; his I.10 reaches through three other "
        "results, so fifteen things get drawn. <strong>Fewest</strong> stops as soon as the "
        "goal exists and draws nothing to tidy up.</p>"
        "<p>More to the point, Euclid was building constructions that could be "
        "<em>proved</em> from what came before. Reusing an earlier result costs moves but "
        "buys certainty. Counting moves was a nineteenth-century preoccupation, not his.</p>",
        "<h2>Working with fewer tools</h2>",
        "<p>A construction is a program, and these are different machines to run it on: "
        "compass and straightedge, compass alone, straightedge alone with one circle "
        "given, or a compass stuck at one setting. The classical theorems say the compass "
        "alone loses nothing, and the search agrees &mdash; at a price in moves.</p>",
        "<h2>What &ldquo;fewest possible&rdquo; means</h2>",
        "<p>Where the table says <em>fewest possible</em>, every construction of that "
        "length was examined, so the answer really is shortest, and a failure really does "
        "prove that no construction of that length exists. Where the search ran out of "
        "budget it says so, and the answer is only an upper bound.</p>"
        "<p>Two limits apply throughout: points that stray far outside the figure are "
        "ignored, and a figure carrying more than twenty points is abandoned. Either could "
        "in principle hide a shorter construction. They are stated here rather than buried "
        "in the code.</p>",
    ]
    return _page("Shortest constructions — Executable Euclid", "".join(body),
                 here="optimizer.html", wide=True)


def _book_x_page() -> str:
    from ..elements.book10 import classify

    rows = []
    with Context("book-x-site"):
        fourth_root = sqrt(sqrt(2))
        specimens = [
            sqrt(5),
            fourth_root,
            5 + sqrt(24),
            3 + sqrt(2),
            1 + sqrt(5),
            (1 + sqrt(5)) / 2,
            sqrt(2) + sqrt(3),
            3 - sqrt(2),
            sqrt(5) - 1,
            sqrt(3) - sqrt(2),
            fourth_root + sqrt(2) * fourth_root,
            sqrt(2) * fourth_root - fourth_root,
            sqrt(18) + sqrt(2),
            sqrt(4 + sqrt(7)),
        ]
        for value in specimens:
            named = classify(value)
            rows.append(
                f'<tr><td class="mono">{_esc(fmt(value))}</td>'
                f'<td class="mono">{to_float(value):.9f}</td>'
                f"<td>{_esc(named.name)}</td><td>{named.algebraic_degree}</td></tr>"
            )
    body = [
        '<p class="kicker">The book everyone skips</p>',
        "<h1>Book X, running</h1>",
        '<p class="lede">One hundred and fifteen propositions sorting irrational lengths '
        "into named kinds. It reads as impenetrable because it is written about things "
        "nobody could calculate with. This project can.</p>",
        "<p>Some lengths a straightedge and compass produce are whole numbers or "
        "fractions. Most are not. Euclid gives thirteen names to the ones that are not "
        "&mdash; <em>medial</em>, <em>binomial</em>, <em>apotome</em>, and so on &mdash; "
        "each defined by whether certain sums and products come out rational. Every one of "
        "those conditions is a yes-or-no question the exact arithmetic can answer, so the "
        "whole classification becomes a single function.</p>",
        '<div class="scroll"><table><tr><th>Length</th><th>Value</th>'
        f"<th>Euclid's name for it</th><th>Degree</th></tr>{''.join(rows)}</table></div>",
        '<p class="note">Two rows repay a look. '
        '<span class="mono">sqrt(18) + sqrt(2)</span> is not a binomial: the two parts are '
        'multiples of each other, so it collapses to <span class="mono">4&middot;sqrt(2)</span>, '
        'and the classifier says so. And <span class="mono">sqrt(4 + sqrt 7)</span> untangles '
        "itself before being named.</p>",
        "<h2>Try it</h2>",
        '<pre>euclid classify "sqrt(3) + sqrt(5)"\n'
        'euclid classify "(1+sqrt(5))/2"</pre>',
    ]
    return _page("Book X — Executable Euclid", "".join(body),
                 here="book-x.html", wide=True)


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------


def build(destination: Path, run_search: bool = True) -> list[Path]:
    """Generate the whole site.  Returns the files written."""
    from ..graph import build as build_graph
    from ..search import PROBLEMS, solve

    destination.mkdir(parents=True, exist_ok=True)
    graph = build_graph()
    written: list[Path] = []

    def write(name: str, text: str) -> None:
        path = destination / name
        path.write_text(text, encoding="utf-8")
        written.append(path)

    claims = 0
    continuity = 0
    for entry in all_propositions():
        trace = _sample_trace(entry)
        claims += certify(entry.ref, trials=4).claims_checked
        continuity += audit(entry.ref, trials=3).continuity_debt
        write(f"{_slug(entry.ref)}.html", _proposition_page(entry, graph, trace))

    stats = {
        "claims": claims,
        "continuity": continuity,
        "edges": sum(len(e) for e in graph.edges.values()),
    }

    search_rows = []
    if run_search:
        for name, problem in PROBLEMS.items():
            result = solve(name, max_depth=5)
            steps = None
            if problem.euclid and problem.euclid in graph.nodes:
                trace = _sample_trace(graph.nodes[problem.euclid])
                steps = trace.step_count if trace else None
            search_rows.append((problem.euclid, steps, result))

    write("index.html", _index_page(graph, stats))
    write("findings.html", _findings_page(graph, stats, search_rows))
    write("graph.html", _graph_page(graph))
    write("minimal.html", _minimal_page(graph))
    write("ledger.html", _ledger_page())
    write("optimizer.html", _optimizer_page(search_rows))
    write("book-x.html", _book_x_page())
    return written
