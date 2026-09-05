"""How a page looks: the stylesheet, the navigation, and the shell
every page is poured into.

The palette is three colours and no opacity, and one width token
governs every column, so a page cannot drift from the others by
being written later.
"""

from __future__ import annotations

import html
from ..elements.registry import HEATH_CREDIT


# Three colours and no more: black, white, and one grey exactly halfway
# between them. The two themes swap black and white; the grey never moves.
# Nothing here uses a fill or an opacity that would manufacture a fourth shade.
STYLE = """
:root { --ink: #000000; --page: #ffffff; --grey: #808080;
        --column: min(94vw, 84rem); }
@media (prefers-color-scheme: dark) {
  :root { --ink: #ffffff; --page: #000000; }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--page); color: var(--ink);
  font: 18px/1.66 Georgia, 'Iowan Old Style', 'Palatino Linotype', serif;
}
/* One width, and everything uses it: the nav, the prose, the tables, the
   diagrams. There used to be two -- a narrow column for prose and a wide one
   for tables -- which left paragraphs wrapping short inside a container three
   times their width. That reads as hard-wrapped text with the margins to match,
   and no amount of tuning the two numbers fixes it. So there is one number. */
.wrap { max-width: var(--column); margin: 0 auto; padding: 2rem 1.5rem 6rem; }
.bar { border-bottom: 1px solid var(--grey); margin-bottom: 2.4rem; }
.bar > nav { max-width: var(--column); margin: 0 auto; padding: 1.1rem 1.5rem .9rem; }
a { color: inherit; text-decoration: underline; text-decoration-thickness: 1px;
    text-underline-offset: 3px; }
a:hover { text-decoration-thickness: 2px; }
h1 { font-size: 1.95rem; line-height: 1.22; margin: 0 0 .5rem; font-weight: normal;
     letter-spacing: -.01em; }
h2 { font-size: 1.22rem; font-weight: normal; margin: 2.8rem 0 .8rem;
     border-bottom: 1px solid var(--grey); padding-bottom: .35rem; }
h2 .section-definition { font-size: inherit; color: var(--ink); letter-spacing: 0; }
h3 { font-size: 1rem; margin: 1.9rem 0 .5rem; font-weight: 700; }
.kicker { font: 700 .68rem/1 ui-sans-serif, system-ui, sans-serif;
  letter-spacing: .16em; text-transform: uppercase; color: var(--grey);
  margin: 0 0 .8rem; }
.lede { color: var(--grey); font-size: 1.05rem; margin: .2rem 0 2rem; }
nav.top { font: .85rem/1.9 ui-sans-serif, system-ui, sans-serif;
          display: flex; flex-wrap: wrap; gap: 0 1.35rem; }
nav.top a { text-decoration: none; color: var(--grey); white-space: nowrap; }
nav.top a:hover, nav.top a.here { color: var(--ink); text-decoration: underline; }
code, pre, .mono { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
pre { border: 1px solid var(--grey); padding: .95rem 1.05rem; overflow-x: auto;
      font-size: .82rem; line-height: 1.6; }
code { font-size: .88em; }
table { border-collapse: collapse; width: 100%; font-size: .92rem; }
th, td { text-align: left; padding: .5rem .7rem; border-bottom: 1px solid var(--grey);
         vertical-align: top; }
th { font: 700 .72rem/1.5 ui-sans-serif, system-ui, sans-serif;
     letter-spacing: .09em; text-transform: uppercase; color: var(--grey); }
/* Columns that are mostly empty read as a broken table rather than a sparse
   one, so the numeric ones are narrow and centred and rows with nothing in
   them are not emitted at all. See _ledger_page. */
td.tally, th.tally { text-align: center; width: 8.5rem; }
tbody tr:last-child td { border-bottom: none; }
.scroll { overflow-x: auto; }
figure { margin: 1.8rem 0; text-align: center; }
figcaption { font: .78rem ui-sans-serif, system-ui, sans-serif; color: var(--grey);
             margin-top: .6rem; }
svg.figure { max-width: 100%; height: auto; border: 1px solid var(--grey); }
svg.figure .arc { stroke: var(--grey); stroke-width: 1; stroke-dasharray: 3 3; }
svg.figure .ray { stroke: var(--ink); stroke-width: 1.4; }
svg.figure .dot { fill: var(--ink); }
svg.figure .letter { fill: var(--ink); font: italic 14px Georgia, serif; }
svg.figure .ray.aside { stroke: var(--grey); stroke-width: .7; }
svg.figure .arc.aside { stroke: var(--grey); stroke-width: .6; stroke-dasharray: 2 4; }
svg.figure .dot.aside { fill: var(--grey); }
/* The full graph is 10,000px wide. Fitting it to the page renders an 11px
   label at one pixel, which is why it read as a smear. It keeps its natural
   size and the box scrolls; a graph that already fits is centred and does not.
   Centring with flex would make the left edge of a 10,000px graph unreachable:
   an overflowing flex item cannot be scrolled back to. Auto margins centre a
   graph that fits and collapse to zero for one that does not. */
.plot { overflow: auto; border: 1px solid var(--grey); max-height: 78vh;
        padding: .5rem; }
.plot svg.graph { display: block; margin: 0 auto; }
svg.graph { height: auto; }
svg.graph .edge { fill: none; stroke: var(--grey); stroke-width: 1.1; }
svg.graph .edge.cited { stroke-dasharray: 3 3; }
svg.graph .edge.lit { stroke: var(--ink); stroke-width: 1.7; }
svg.graph .node { fill: var(--page); stroke: var(--grey); }
svg.graph .node.lit { fill: var(--ink); }
svg.graph .node-label { font: 11px ui-monospace, monospace; fill: var(--ink); }
svg.graph .node.lit + .node-label { fill: var(--page); }
svg.graph a:hover .node { stroke: var(--ink); stroke-width: 1.6; }
ul.claims { list-style: none; padding: 0; margin: 1rem 0; }
ul.claims li { padding: .5rem 0 .5rem 1rem; border-left: 2px solid var(--ink);
               margin-bottom: .3rem; }
ul.claims li.hyp { border-left: 2px solid var(--grey); }
.cite { font: .7rem ui-sans-serif, system-ui, sans-serif; color: var(--grey);
        display: block; margin-top: .2rem; letter-spacing: .02em; }
.grid { display: grid; gap: .25rem .9rem;
        grid-template-columns: repeat(auto-fill, minmax(4.6rem, 1fr)); }
.grid a { display: block; padding: .18rem 0; font-size: .88rem;
          font-family: ui-monospace, monospace; text-decoration: none;
          border-bottom: 1px solid transparent; }
.grid a:hover { border-bottom-color: var(--ink); }
.stat { display: grid; grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
        gap: 0; margin: 1.8rem 0; border: 1px solid var(--grey); }
.stat div { padding: .9rem 1rem; border-right: 1px solid var(--grey); }
.stat div:last-child { border-right: none; }
.stat b { display: block; font: 400 1.6rem/1.15 Georgia, serif; }
.stat span { font: .68rem ui-sans-serif, system-ui, sans-serif; color: var(--grey);
             letter-spacing: .05em; text-transform: uppercase; }
blockquote { margin: 0 0 1.2rem; padding: .2rem 0 .2rem 1.1rem;
             border-left: 3px solid var(--ink); font-size: 1.06rem; }
blockquote .src { display: block; font: .7rem ui-sans-serif, system-ui, sans-serif;
                  color: var(--grey); margin-top: .55rem; letter-spacing: .04em;
                  text-transform: uppercase; }
.note { color: var(--grey); font-size: .95rem; }
.finding { padding-top: 1.1rem; margin-top: 1.8rem; }
.finding h3 { margin-top: 0; }
.legend { font: .78rem/1.6 ui-sans-serif, system-ui, sans-serif; color: var(--grey);
          display: flex; flex-wrap: wrap; gap: .3rem 1.6rem; margin: .7rem 0 0; }
.legend span { display: inline-flex; align-items: center; gap: .45rem; }
.legend i { display: inline-block; width: 2.2rem; height: 0; font-style: normal;
            border-top: 2px solid var(--grey); }
.legend i.dash { border-top-style: dashed; }
footer { margin-top: 4.5rem; padding-top: 1rem; border-top: 1px solid var(--grey);
         font: .82rem/1.7 ui-sans-serif, system-ui, sans-serif; color: var(--grey); }
"""


NAV = [
    ("index.html", "Overview"),
    ("findings.html", "Findings"),
    ("graph.html", "Dependencies"),
    ("minimal.html", "Minimal Elements"),
    ("ledger.html", "What Euclid assumes"),
    ("optimizer.html", "Shortest constructions"),
    ("book-x.html", "Book X"),
    ("text.html", "Text and figures"),
]


def _esc(text) -> str:
    return html.escape(str(text), quote=False)


def _slug(ref: str) -> str:
    return ref.replace(".", "-")


def _page(title: str, body: str, here: str = "") -> str:
    links = "".join(
        '<a href="{}"{}>{}</a>'.format(href, ' class="here"' if href == here else "", label)
        for href, label in NAV
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_esc(title)}</title>"
        # One stylesheet, fetched once and cached, rather than the same 5 KB
        # inlined into all 398 pages. That was 61% of everything shipped, and it
        # meant a one-line CSS change rewrote every file in docs/.
        '<link rel="stylesheet" href="style.css">'
        "</head><body>"
        f'<div class="bar"><nav class="top">{links}</nav></div>'
        '<div class="wrap">'
        f"{body}"
        "<footer><p>The diagrams record constructions that ran, so they do not resemble "
        "Euclid's composed figures. A cross-reference is either a call that was recorded "
        "as it happened or a name written beside the step by hand. "
        '<a href="graph.html">Which is which &rarr;</a></p>'
        f"<p>Every proposition statement here is {HEATH_CREDIT} "
        '<a href="text.html">Where the text comes from &rarr;</a></p></footer>'
        "</div></body></html>"
    )
